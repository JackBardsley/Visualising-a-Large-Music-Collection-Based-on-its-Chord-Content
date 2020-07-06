import pyspark.sql.functions as F
from pyspark.sql.types import ArrayType,StringType
from pyspark.ml.fpm import FPGrowth
from collections import Counter
from itertools import combinations,chain
from operator import add

class ChordLoader:
    """
    Load chord data into a spark dataframe and apply some preprocessing to extract chord values
    
    Parameters
    ----------
    spark : SparkSession
        The spark session object
    limit : int, optional
        Limit the number of documents loaded from mongodb source

    """
    def __init__(self,spark,limit=None):
        self.limit = limit
        self.spark = spark
        self.df = self._load_data()

    def _load_data(self):
        """
        Loads data from mongodb source and extracts non zero chord values

        Returns
        -------
        pyspark.sql.DataFrame
            In the form:
                +---+--------------------+
                |_id|          chordItems|
                +---+--------------------+
                |214|[Bbmin7, Emin7, B...|
                |215|[Emaj, A7, Gmin, ...|
                |216|[Emaj, Dbmin7, Gb...|
                |217|[Ab7, F7, Abmaj, ...|
                |218|[Emaj, Dbmin7, Ab...|
                |219|[Emaj, Bbmin7, Em...|
                |220|[Emin7, Bmaj, Dbm...|

        """
        # Load data from mongodb source
        if self.limit:
            df = self.spark.read.format("mongo").option('database', 'jamendo').option('collection', 'chords').load().limit(self.limit)
        else:
            df = self.spark.read.format("mongo").option('database', 'jamendo').option('collection', 'chords').load()

        # Times out without this? 
        df = df.sample(withReplacement=False,fraction=1.0)

        # User defined function to get key values (chords) from nested structure in dataframe
        getKeysUDF = F.udf(lambda x: list({k for k,v in x.asDict().items() if type(v) is float}),ArrayType(StringType()))

        # Apply UDF and select only chord and id cols
        return df.withColumn("chordItems",getKeysUDF(df['chordRatio'])).select("_id","chordItems")


class SparkFrequentItemsetsFPG(ChordLoader):
    """
    Apply FPGrowth frequent itemset mining algorithm from Spark ML lib to chord data

    Parameters
    ----------
    spark : SparkSession
        The spark session object
    limit : int, optional
        Limit the number of documents loaded from mongodb source
    params : dict, optional
        Parameter key/value pairs for minSupport (the algorithms support threshold) and 
        minConfidence (for generating association rules, can ignore here as we are only 
        interested in generating frequent itemsets)

    """

    def __init__(self,spark,limit=None,params={"minSupport":0.2, "minConfidence":0.5}):
        ChordLoader.__init__(self,spark,limit)
        self.params = params

    def _run_FPGrowth(self,df):
        # Apply spark ml libs FP-growth algorithm for frequent itemset mining
        fpGrowth = FPGrowth(itemsCol="chordItems", minSupport = self.params["minSupport"], minConfidence=self.params["minConfidence"])
        model = fpGrowth.fit(df)
        return model

    def get_itemsets(self):
        n_items = self.df.count()
        self.model = self._run_FPGrowth(self.df)
        # Add support % val
        itemsets = self.model.freqItemsets.withColumn("supportPc",self.model.freqItemsets['freq']/n_items)
        return itemsets.toPandas()


class SparkFrequentItemsetsSON(ChordLoader):
    """
    Implementation of the SON algorithm - 
    
    "Savasere, A., Omiecinski, E. & Navathe, S. B., 1995. 
    An Efficient Algorithm for Mining Association Rules in Large Databases. s.l., 
    Proceedings of the 21st International Conference on Very Large Data Bases."

    Parameters
    ----------
    spark : SparkSession
        The spark session object
    limit : int, optional
        Limit the number of documents loaded from mongodb source
    params : dict, optional
        Parameter key/value pairs for minSupport (the algorithms support threshold) and 
        minConfidence (for generating association rules, can ignore here as we are only 
        interested in generating frequent itemsets)


    """
    def __init__(self,spark,limit=None,params={"minSupport":0.2}):
        ChordLoader.__init__(self,spark,limit)
        self.params = params


    def get_itemsets(self):
        """
            MapReduce calculation of frequent itemsets

            Returns
            -------
            frequent_itemsets : list[tuple]
                Key value pairs of frequent itemsets with support value
        """
        # Apriori algorithm implementation for frequent itemsets
        def apriori(part,support):
            frequent_itemsets = []
            # Init combination length
            n = 1
            # Get chord from spark Row items
            part = [row['chordItems'] for row in part]
            while(True):
                # Init counter
                cnt = Counter()
                # Iterate over items in RDD
                for row in part:
                    # Count combinations
                    for comb in combinations(row,n):
                        cnt[comb] += 1
                # Filter by support value threshold
                k_fi = [(k,v) for k,v in cnt.items() if v > support]
                # Filter data
                # Get keys from filtered k length frequent itemsets
                item_keys = [k[0] for k in k_fi]
                item_set = set(chain(*item_keys))
                # Filter out items not in frequent itemsets
                part = [list(set(row).intersection(item_set)) for row in part]
                # Remove items with length 0
                part = list(filter(lambda x: len(x)>0,part))
                # If frequent sets still present add to fi list else break
                if len(part) > 0:
                    frequent_itemsets += k_fi
                    n += 1
                else:
                    break
            return frequent_itemsets

        # Convert dataframe to rdd
        chord_rdd = self.df.select(self.df['chordItems']).rdd
        print(f"N Partitions: {chord_rdd.getNumPartitions()}")
        # Support threshold determined by no. partitions
        s = self.params['minSupport']*chord_rdd.count()
        ps = s/chord_rdd.getNumPartitions()
        # 1st map function, generate candidate itemsets
        itemset_kv = dict(chord_rdd.mapPartitions(lambda x: apriori(x,ps)).reduceByKey(add).map(lambda x: (x[0],0)).collect())

        def count_sets(part,sets):
            for row in part:
                row = row['chordItems']
                for freq_set in sets:
                    if set(freq_set).issubset(set(row)):
                        sets[freq_set] += 1
            return sets.items()

        # Count the sets present in data from candidate list
        frequent_itemsets = chord_rdd.mapPartitions(lambda x: count_sets(x,itemset_kv)) \
                                     .reduceByKey(add)
        # Filter by min support value
        frequent_itemsets = frequent_itemsets.filter(lambda x: x[1]>s)

        return frequent_itemsets.collect()
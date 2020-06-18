import os
import findspark
import pyspark
import pyspark.sql.functions as F
from pyspark.sql.types import ArrayType,StringType,DataType
from pyspark.ml.fpm import FPGrowth
from time import time

os.environ['PYSPARK_SUBMIT_ARGS'] = '"--packages" "org.mongodb.spark:mongo-spark-connector_2.11:2.4.1" "pyspark-shell"'

findspark.init()

# Spark context
sc = pyspark.SparkContext.getOrCreate()
spark = pyspark.sql.SparkSession.builder \
    .config("spark.mongodb.input.uri", os.environ['MSC_CHORD_DB_URI'])\
    .getOrCreate()

# Load data from mongodb source
df = spark.read.format("mongo").option('database', 'jamendo').option('collection', 'chords').load()

# User defined function to get key values (chords) from nested structure in dataframe
getKeysUDF = F.udf(lambda x: list({k for k,v in x.asDict().items() if type(v) is float}),ArrayType(StringType()))

# Apply UDF and select only chord and id cols
df_chord_items = df.withColumn("chordItems",getKeysUDF(df['chordRatio'])).select("_id","chordItems")


startTime = time()
# Apply spark ml libs FP-growth algorithm for frequent itemset mining
fpGrowth = FPGrowth(itemsCol="chordItems", minSupport=0.2, minConfidence=1)
model = fpGrowth.fit(df_chord_items)

# Display frequent itemsets
print(model.freqItemsets.show())
print(f"Time elapsed: {startTime-time()}")


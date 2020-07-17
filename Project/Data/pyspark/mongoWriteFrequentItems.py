"""
Write itemset data to mongodb collection to be used by the API.
"""

from pymongo import MongoClient
import os
import json

with MongoClient(os.environ['MSC_MONGO_PERSONAL_URI']) as client:
    col = client.jamendo.itemsetData
    with open("Project/Data/pyspark/itemsets.json", "r") as filename:
        data = json.load(filename)
        for d in data:
            col.update_one({"_id": d['_id']}, {"$set":
                                               {"filter_params": d['filter_params'],
                                               "fi_params": d['fi_params'],
                                               "itemsets": d['itemsets'],
                                               "AVSDF_order": d["AVSDF_order"]
                                                }}, upsert=True)

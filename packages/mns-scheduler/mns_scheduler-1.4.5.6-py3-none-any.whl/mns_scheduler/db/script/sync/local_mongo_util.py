import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import pymongo
from mns_common.utils.async_fun import async_fun
from loguru import logger
import warnings

warnings.filterwarnings("ignore")


class LocalMongodbUtil:
    def __init__(self, port):
        self.port = port

    def get_db(self):
        client = pymongo.MongoClient("mongodb://127.0.0.1:" + '27017' + "/patience")
        return client.patience

    def group(self, query, coll_name):
        db = self.get_db()
        collection = db[coll_name]
        data = collection.aggregate(query)
        return pd.DataFrame(list(data))

    def remove_data(self, query, coll_name):
        db = self.get_db()
        collection = db[coll_name]
        return collection.delete_many(query)

    def exist_data_query(self, coll_name, query):
        db = self.get_db()
        collection = db[coll_name]
        return collection.count(query, limit=1) > 0

    def find_one(self, coll_name, _id):
        db = self.get_db()
        collection = db[coll_name]
        return collection.find_one({'_id': _id})

    def find_one_query(self, coll_name, query):
        db = self.get_db()
        collection = db[coll_name]
        return pd.DataFrame(collection.find_one(query), index=[0])

    def find_all_data(self, coll_name):
        db = self.get_db()
        collection = db[coll_name]
        rows = collection.find({})
        df = pd.DataFrame([basic for basic in rows])
        return df

    def find_query_data(self, coll_name, query):
        db = self.get_db()
        collection = db[coll_name]
        rows = collection.find(query)
        df = pd.DataFrame(list(rows))
        return df

    def find_query_data_choose_field(self, coll_name, query, query_field):
        db = self.get_db()
        collection = db[coll_name]
        rows = collection.find(query, query_field)
        df = pd.DataFrame(list(rows))
        return df

    def find_query_data_list(self, coll_name, query):
        db = self.get_db()
        collection = db[coll_name]
        rows = collection.find(query)
        return list(rows)

    def find_query_data_list(self, coll_name, query):
        db = self.get_db()
        collection = db[coll_name]
        rows = collection.find(query)
        return list(rows)

    def remove_all_data(self, database):
        db = self.get_db()
        collection = db[database]
        query = {"_id": {"$ne": "null"}}
        return collection.delete_many(query)

    def drop_collection(self, database):
        db = self.get_db()
        collection = db[database]
        collection.drop()

    def ascend_query(self, query, coll_name, field, num):
        db = self.get_db()
        collection = db[coll_name]
        return pd.DataFrame(list(collection.find(query).sort(field, 1).skip(0).limit(num)));

    def descend_query(self, query, coll_name, field, num):
        db = self.get_db()
        collection = db[coll_name]
        return pd.DataFrame(list(collection.find(query).sort(field, -1).skip(0).limit(num)));

    def count(self, query, coll_name):
        db = self.get_db()
        collection = db[coll_name]
        return collection.count_documents(query)

    def query_max(self, query, coll_name, field, num):
        db = self.get_db()
        collection = db[coll_name]
        return pd.DataFrame(list(collection.find(query).sort(field, -1).skip(0).limit(num)));

    def query_min(self, query, coll_name, field):
        db = self.get_db()
        collection = db[coll_name]
        return pd.DataFrame(list(collection.find(query).sort(field, 1).skip(0).limit(1)));

    def insert_mongo(self, df, database):
        db = self.get_db()
        if df is None or len(df) == 0:
            return
        collection = db[database]
        # 格式转换
        try:
            df = df.drop_duplicates()
            # df = df.T.drop_duplicates().T
            records = df.to_dict('records')
            collection.insert_many(records)
        except BaseException as e:
            logger.error("插入数据异常:{}", e)

    def insert_mongo_json(self, json, database):
        db = self.get_db()
        collection = db[database]
        # 格式转换
        try:
            collection.insert_many(json)
        except BaseException as e:
            logger.error("插入数据异常:{}", e)

    def save_mongo_json(self, json, database):
        db = self.get_db()
        collection = db[database]
        for record in json:
            try:
                collection.save(record)
            except BaseException as e:
                logger.error("保存数据出现异常:{}", e)

    def save_mongo(self, df, database):
        db = self.get_db()
        if df is None or len(df) == 0:
            return
        collection = db[database]
        # df = df.T.drop_duplicates().T
        # 格式转换
        records = df.to_dict('records')
        for record in records:
            try:
                collection.save(record)
            except BaseException as e:
                logger.error("保存数据出现异常:{},{}", record, e)

    def save_mongo_no_catch_exception(self, df, database):
        db = self.get_db()
        if df is None or len(df) == 0:
            return
        collection = db[database]
        # df = df.T.drop_duplicates().T
        # 格式转换
        records = df.to_dict('records')
        for record in records:
            collection.save(record)

    def update_one(self, df, database):
        db = self.get_db()
        condition = {'_id': list(df['_id'])[0]}
        if len(df) == 0:
            return
        collection = db[database]
        collection.update(condition, df)

    def update_many(self, query, new_values, database):
        db = self.get_db()
        collection = db[database]
        x = collection.update_many(query, new_values)
        return x

    @async_fun
    def update_one_query(self, query, new_values, database):
        db = self.get_db()
        collection = db[database]
        x = collection.update(query, new_values)
        return x

    def distinct_field(self, database, field, query):
        db = self.get_db()
        collection = db[database]
        return collection.distinct(field, query)

    def create_index(self, database, index):
        db = self.get_db()
        collection = db[database]
        collection.create_index(
            index)

    def aggregate(self, pipeline, database):
        db = self.get_db()
        collection = db[database]
        data = collection.aggregate(pipeline)
        return pd.DataFrame(list(data))

    def get_col_keys(self, database):
        db = self.get_db()
        collection = db[database]
        keys = collection.find_one().keys()
        return keys

    # 分页查询 descend 是否降序
    def find_page_skip_data(self, coll_name, page_query, page, page_number, field, descend):
        db = self.get_db()
        collection = db[coll_name]
        if descend:
            sort_tag = -1
        else:
            sort_tag = 1
        rows = collection.find(page_query).sort(field, sort_tag).skip((page - 1) * page_number).limit(page_number)
        df = pd.DataFrame(list(rows))
        return df

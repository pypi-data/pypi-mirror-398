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


class RemoteMongodbUtil:
    def __init__(self, port):
        self.port = port

    def get_db(self):
        client = pymongo.MongoClient("mongodb://100.87.2.149:" + '27017' + "/patience")
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
        collection.delete_many(query)

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


# if __name__ == '__main__':
#     symbol = '002992'
#     query = {'symbol': symbol,
#              '$and': [{'str_day': {'$gte': '2022-07-06'}}, {'str_day': {'$lte': '2022-11-06'}}]}
#     mongodb_util = MongodbUtil('27017')
#     # num = mongodb_util.count(query, 'stock_zt_pool')
#     # print(num)
#     key = mongodb_util.get_col_keys('stock_zt_pool')
#     print(key)
#
#     # num = mongodb_util.count(query, 'stock_zt_pool')
#     # print(num)
#
#     pipeline = [
#         {'$match': {
#             "classification": {'$in': ["K", "C"]},
#             "str_day": {'$gte': "2022-03-16"}}},
#         {'$group': {'_id': "$flow_mv_level", 'count': {'$sum': 1}}}
#     ]
#     result = mongodb_util.aggregate(pipeline, 'realtime_quotes_now_zt_new_kc_open')
#
#     result = result.sort_values(by=['_id'], ascending=True)
#     print(result)
from io import StringIO
import re

if __name__ == '__main__':
    mongodb_util = RemoteMongodbUtil('27017')
    #
    # kpl_best_choose_index_df = mongodb_util.find_page_skip_data('kpl_best_choose_index', {"index_class": "sub_index"},
    #                                                             1, 100, 'create_time', True)
    key_word = '高速连接'
    EXCLUDE_INFO_KEY = '股东人数'
    # query = {
    #     "$or": [{'question': {"$regex": re.compile(key_word, re.IGNORECASE)}},
    #             {'answer_content': {"$regex": re.compile(key_word, re.IGNORECASE)}}],
    #     "$and": [{'question': {"$not": re.compile(EXCLUDE_INFO_KEY, re.IGNORECASE)}},
    #              {'answer_content': {"$not": re.compile(EXCLUDE_INFO_KEY, re.IGNORECASE)}}],
    # }
    #
    # pipeline = [
    #     {'$match': query},
    #     {'$group': {'_id': "$symbol", 'count': {'$sum': 1}}}
    # ]
    # result = mongodb_util.aggregate(pipeline, 'stock_interactive_question')
    #
    # result = result.sort_values(by=['_id'], ascending=True)
    # print(result)
    #
    # # ths_new_concept = mongodb_util.find_all_data('ths_new_concept')
    # key = mongodb_util.get_col_keys('company_info')
    # print(key)

    # mongodb_util.create_index('realtime_quotes_now_open', [("number", 1)])
    # mongodb_util.create_index('realtime_quotes_now_open', [("symbol", 1), ("number", 1)])
    # mongodb_util.create_index('realtime_quotes_now_open', [("str_day", 1)])
    # update_query = {"str_day": "2023-06-30"}
    # mongodb_util.update_many(update_query, {"$set": {"number": 1}}, "realtime_quotes_now_open")
    # query = {"symbol": "000617"}
    # company_info_base = mongodb_util.find_query_data('company_info_base', query)
    # ths_stock_concept_detail = mongodb_util.find_query_data('ths_stock_concept_detail', query)
    # ths_stock_concept_detail = ths_stock_concept_detail[[
    #     'concept_code',
    #     'concept_name',
    #     'str_now_time',
    #     'concept_create_day']]
    # # 去除空格
    # ths_stock_concept_detail['concept_name'] = ths_stock_concept_detail['concept_name'].str.replace(' ', '')
    # company_info_base.loc[:, 'ths_concept_list_info'] = ths_stock_concept_detail.to_string(index=False)
    # for company_one in company_info_base.itertuples():
    #     ths_concept_list_info = company_one.ths_concept_list_info
    #     ths_concept_list_info_df = pd.read_csv(StringIO(ths_concept_list_info), delim_whitespace=True)
    #     print(ths_concept_list_info_df)

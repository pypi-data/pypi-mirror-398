import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pymongo
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')

client_win = pymongo.MongoClient("mongodb://192.168.1.6:" + '27017' + "/patience")
from loguru import logger


def insert_mongo(df, col):
    db = client_win.patience

    if df is None or len(df) == 0:
        return
    collection = db[col]
    # 格式转换
    try:
        df = df.drop_duplicates()
        # df = df.T.drop_duplicates().T
        records = df.to_dict('records')
        collection.insert_many(records)
    except BaseException as e:
        logger.error("插入数据异常:{}", e)


def col_move():
    col = 'realtime_quotes_now_2024-09-23'
    number = 8
    while number < 3312:
        query = {'number': number}
        realtime_quotes_now_df = mongodb_util.find_query_data(col, query)
        insert_mongo(realtime_quotes_now_df, col)
        number = number + 1
        print(number)


if __name__ == '__main__':
    col_move()

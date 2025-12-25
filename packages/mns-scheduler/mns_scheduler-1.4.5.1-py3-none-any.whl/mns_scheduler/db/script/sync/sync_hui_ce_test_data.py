import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_scheduler.db.script.sync.remote_mongo_util import RemoteMongodbUtil
from mns_scheduler.db.script.sync.local_mongo_util import LocalMongodbUtil
from loguru import logger

remote_mongodb_util = RemoteMongodbUtil('27017')
local_mongodb_util = LocalMongodbUtil('27017')


def create_index(db_name):
    local_mongodb_util.create_index(db_name, [("symbol", 1)])

    local_mongodb_util.create_index(db_name, [("str_now_date", 1)])

    local_mongodb_util.create_index(db_name, [("symbol", 1), ("number", 1)])


def sync_real_time_data(str_day, min_number, max_number):
    db_name = 'realtime_quotes_now_' + str_day
    # 创建索引
    create_index(db_name)
    while min_number <= max_number:
        query = {'number': min_number}
        data_df = remote_mongodb_util.find_query_data(db_name, query)
        local_mongodb_util.insert_mongo(data_df, db_name)
        min_number = min_number + 1
        logger.info(min_number)


def sync_k_line(str_day):
    query = {"str_day": str_day}
    db_name = 'k_line_info'
    data_df = remote_mongodb_util.find_query_data(db_name, query)
    try:
        local_mongodb_util.insert_mongo(data_df, db_name)
    except BaseException as e:
        logger.error("出现异常:{}", e)
        pass


if __name__ == '__main__':
    str_day_01 = '2025-09-10'
    sync_k_line(str_day_01)

    # sync_real_time_data(str_day_01, 1, 2500)

    # sync_k_line(str_day_01)
    # sync_k_line('2024-11-13')
    # sync_k_line('2024-11-12')
    # sync_k_line('2024-11-15') 232

    # sync_real_time_data('2024-11-15', 10, 1010)

    # sync_k_line('2024-12-20')
    # sync_k_line('2024-12-19')
    # sync_k_line('2024-12-18')
    # sync_k_line('2024-12-17')
    # sync_k_line('2024-12-16')
    #
    # sync_k_line('2024-12-13')
    # sync_k_line('2024-12-12')
    # sync_k_line('2024-12-11')
    # sync_k_line('2024-12-10')
    # sync_k_line('2024-12-09')
    #
    # sync_k_line('2024-12-06')
    # sync_k_line('2024-12-05')
    # sync_k_line('2024-12-04')
    # sync_k_line('2024-12-03')
    # sync_k_line('2024-12-02')

    # sync_real_time_data('2024-12-20', 1000, 2000)
    # sync_real_time_data('2024-11-13', 10, 1010)

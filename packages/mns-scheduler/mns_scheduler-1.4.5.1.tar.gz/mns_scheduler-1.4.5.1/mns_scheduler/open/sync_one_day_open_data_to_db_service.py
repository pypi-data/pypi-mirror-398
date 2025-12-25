import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
# 同步当天所有开盘数据
import mns_common.utils.date_handle_util as date_handle_util
from loguru import logger
from datetime import time
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.data.data_init_api as data_init_api
import mns_common.utils.db_util as db_util

mongodb_util = MongodbUtil('27017')


def sync_one_day_open_data(str_day):
    realtime_quotes_db_name = 'realtime_quotes_now_' + str_day

    number = db_util.get_realtime_quotes_now_min_number(str_day, None, None)

    query = {"number": number}
    db = db_util.get_db(str_day)
    realtime_quotes_now_list = db.find_query_data(realtime_quotes_db_name, query)

    realtime_quotes_now_one = realtime_quotes_now_list.iloc[0]
    str_now_date = realtime_quotes_now_one['_id']
    str_now_date = str_now_date[7:26]

    now_date = date_handle_util.str_to_date(str_now_date, "%Y-%m-%d %H:%M:%S")
    now_date_time = now_date.time()

    target_time_09_31 = time(9, 31)
    if now_date_time >= target_time_09_31:
        return

    realtime_quotes_now_list['str_day'] = str_day

    realtime_quotes_now_list = handle_init_real_time_quotes_data(
        realtime_quotes_now_list.copy(),
        str_now_date, number)

    mongodb_util.insert_mongo(realtime_quotes_now_list, 'realtime_quotes_now_open')

    logger.info("同步str_day:{}开盘数据", str_day)


def handle_init_real_time_quotes_data(real_time_quotes_now, str_now_date, number):
    #  fix industry
    real_time_quotes_now = company_common_service_new_api.amend_ths_industry(real_time_quotes_now.copy())
    #  exclude b symbol
    real_time_quotes_now = common_service_fun_api.exclude_b_symbol(real_time_quotes_now.copy())
    #  classification symbol
    real_time_quotes_now = common_service_fun_api.classify_symbol(real_time_quotes_now.copy())

    #  calculate parameter
    real_time_quotes_now = data_init_api.calculate_parameter_factor(real_time_quotes_now.copy())

    real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['amount'] != 0]
    real_time_quotes_now['str_now_date'] = str_now_date
    real_time_quotes_now['number'] = number
    return real_time_quotes_now


if __name__ == '__main__':
    sync_one_day_open_data('2025-03-21')

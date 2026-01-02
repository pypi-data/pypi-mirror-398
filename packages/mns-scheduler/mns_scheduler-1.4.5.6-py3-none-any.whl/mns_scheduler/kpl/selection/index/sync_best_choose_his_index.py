import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import sys
import os

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import threading
import pandas as pd
import mns_common.api.kpl.common.kpl_common_api as kpl_common_api
import mns_common.utils.data_frame_util as data_frame_util

KPL_MINUTE_LIST = ['0930', '0935', '0940', '0945', '0950', '0955',
                   '1000', '1005', '1010', '1015', '1020', '1025',
                   '1030', '1035', '1040', '1045', '1050', '1055',
                   '1100', '1105', '1110', '1115', '1120', '1125',
                   '1130',
                   '1305', '1310', '1315', '1320', '1325',
                   '1330', '1335', '1340', '1345', '1350', '1355',
                   '1400', '1405', '1410', '1415', '1420', '1425',
                   '1430', '1435', '1440', '1445', '1450', '1455',
                   '1500']

KPL_MINUTE_BEGIN = "0925"
KPL_MINUTE_END = "1500"
file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

mongodb_util = MongodbUtil('27017')
# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = pd.DataFrame()


def sync_best_choose_his_index(str_day):
    all_kpl_best_choose_index_df = kpl_common_api \
        .get_plate_index(kpl_common_api.BEST_CHOOSE)
    kpl_best_choose_index_number = all_kpl_best_choose_index_df.shape[0]
    page_max_number = kpl_best_choose_index_number / kpl_common_api.HIS_PAGE_MAX_COUNT
    page_number = 0
    number = 1
    for end_time in KPL_MINUTE_LIST:
        while page_number <= page_max_number:
            index = page_number * kpl_common_api.HIS_PAGE_MAX_COUNT
            kpl_plate_best_index_df = kpl_common_api.get_plate_index_his(index, kpl_common_api.BEST_CHOOSE,
                                                                         str_day, KPL_MINUTE_BEGIN,
                                                                         end_time)

            if data_frame_util.is_empty(kpl_plate_best_index_df):
                continue
            kpl_plate_best_index_df['number'] = number
            kpl_plate_best_index_df['str_day'] = str_day
            hour = end_time[0:2]
            minute = end_time[2:4]
            str_now_date = str_day + " " + hour + ":" + minute + ":" + "00"
            kpl_plate_best_index_df['str_now_date'] = str_now_date
            kpl_plate_best_index_df = kpl_plate_best_index_df[[
                "plate_code",
                "plate_name",
                "heat_score",
                "chg",
                "speed",
                "amount",
                "main_net_inflow",
                "main_inflow_in",
                "main_inflow_out",
                "quantity_ratio",
                "flow_mv",
                "super_order_net",
                "total_mv",
                "last_reason_organ_add",
                "ava_pe_now",
                "ava_pe_next",
                "number",
                "str_day",
                "str_now_date"

            ]]
            save_kpl_his_index(kpl_plate_best_index_df, str_day, end_time)
            if end_time == KPL_MINUTE_END:
                save_kpl_his_daily(kpl_plate_best_index_df, str_day, end_time)
            page_number = page_number + 1
        # 执行下一个时间段
        page_number = 0
        number = number + 1


def save_kpl_his_index(kpl_plate_best_index_df, str_day, end_time):
    kpl_plate_best_index_df['_id'] = str_day + '-' + end_time + '-' + kpl_plate_best_index_df['plate_code']
    mongodb_util.save_mongo(kpl_plate_best_index_df, db_name_constant.KPL_BEST_CHOOSE_HIS)


def save_kpl_his_daily(kpl_plate_best_index_df, str_day, end_time):
    kpl_plate_best_index_df['_id'] = str_day + '-' + end_time + '-' + kpl_plate_best_index_df['plate_code']
    mongodb_util.save_mongo(kpl_plate_best_index_df, db_name_constant.KPL_BEST_CHOOSE_DAILY)


def sync_all_days():
    query = {"_id": {"$gte": '2024-04-26'}, 'trade_date': {"$lte": "2024-05-07"}}
    trade_date_list = mongodb_util.find_query_data('trade_date_list', query)
    trade_date_list = trade_date_list.sort_values(by=['trade_date'], ascending=False)
    for trade_one in trade_date_list.itertuples():
        sync_best_choose_his_index(trade_one.trade_date)


if __name__ == '__main__':
    sync_all_days()
    # sync_best_choose_his_index('2024-04-19')

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_scheduler.zt.open_data.kcx_high_chg_open_data_sync as kcx_high_chg_open_data_sync
from loguru import logger

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')
mongodb_util_21019 = MongodbUtil('27019')
realtime_quotes_now_zt_new_kc_open_field = ['_id',
                                            'symbol',
                                            'name',
                                            'chg',
                                            'quantity_ratio',
                                            'amount_level',
                                            'real_exchange',
                                            'sum_main_inflow_disk',
                                            'disk_diff_amount',
                                            'flow_mv_level',
                                            'total_mv_level',
                                            'today_chg',
                                            'industry',
                                            'first_sw_industry',
                                            'second_sw_industry',
                                            'third_sw_industry',
                                            'ths_concept_name',
                                            'ths_concept_code',
                                            'em_industry',
                                            'disk_ratio',
                                            'company_type',
                                            'reference_main_inflow',
                                            'main_inflow_multiple', 'super_main_inflow_multiple',
                                            'disk_diff_amount_exchange', 'exchange', 'amount', 'today_main_net_inflow',
                                            'today_main_net_inflow_ratio', 'super_large_order_net_inflow',
                                            'super_large_order_net_inflow_ratio', 'large_order_net_inflow',
                                            'large_order_net_inflow_ratio', 'now_price',
                                            'high', 'low', 'open', 'yesterday_price',
                                            'volume', 'total_mv', 'flow_mv',
                                            'outer_disk', 'inner_disk',
                                            'classification', 'str_now_date', 'number', 'str_day',
                                            'yesterday_high_chg',
                                            'ths_concept_sync_day', 'mv_circulation_ratio',
                                            'large_inflow_multiple', 'real_main_inflow_multiple',
                                            'max_real_main_inflow_multiple', 'list_date',
                                            'real_super_main_inflow_multiple', 'real_flow_mv',
                                            'real_disk_diff_amount_exchange', 'no_open_data']


#     query = {'$and': [{"_id": {'$lte': str_end}}, {"_id": {'$gte': '2022-04-25'}}]}
def sync_all_high_chg_data(str_end):
    query = {'$and': [{"_id": {'$lte': str_end}}, {"_id": {'$gte': '2024-03-01'}}]}
    trade_date_list = mongodb_util.find_query_data('trade_date_list', query)
    trade_date_list = trade_date_list.sort_values(by=['trade_date'], ascending=False)
    for date_one in trade_date_list.itertuples():
        try:
            str_day = date_one.trade_date
            kcx_high_chg_open_data_sync.sync_all_kc_zt_data(str_day, None)
        except BaseException as e:
            logger.error("发生异常:{},{}", str_day, e)


def fix_miss_data(str_end):
    query = {'$and': [{"_id": {'$lte': str_end}}, {"_id": {'$gte': '2023-12-05'}}]}
    trade_date_list = mongodb_util.find_query_data('trade_date_list', query)
    trade_date_list = trade_date_list.sort_values(by=['trade_date'], ascending=False)
    for date_one in trade_date_list.itertuples():
        try:
            str_day = date_one.trade_date
            query = {"str_day": str_day, "miss_out": True}
            stock_high_chg_pool_df = mongodb_util.find_query_data('stock_high_chg_pool', query)
            if data_frame_util.is_empty(stock_high_chg_pool_df):
                continue
            miss_symbol_list = list(stock_high_chg_pool_df['symbol'])
            kcx_high_chg_open_data_sync.sync_all_kc_zt_data(str_day, miss_symbol_list)
        except BaseException as e:
            logger.error("发生异常:{},{}", str_day, e)


if __name__ == '__main__':
    kcx_high_chg_open_data_sync.sync_all_kc_zt_data('2025-06-30', None)
    # sync_all_kc_zt_data('2023-08-16')
    # sync_all_kc_zt_data('2023-07-07')
    # realtime_quotes_now_zt_new_kc_open_sync()
    # hui_ce_all('2023-06-16')
    # fix_diff_day()
    # sync_all_kc_zt_data('2023-06-30')

    # sync_all_kc_zt_data('2023-07-05')
    # sync_one_day_open_data('2023-07-05')
    # sync_all_kc_zt_data('2023-06-30')
    # sync_one_day_open_data('2023-05-31')
    # hui_ce_all('2023-03-16')
    # sync_all_kc_zt_data('2023-06-28')
    # sync_all_kc_zt_data('2023-05-12')
    # sync_all_kc_zt_data('2023-05-15')
    # sync_all_kc_zt_data('2023-05-16')
    # sync_all_kc_zt_data('2023-05-17')
    # sync_all_kc_zt_data('2023-05-10')

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.utils.data_frame_util as data_frame_util
from mns_scheduler.db.script.sync.remote_mongo_util import RemoteMongodbUtil
from mns_scheduler.db.script.sync.local_mongo_util import LocalMongodbUtil
from loguru import logger
import numpy as np

remote_mongodb_util = RemoteMongodbUtil('27017')
local_mongodb_util = LocalMongodbUtil('27017')

col_list = [
    'zt_reason_analysis',
    'today_exclude_stocks',
    'today_self_choose_stock',
    'main_line_detail',
    'em_a_stock_info',
    'em_etf_info',
    'em_kzz_info',
    'em_hk_stock_info',
    'company_info',
    'company_remark_info',
    'company_holding_info',
    'industry_concept_remark',
    'trade_date_list',
    'de_list_stock',
    'kpl_best_choose_index',
    'kpl_best_choose_index_detail',
    'realtime_quotes_now_zt_new_kc_open',
    'industry_concept_remark',
    'self_black_stock',
    'self_choose_plate',
    'self_choose_stock',
    'stock_account_info',
    'ths_concept_list',
    'stock_zt_pool_five',
    'ths_stock_concept_detail',
    'stock_high_chg_pool',
    'today_new_concept_list',
    'ths_stock_concept_detail_app',

]


def remote_data():
    for col in col_list:
        try:
            col_df = remote_mongodb_util.find_all_data(col)
            if data_frame_util.is_not_empty(col_df):
                result = local_mongodb_util.remove_all_data(col)
                if result.acknowledged:
                    col_df.replace([np.inf, -np.inf], 0, inplace=True)

                    local_mongodb_util.save_mongo(col_df, col)

                logger.info("同步集合完成:{}", col)
        except BaseException as e:
            logger.error("同步失败:{},{}", e, col)


def sync_zt_data(str_day):
    col = 'stock_zt_pool'
    try:
        query = {'str_day': str_day}
        col_df = remote_mongodb_util.find_query_data(col, query)
        if data_frame_util.is_not_empty(col_df):
            col_df.replace([np.inf, -np.inf], 0, inplace=True)
            local_mongodb_util.save_mongo(col_df, col)

        logger.info("同步集合完成:{}", col)
    except BaseException as e:
        logger.error("同步失败:{},{}", e, col)


def sync_open_data():
    query = {"$and": [{'trade_date': {"$gte": "2025-03-21"}}, {'trade_date': {"$lte": "2025-04-02"}}]}
    trade_date_list_df = remote_mongodb_util.find_query_data('trade_date_list', query)
    trade_date_list_df = trade_date_list_df.sort_values(by=['trade_date'], ascending=False)
    for trade_date_one in trade_date_list_df.itertuples():
        try:
            trade_date = trade_date_one.trade_date
            query_01 = {"str_day": trade_date}
            realtime_quotes_now_open_df = remote_mongodb_util.find_query_data('realtime_quotes_now_open', query_01)
            if 'ths_concept_list' in realtime_quotes_now_open_df.columns:
                del realtime_quotes_now_open_df['ths_concept_list']
            local_mongodb_util.insert_mongo(realtime_quotes_now_open_df, 'realtime_quotes_now_open')
            logger.info("同步到:{}", trade_date)
        except BaseException as e:
            logger.error("同步异常:{}", e)
    return trade_date_list_df


if __name__ == '__main__':
    sync_zt_data('2025-12-21')
    sync_zt_data('2025-12-23')
    sync_zt_data('2025-12-24')
    sync_zt_data('2025-12-25')
    sync_zt_data('2025-12-26')
    remote_data()
    # sync_zt_data('2025-08-26')
    # sync_zt_data('2025-08-25')
    # sync_zt_data('2025-08-26')
    # remote_data()
    # sync_zt_data('2025-07-23')
    # sync_zt_data('2025-07-24')
    # sync_zt_data('2025-07-25')
    # sync_open_data()
    # remote_data()

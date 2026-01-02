import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger
from mns_common.db.MongodbUtil import MongodbUtil
from datetime import datetime
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.api.akshare.stock_dt_pool as stock_dt_pool_api

mongodb_util = MongodbUtil('27017')


def fix_industry(stock_em_zt_pool_df_data, str_day):
    if stock_em_zt_pool_df_data is None or stock_em_zt_pool_df_data.shape[0] == 0:
        return None
    industry_group_df = company_common_service_api.get_company_info_industry_list_date()
    industry_group_df = industry_group_df.set_index(['_id'], drop=True)

    stock_em_zt_pool_df_data.drop(columns=['industry'], inplace=True)
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.set_index(['symbol'], drop=False)
    stock_em_zt_pool_df_data = pd.merge(stock_em_zt_pool_df_data, industry_group_df, how='outer',
                                        left_index=True, right_index=True)
    stock_em_zt_pool_df_data['symbol'] = stock_em_zt_pool_df_data.index
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.loc[stock_em_zt_pool_df_data['amount'] > 0]
    stock_em_zt_pool_df_data = common_service_fun_api.classify_symbol(stock_em_zt_pool_df_data)

    stock_em_zt_pool_df_data['_id'] = stock_em_zt_pool_df_data['symbol'] + "_" + str_day

    stock_em_zt_pool_df_data['str_day'] = str_day

    stock_em_zt_pool_df_data = common_service_fun_api.total_mv_classification(stock_em_zt_pool_df_data)
    return stock_em_zt_pool_df_data


def sync_stock_dt_pool(str_day):
    try:
        if str_day is None:
            now_date_time = datetime.now()
            str_day = now_date_time.strftime('%Y-%m-%d')
        logger.info('同步所有跌停股:' + str_day)
        stock_em_dt_pool_df_data = stock_dt_pool_api.stock_em_dt_pool_df(
            date_handle_util.no_slash_date(str_day))
        if data_frame_util.is_empty(stock_em_dt_pool_df_data):
            return None
        stock_em_dt_pool_df_data = fix_industry(stock_em_dt_pool_df_data, str_day)
        mongodb_util.save_mongo(stock_em_dt_pool_df_data, 'stock_dt_pool')
        return stock_em_dt_pool_df_data
    except BaseException as e:
        logger.error("实时股票跌停信息数据同步异常:{},{}", e, str_day)
        return None


if __name__ == '__main__':
    sync_date = date_handle_util.add_date_day('20231214', 1)

    now_date = datetime.now()

    str_now_day_01 = sync_date.strftime('%Y-%m-%d')

    while now_date > sync_date:
        stock_em_zt_pool_df_day = sync_stock_dt_pool(str_now_day_01)
        if stock_em_zt_pool_df_day is None:
            sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day_01), 1)
            str_now_day_01 = sync_date.strftime('%Y-%m-%d')
            continue
        mongodb_util.save_mongo(stock_em_zt_pool_df_day, 'stock_dt_pool')
        sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day_01), 1)
        str_now_day_01 = sync_date.strftime('%Y-%m-%d')

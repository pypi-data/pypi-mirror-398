import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.component.common_service_fun_api as common_service_fun_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')


def get_sec_code(symbol):
    classification = common_service_fun_api.classify_symbol_one(symbol)
    if classification in ['K', 'H']:
        return 'SH' + symbol
    elif classification in ['C', 'S']:
        return 'SZ' + symbol
    else:
        return 'BJ' + symbol


# 查询利润表数据
def find_profit_report(period_time):
    query = {"REPORT_DATE": period_time}
    return mongodb_util.find_query_data(db_name_constant.EM_STOCK_PROFIT, query)


# 查询资产表
def find_asset_liability_report(period_time):
    query = {"REPORT_DATE": period_time}
    return mongodb_util.find_query_data(db_name_constant.EM_STOCK_ASSET_LIABILITY, query)


# 查出未报告的股票
def find_un_report_symbol(period_time, report_name):
    real_time_quotes_df = em_stock_info_api.get_a_stock_info()
    real_time_quotes_df = real_time_quotes_df.loc[~(real_time_quotes_df['name'].str.contains('退'))]
    real_time_quotes_df.dropna(subset=['list_date'], axis=0, inplace=True)

    de_list_stock_df = mongodb_util.find_all_data(db_name_constant.DE_LIST_STOCK)
    real_time_quotes_df = real_time_quotes_df.loc[
        ~(real_time_quotes_df['symbol'].isin(list(de_list_stock_df['symbol'])))]

    if report_name == db_name_constant.EM_STOCK_ASSET_LIABILITY:
        had_asset_df = find_asset_liability_report(period_time)
        if data_frame_util.is_not_empty(had_asset_df):
            real_time_quotes_df = real_time_quotes_df.loc[
                ~(real_time_quotes_df['symbol'].isin(list(had_asset_df['SECURITY_CODE'])))]
    if report_name == db_name_constant.EM_STOCK_PROFIT:
        had_profit_df = find_profit_report(period_time)
        if data_frame_util.is_not_empty(had_profit_df):
            real_time_quotes_df = real_time_quotes_df.loc[
                ~(real_time_quotes_df['symbol'].isin(list(had_profit_df['SECURITY_CODE'])))]
    return real_time_quotes_df

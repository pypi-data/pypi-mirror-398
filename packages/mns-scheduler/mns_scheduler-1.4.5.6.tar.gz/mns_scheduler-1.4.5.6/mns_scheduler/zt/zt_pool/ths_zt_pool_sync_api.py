import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.zt.ths_stock_zt_pool_api as ths_stock_zt_pool_api
from datetime import datetime
import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.common_service_fun_api as common_service_fun_api
from loguru import logger
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_scheduler.k_line.common.k_line_common_api as k_line_common_api

mongodb_util = MongodbUtil('27017')


def ths_zt_pool(str_day, real_time_quotes_all_stocks):
    '''
    获取请求头
    :param str_day: 日期
    :param real_time_quotes_all_stocks: 实时行情
    :return:
    '''
    now_date = datetime.now()
    now_day_str_day = now_date.strftime('%Y-%m-%d')
    ths_zt_pool_df = ths_stock_zt_pool_api.get_zt_reason(str_day)
    ths_zt_pool_df_copy = ths_zt_pool_df.copy()

    if data_frame_util.is_empty(ths_zt_pool_df_copy):
        return pd.DataFrame()
    if str_day == now_day_str_day:
        ths_zt_pool_df = merge_his_day_zt_info(ths_zt_pool_df_copy, str_day)
    else:
        ths_zt_pool_df = merge_his_day_zt_info(ths_zt_pool_df_copy, str_day)

    return ths_zt_pool_df


# 历史数据merge
def merge_his_day_zt_info(ths_zt_pool_df, str_day):
    '''
       获取请求头
       :param ths_zt_pool_df: 涨停df
       :param str_day: 日期
       :return:
       '''

    query_field = {
        "ths_concept_name": 1,
        "ths_concept_code": 1,
        "ths_concept_sync_day": 1,
        "company_type": 1,
        "concept_create_day": 1,
        "first_sw_industry": 1,
        "third_sw_industry": 1,
        "industry": 1,
        "list_date": 1,
    }
    query_field_key = str(query_field)
    query_key = str({'symbol': {"$in": list(ths_zt_pool_df['symbol'])}})
    company_df_zt = company_common_service_new_api.get_company_info_by_field(query_key, query_field_key)

    bfq_k_line_df = get_bfq_daily_line(ths_zt_pool_df, str_day)
    bfq_k_line_df['total_mv'] = bfq_k_line_df['flow_mv']

    company_df_zt = company_df_zt.set_index(['_id'], drop=True)
    bfq_k_line_df = bfq_k_line_df.set_index(['symbol'], drop=True)
    ths_zt_pool_df = ths_zt_pool_df.set_index(['symbol'], drop=False)

    if 'chg' in ths_zt_pool_df.columns:
        del ths_zt_pool_df['chg']
    if 'now_price' in ths_zt_pool_df.columns:
        del ths_zt_pool_df['now_price']

    ths_zt_pool_df = pd.merge(ths_zt_pool_df, company_df_zt, how='outer',
                              left_index=True, right_index=True)

    ths_zt_pool_df = pd.merge(ths_zt_pool_df, bfq_k_line_df, how='outer',
                              left_index=True, right_index=True)
    ths_zt_pool_df = common_service_fun_api.classify_symbol(ths_zt_pool_df)
    ths_zt_pool_df = common_service_fun_api.total_mv_classification(ths_zt_pool_df)
    ths_zt_pool_df.fillna('', inplace=True)
    if 'zt_flag' in ths_zt_pool_df.columns:
        del ths_zt_pool_df['zt_flag']
    if 'zt_tag' in ths_zt_pool_df.columns:
        del ths_zt_pool_df['zt_tag']

    return ths_zt_pool_df


# 获取不复权k线信息
def get_bfq_daily_line(ths_zt_pool_df, str_day):
    query_k_line = {'symbol': {"$in": list(ths_zt_pool_df['symbol'])}, 'date': date_handle_util.no_slash_date(str_day)}
    bfq_daily_line_df = mongodb_util.find_query_data('stock_bfq_daily', query_k_line)
    if bfq_daily_line_df.shape[0] >= ths_zt_pool_df.shape[0]:
        bfq_daily_line_df = bfq_daily_line_df[['amount', 'chg', 'close', 'exchange',
                                               'symbol', 'amount_level',
                                               'flow_mv', 'flow_mv_sp'
                                               ]]
        bfq_daily_line_df = bfq_daily_line_df.rename(columns={"close": 'now_price'})
        return bfq_daily_line_df
    else:
        bfq_k_line_result_df = pd.DataFrame()
        for zt_one in ths_zt_pool_df.itertuples():
            symbol = zt_one.symbol
            try:

                bfq_daily_line_df = k_line_common_api.get_k_line_common_adapter(symbol, 'daily', '', str_day)

                if data_frame_util.is_empty(bfq_daily_line_df):
                    continue

                bfq_daily_line_df_one = bfq_daily_line_df.loc[
                    bfq_daily_line_df['date'] == date_handle_util.no_slash_date(str_day)]

                bfq_daily_line_df_one = bfq_daily_line_df_one[['amount', 'chg', 'close', 'exchange',
                                                               'symbol', 'amount_level',
                                                               'flow_mv', 'flow_mv_sp'
                                                               ]]
                bfq_daily_line_df_one = bfq_daily_line_df_one.rename(columns={"close": 'now_price'})
                bfq_k_line_result_df = pd.concat([bfq_k_line_result_df, bfq_daily_line_df_one])
            except BaseException as e:
                logger.warning("同步不复权k线异常:{},{}", symbol, e)

        return bfq_k_line_result_df


def save_ths_zt_pool(ths_zt_pool_df, str_day):
    ths_zt_pool_df = ths_zt_pool_df[[
        "symbol",
        "name",
        "chg",
        "connected_boards_numbers",
        "statistics",
        "statistics_detail",
        "first_closure_time",
        "last_closure_time",
        "zt_detail",
        "zt_reason",
        "closure_volume",
        "closure_funds",
        "closure_funds_per_amount",
        "closure_funds_per_flow_mv",
        "frying_plates_numbers",
        "zt_type",
        "market_code",
        "str_day",
        "industry",
        "first_sw_industry",
        "third_sw_industry",
        "ths_concept_name",
        "ths_concept_code",
        "ths_concept_sync_day",
        "list_date",
        "company_type",
        "amount",
        "now_price",
        "exchange",
        "amount_level",
        "flow_mv",
        "flow_mv_sp",
        "total_mv",
        "classification",
        "total_mv_sp",
        "flow_mv_level"
    ]]
    ths_zt_pool_df['_id'] = ths_zt_pool_df['symbol'] + '_' + ths_zt_pool_df['str_day']
    ths_zt_pool_df = ths_zt_pool_df.sort_values(by=['connected_boards_numbers'], ascending=False)

    # 将日期数值转换为日期时间格式
    ths_zt_pool_df['list_date_01'] = pd.to_datetime(ths_zt_pool_df['list_date'], format='%Y%m%d')
    str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')
    # 计算日期差值 距离现在上市时间
    ths_zt_pool_df['diff_days'] = ths_zt_pool_df.apply(
        lambda row: (str_day_date - row['list_date_01']).days, axis=1)
    del ths_zt_pool_df['list_date_01']

    mongodb_util.save_mongo(ths_zt_pool_df, db_name_constant.THS_ZT_POOL)


if __name__ == '__main__':
    # trade_date = '2024-08-01'
    # zt_df = ths_zt_pool(trade_date, None)
    # save_ths_zt_pool(zt_df, trade_date)
    trade_date = '2025-11-04'
    ths_zt_pool_df_test = ths_zt_pool(trade_date, None)
    save_ths_zt_pool(ths_zt_pool_df_test, trade_date)

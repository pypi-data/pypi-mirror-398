import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.utils.date_handle_util as date_handle_util
from loguru import logger

import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.data.data_init_api as data_init_api
import pandas as pd
from datetime import time
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.db_util as db_util

mongodb_util = MongodbUtil('27017')

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


def sync_all_kc_zt_data(str_day, symbols):
    if symbols is None:
        query_daily = {'date': date_handle_util.no_slash_date(str_day),
                       "chg": {"$gte": common_service_fun_api.ZT_CHG}}
    else:
        query_daily = {'date': date_handle_util.no_slash_date(str_day),
                       'symbol': {"$in": symbols},
                       "chg": {"$gte": common_service_fun_api.ZT_CHG}}

    kc_stock_qfq_daily = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_DAILY, query_daily)
    if data_frame_util.is_empty(kc_stock_qfq_daily):
        logger.error("无k线数据:{}", symbols)
        return

    kc_stock_qfq_daily = company_common_service_new_api.amend_ths_industry(kc_stock_qfq_daily)

    for stock_one in kc_stock_qfq_daily.itertuples():
        try:

            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'industry'] = stock_one.industry
            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'first_sw_industry'] = stock_one.first_sw_industry
            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily[
                    'symbol'] == stock_one.symbol, 'second_sw_industry'] = stock_one.second_sw_industry
            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'third_sw_industry'] = stock_one.third_sw_industry

            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'list_date'] = stock_one.list_date

            str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')

            list_date = date_handle_util.str_to_date(str(stock_one.list_date).replace(".0", ""), '%Y%m%d')

            # 计算日期差值 距离现在上市时间
            kc_stock_qfq_daily.loc[
                kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'diff_days'] = (str_day_date - list_date).days

            last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)

            query_high_chg = {'chg': {"$gte": 11}, 'date': date_handle_util.no_slash_date(last_trade_day),
                              "symbol": stock_one.symbol}
            yesterday_high_chg = mongodb_util.exist_data_query('stock_qfq_daily', query_high_chg)
            if yesterday_high_chg:
                kc_stock_qfq_daily.loc[
                    kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'yesterday_high_chg'] = True
            else:
                kc_stock_qfq_daily.loc[
                    kc_stock_qfq_daily['symbol'] == stock_one.symbol, 'yesterday_high_chg'] = False

        except BaseException as e:
            logger.error("出现异常:{},{},{}", e, str_day, stock_one.symbol)

    mongodb_util.save_mongo(kc_stock_qfq_daily, 'kc_stock_qfq_daily')
    kc_stock_qfq_daily = kc_stock_qfq_daily.loc[(kc_stock_qfq_daily['classification'].isin(['K', 'C', 'X']))
                                                | (kc_stock_qfq_daily['name'].str.startswith('C'))]
    kc_stock_qfq_daily = common_service_fun_api.exclude_new_stock(kc_stock_qfq_daily)

    kc_stock_qfq_daily = kc_stock_qfq_daily.sort_values(by=['chg'], ascending=False)

    for kc_one in kc_stock_qfq_daily.itertuples():
        try:
            db_name = 'realtime_quotes_now_' + str_day
            logger.info("同步高涨幅开盘日期和代码:{},{}", str_day, kc_one.symbol)

            query_real_time = {'symbol': kc_one.symbol}
            db = db_util.get_db(str_day)
            realtime_quotes_now_kc = db.find_query_data(db_name, query_real_time)
            stock_name = kc_one.name
            if stock_name.startswith('N'):
                continue
            if realtime_quotes_now_kc.shape[0] == 0:
                logger.error("当期日期代码无开盘数据:{},{}", str_day, kc_one.symbol)
                continue
            # 同步当天高涨幅集合竞价数据
            one_symbol_day_open_data(realtime_quotes_now_kc, kc_one, str_day)
        except BaseException as e:
            logger.error("出现异常:{},{},{}", e, str_day, kc_one.symbol)


# k c x 高涨幅当天开盘数据
def one_symbol_day_open_data(realtime_quotes_now_kc, kc_one, str_day):
    realtime_quotes_now_kc = realtime_quotes_now_kc.sort_values(by=['_id'], ascending=True)
    realtime_quotes_now_kc = realtime_quotes_now_kc.loc[realtime_quotes_now_kc['str_now_date'] >= str_day + " 09:26:00"]
    realtime_quotes_now_zt_new_kc_open = realtime_quotes_now_kc.iloc[0:1]
    _id = list(realtime_quotes_now_zt_new_kc_open['_id'])[0]
    str_now_date = _id[7:26]
    now_date = date_handle_util.str_to_date(str_now_date, "%Y-%m-%d %H:%M:%S")
    now_date_time = now_date.time()
    target_time_09_31 = time(9, 31)
    realtime_quotes_now_zt_new_kc_open_copy = realtime_quotes_now_zt_new_kc_open.copy()

    if now_date_time > target_time_09_31:
        logger.error("当期日期代码无开盘数据:{},{}", str_day, kc_one.symbol)
        realtime_quotes_now_zt_new_kc_open_copy.loc[:, 'no_open_data'] = True
    else:
        realtime_quotes_now_zt_new_kc_open_copy.loc[:, 'no_open_data'] = False
        #

    realtime_quotes_now_zt_new_kc_open_copy.loc[:, 'yesterday_high_chg'] = kc_one.yesterday_high_chg
    realtime_quotes_now_zt_new_kc_open_copy.loc[:, 'today_chg'] = kc_one.chg
    realtime_quotes_now_zt_new_kc_open_copy.loc[:, 'str_day'] = str_day
    realtime_quotes_now_zt_new_kc_open_copy = company_common_service_new_api.amend_ths_industry(
        realtime_quotes_now_zt_new_kc_open_copy)
    realtime_quotes_now_zt_new_kc_open_copy = handle_init_real_time_quotes_data(
        realtime_quotes_now_zt_new_kc_open_copy.copy(),
        str_now_date,
        1)
    if data_frame_util.is_empty(realtime_quotes_now_zt_new_kc_open_copy):
        return None
    realtime_quotes_now_zt_new_kc_open_copy = realtime_quotes_now_zt_new_kc_open_copy[
        realtime_quotes_now_zt_new_kc_open_field]

    # 将日期数值转换为日期时间格式
    realtime_quotes_now_zt_new_kc_open_copy['list_date_01'] = pd.to_datetime(
        realtime_quotes_now_zt_new_kc_open_copy['list_date'],
        format='%Y%m%d')
    # 将日期字符串转换为日期时间格式
    realtime_quotes_now_zt_new_kc_open_copy['str_day_01'] = pd.to_datetime(
        realtime_quotes_now_zt_new_kc_open_copy['str_day'],
        format='%Y-%m-%d')

    # 计算日期差值 距离现在上市时间
    realtime_quotes_now_zt_new_kc_open_copy['diff_days'] = realtime_quotes_now_zt_new_kc_open_copy.apply(
        lambda row: (row['str_day_01'] - row['list_date_01']).days, axis=1)

    del realtime_quotes_now_zt_new_kc_open_copy['str_day_01']
    del realtime_quotes_now_zt_new_kc_open_copy['list_date_01']

    deal_days = k_line_common_service_api.get_deal_days(str_day, kc_one.symbol)

    realtime_quotes_now_zt_new_kc_open_copy['deal_days'] = deal_days

    mongodb_util.save_mongo(realtime_quotes_now_zt_new_kc_open_copy, db_name_constant.KCX_HIGH_CHG_OPEN_DATA)


# 初始化数据
def handle_init_real_time_quotes_data(real_time_quotes_now, str_now_date, number):
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

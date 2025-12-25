import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
from loguru import logger
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.component.company.company_common_service_api as company_common_service_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.zt.zt_common_service_api as zt_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
from datetime import datetime
import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api

mongodb_util = MongodbUtil('27017')


# 保存高涨股票列表


def sync_stock_high_chg_pool_list(str_day, symbol_list):
    zt_pool_stocks = get_zt_pool(str_day)
    k_line_high_chg_stocks = k_line_high_chg(str_day, symbol_list)
    if data_frame_util.is_empty(zt_pool_stocks):
        return None
    # 涨停池中的股票
    zt_pool_stocks_symbol_list = list(zt_pool_stocks['symbol'])
    zt_pool_stocks = zt_pool_stocks[['symbol',
                                     'name',
                                     "chg",
                                     'now_price',
                                     "first_closure_time",
                                     "last_closure_time",
                                     "connected_boards_numbers",
                                     "zt_reason",
                                     "closure_funds",
                                     "frying_plates_numbers",
                                     "statistics",
                                     "ths_concept_name",
                                     "ths_concept_code",
                                     "ths_concept_sync_day",
                                     "amount",
                                     "high",
                                     "low",
                                     "open",

                                     "exchange",
                                     "flow_mv",
                                     "total_mv",
                                     "classification",
                                     "flow_mv_sp",
                                     "total_mv_sp",
                                     "flow_mv_level",
                                     "amount_level",
                                     "str_day"
                                     ]]

    all_company_info_df = company_common_service_api.get_company_info_industry_list_date()

    zt_pool_company_df = all_company_info_df[[
        '_id',
        'industry',
        'company_type',
        'list_date'
    ]]

    zt_pool_company_df = zt_pool_company_df.loc[all_company_info_df['_id'].isin(zt_pool_stocks_symbol_list)]
    zt_pool_company_df = zt_pool_company_df.set_index(['_id'], drop=True)
    zt_pool_stocks = zt_pool_stocks.set_index(['symbol'], drop=False)
    zt_pool_stocks = pd.merge(zt_pool_stocks, zt_pool_company_df, how='outer',
                              left_index=True, right_index=True)

    # 高涨幅股票未涨停 wei_bi !=100
    high_chg_no_zt_pool = k_line_high_chg_stocks.loc[
        ~(k_line_high_chg_stocks['symbol'].isin(zt_pool_stocks_symbol_list))]

    high_chg_no_zt_pool = high_chg_no_zt_pool.rename(columns={
        "close": "now_price"})

    high_chg_no_zt_pool = high_chg_no_zt_pool[[
        'symbol',
        'name',
        'chg',
        'now_price',
        "amount",
        "high",
        "low",
        "open",
        "exchange",
        "classification",
        "flow_mv",
        "flow_mv_sp",
        "amount_level"
    ]]
    high_chg_no_zt_pool['first_closure_time'] = '无'
    high_chg_no_zt_pool['last_closure_time'] = '无'
    high_chg_no_zt_pool['connected_boards_numbers'] = 1
    high_chg_no_zt_pool['zt_reason'] = '无'
    high_chg_no_zt_pool['closure_funds'] = 0
    high_chg_no_zt_pool['frying_plates_numbers'] = 0
    high_chg_no_zt_pool['statistics'] = '1/1'
    # 暂无
    high_chg_no_zt_pool['total_mv'] = 0
    high_chg_no_zt_pool['total_mv_sp'] = 0
    high_chg_no_zt_pool['flow_mv_level'] = 0

    high_chg_no_zt_pool['str_day'] = str_day

    high_chg_no_zt_company_df = all_company_info_df[[
        '_id',
        'industry',
        'company_type',
        'list_date',
        'ths_concept_name',
        'ths_concept_code',
        'ths_concept_sync_day'
    ]]

    high_chg_no_zt_company_df = high_chg_no_zt_company_df.loc[
        all_company_info_df['_id'].isin(list(high_chg_no_zt_pool['symbol']))]

    high_chg_no_zt_company_df = high_chg_no_zt_company_df.set_index(['_id'], drop=True)
    high_chg_no_zt_pool = high_chg_no_zt_pool.set_index(['symbol'], drop=False)

    high_chg_no_zt_pool = pd.merge(high_chg_no_zt_pool, high_chg_no_zt_company_df, how='outer',
                                   left_index=True, right_index=True)

    high_chg_pool = pd.concat([zt_pool_stocks, high_chg_no_zt_pool])

    now_date = datetime.now()
    now_day = now_date.strftime('%Y-%m-%d')

    real_time_quotes_now_init = em_stock_info_api.get_a_stock_info()

    last_trade_zt_pool = zt_common_service_api.get_last_trade_day_zt(str_day)

    zt_symbol_connected_boards_numbers_list = last_trade_zt_pool.loc[
        last_trade_zt_pool['symbol'].isin(high_chg_pool['symbol'])]

    # 所有重置为1
    high_chg_pool['connected_boards_numbers'] = 1

    if zt_symbol_connected_boards_numbers_list is not None and zt_symbol_connected_boards_numbers_list.shape[0] != 0:
        for yesterday_zt in zt_symbol_connected_boards_numbers_list.itertuples():
            high_chg_pool.loc[
                high_chg_pool["symbol"] == yesterday_zt.symbol, ['connected_boards_numbers']] \
                = 1 + yesterday_zt.connected_boards_numbers

    for stock_one in high_chg_pool.itertuples():
        try:

            symbol = stock_one.symbol
            stock_one_df = high_chg_pool.loc[high_chg_pool['symbol'] == symbol]

            classification = common_service_fun_api.classify_symbol_one(symbol)
            stock_one_df['classification'] = classification

            if classification == "X" and stock_one.chg > 31:
                continue

            list_date = stock_one.list_date
            if list_date is None or pd.isna(list_date):
                list_date = '1989-07-29'
                diff_days = 10000
            else:
                list_date = str(list_date)
                list_date = list_date.replace(".0", "")
                list_date = date_handle_util.lash_date(list_date)

                list_date_time = date_handle_util.str_to_date(list_date, "%Y-%m-%d")
                str_now_day_time = date_handle_util.str_to_date(str_day, "%Y-%m-%d")

                diff_days = date_handle_util.days_diff(str_now_day_time, list_date_time)
                # 上市新股
                if diff_days == 0:
                    continue

            stock_one_df['list_day'] = list_date
            # 上市天数
            stock_one_df['diff_days'] = diff_days
            # 交易天数
            deal_days = k_line_common_service_api.get_deal_days(str_day, symbol)
            stock_one_df['deal_days'] = deal_days

            last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)

            # 上个交易日是否是高涨幅
            last_day_high_chg = mongodb_util.exist_data_query(db_name_constant.STOCK_QFQ_DAILY,
                                                              query={"symbol": symbol, "date": last_trade_day,
                                                                     "chg": {'$gte': common_service_fun_api.ZT_CHG}})
            stock_one_df['last_day_high_chg'] = last_day_high_chg

            open_price = stock_one.open
            high = stock_one.high
            close = stock_one.now_price
            yi_zhi_ban = False
            if open_price == high and open_price == close:
                yi_zhi_ban = True

            stock_one_df['yi_zhi_ban'] = yi_zhi_ban
            stock_one_df['today_main_net_inflow'] = 0

            if now_day == str_day:
                real_time_quotes_now_one = real_time_quotes_now_init.loc[
                    real_time_quotes_now_init['symbol'] == symbol]
                stock_one_df['total_mv'] = list(real_time_quotes_now_one['total_mv'])[0]
                stock_one_df['today_main_net_inflow'] = list(real_time_quotes_now_one['today_main_net_inflow'])[0]

            stock_one_df.loc[:, ['flow_mv_level']] \
                = ((stock_one_df["flow_mv"] / common_service_fun_api.HUNDRED_MILLION) // 10) + 1
            stock_one_df['total_mv_sp'] = round((stock_one_df['total_mv'] / common_service_fun_api.HUNDRED_MILLION), 2)
            stock_one_df["_id"] = stock_one_df['symbol'] + "_" + str_day
            stock_one_df['remark'] = ''
            symbol_last_concept_df = get_symbol_last_concept(symbol, str_day)
            if data_frame_util.is_not_empty(symbol_last_concept_df):
                ths_concept_name = list(symbol_last_concept_df['concept_name'])[0]
                ths_concept_sync_day = list(symbol_last_concept_df['str_day'])[0]
                ths_concept_code = list(symbol_last_concept_df['concept_code'])[0]
                stock_one_df['ths_concept_name'] = ths_concept_name
                stock_one_df['ths_concept_code'] = ths_concept_code
                stock_one_df['ths_concept_sync_day'] = ths_concept_sync_day

            stock_one_df['ths_concept_name'].fillna('退市', inplace=True)
            stock_one_df['ths_concept_code'].fillna(0, inplace=True)
            stock_one_df['ths_concept_sync_day'].fillna('1989-07-29', inplace=True)
            stock_one_df['industry'].fillna('退市', inplace=True)
            stock_one_df['company_type'].fillna('', inplace=True)
            stock_one_df['list_date'].fillna(19890729, inplace=True)
            stock_one_df['chg'] = round(stock_one_df['chg'], 2)
            stock_one_df['exchange'] = round(stock_one_df['exchange'], 2)
            stock_one_df['today_main_net_inflow'] = round(
                stock_one_df['today_main_net_inflow'] / common_service_fun_api.TEN_THOUSAND, 2)
            stock_one_df['flag'] = ''
            id_key = symbol + "_" + str_day
            if mongodb_util.exist_data_query(db_name_constant.STOCK_HIGH_CHG_POOL, query={"_id": id_key}):
                continue

            mongodb_util.save_mongo(stock_one_df, db_name_constant.STOCK_HIGH_CHG_POOL)
            logger.info("更新高涨幅数据成功{},{}", stock_one.symbol, str_day)
        except Exception as e:
            logger.error("更新高涨幅数据异常:{},{},{}", stock_one.symbol, str_day, e)
            continue

    return high_chg_no_zt_pool


# 通过k线获取高涨幅股票
def k_line_high_chg(str_day, symbol_list):
    if symbol_list is None:
        query = {"date": date_handle_util.no_slash_date(str_day), "chg": {'$gte': common_service_fun_api.ZT_CHG}}
    else:
        query = {"date": date_handle_util.no_slash_date(str_day), "symbol": {'$in': symbol_list}}
    # 今日高涨幅的list
    return mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_DAILY, query)


# 获取当日涨停池中股票
def get_zt_pool(str_day):
    # 今日涨停股
    query_zt = {'str_day': str_day}
    zt_pool = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL, query_zt)
    if data_frame_util.is_empty(zt_pool):
        return pd.DataFrame()
    if 'zt_reason' not in zt_pool.columns:
        zt_pool['zt_reason'] = '无'
    if 'ths_concept_name' not in zt_pool.columns:
        zt_pool['ths_concept_name'] = '无'
    if 'ths_concept_code' not in zt_pool.columns:
        zt_pool['ths_concept_code'] = 0
    if 'ths_concept_sync_day' not in zt_pool.columns:
        zt_pool['ths_concept_sync_day'] = 0
    if 'high' not in zt_pool.columns:
        zt_pool['high'] = 0
    if 'low' not in zt_pool.columns:
        zt_pool['low'] = 0
    if 'open' not in zt_pool.columns:
        zt_pool['open'] = 0
    zt_pool['amount_level'] = round(zt_pool['amount'] / common_service_fun_api.HUNDRED_MILLION, 2)
    return zt_pool


def get_symbol_last_concept(symbol, str_day):
    ths_effective_concept_df = ths_concept_common_service_api.get_all_ths_effective_concept()
    ths_effective_concept_code = list(ths_effective_concept_df['symbol'])
    query = {"symbol": symbol, 'str_day': {"$lte": str_day}, 'concept_code': {"$in": ths_effective_concept_code}}
    return mongodb_util.descend_query(query, db_name_constant.THS_STOCK_CONCEPT_DETAIL, 'str_day', 1)



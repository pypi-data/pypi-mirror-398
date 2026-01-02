import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.api.akshare.stock_zt_pool_api as stock_zt_pool_api
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_api as company_common_service_api
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.api.ths.zt.ths_stock_zt_pool_v2_api as ths_stock_zt_pool_v2_api
import mns_common.component.zt.zt_common_service_api as zt_common_service_api
import mns_common.component.em.em_real_time_quotes_api as em_real_time_quotes_api
from datetime import datetime
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.deal.deal_service_api as deal_service_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.main_line.main_line_zt_reason_service as main_line_zt_reason_service
from mns_common.utils.async_fun import async_fun

'''
东方财富涨停池
'''

mongodb_util = MongodbUtil('27017')

ZT_FIELD = ['_id', 'symbol', 'name', 'now_price', 'chg', 'first_closure_time',
            'last_closure_time', 'connected_boards_numbers',
            'zt_reason', 'zt_analysis', 'closure_funds',
            # 'closure_funds_per_amount', 'closure_funds_per_flow_mv',
            'frying_plates_numbers',
            # 'statistics_detail', 'zt_type', 'market_code',
            'statistics',
            # 'zt_flag',
            'industry', 'first_sw_industry',
            'second_sw_industry',
            'third_sw_industry', 'ths_concept_name',
            'ths_concept_code', 'ths_concept_sync_day', 'em_industry',
            'mv_circulation_ratio', 'ths_concept_list_info', 'kpl_plate_name',
            'kpl_plate_list_info', 'company_type', 'diff_days', 'amount',
            'list_date',
            'exchange', 'flow_mv', 'total_mv',
            'classification', 'flow_mv_sp', 'total_mv_sp', 'flow_mv_level',
            'amount_level', 'new_stock', 'list_date_01', 'index', 'str_day', 'main_line', 'sub_main_line']


def save_zt_info(str_day):
    if bool(1 - trade_date_common_service_api.is_trade_day(str_day)):
        return pd.DataFrame()

    stock_em_zt_pool_df_data = stock_zt_pool_api.stock_em_zt_pool_df(
        date_handle_util.no_slash_date(str_day))

    # fix 涨停池没有的股票
    stock_em_zt_pool_df_data = handle_miss_zt_data(stock_em_zt_pool_df_data.copy(), str_day)

    try:
        # 同花顺问财涨停池
        ths_zt_pool_df_data = ths_stock_zt_pool_v2_api.get_ths_stock_zt_reason_with_cache(str_day)
    except BaseException as e:
        logger.error("使用问财同步ths涨停数据异常:{}", e)
        ths_zt_pool_df_data = pd.DataFrame()

    stock_em_zt_pool_df_data = handle_ths_em_diff_data(ths_zt_pool_df_data, stock_em_zt_pool_df_data)
    # 更新涨停分析和原因数据
    update_zt_reason_analysis(stock_em_zt_pool_df_data, str_day)

    stock_em_zt_pool_df_data = common_service_fun_api.total_mv_classification(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.classify_symbol(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = common_service_fun_api.symbol_amount_simple(stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data = company_common_service_api.amendment_industry(stock_em_zt_pool_df_data.copy())

    # 上个交易交易日涨停股票
    last_trade_day_zt_df = zt_common_service_api.get_last_trade_day_zt(str_day)
    # 设置连板
    stock_em_zt_pool_df_data = set_connected_boards_numbers(stock_em_zt_pool_df_data.copy(),
                                                            last_trade_day_zt_df.copy())

    # 添加主线信息
    stock_em_zt_pool_df_data = main_line_zt_reason_service.merge_main_line_info(str_day,
                                                                                stock_em_zt_pool_df_data.copy())
    # 添加涨停原因和分析信息
    stock_em_zt_pool_df_data = main_line_zt_reason_service.merge_zt_reason_info(str_day,
                                                                                stock_em_zt_pool_df_data.copy())

    stock_em_zt_pool_df_data['first_closure_time'] = stock_em_zt_pool_df_data['first_closure_time'].str.strip()
    stock_em_zt_pool_df_data['list_date'] = stock_em_zt_pool_df_data['list_date'].apply(
        lambda x: pd.to_numeric(x, errors="coerce"))

    stock_em_zt_pool_df_data['new_stock'] = False
    # 将日期数值转换为日期时间格式
    stock_em_zt_pool_df_data['list_date_01'] = pd.to_datetime(stock_em_zt_pool_df_data['list_date'], format='%Y%m%d')
    str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')
    # 计算日期差值 距离现在上市时间
    stock_em_zt_pool_df_data['diff_days'] = stock_em_zt_pool_df_data.apply(
        lambda row: (str_day_date - row['list_date_01']).days, axis=1)
    # 上市时间小于100天为新股
    stock_em_zt_pool_df_data.loc[
        stock_em_zt_pool_df_data["diff_days"] < 100, ['new_stock']] \
        = True
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.dropna(subset=['diff_days'], axis=0, inplace=False)

    # 按照"time"列进行排序，同时将值为0的数据排到最末尾
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data.sort_values(by=['first_closure_time'])

    # 重置索引，并将排序结果保存到新的"index"列中
    stock_em_zt_pool_df_data['str_day'] = str_day
    stock_em_zt_pool_df_data['_id'] = stock_em_zt_pool_df_data['symbol'] + "_" + str_day
    stock_em_zt_pool_df_data.drop_duplicates('symbol', keep='last', inplace=True)

    query_today_zt = {'str_day': str_day}
    stock_exist_zt_pool_df = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL, query_today_zt)
    if data_frame_util.is_empty(stock_exist_zt_pool_df):
        today_new_zt_pool_df = stock_em_zt_pool_df_data.copy()
    else:
        today_new_zt_pool_df = stock_em_zt_pool_df_data.loc[
            ~stock_em_zt_pool_df_data['symbol'].isin(stock_exist_zt_pool_df['symbol'])]

    mongodb_util.save_mongo(today_new_zt_pool_df, db_name_constant.STOCK_ZT_POOL)
    stock_em_zt_pool_df_data = pd.concat([stock_exist_zt_pool_df, today_new_zt_pool_df])
    # 保存连板股票主线
    save_last_trade_day_main_line(str_day, stock_em_zt_pool_df_data)

    stock_em_zt_pool_df_data.fillna('', inplace=True)
    stock_em_zt_pool_df_data = stock_em_zt_pool_df_data[ZT_FIELD]
    return stock_em_zt_pool_df_data


# 设置连板数目
def set_connected_boards_numbers(stock_em_zt_pool_df_data, last_trade_day_zt_df):
    if data_frame_util.is_empty(stock_em_zt_pool_df_data):
        return stock_em_zt_pool_df_data
    if data_frame_util.is_empty(last_trade_day_zt_df):
        return stock_em_zt_pool_df_data
    # 连板股票
    connected_boards_df_copy = last_trade_day_zt_df.loc[
        last_trade_day_zt_df['symbol'].isin(stock_em_zt_pool_df_data['symbol'])]

    connected_boards_df = connected_boards_df_copy.copy()
    #
    connected_boards_df['connected_boards_numbers'] = connected_boards_df['connected_boards_numbers'] + 1

    symbol_mapping_connected_boards_numbers = dict(
        zip(connected_boards_df['symbol'], connected_boards_df['connected_boards_numbers']))
    # 使用map进行替换，不匹配的保持原值
    stock_em_zt_pool_df_data['connected_boards_numbers'] = stock_em_zt_pool_df_data['symbol'].map(
        symbol_mapping_connected_boards_numbers).fillna(1)
    return stock_em_zt_pool_df_data


def handle_miss_zt_data(stock_em_zt_pool_df_data, str_day):
    now_date = datetime.now()
    now_day = now_date.strftime('%Y-%m-%d')
    if now_day == str_day:
        real_time_quotes_all_stocks_df = em_real_time_quotes_api.get_real_time_quotes_now(None, None)
        if data_frame_util.is_empty(real_time_quotes_all_stocks_df):
            return stock_em_zt_pool_df_data
        real_time_quotes_all_stocks_df = real_time_quotes_all_stocks_df.loc[
            (real_time_quotes_all_stocks_df['wei_bi'] == 100) & (real_time_quotes_all_stocks_df['chg'] >= 9)]
        miss_zt_data_df_copy = real_time_quotes_all_stocks_df.loc[~(
            real_time_quotes_all_stocks_df['symbol'].isin(stock_em_zt_pool_df_data['symbol']))]
        miss_zt_data_df = miss_zt_data_df_copy.copy()
        if data_frame_util.is_not_empty(miss_zt_data_df):
            miss_zt_data_df['buy_1_num'] = miss_zt_data_df['buy_1_num'].astype(float)
            miss_zt_data_df['now_price'] = miss_zt_data_df['now_price'].astype(float)
            miss_zt_data_df['closure_funds'] = round(miss_zt_data_df['buy_1_num'] * 100 * miss_zt_data_df['now_price'],
                                                     2)

            company_info_industry_df = company_common_service_api.get_company_info_name()
            company_info_industry_df = company_info_industry_df.loc[
                company_info_industry_df['_id'].isin(miss_zt_data_df['symbol'])]

            company_info_industry_df = company_info_industry_df[['_id', 'industry', 'name']]

            company_info_industry_df = company_info_industry_df.set_index(['_id'], drop=True)
            miss_zt_data_df = miss_zt_data_df.set_index(['symbol'], drop=False)

            miss_zt_data_df = pd.merge(miss_zt_data_df, company_info_industry_df, how='outer',
                                       left_index=True, right_index=True)

            miss_zt_data_df = miss_zt_data_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                'amount',
                'flow_mv',
                'total_mv',
                'exchange',
                'industry',
                'closure_funds'

            ]]
            miss_zt_data_df['index'] = 10000
            miss_zt_data_df['first_closure_time'] = '150000'
            miss_zt_data_df['last_closure_time'] = '150000'
            miss_zt_data_df['statistics'] = '1/1'
            miss_zt_data_df['frying_plates_numbers'] = 0
            miss_zt_data_df['connected_boards_numbers'] = 0

            stock_em_zt_pool_df_data = pd.concat([miss_zt_data_df, stock_em_zt_pool_df_data])
        return stock_em_zt_pool_df_data
    else:
        return stock_em_zt_pool_df_data


def handle_ths_em_diff_data(ths_zt_pool_df_data, stock_em_zt_pool_df_data):
    if data_frame_util.is_empty(ths_zt_pool_df_data):
        return stock_em_zt_pool_df_data
    else:
        diff_ths_zt_df = ths_zt_pool_df_data.loc[
            ~(ths_zt_pool_df_data['symbol'].isin(stock_em_zt_pool_df_data['symbol']))]
        if data_frame_util.is_empty(diff_ths_zt_df):
            return stock_em_zt_pool_df_data
        else:
            diff_ths_zt_df = diff_ths_zt_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                # 'amount',
                # 'flow_mv',
                # 'total_mv',
                # 'exchange',
                'closure_funds',
                'first_closure_time',
                'last_closure_time',
                'frying_plates_numbers',
                'statistics',
                'connected_boards_numbers'

            ]]

            company_info_df = query_company_info_with_share()
            company_info_df['symbol'] = company_info_df['_id']
            company_info_df = company_info_df.loc[company_info_df['symbol'].isin(list(diff_ths_zt_df['symbol']))]

            company_info_df = common_service_fun_api.add_after_prefix(company_info_df)

            symbol_prefix_list = list(company_info_df['symbol_prefix'])
            real_time_quotes_list = deal_service_api.get_qmt_real_time_quotes_detail('qmt',
                                                                                     symbol_prefix_list)

            real_time_quotes_df = pd.DataFrame(real_time_quotes_list)

            real_time_quotes_df['symbol'] = real_time_quotes_df['symbol'].str.slice(0, 6)
            company_info_df = company_info_df.set_index(['symbol'], drop=True)
            real_time_quotes_df = real_time_quotes_df.set_index(['symbol'], drop=False)

            real_time_quotes_df = pd.merge(company_info_df, real_time_quotes_df, how='outer',
                                           left_index=True, right_index=True)

            real_time_quotes_df['amount'] = round(real_time_quotes_df['amount'], 1)

            real_time_quotes_df['total_mv'] = round(
                real_time_quotes_df['lastPrice'] * real_time_quotes_df['total_share'], 1)
            real_time_quotes_df['flow_mv'] = round(real_time_quotes_df['lastPrice'] * real_time_quotes_df['flow_share'],
                                                   1)
            real_time_quotes_df['exchange'] = round(
                real_time_quotes_df['amount'] * 100 / real_time_quotes_df['flow_mv'], 1)

            real_time_quotes_df = real_time_quotes_df[
                ['symbol', 'amount', 'total_mv', 'flow_mv', 'exchange', 'industry']]

            real_time_quotes_df = real_time_quotes_df.set_index(['symbol'], drop=True)
            diff_ths_zt_df = diff_ths_zt_df.set_index(['symbol'], drop=False)
            diff_ths_zt_df = pd.merge(real_time_quotes_df, diff_ths_zt_df, how='outer',
                                      left_index=True, right_index=True)

            diff_ths_zt_df = diff_ths_zt_df[[
                'symbol',
                'name',
                'chg',
                'now_price',
                'amount',
                'flow_mv',
                'total_mv',
                'exchange',
                'closure_funds',
                'first_closure_time',
                'last_closure_time',
                'frying_plates_numbers',
                'statistics',
                'connected_boards_numbers',
                'industry'

            ]]

            exist_number = stock_em_zt_pool_df_data.shape[0] + 1

            diff_ths_zt_df.index = range(exist_number, exist_number + len(diff_ths_zt_df))
            diff_ths_zt_df['index'] = diff_ths_zt_df.index

            stock_em_zt_pool_df_data = pd.concat([stock_em_zt_pool_df_data, diff_ths_zt_df])
            return stock_em_zt_pool_df_data


def query_company_info_with_share():
    query_field = {"_id": 1,
                   "industry": 1,
                   "company_type": 1,
                   "ths_industry_code": 1,
                   "ths_concept_name": 1,
                   "ths_concept_code": 1,
                   "ths_concept_sync_day": 1,
                   "first_sw_industry": 1,
                   "second_sw_industry": 1,
                   "second_industry_code": 1,
                   "third_sw_industry": 1,
                   "mv_circulation_ratio": 1,
                   "list_date": 1,
                   "diff_days": 1,
                   'em_industry': 1,
                   'operate_profit': 1,
                   'total_operate_income': 1,
                   "name": 1,
                   'pb': 1,
                   'pe_ttm': 1,
                   'ROE': 1,
                   'ths_industry_name': 1,
                   'total_share': 1,
                   'flow_share': 1
                   }
    de_list_company_symbols = company_common_service_new_api.get_de_list_company()
    query_field_key = str(query_field)
    query = {"_id": {"$regex": "^[^48]"},
             'symbol': {"$nin": de_list_company_symbols}, }
    query_key = str(query)
    company_info_df = company_common_service_new_api.get_company_info_by_field(query_key, query_field_key)

    return company_info_df


# 异步更新涨停分析和数据
@async_fun
def update_zt_reason_analysis(stock_em_zt_pool_df_data, str_day):
    if data_frame_util.is_empty(stock_em_zt_pool_df_data):
        return
    now_date = datetime.now()
    now_str_day = now_date.strftime('%Y-%m-%d')
    if now_str_day != str_day:
        return

    stock_em_zt_pool_df_data['str_day'] = str_day
    main_line_zt_reason_service.update_symbol_list_zt_reason_analysis(stock_em_zt_pool_df_data, True)


# 保存连板股票主线
@async_fun
def save_last_trade_day_main_line(str_day, stock_em_zt_pool_df_data):
    last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)
    stock_em_zt_pool_connected_df = stock_em_zt_pool_df_data.loc[
        stock_em_zt_pool_df_data['connected_boards_numbers'] > 1]
    if data_frame_util.is_empty(stock_em_zt_pool_connected_df):
        return
    else:
        query = {'str_day': last_trade_day, 'symbol': {"$in": list(stock_em_zt_pool_connected_df['symbol'])}}
        last_trade_day_main_line_detail_df = mongodb_util.find_query_data(db_name_constant.MAIN_LINE_DETAIL, query)
        if data_frame_util.is_empty(last_trade_day_main_line_detail_df):
            return
        else:
            last_trade_day_main_line_detail_df['_id'] = last_trade_day_main_line_detail_df['symbol'] + '_' + str_day
            last_trade_day_main_line_detail_df['str_day'] = str_day
            last_trade_day_main_line_detail_df['connected_boards_numbers'] = last_trade_day_main_line_detail_df[
                                                                                 'connected_boards_numbers'] + 1
            now_date = datetime.now()
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
            last_trade_day_main_line_detail_df['update_time'] = str_now_date
            today_exist_main_line_df = mongodb_util.find_query_data(db_name_constant.MAIN_LINE_DETAIL,
                                                                    {'str_day': str_day})
            if data_frame_util.is_not_empty(today_exist_main_line_df):
                today_new_main_line_df = last_trade_day_main_line_detail_df.loc[
                    last_trade_day_main_line_detail_df['symbol'].isin(list(today_exist_main_line_df['symbol']))]
            else:
                today_new_main_line_df = last_trade_day_main_line_detail_df.copy()
            mongodb_util.save_mongo(today_new_main_line_df, db_name_constant.MAIN_LINE_DETAIL)


if __name__ == '__main__':
    save_zt_info('2025-12-26')

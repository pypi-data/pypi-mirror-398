import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_scheduler.k_line.clean.daily.daily_k_line_clean_common_service as daily_k_line_clean_common_service
import mns_scheduler.k_line.common.k_line_common_api as k_line_common_api
mongodb_util = MongodbUtil('27017')


# 多线程接口容易拉爆

def save_one_symbol(symbol, period, end_date, hq, hq_col, real_time_quotes_now):
    # 检查symbol是否以'6'开头

    stock_hfq_df = k_line_common_api.get_k_line_common_adapter(symbol, period, hq, end_date)

    real_time_quotes_now_one = real_time_quotes_now.loc[real_time_quotes_now['symbol'] == symbol]
    stock_hfq_df.rename(columns={"日期": "date", "开盘": "open",
                                 "收盘": "close", "最高": "high",
                                 "最低": "low", "成交量": "volume",
                                 "成交额": "amount", "振幅": "pct_chg",
                                 "涨跌幅": "chg", "涨跌额": "change",
                                 "换手率": "exchange"}, inplace=True)
    classification = common_service_fun_api.classify_symbol_one(symbol)
    stock_hfq_df['symbol'] = symbol
    stock_hfq_df['name'] = list(real_time_quotes_now_one['name'])[0]
    stock_hfq_df['industry'] = list(real_time_quotes_now_one['industry'])[0]
    stock_hfq_df['_id'] = stock_hfq_df['symbol'] + '-' + stock_hfq_df['date']
    stock_hfq_df['last_price'] = round(((stock_hfq_df['close']) / (1 + stock_hfq_df['chg'] / 100)), 2)
    stock_hfq_df['max_chg'] = round(
        ((stock_hfq_df['high'] - stock_hfq_df['last_price']) / stock_hfq_df['last_price']) * 100, 2)
    stock_hfq_df['amount_level'] = round((stock_hfq_df['amount'] / common_service_fun_api.HUNDRED_MILLION), 2)
    stock_hfq_df['flow_mv'] = round(stock_hfq_df['amount'] * 100 / stock_hfq_df['exchange'], 2)
    stock_hfq_df['flow_mv_sp'] = round(stock_hfq_df['flow_mv'] / common_service_fun_api.HUNDRED_MILLION, 2)
    stock_hfq_df['classification'] = classification
    stock_hfq_df = stock_hfq_df.sort_values(by=['date'], ascending=False)
    stock_hfq_df = daily_k_line_clean_common_service.calculate_exchange_and_k_line_avg_param(stock_hfq_df)
    insert_data(stock_hfq_df, hq_col, symbol)
    logger.info(period + 'k线同步-' + hq + '-' + symbol)
    return stock_hfq_df


def insert_data(stock_hfq_df, hq_col, symbol):
    query = {'symbol': symbol}
    tag = mongodb_util.remove_data(query, hq_col)
    success = tag.acknowledged
    if success:
        mongodb_util.insert_mongo(stock_hfq_df, hq_col)


# k线同步 全量
def sync_all_daily_data(period='daily',
                        hq='hfq',
                        hq_col='stock_hfq_daily',
                        end_date='22220101',
                        symbol_list=None):
    create_db_index(hq_col)

    real_time_quotes_now_es = em_stock_info_api.get_a_stock_info()
    # exclude b symbol
    real_time_quotes_now = common_service_fun_api.exclude_b_symbol(real_time_quotes_now_es.copy())

    real_time_quotes_now = common_service_fun_api.total_mv_classification(real_time_quotes_now.copy())
    if symbol_list is not None:
        real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['symbol'].isin(symbol_list)]

    real_time_quotes_now = real_time_quotes_now.sort_values(by=['chg'], ascending=False)
    fail_symbol_list = []
    for company_info in real_time_quotes_now.itertuples():
        symbol = company_info.symbol
        try:
            k_line_df = save_one_symbol(symbol, period, end_date, hq, hq_col, real_time_quotes_now)
        except BaseException as e:
            fail_symbol_list.append(symbol)
            logger.error('发生异常:{},{}', symbol, e)

    if len(fail_symbol_list) > 0:
        for symbol in fail_symbol_list:
            try:
                k_line_df = save_one_symbol(symbol, period, end_date, hq, hq_col, real_time_quotes_now)
            except BaseException as e:
                logger.error('发生异常:{},{}', symbol, e)
    return k_line_df


def create_db_index(db_name):
    try:

        mongodb_util.create_index(db_name, [("symbol", 1)])
        mongodb_util.create_index(db_name, [("date", 1)])
        mongodb_util.create_index(db_name, [("symbol", 1), ("date", 1)])
        logger.info("创建索引成功:{}", db_name)
    except BaseException as e:
        logger.warning("创建索引异常:{}", e)


if __name__ == '__main__':
    # sync_all_daily_data('monthly', 'qfq', 'stock_qfq_monthly', None, None)
    # sync_all_daily_data('daily', 'qfq', 'stock_qfq_daily', None, None)
    # sync_all_daily_data('daily', 'qfq', 'stock_qfq_weekly', None, None)
    sync_all_daily_data('weekly', 'qfq', 'stock_qfq_weekly', '2025-07-19', None)
    # sync_all_daily_data('monthly', 'qfq', 'stock_qfq_monthly', None, None)

    # sync_all_daily_data('monthly', '1990-12-19', 'qfq', 'stock_qfq_monthly', None, None)
    # sync_all_daily_data('daily', '1990-12-19', 'qfq', 'stock_qfq_daily', '2023-10-31', None)
    # sync_all_daily_data('weekly', '1990-12-19', 'qfq', 'stock_qfq_weekly', '2023-10-15', None)
    # sync_all_daily_data('monthly', '1990-12-19', 'qfq', 'stock_qfq_monthly', '2023-09-30', None)

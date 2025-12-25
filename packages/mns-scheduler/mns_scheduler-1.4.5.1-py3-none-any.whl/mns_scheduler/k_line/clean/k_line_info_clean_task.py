import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import pandas as pd
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from loguru import logger
import threading
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_scheduler.k_line.month_week_daily.daily_week_month_line_sync as daily_week_month_line_sync_api
import mns_scheduler.k_line.clean.k_line_info_clean_impl as k_line_info_clean_impl
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.constant.db_name_constant as db_name_constant

K_LINE_CLEAN_DB_NAME = 'k_line_clean_fail_name'

# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = pd.DataFrame()
# 分页大小
MAX_PAGE_NUMBER = 1000
mongodb_util = MongodbUtil('27017')


def sync_k_line_info_task(str_day):
    # 创建索引
    create_k_line_index()

    last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)
    query = {'date': date_handle_util.no_slash_date(last_trade_day)}
    count = mongodb_util.count(query, 'stock_qfq_daily')
    # 当天没有k线数据时 进行同步
    if count == 0:
        daily_week_month_line_sync_api.sync_all_daily_data('daily', 'qfq', 'stock_qfq_daily', str_day,
                                                           None)
    sync_k_line_info(str_day, None)


def sync_k_line_info(str_day, symbol_list):
    result_k_line_list_df = None
    if symbol_list is not None:
        for symbol in symbol_list:
            try:
                company_df = company_common_service_api.get_company_info_industry_list_date()
                company_info_df = company_df.loc[company_df['_id'] == symbol]
                if data_frame_util.is_not_empty(company_info_df):

                    # 将日期数值转换为日期时间格式
                    company_info_df['list_date_01'] = pd.to_datetime(
                        company_info_df['list_date'],
                        format='%Y%m%d')
                    # 将日期字符串转换为日期时间格式
                    str_day_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')

                    # 计算日期差值 距离现在上市时间
                    company_info_df[
                        'diff_days'] = company_info_df.apply(
                        lambda row: (str_day_date - row['list_date_01']).days, axis=1)

                    diff_days = list(company_info_df['diff_days'])[0]

                    now_year = int(str_day[0:4])
                    last_year = now_year - 1

                    query_year_line = {'symbol': symbol, 'year': {"$in": [str(now_year), str(last_year)]}}
                    stock_qfq_year_df = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_YEAR, query_year_line)

                    k_line_result = k_line_info_clean_impl.calculate_k_line_info(str_day, symbol, diff_days,
                                                                                 stock_qfq_year_df)
                    save_k_line_data(symbol, str_day, k_line_result)
                    if result_k_line_list_df is None:
                        result_k_line_list_df = k_line_result
                    else:
                        result_k_line_list_df = pd.concat([result_k_line_list_df, k_line_result])

            except BaseException as e:
                logger.error("k线同步错误:{},{},{}", str_day, symbol, e)
    else:
        result_k_line_list_df = multi_threaded_k_line_sync(str_day)
    logger.info("计算k线数据任务完成:{}", str_day)
    return result_k_line_list_df


def handle_fail_data(str_day, real_time_quotes_now):
    query = {'str_day': str_day}
    k_line_fail_df = mongodb_util.find_query_data(K_LINE_CLEAN_DB_NAME, query)
    if data_frame_util.is_not_empty(k_line_fail_df):
        fail_data_df = real_time_quotes_now.loc[real_time_quotes_now['symbol'].isin(k_line_fail_df['symbol'])]
        now_year = int(str_day[0:4])
        last_year = now_year - 1

        query_year_line = {'year': {"$in": [str(now_year), str(last_year)]}}
        stock_qfq_year_df = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_YEAR, query_year_line)
        single_threaded_sync_task(fail_data_df, str_day, 88, stock_qfq_year_df)


# 多线程同步任务
def multi_threaded_k_line_sync(str_day):
    # 退市代码

    de_list_company_df = mongodb_util.find_all_data(db_name_constant.DE_LIST_STOCK)
    de_list_company_df = de_list_company_df.loc[de_list_company_df['de_list_date'] < str_day]
    real_time_quotes_now = em_stock_info_api.get_a_stock_info()
    real_time_quotes_now = real_time_quotes_now.loc[
        ~(real_time_quotes_now['symbol'].isin(de_list_company_df['symbol']))]

    # 将list_date列中的所有NaN值设置为19890604
    real_time_quotes_now['list_date'].fillna(19890604, inplace=True)
    real_time_quotes_now['list_date'] = real_time_quotes_now['list_date'].replace(99990909, 19890604)

    # 将日期数值转换为日期时间格式
    real_time_quotes_now['list_date_01'] = pd.to_datetime(real_time_quotes_now['list_date'], format='%Y%m%d')

    now_date = date_handle_util.str_to_date(str_day, '%Y-%m-%d')

    # 计算日期差值 距离现在上市时间
    real_time_quotes_now['diff_days'] = real_time_quotes_now.apply(
        lambda row: (now_date - row['list_date_01']).days, axis=1)

    #  exclude b symbol
    real_time_quotes_now = common_service_fun_api.exclude_b_symbol(real_time_quotes_now.copy())

    real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['list_date_01'] <= now_date]

    now_year = int(str_day[0:4])
    last_year = now_year - 1

    query_year_line = {'year': {"$in": [str(now_year), str(last_year)]}}
    stock_qfq_year_df = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_YEAR, query_year_line)

    total_count = real_time_quotes_now.shape[0]
    global result
    result = pd.DataFrame()  # 重新初始化 result 变量
    threads = []
    page_number = round(total_count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到page_number页
        logger.info("启动第{}个线程", page + 1)

        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        page_df = real_time_quotes_now.iloc[begin_count:end_count]

        thread = threading.Thread(target=single_threaded_sync_task, args=(page_df, str_day, page, stock_qfq_year_df))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()
    # 处理失败数据
    handle_fail_data(str_day, real_time_quotes_now)
    # 返回获取的接口数据
    return result


# 单线程同步任务
def single_threaded_sync_task(page_df, str_day, page, stock_qfq_year_df):
    global result
    for stock_one in page_df.itertuples():
        try:
            k_line_df = k_line_info_clean_impl.calculate_k_line_info(str_day, stock_one.symbol, stock_one.diff_days,
                                                                     stock_qfq_year_df)
            save_k_line_data(stock_one.symbol, str_day, k_line_df)
            if k_line_df is None:
                result = k_line_df
            else:
                result = pd.concat([k_line_df, result])

        except BaseException as e:
            fail_symbol = {
                '_id': str_day + "_" + stock_one.symbol,
                'symbol': stock_one.symbol,
                'str_day': str_day}
            fail_symbol_df = pd.DataFrame(fail_symbol, index=[1])
            logger.error("k线数据清异常:{},{}", stock_one.symbol, e)
            mongodb_util.save_mongo(fail_symbol_df, K_LINE_CLEAN_DB_NAME)
    logger.info("k线数据清洗到:{}页", page + 1)
    return result


def save_k_line_data(symbol, str_day, k_line_info):
    k_line_info['_id'] = symbol + '_' + str_day
    mongodb_util.save_mongo_no_catch_exception(k_line_info, 'k_line_info')


# 创建索引
def create_k_line_index():
    mongodb_util.create_index('k_line_info', [("symbol", 1)])
    mongodb_util.create_index('k_line_info', [("str_day", 1)])
    mongodb_util.create_index('k_line_info', [("str_day", 1), ("symbol", 1)])


if __name__ == '__main__':
    sync_k_line_info_task('2025-11-13')

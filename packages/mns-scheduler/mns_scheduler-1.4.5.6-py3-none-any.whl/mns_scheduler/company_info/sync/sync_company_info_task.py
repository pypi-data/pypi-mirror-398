import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from datetime import datetime
import pandas as pd
from loguru import logger

import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.api.kpl.symbol.kpl_real_time_quotes_api as kpl_real_time_quotes_api
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
import mns_scheduler.company_info.sync.company_info_set_service as company_info_set_service
import mns_scheduler.company_info.constant.company_constant_data as company_constant_data

mongodb_util = MongodbUtil('27017')
# 分页大小
MAX_PAGE_NUMBER = 500
import threading

# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = []


# 同步公司基本信息

def sync_company_base_info(symbol_list):
    global result
    result = []

    east_money_stock_info = get_company_info()

    east_money_stock_info = common_service_fun_api.total_mv_classification(east_money_stock_info)
    east_money_stock_info = common_service_fun_api.classify_symbol(east_money_stock_info)
    # 将日期数值转换为日期时间格式
    east_money_stock_info['list_date_01'] = pd.to_datetime(east_money_stock_info['list_date'], format='%Y%m%d')
    # 开盘啦实时数据
    kpl_real_time_quotes = kpl_real_time_quotes_api.get_kpl_real_time_quotes()
    if len(symbol_list) > 0:
        east_money_stock_info = east_money_stock_info.loc[east_money_stock_info['symbol'].isin(symbol_list)]
    count = east_money_stock_info.shape[0]
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    threads = []
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        page_df = east_money_stock_info.iloc[begin_count:end_count]
        thread = threading.Thread(target=single_thread_sync_company_info,
                                  args=(page_df, kpl_real_time_quotes))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    fail_df = east_money_stock_info.loc[east_money_stock_info['symbol'].isin(result)]
    single_thread_sync_company_info(fail_df, kpl_real_time_quotes)


def single_thread_sync_company_info(east_money_stock_info,
                                    kpl_real_time_quotes):
    global result
    fail_list = []
    for company_one in east_money_stock_info.itertuples():
        try:

            company_one_df = east_money_stock_info.loc[east_money_stock_info['symbol'] == company_one.symbol]

            company_one_df = company_one_df.rename(columns={
                "industry": "em_industry",
                "concept": "em_concept"
            })
            now_date = datetime.now()
            str_day = now_date.strftime('%Y-%m-%d')
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

            # 计算日期差值 距离现在上市时间
            company_one_df['diff_days'] = (now_date - company_one.list_date_01).days
            company_one_df = company_one_df[[
                'symbol',
                'name',
                'em_industry',
                'em_concept',
                'hk_stock_code',
                'hk_stock_name',
                'amount',
                'now_price',
                'total_share',
                'flow_share',
                'total_mv',
                'flow_mv',
                'area',
                'list_date',
                'diff_days',
                'pe_ttm',
                'pb',
                'ROE',
                'flow_mv_sp',
                'total_mv_sp',
                'flow_mv_level',
                'classification',
            ]]

            company_one_df['sync_date'] = str_now_date

            # 行业信息
            company_industry_info_df = mongodb_util.find_query_data(db_name_constant.COMPANY_INDUSTRY_INFO,
                                                                    {"symbol": company_one.symbol})

            if data_frame_util.is_empty(company_industry_info_df):
                company_one_df['business_nature'] = '数据异常'
                company_one_df['holder_controller_name'] = '数据异常'
                company_one_df['holder_controller_rate'] = 0
                company_one_df['final_controller_name'] = '数据异常'
                company_one_df['final_controller_rate'] = 0
                company_one_df['actual_controller_name'] = '数据异常'
                company_one_df['actual_controller_rate'] = 0
                company_one_df['base_business'] = ''
                company_one_df['intro'] = ''
                company_one_df['address'] = ''
                company_one_df['market_id'] = ''
                company_one_df['main_business_list'] = [[] for _ in range(len(company_one_df))]
                company_one_df['most_profitable_business'] = ''
                company_one_df['most_profitable_business_rate'] = '0'
                company_one_df['most_profitable_business_profit'] = 0
                company_one_df['first_industry_code'] = '0'
                company_one_df['second_industry_code'] = '0'
                company_one_df['third_industry_code'] = '0'
                company_one_df['first_sw_industry'] = '数据异常'
                company_one_df['second_sw_industry'] = '数据异常'
                company_one_df['third_sw_industry'] = '数据异常'
                company_one_df['industry'] = '数据异常'
            else:

                del company_industry_info_df['_id']
                del company_industry_info_df['name']
                # 申万二级行业 作业行业
                company_industry_info_df['industry'] = company_industry_info_df['second_sw_industry']

                company_industry_info_df = company_industry_info_df.set_index(['symbol'], drop=True)
                company_one_df = company_one_df.set_index(['symbol'], drop=False)
                company_one_df = pd.merge(company_one_df, company_industry_info_df, how='outer',
                                          left_index=True, right_index=True)

            # 设置流通比例和外资持股
            company_one_df = company_info_set_service.set_calculate_circulation_ratio(company_one.symbol, str_day,
                                                                                      company_one_df)

            # 获取同花顺最新概念
            company_one_df = ths_concept_common_service_api.set_ths_concept(company_one.symbol, company_one_df)
            # 修改行业
            fix_symbol_industry_df = company_constant_data.get_fix_symbol_industry()
            if company_one.symbol in list(fix_symbol_industry_df['symbol']):
                # fix sw_industry
                company_one_df = company_constant_data.fix_symbol_industry(company_one_df,
                                                                           company_one.symbol)

            # 交易天数
            deal_days = k_line_common_service_api.get_deal_days(str_day, company_one.symbol)
            company_one_df['deal_days'] = deal_days

            # 设置财务年报信息
            company_one_df = company_info_set_service.set_recent_year_income(company_one.symbol, company_one_df)
            # 设置开盘信息
            company_one_df['kpl_plate_list_info'] = '-'
            company_one_df['kpl_plate_name'] = '-'
            company_one_df['kpl_most_relative_name'] = '-'
            company_one_df = company_info_set_service.set_kpl_plate_info(company_one_df, company_one,
                                                                         kpl_real_time_quotes)
            # 设置可转债 信息
            company_one_df['kzz_debt_list'] = [[] for _ in range(len(company_one_df))]
            company_one_df = company_info_set_service.set_kzz_debt(company_one_df, company_one.symbol)

            company_one_df['_id'] = company_one_df['symbol']

            company_one_df = company_constant_data.filed_sort(company_one_df)
            mongodb_util.save_mongo(company_one_df.copy(), db_name_constant.COMPANY_INFO_TEMP)
            logger.info("同步公司信息完成:{}", company_one.symbol + '-' + company_one.name)
        except BaseException as e:
            fail_list.append(company_one.symbol)
            logger.error("同步公司信息发生异常:{},{}", company_one.symbol, e)
    with result_lock:
        # 使用锁来保护 result 变量的访问，将每页的数据添加到结果中
        result = fail_list


if __name__ == '__main__':

    sync_company_base_info(['688795'])
    # sync_company_base_info([])

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.extra_income_db_name as extra_income_db_name
import mns_scheduler.finance.xue_qiu.down_load_xueqiu_report_api as down_load_xueqiu_report_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import pandas as pd
from loguru import logger
import time
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.cookie.cookie_info_service as cookie_info_service
from datetime import datetime
import mns_common.component.em.em_stock_info_api as em_stock_info_api

mongodb_util_27017 = MongodbUtil('27017')


# report_type income 利润表
# cash_flow 现金流量
# balance 资产负债
# 同步所有股票 报表
def sync_all_stocks_report():
    em_a_stock_info_df = em_stock_info_api.get_a_stock_info()
    em_a_stock_info_df = common_service_fun_api.add_pre_prefix(em_a_stock_info_df)
    # 或等效写法 df['A'].str[0:6]

    fail_list = []

    xue_qiu_cookie = cookie_info_service.get_xue_qiu_cookie()
    report_type_list = ['income', 'balance', 'cash_flow']
    for stock_one in em_a_stock_info_df.itertuples():
        fail_list = save_one_symbol_data(stock_one, report_type_list, xue_qiu_cookie, True, fail_list, '', False)

    handle_number = 0
    # 处理失败的
    while len(fail_list) > 0:
        fail_df = em_a_stock_info_df.loc[em_a_stock_info_df['symbol'].isin(fail_list)]
        for fail_one in fail_df.itertuples():
            fail_list = save_one_symbol_data(fail_one, report_type_list, xue_qiu_cookie, True, fail_list, '', False)
        handle_number = handle_number + 1
        if handle_number > 10:
            break


def save_one_symbol_data(stock_one, report_type_list, xue_qiu_cookie, save_tag, fail_list, report_name, check_exist):
    try:
        symbol_prefix = stock_one.symbol_prefix
        name = stock_one.name
        symbol = stock_one.symbol
        for report_type in report_type_list:
            if report_type == 'income':
                col_name = extra_income_db_name.XUE_QIU_LRB_INCOME
            elif report_type == 'balance':
                col_name = extra_income_db_name.XUE_QIU_ASSET_DEBT
            elif report_type == 'cash_flow':
                col_name = extra_income_db_name.XUE_QIU_CASH_FLOW
            if check_exist:
                query_exist = {'symbol': symbol, 'report_name': report_name}
                # 存在数据 不在同步
                if mongodb_util_27017.exist_data_query(col_name, query_exist):
                    continue

            index_create = [('symbol', 1), ('report_date', 1)]
            mongodb_util_27017.create_index(col_name, index_create)

            index_create_01 = [('symbol', 1), ('sync_time', 1)]
            mongodb_util_27017.create_index(col_name, index_create_01)

            if check_exist:
                # 季度同步只同步一条数据
                result_df = down_load_xueqiu_report_api.get_xue_qiu_report(symbol_prefix, report_type, xue_qiu_cookie,
                                                                           1,
                                                                           'all')
            else:
                result_df = down_load_xueqiu_report_api.get_xue_qiu_report(symbol_prefix, report_type, xue_qiu_cookie,
                                                                           200,
                                                                           'all')

            now_date = datetime.now()
            sync_time = now_date.strftime('%Y-%m-%d %H:%M:%S')

            if data_frame_util.is_empty(result_df):
                logger.error("财务信息为空,代码:{}:{}", symbol, name)
                continue
            else:
                # 季度同步check
                if check_exist:
                    result_df = result_df.loc[result_df['report_name'] == report_name]
                    if data_frame_util.is_empty(result_df):
                        continue

            result_df['sync_time'] = sync_time
            time.sleep(0.5)
            # 1. 将毫秒时间戳转为 datetime
            result_df['report_date'] = pd.to_datetime(result_df['report_date'], unit='ms')

            # 2. 格式化为 '%Y-%m-%d' 字符串
            result_df['report_date'] = result_df['report_date'].dt.strftime('%Y-%m-%d')

            result_df['_id'] = symbol + '_' + result_df['report_date']
            result_df['symbol'] = symbol

            # 1. 将毫秒时间戳转为 datetime
            result_df['ctime'] = pd.to_datetime(result_df['ctime'], unit='ms')

            # 2. 格式化为 '%Y-%m-%d' 字符串
            result_df['ctime'] = result_df['ctime'].dt.strftime('%Y-%m-%d')
            result_df.loc[result_df['report_name'].str.contains('年报'), 'period'] = 4
            result_df.loc[result_df['report_name'].str.contains('一季报'), 'period'] = 1
            result_df.loc[result_df['report_name'].str.contains('中报'), 'period'] = 2
            result_df.loc[result_df['report_name'].str.contains('三季报'), 'period'] = 3
            result_df['year'] = result_df['report_name'].str[:4]
            if save_tag:
                mongodb_util_27017.save_mongo(result_df, col_name)
            else:
                mongodb_util_27017.insert_mongo(result_df, col_name)

            if symbol in fail_list:
                fail_list.remove(symbol)
        logger.info("同步财务数据完成:{}:{}", symbol, name, report_name)
    except BaseException as e:
        logger.error("同步错误:{},异常信息:{}", symbol, e)
        fail_list.append(symbol)
    return fail_list


def sync_xue_qiu_very_period_report(report_name, symbol):
    em_a_stock_info_df = em_stock_info_api.get_a_stock_info()
    if symbol is not None:
        em_a_stock_info_df = em_a_stock_info_df.loc[em_a_stock_info_df['symbol'] == symbol]
    em_a_stock_info_df = common_service_fun_api.add_pre_prefix(em_a_stock_info_df)
    # 或等效写法 df['A'].str[0:6]

    fail_list = []

    xue_qiu_cookie = cookie_info_service.get_xue_qiu_cookie()
    report_type_list = ['income', 'balance', 'cash_flow']
    for stock_one in em_a_stock_info_df.itertuples():
        fail_list = save_one_symbol_data(stock_one, report_type_list, xue_qiu_cookie, False, fail_list, report_name,
                                         True)

    handle_number = 0
    # 处理失败的
    while len(fail_list) > 0:
        fail_df = em_a_stock_info_df.loc[em_a_stock_info_df['symbol'].isin(fail_list)]
        for fail_one in fail_df.itertuples():
            fail_list = save_one_symbol_data(fail_one, report_type_list, xue_qiu_cookie, False, fail_list, report_name,
                                             True)
        handle_number = handle_number + 1
        if handle_number > 10:
            break


if __name__ == '__main__':
    sync_all_stocks_report()

import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.api.ths.company.company_product_area_industry_index_query as company_product_area_industry_index_query
from loguru import logger
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
from datetime import datetime
from mns_scheduler.company_info.common.company_common_query_service import get_company_info

mongodb_util = MongodbUtil('27017')


def sync_company_business_task(symbol_list):
    now_date = datetime.now()
    now_year = now_date.year
    now_month = now_date.month

    if now_month in [1, 2, 3, 4]:
        period_time_year = str(now_year - 1) + "-12-31"
        sync_company_product_area_industry(symbol_list, period_time_year)

    if now_month in [4, 5, 6]:
        period_time_one = str(now_year) + "-03-31"
        sync_company_product_area_industry(symbol_list, period_time_one)

    elif now_month in [7, 8, 9]:
        period_time_two = str(now_year) + "-06-30"
        sync_company_product_area_industry(symbol_list, period_time_two)

    elif now_month in [10, 11, 12]:
        period_time_three = str(now_year) + "-09-30"
        sync_company_product_area_industry(symbol_list, period_time_three)


def sync_company_product_area_industry(symbol_list, date):
    all_company_info_df = get_company_info()

    all_company_info_df = common_service_fun_api.classify_symbol(all_company_info_df)
    if len(symbol_list) > 0:
        all_company_info_df = all_company_info_df.loc[all_company_info_df['symbol'].isin(symbol_list)]
    for stock_one in all_company_info_df.itertuples():
        try:
            symbol = stock_one.symbol

            classification = stock_one.classification
            if classification in ['H', 'K']:
                market = '17'
            elif classification in ['S', 'C']:
                market = '33'
            elif classification in ['X']:
                market = '151'

            query_exist = {'symbol': symbol, 'time': date}
            exist_company_business_info_df = mongodb_util.find_query_data(db_name_constant.COMPANY_BUSINESS_INFO,
                                                                          query_exist)
            if data_frame_util.is_empty(exist_company_business_info_df):
                exist_all = False
            else:
                exist_all = (
                        (exist_company_business_info_df.loc[
                             exist_company_business_info_df['analysis_type'] == 'area'].shape[0] > 0)
                        and (exist_company_business_info_df.loc[
                                 exist_company_business_info_df['analysis_type'] == 'industry'].shape[0] > 0)
                        and (exist_company_business_info_df.loc[
                                 exist_company_business_info_df['analysis_type'] == 'product'].shape[
                                 0] > 0))
            if exist_all:
                continue
            company_product_area_industry_list = company_product_area_industry_index_query.company_product_area_industry(
                symbol, market, date)
            for company_one in company_product_area_industry_list:
                try:
                    analysis_type = company_one['analysis_type']
                    time_operate_index_item_list = company_one['time_operate_index_item_list']
                    time_operate_index_item_df = pd.DataFrame(time_operate_index_item_list)
                    if data_frame_util.is_empty(time_operate_index_item_df):
                        continue
                    time_operate_index_item_df['symbol'] = symbol
                    time_operate_index_item_df['analysis_type'] = analysis_type

                    time_operate_index_item_df['_id'] = symbol + '_' + time_operate_index_item_df[
                        'time'] + '_' + analysis_type
                    handle_industry_area_product(time_operate_index_item_df, symbol)
                except BaseException as e:
                    logger.error("同步经营数据异常:{},{}", symbol, e)
        except BaseException as e:
            logger.error("同步经营数据异常:{},{}", stock_one.symbol, e)


def handle_industry_area_product(time_operate_index_item_df, symbol):
    if data_frame_util.is_empty(time_operate_index_item_df):
        return None

    for business_one in time_operate_index_item_df.itertuples():
        time = business_one.time
        analysis_type = business_one.analysis_type

        product_index_item_list = business_one.product_index_item_list
        for product_one in product_index_item_list:
            try:
                # 初始化数据
                income_amount = 0
                income_percent = 0
                cost_amount = 0
                cost_percent = 0
                gross_profit_amount = 0
                gross_profit_percent = 0
                gross_profit_rate_amount = 0
                gross_profit_rate_percent = 0

                product_name = product_one['product_name']
                index_analysis_list = product_one['index_analysis_list']
                for index_one in index_analysis_list:
                    try:
                        index_id = index_one['index_id']
                        if index_id == 'income':
                            income_amount = index_one['index_value']
                            income_percent = index_one['account']
                        elif index_id == 'cost':
                            cost_amount = index_one['index_value']
                            cost_percent = index_one['account']
                        elif index_id == 'gross_profit':
                            gross_profit_amount = index_one['index_value']
                            gross_profit_percent = index_one['account']

                        elif index_id == 'gross_profit_rate':
                            gross_profit_rate_amount = index_one['index_value']
                            gross_profit_rate_percent = index_one['account']
                    except BaseException as e:
                        logger.error("同步经营数据异常:{},{}", symbol, e)

                id_key = symbol + '_' + time + '_' + analysis_type + '_' + product_name
                result_dict = {
                    '_id': id_key,
                    'symbol': symbol,
                    'time': time,
                    'analysis_type': analysis_type,
                    'product_name': product_name,

                    'income_amount': income_amount,
                    'income_percent': income_percent,

                    'cost_amount': cost_amount,
                    'cost_percent': cost_percent,

                    'gross_profit_amount': gross_profit_amount,
                    'gross_profit_percent': gross_profit_percent,

                    'gross_profit_rate_amount': gross_profit_rate_amount,
                    'gross_profit_rate_percent': gross_profit_rate_percent,
                }
                result_dict_df = pd.DataFrame(result_dict, index=[1])
                mongodb_util.save_mongo(result_dict_df, db_name_constant.COMPANY_BUSINESS_INFO)
            except BaseException as e:
                logger.error("同步经营数据异常:{},{}", symbol, e)


if __name__ == '__main__':
    sync_company_product_area_industry('300211', '2024-12-31')
    # sync_company_product_area_industry('002323')
    # sync_company_product_area_industry('300901')
    # sync_company_product_area_industry('603225')
    # sync_company_product_area_industry('688039')
    # sync_company_product_area_industry('600849')
    # sync_company_product_area_industry('000508')
    # sync_company_product_area_industry('810011')

    sync_company_product_area_industry([], None)

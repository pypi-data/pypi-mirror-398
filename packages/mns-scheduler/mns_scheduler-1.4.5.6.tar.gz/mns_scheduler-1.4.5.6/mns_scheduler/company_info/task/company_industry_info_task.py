import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.company.ths_company_info_web as ths_company_info_web
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from loguru import logger
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
import time
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.common_service_fun_api as common_service_fun_api

mongodb_util = MongodbUtil('27017')


def sync_company_industry_info_task(symbol_list):
    all_company_info_df = get_company_info()
    if len(symbol_list) > 0:
        all_company_info_df = all_company_info_df.loc[all_company_info_df['symbol'].isin(symbol_list)]

    all_company_info_df = common_service_fun_api.classify_symbol(all_company_info_df)
    fail_list = []
    for stock_one in all_company_info_df.itertuples():
        try:
            tag = sync_one_company_industry_info(stock_one.symbol, stock_one.classification)
            if bool(1 - tag):
                fail_list.append(stock_one.symbol)
            time.sleep(0.5)
        except BaseException as e:
            time.sleep(1)
            logger.error("同步公司行业信息发生异常:{},{}", stock_one.symbol, e)
            fail_list.append(stock_one.symbol)
    sync_number = 1
    while len(fail_list) > 0 and sync_number < 10:
        for symbol in fail_list:
            try:
                company_info_one_df = all_company_info_df.loc[all_company_info_df['symbol'] == symbol]
                classification = list(company_info_one_df['classification'])[0]
                tag = sync_one_company_industry_info(symbol, classification)
                if tag and symbol in fail_list:
                    fail_list.remove(symbol)
                time.sleep(2)
            except BaseException as e:
                time.sleep(3)
                logger.error("同步公司行业信息发生异常:{},{}", symbol, e)
        sync_number = sync_number + 1


def sync_one_company_industry_info(symbol, classification):
    if classification in ['H', 'K']:
        market_id = '17'
    elif classification in ['S', 'C']:
        market_id = '33'
    elif classification in ['X']:
        market_id = '151'

    company_industry_info = ths_company_info_web.get_company_info_detail(symbol, market_id)
    if data_frame_util.is_empty(company_industry_info):
        return False

    company_industry_info['first_industry_code'] = company_industry_info['hycode'].apply(
        lambda x: x[1:3] + '0000')
    company_industry_info['second_industry_code'] = company_industry_info['hy2code'].apply(
        lambda x: x[1:5] + '00')
    company_industry_info['third_industry_code'] = company_industry_info['hy3code'].apply(
        lambda x: x[1:7])

    company_industry_info['first_sw_industry'] = company_industry_info['hy']
    company_industry_info['second_sw_industry'] = company_industry_info['hy2']
    company_industry_info['third_sw_industry'] = company_industry_info['hy3']
    del company_industry_info['hy']
    del company_industry_info['hy2']
    del company_industry_info['hy3']
    del company_industry_info['hycode']
    del company_industry_info['hy2code']
    del company_industry_info['hy3code']

    company_industry_info['_id'] = symbol
    company_industry_info['symbol'] = symbol
    mongodb_util.save_mongo(company_industry_info, db_name_constant.COMPANY_INDUSTRY_INFO)
    # 保存股票申万行业原始信息
    save_sw_data(company_industry_info)
    return True


# 保存申万行业分类
def save_sw_data(company_industry_info):
    first_sw_info = company_industry_info[[
        'first_sw_industry',
        'first_industry_code'
    ]].copy()

    first_sw_info.loc[:, "industry_code"] = first_sw_info['first_industry_code']
    first_sw_info.loc[:, "_id"] = first_sw_info['first_industry_code']
    first_sw_info.loc[:, "second_sw_industry"] = 0
    first_sw_info.loc[:, "third_sw_industry"] = 0
    first_sw_info.loc[:, "second_industry_code"] = 0
    first_sw_info.loc[:, "third_industry_code"] = 0
    first_sw_info = first_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(first_sw_info, 'sw_industry')

    second_sw_info = company_industry_info[[
        'first_industry_code',
        'first_sw_industry',
        'second_sw_industry',
        'second_industry_code',
    ]].copy()

    second_sw_info.loc[:, "industry_code"] = second_sw_info['second_industry_code']
    second_sw_info.loc[:, "_id"] = second_sw_info['industry_code']

    second_sw_info.loc[:, "third_sw_industry"] = 0
    second_sw_info.loc[:, "third_sw_industry"] = 0
    second_sw_info.loc[:, "third_industry_code"] = 0
    second_sw_info = second_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(second_sw_info, 'sw_industry')

    third_sw_info = company_industry_info[[
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]].copy()

    third_sw_info.loc[:, "industry_code"] = third_sw_info['third_industry_code']

    third_sw_info.loc[:, "_id"] = third_sw_info['industry_code']

    third_sw_info = third_sw_info[[
        "_id",
        "industry_code",
        'first_industry_code',
        'first_sw_industry',
        'second_industry_code',
        'second_sw_industry',
        'third_industry_code',
        'third_sw_industry'
    ]]
    mongodb_util.save_mongo(third_sw_info, 'sw_industry')


if __name__ == '__main__':
    sync_company_industry_info_task(['688795'])

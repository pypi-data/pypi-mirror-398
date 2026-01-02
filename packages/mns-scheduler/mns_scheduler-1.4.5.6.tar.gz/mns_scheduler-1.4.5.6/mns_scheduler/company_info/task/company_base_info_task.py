import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.company.ths_company_info_web as ths_company_info_web
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.constant.db_name_constant as db_name_constant
from loguru import logger
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
import time
from datetime import datetime

mongodb_util = MongodbUtil('27017')


def sync_company_base_info_task(symbol_list):
    all_company_info_df = get_company_info()
    if len(symbol_list) > 0:
        all_company_info_df = all_company_info_df.loc[all_company_info_df['symbol'].isin(symbol_list)]
    fail_list = []
    for stock_one in all_company_info_df.itertuples():
        try:
            sync_one_symbol_base_info(stock_one.symbol)
            time.sleep(0.5)
        except BaseException as e:
            time.sleep(3)
            logger.error("同步公司基础信息发生异常:{},{}", stock_one.symbol, e)
            fail_list.append(stock_one.symbol)
    sync_number = 1
    while len(fail_list) > 0 and sync_number < 10:
        for symbol in fail_list:
            try:
                sync_one_symbol_base_info(symbol)
                time.sleep(5)
            except BaseException as e:
                time.sleep(10)
                logger.error("同步公司基础信息发生异常:{},{}", symbol, e)
        sync_number = sync_number + 1


def sync_one_symbol_base_info(symbol):
    company_remark_info = ths_company_info_web.get_company_info(symbol)
    company_remark_info['_id'] = symbol
    company_remark_info['symbol'] = symbol
    company_remark_info['remark'] = ''

    now_date = datetime.now()
    sync_str_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

    company_remark_info['sync_str_date'] = sync_str_date

    exist_company_remark_df = mongodb_util.find_query_data(db_name_constant.COMPANY_BASE_INFO,
                                                           query={"symbol": symbol})
    if data_frame_util.is_not_empty(exist_company_remark_df):
        company_remark_info['remark'] = list(exist_company_remark_df['remark'])[0]
    mongodb_util.save_mongo(company_remark_info, db_name_constant.COMPANY_BASE_INFO)


if __name__ == '__main__':
    sync_company_base_info_task([])

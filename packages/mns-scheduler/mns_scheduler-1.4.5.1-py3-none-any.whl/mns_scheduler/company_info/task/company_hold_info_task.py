import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.company.ths_company_info_api as ths_company_info_api
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from datetime import datetime
from loguru import logger
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
import time

mongodb_util = MongodbUtil('27017')


# 同步公司控股子公司信息任务
def sync_one_company_hold_info(symbol):
    try:
        ths_cookie = cookie_info_service.get_ths_cookie()
        company_hold_info_df = ths_company_info_api.get_company_hold_info(symbol, ths_cookie)

        now_date = datetime.now()
        sync_str_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

        if data_frame_util.is_not_empty(company_hold_info_df):
            query_exist = {'symbol': symbol}
            exist_company_holding_info_df = mongodb_util.find_query_data(db_name_constant.COMPANY_HOLDING_INFO,
                                                                         query_exist)
            if data_frame_util.is_not_empty(exist_company_holding_info_df):
                # 作废不在参股控股的子公司
                invalid_symbol_df = exist_company_holding_info_df.loc[
                    ~exist_company_holding_info_df['symbol'].isin(list(company_hold_info_df['symbol']))]
                invalid_symbol_df['valid'] = False

            company_hold_info_df['valid'] = True
            company_hold_info_df['_id'] = company_hold_info_df['symbol'] + '_' + company_hold_info_df[
                'holding_company']
            company_hold_info_df['sync_str_date'] = sync_str_date
            mongodb_util.save_mongo(company_hold_info_df, db_name_constant.COMPANY_HOLDING_INFO)
        else:
            logger.warning("同步控股子公司为空:{}", symbol)

    except BaseException as e:
        logger.error("同步公司控股子公司信息:{},{}", symbol, e)


def sync_all_company_hold_info_task(symbol_list):
    all_company_info_df = get_company_info()
    if len(symbol_list) > 0:
        all_company_info_df = all_company_info_df.loc[all_company_info_df['symbol'].isin(symbol_list)]
    for stock_one in all_company_info_df.itertuples():
        try:
            sync_one_company_hold_info(stock_one.symbol)
            time.sleep(1)
        except BaseException as e:
            logger.error("同步控股子公司信息异常:{},{}", stock_one.symbol, e)
            time.sleep(5)


if __name__ == '__main__':
    sync_all_company_hold_info_task([])

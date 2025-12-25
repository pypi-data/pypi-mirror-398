import sys
import os
import time

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.company.ths_company_announce_api as ths_company_announce_api
from loguru import logger
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
import mns_common.component.common_service_fun_api as common_service_fun_api

mongodb_util = MongodbUtil('27017')


# 同步最新公告
# eq-f1001 业绩预告 eq-f1002 重大事项   eq-f1003 股份变动公告

def sync_company_announce_task(symbol_list):
    page_size = 100
    announce_type_list = ['all', 'eq-f1003', 'eq-f1001', 'eq-f1002']
    for announce_type_one in announce_type_list:
        try:
            get_company_announce(announce_type_one, page_size, symbol_list)
        except BaseException as e:
            logger.error("更新公告出现异常:{}", e)


def get_company_announce(announce_type, page_size, symbol_list):
    all_company_info_df = get_company_info()

    if len(symbol_list) > 0:
        all_company_info_df = all_company_info_df.loc[(all_company_info_df['symbol'].isin(symbol_list))]
    all_company_info_df = common_service_fun_api.classify_symbol(all_company_info_df)

    for stock_one in all_company_info_df.itertuples():
        try:
            symbol = stock_one.symbol
            classification = stock_one.classification
            if classification in ['H', 'K']:
                market_id = '17'
            elif classification in ['S', 'C']:
                market_id = '33'
            elif classification in ['X']:
                market_id = '151'
            # 公告应该不多 只更新一页的数据 页码设置100已经是最大
            page_number = 1
            try:
                ths_company_announce_result = ths_company_announce_api.get_company_announce_info(symbol, market_id,
                                                                                                 announce_type,
                                                                                                 page_size,
                                                                                                 page_number)
            except BaseException as e:
                logger.error("更新公告出现异常:{}.{}", e, symbol)
                continue
            ths_company_announce_result['type'] = announce_type
            ths_company_announce_result['symbol'] = symbol
            ths_company_announce_result['_id'] = ths_company_announce_result['guid'] + '_' + \
                                                 ths_company_announce_result['seq'] + "_" + announce_type
            mongodb_util.save_mongo(ths_company_announce_result, db_name_constant.COMPANY_ANNOUNCE_INFO)
            time.sleep(1)
        except BaseException as e:
            logger.error("更新公告出现异常:{}", e)


if __name__ == '__main__':
    sync_company_announce_task([])

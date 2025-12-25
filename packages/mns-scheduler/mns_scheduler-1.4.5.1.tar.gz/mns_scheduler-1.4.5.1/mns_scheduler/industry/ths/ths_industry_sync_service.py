import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_scheduler.industry.ths.ths_industry_index_service as ths_industry_index_service
from mns_common.db.MongodbUtil import MongodbUtil
import time
from datetime import datetime
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.ths.concept.app.ths_concept_detail_app as ths_concept_detail_app

mongodb_util = MongodbUtil('27017')
import mns_common.constant.db_name_constant as db_name_constant


# 同步同花顺行业指数
def sync_ths_industry_index():
    ths_industry_index_df = ths_industry_index_service.get_ths_index_by_api(1)
    if data_frame_util.is_empty(ths_industry_index_df):
        return None
    ths_industry_index_df['_id'] = ths_industry_index_df['block_code']
    ths_industry_index_df = ths_industry_index_df[[
        '_id',
        'turnover',
        'block_market',
        'block_code',
        'block_name',
        'net_inflow_of_main_force',
        'chg'
    ]]
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    ths_industry_index_df['str_now_date'] = str_now_date
    mongodb_util.save_mongo(ths_industry_index_df, db_name_constant.THS_INDUSTRY_LIST)


def sync_ths_industry_detail():
    ths_industry_list_df = mongodb_util.find_all_data(db_name_constant.THS_INDUSTRY_LIST)
    for industry_one in ths_industry_list_df.itertuples():
        try:
            time.sleep(1)
            now_date = datetime.now()
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

            ths_industry_symbol_detail_df = ths_concept_detail_app.get_ths_concept_detail_by_app(
                industry_one.block_code)
            ths_industry_symbol_detail_df = ths_industry_symbol_detail_df.rename(
                columns={"concept_code": 'ths_industry_code',
                         "concept_name": 'ths_industry_name',
                         })
            if data_frame_util.is_empty(ths_industry_symbol_detail_df):
                continue
            ths_industry_symbol_detail_df['str_now_date'] = str_now_date
            ths_industry_symbol_detail_df['_id'] = ths_industry_symbol_detail_df['symbol']
            mongodb_util.save_mongo(ths_industry_symbol_detail_df, db_name_constant.THS_STOCK_INDUSTRY_DETAIL)
            logger.info("同步ths行业股票详情:{}", industry_one.block_name)

        except BaseException as e:
            logger.error("同步ths行业股票详情异常:{}", e)


if __name__ == '__main__':
    sync_ths_industry_index()
    sync_ths_industry_detail()

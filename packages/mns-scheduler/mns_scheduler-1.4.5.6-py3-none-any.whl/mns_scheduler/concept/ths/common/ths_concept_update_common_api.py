import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
from datetime import datetime
import mns_common.api.ths.concept.web.ths_concept_detail_web as ths_concept_detail_web
mongodb_util = MongodbUtil('27017')


# 更新概念入选理由
def update_ths_concept_choose_reason(ths_symbol_all_concepts, symbol):
    all_ths_concept = ths_concept_common_service_api.get_all_ths_concept()
    for concept_one in ths_symbol_all_concepts.itertuples():
        try:
            ths_concept_one_db_list = all_ths_concept.loc[all_ths_concept['web_concept_code'] == int(concept_one.cid)]
            if data_frame_util.is_not_empty(ths_concept_one_db_list):

                for ths_one_concept in ths_concept_one_db_list.itertuples():
                    concept_code = ths_one_concept.symbol
                    query = {"$or": [{'symbol': symbol, "concept_code": int(concept_code)},
                                     {'symbol': symbol, "concept_code": int(concept_one.cid)}]}
                    short = concept_one.short
                    long = concept_one.long
                    if data_frame_util.is_string_not_empty(long):
                        new_values = {"$set": {"short": short, "long": long}}
                    else:
                        new_values = {"$set": {"grade": 0}}
                    mongodb_util.update_many(query, new_values, db_name_constant.THS_STOCK_CONCEPT_DETAIL)
        except BaseException as e:
            logger.error("更新ths概念入选理由异常{},{},{}", symbol, concept_one.title, e)


# 更新空的入选概念
def update_ths_concept_choose_null_reason():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    last_trade_day = trade_date_common_service_api.get_last_trade_day(str_day)
    query = {"$and": [{"str_day": {"$gte": last_trade_day}},
                      {"str_day": {"$lte": str_day}}],
             "$or": [{"long": ""},
                     {"long": {"$exists": False}}]}
    nan_reason_df = mongodb_util.find_query_data(db_name_constant.TODAY_NEW_CONCEPT_LIST, query)
    update_null_reason(nan_reason_df)

    nan_reason_df_detail = mongodb_util.find_query_data(db_name_constant.THS_STOCK_CONCEPT_DETAIL, query)
    update_null_reason(nan_reason_df_detail)


# 更新空入选理由
def update_null_reason(nan_reason_df):
    # 所有概念
    all_ths_concept = ths_concept_common_service_api.get_all_ths_concept()
    for nan_one in nan_reason_df.itertuples():
        try:
            concept_code = nan_one.concept_code
            ths_concept_one_df = all_ths_concept.loc[
                (all_ths_concept['symbol'] == concept_code)
                | (all_ths_concept['web_concept_code'] == concept_code)]
            if data_frame_util.is_empty(ths_concept_one_df):
                continue
            web_concept_code = list(ths_concept_one_df['web_concept_code'])[0]

            symbol_ths_concept_all_df = ths_concept_detail_web.get_one_symbol_all_ths_concepts(nan_one.symbol)

            symbol_ths_concept_one_df = symbol_ths_concept_all_df[
                symbol_ths_concept_all_df['cid'] == web_concept_code]
            if data_frame_util.is_empty(symbol_ths_concept_one_df):
                continue

            query = {"$or": [{'symbol': nan_one.symbol, "concept_code": int(concept_code)},
                             {'symbol': nan_one.symbol, "concept_code": int(web_concept_code)}]}
            short = list(symbol_ths_concept_one_df['short'])[0]
            long = list(symbol_ths_concept_one_df['long'])[0]
            new_values = {"$set": {"short": short, "long": long}}
            mongodb_util.update_many(query, new_values, db_name_constant.THS_STOCK_CONCEPT_DETAIL)
            mongodb_util.update_many(query, new_values, db_name_constant.TODAY_NEW_CONCEPT_LIST)
        except BaseException as e:
            logger.error("更新概念入选理由异常:{},{}", nan_one.symbol, e)


if __name__ == '__main__':
    update_ths_concept_choose_null_reason()

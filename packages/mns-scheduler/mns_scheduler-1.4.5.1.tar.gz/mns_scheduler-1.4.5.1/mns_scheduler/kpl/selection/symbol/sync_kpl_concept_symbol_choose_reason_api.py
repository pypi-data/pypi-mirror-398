import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.kpl.common.kpl_common_api as kpl_common_api
from loguru import logger
from datetime import datetime, timedelta
import pandas as pd

mongodb_util = MongodbUtil('27017')


# 更新所有概念入选原因
def update_all_kpl_symbol_choose_reason():
    kpl_best_choose_index_df = mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX, {})
    for concept_one in kpl_best_choose_index_df.itertuples():
        try:
            concept_code = concept_one.plate_code
            kpl_best_choose_index_detail_df = mongodb_util.find_query_data(
                db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL, {"plate_code": concept_code})
            if data_frame_util.is_not_empty(kpl_best_choose_index_detail_df):
                kpl_symbol_list = list(kpl_best_choose_index_detail_df['symbol'])
                symbol_str = ','.join(kpl_symbol_list)
                choose_reason_df = kpl_common_api.get_kpl_concept_choose_reason(concept_code, symbol_str)
                if data_frame_util.is_not_empty(choose_reason_df):
                    for choose_reason_one in choose_reason_df.itertuples():
                        symbol = choose_reason_one.symbol
                        try:

                            choose_reason = choose_reason_one.choose_reason
                            update_query = {'symbol': symbol, 'plate_code': concept_code}
                            new_values = {"$set": {"long": choose_reason}}
                            mongodb_util.update_many(update_query, new_values,
                                                     db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL)
                        except BaseException as e:
                            logger.error("更新开票啦入选原因异常:{},{},{}", symbol, concept_code, e)
            logger.info("更新开票啦入选原因完成:{},{}", concept_one.plate_code, concept_one.plate_name)
        except BaseException as e:
            logger.error("更新开票啦入选原因异常:{},{},{}", concept_one.plate_code, concept_one.plate_name, e)


# 更新入选概念原因
def update_symbol_new_concept_reason(plate_code, kpl_symbol_list):
    symbol_str = ','.join(kpl_symbol_list)
    choose_reason_df = kpl_common_api.get_kpl_concept_choose_reason(plate_code, symbol_str)
    if data_frame_util.is_not_empty(choose_reason_df):
        choose_reason_df = choose_reason_df[choose_reason_df['choose_reason'] != '']
        if data_frame_util.is_empty(choose_reason_df):
            return
        for choose_reason_one in choose_reason_df.itertuples():
            symbol = choose_reason_one.symbol
            try:

                choose_reason = choose_reason_one.choose_reason
                update_query = {'symbol': symbol, 'plate_code': plate_code}
                new_values = {"$set": {"long": choose_reason}}
                mongodb_util.update_many(update_query, new_values,
                                         db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL)
                # 更新今日新增概念列表 入选原因
                mongodb_util.update_many(update_query, new_values,
                                         db_name_constant.TODAY_NEW_CONCEPT_LIST)
            except BaseException as e:
                logger.error("更新开票啦入选原因异常:{},{},{}", symbol, plate_code, e)


def update_null_choose_reason():
    # 获取当前日期时间
    now = datetime.now()

    # 计算前15天的日期时间
    days_ago_15 = now - timedelta(days=30)

    # 按指定格式输出
    formatted_date = days_ago_15.strftime("%Y-%m-%d %H:%M:%S")
    query = {"create_time": {"$gte": formatted_date}, '$or': [{"long": {"$exists": False}}, {"long": ''}]}
    null_choose_reason_detail_df = mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL, query)
    if data_frame_util.is_not_empty(null_choose_reason_detail_df):
        grouped_null_reason_df = null_choose_reason_detail_df.groupby('plate_code')
        grouped_null_reason_list = grouped_null_reason_df.size()
        group_null_reason = pd.DataFrame(grouped_null_reason_list, columns=['number'])
        group_null_reason['plate_code'] = group_null_reason.index
        group_null_reason = group_null_reason.sort_values(by=['number'], ascending=False)
        for null_reason_one in group_null_reason.itertuples():
            plate_code = null_reason_one.plate_code
            try:

                null_reason_one_plate_df = null_choose_reason_detail_df.loc[
                    null_choose_reason_detail_df['plate_code'] == plate_code]
                kpl_symbol_list = list(null_reason_one_plate_df['symbol'])
                update_symbol_new_concept_reason(plate_code, kpl_symbol_list)
                logger.info("更新开票啦入选原因完成:{},{}", null_reason_one.plate_code,
                            list(null_reason_one_plate_df['plate_name'])[0])
            except BaseException as e:
                logger.error("更新kpl入选原因异常:{},{}", null_reason_one.plate_code, e)

    return formatted_date


if __name__ == '__main__':
    update_null_choose_reason()
    # update_all_kpl_symbol_choose_reason()

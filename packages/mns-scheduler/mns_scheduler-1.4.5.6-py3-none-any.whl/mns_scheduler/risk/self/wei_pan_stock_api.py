import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_scheduler.concept.ths.detaill.ths_concept_detail_api as ths_concept_detail_api
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
from datetime import datetime
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.constant.black_list_classify_enum import BlackClassify


def add_concept_to_lack_list(concept_code, reason):
    new_concept_symbol_list = ths_concept_detail_api.get_ths_concept_detail(concept_code, None)
    if data_frame_util.is_empty(new_concept_symbol_list):
        return None

    now_date = datetime.now()
    str_now_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    for stock_one in new_concept_symbol_list.itertuples():
        try:
            symbol = stock_one.symbol
            key_id = str(concept_code) + "_" + symbol
            black_list_service_api.save_black_stock(
                key_id,
                symbol,
                stock_one.name,
                str_now_day,
                str_now_date,
                reason,
                reason,
                '',
                BlackClassify.SELF_SHIELD_OTHER.up_level_code,
                BlackClassify.SELF_SHIELD_OTHER.up_level_name,
                BlackClassify.SELF_SHIELD_OTHER.level_code,
                BlackClassify.SELF_SHIELD_OTHER.level_name,

            )
        except BaseException as e:
            logger.error("概念拉黑异常:{}", e)


# 微盘股拉黑
if __name__ == '__main__':
    reason_detail = '微盘股拉黑'
    concept_code_wei_pan = '883418'
    add_concept_to_lack_list(concept_code_wei_pan, reason_detail)

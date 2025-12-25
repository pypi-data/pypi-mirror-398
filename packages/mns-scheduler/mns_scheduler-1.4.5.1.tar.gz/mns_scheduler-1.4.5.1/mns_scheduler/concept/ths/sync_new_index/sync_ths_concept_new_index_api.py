import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.concept.app.ths_concept_index_app as ths_concept_index_app
import mns_scheduler.concept.ths.common.ths_concept_sync_common_api as ths_concept_sync_common_api
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger
import mns_common.api.ths.concept.web.ths_concept_index_web as ths_concept_index_web
from mns_common.db.MongodbUtil import MongodbUtil
from datetime import datetime
import mns_scheduler.concept.clean.ths_concept_clean_api as ths_concept_clean_api
import pandas as pd
import mns_scheduler.concept.ths.detaill.ths_concept_detail_api as ths_concept_detail_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.redis_msg.redis_msg_publish_service as redis_msg_publish_service
import mns_common.constant.redis_msg_constant as redis_msg_constant

mongodb_util = MongodbUtil('27017')
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api


def sync_ths_concept_new_index():
    # 同步ths新概念 通过app搜索
    sync_ths_concept_new_index_from_app()
    # 通过ths详情搜索
    sync_ths_concept_new_index_from_detail()


'''
同步ths新概念 通过app搜索代码
'''


def sync_ths_concept_new_index_from_app():
    # 当前最大概念代码
    max_concept_code = int(ths_concept_sync_common_api.get_max_concept_code())
    # 最大概念代码上限
    max_concept_code_limit = max_concept_code + 2
    # 同花顺概念列表
    ths_concept_list_exist = ths_concept_common_service_api.get_all_ths_concept()
    # 同步向上3次
    while max_concept_code <= max_concept_code_limit:
        try:
            max_concept_code = max_concept_code + 1
            concept_new_index_df = ths_concept_index_app.get_new_concept_from_app_search(max_concept_code)
            if data_frame_util.is_empty(concept_new_index_df):
                continue
            concept_name = list(concept_new_index_df['concept_name'])[0]

            if data_frame_util.is_string_empty(concept_name):
                concept_name = ths_concept_index_web.get_concept_name(max_concept_code)

            exist_concept_df_one = ths_concept_list_exist.loc[
                (ths_concept_list_exist['symbol'] == max_concept_code)
                | (ths_concept_list_exist['web_concept_code'] == max_concept_code)]
            now_date = datetime.now()
            str_now_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
            str_day = now_date.strftime('%Y-%m-%d')
            if data_frame_util.is_empty(exist_concept_df_one):
                concept_code = max_concept_code

                url = 'http://q.10jqka.com.cn/thshy/detail/code/' + str(concept_code)
                new_concept_one = {
                    '_id': int(concept_code),
                    'symbol': int(concept_code),
                    'name': concept_name,
                    'url': url,
                    'str_day': str_day,
                    'success': True,
                    'str_now_time': str_now_time,
                    'web_concept_code': concept_code,
                    'web_concept_url': url,
                    'valid': True,
                    'grade': 1,
                    'remark': ''
                }
                diff_one_df = pd.DataFrame(new_concept_one, index=[1])
                # 保存新增概念信息
                mongodb_util.save_mongo(diff_one_df, db_name_constant.THS_CONCEPT_LIST)
                # 新增概念信息处理 推送到微信
                ths_concept_sync_common_api.push_msg_to_we_chat_and_redis(concept_code, concept_name,
                                                                          url)
                #    同步概念详情到db
                ths_concept_detail_api.sync_ths_concept_detail_to_db(concept_code, concept_name)
                # 更新ths概念统计信息
                ths_concept_clean_api.update_ths_concept_info()

                logger.info("新增同花顺新概念:{}", concept_name)

        except BaseException as e:
            logger.error("同步新增概念代码:{},信息异常:{}", max_concept_code, e)


'''
同步新概念 by ths detail 通过详情判断
'''


def sync_ths_concept_new_index_from_detail():
    # 当前最大概念代码
    max_concept_code = ths_concept_sync_common_api.get_max_concept_code()
    # 最大概念代码上线
    max_concept_code_limit = max_concept_code + 2
    # 同花顺概念列表
    ths_concept_list_exist = mongodb_util.find_all_data(db_name_constant.THS_CONCEPT_LIST)
    # 同步向上3次
    while max_concept_code <= max_concept_code_limit:
        try:
            max_concept_code = max_concept_code + 1
            concept_code = max_concept_code
            concept_name = ths_concept_index_web.get_concept_name(concept_code)
            new_concept_symbol_detail_df = ths_concept_detail_api.get_ths_concept_detail(concept_code, concept_name)
            if data_frame_util.is_empty(new_concept_symbol_detail_df):
                continue

            exist_concept_df_one = ths_concept_list_exist.loc[
                (ths_concept_list_exist['symbol'] == concept_code)
                | (ths_concept_list_exist['web_concept_code'] == concept_code)]
            now_date = datetime.now()
            str_now_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
            str_day = now_date.strftime('%Y-%m-%d')
            if data_frame_util.is_empty(exist_concept_df_one):
                concept_code = max_concept_code

                url = 'http://q.10jqka.com.cn/thshy/detail/code/' + str(concept_code)
                new_concept_one = {
                    '_id': int(concept_code),
                    'symbol': int(concept_code),
                    'name': concept_name,
                    'url': url,
                    'str_day': str_day,
                    'success': True,
                    'str_now_time': str_now_time,
                    'web_concept_code': concept_code,
                    'web_concept_url': url,
                    'valid': True,
                    'grade': 1,
                    'remark': ''
                }
                diff_one_df = pd.DataFrame(new_concept_one, index=[1])
                mongodb_util.save_mongo(diff_one_df, db_name_constant.THS_CONCEPT_LIST)
                # 新增概念信息处理
                ths_concept_sync_common_api.push_msg_to_we_chat_and_redis(concept_code, concept_name,
                                                                          url)

                new_concept_symbol_detail_df.loc[:, 'way'] = 'index_sync'
                ths_concept_sync_common_api.save_ths_concept_detail(new_concept_symbol_detail_df,
                                                                    concept_name,
                                                                    str_day,
                                                                    str_now_time,
                                                                    concept_code)

                logger.info("新增同花顺新概念:{}", concept_name)

        except BaseException as e:
            logger.error("同步新增概念代码:{},信息异常:{}", max_concept_code, e)
    # 更新ths概念统计信息
    ths_concept_clean_api.update_ths_concept_info()
    # 项目之间推送消息
    redis_msg_publish_service.send_redis_msg(redis_msg_constant.THS_CONCEPT_MSG_TOPIC,
                                             redis_msg_constant.THS_NEW_CONCEPT_ADD_MSG)


if __name__ == '__main__':
    sync_ths_concept_new_index()

import sys
import os
import mns_common.component.concept.kpl_concept_common_service_api as kpl_concept_common_service_api
import mns_common.api.kpl.selection.kpl_selection_plate_api as selection_plate_api
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
import mns_scheduler.kpl.selection.index.sync_best_choose_index as sync_best_choose_first_index
import mns_scheduler.kpl.selection.symbol.sync_best_choose_symbol as sync_best_choose_symbol
import threading
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.api.kpl.constant.kpl_constant as kpl_constant
import mns_scheduler.kpl.selection.symbol.sync_kpl_concept_symbol_choose_reason_api as sync_kpl_concept_symbol_choose_reason_api

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

mongodb_util = MongodbUtil('27017')

# 分页大小
MAX_PAGE_NUMBER = 10


# 同步开盘啦精选概念股票组成
def sync_best_choose_symbol_detail(first_index_df, page_number):
    for stock_one in first_index_df.itertuples():
        try:
            # 保存一级精选指数股票组成
            sync_best_choose_symbol.save_one_plate_detail_data(stock_one.plate_code,
                                                               stock_one.plate_name,
                                                               kpl_constant.FIRST_INDEX,
                                                               stock_one.plate_code,
                                                               stock_one.plate_name)

            kpl_best_choose_sub_index_detail = selection_plate_api.best_choose_sub_index(stock_one.plate_code)

            if data_frame_util.is_not_empty(kpl_best_choose_sub_index_detail):
                for sub_one in kpl_best_choose_sub_index_detail.itertuples():
                    try:
                        sync_best_choose_symbol.save_one_plate_detail_data(sub_one.plate_code,
                                                                           sub_one.plate_name,
                                                                           kpl_constant.SUB_INDEX,
                                                                           stock_one.plate_code,
                                                                           stock_one.plate_name)
                    except BaseException as e:
                        logger.error("同步开盘啦精选板块二级指数详情异常:{},{}", sub_one.plate_code, e)

        except BaseException as e:
            logger.error("同步开盘啦精选板块二级指数异常:{},{}", stock_one.plate_code, e)


def multi_thread_sync_kpl_best_choose_detail():
    first_index_df = sync_best_choose_first_index.choose_field_choose_first_index()
    count = first_index_df.shape[0]
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    threads = []
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        page_df = first_index_df.iloc[begin_count:end_count]
        thread = threading.Thread(target=sync_best_choose_symbol_detail, args=(page_df, page_number))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()


# 同步所有精选指数信息
def sync_all_plate_info():
    # 同步第一和第二级别精选指数
    # 更新一级和二级之间的关联关系
    # 找出新增精选指数
    sync_best_choose_first_index.sync_best_choose_index()
    logger.info("同步开盘啦精选概念指数完成")
    # 同步精选概念股票组成
    multi_thread_sync_kpl_best_choose_detail()
    logger.info("同步开盘啦精选概念股票组成完成")
    # 更新开盘啦空名字名称
    update_null_name()
    logger.info("更新开盘啦空名字名称")

    # 更新开盘啦入选原因
    sync_kpl_concept_symbol_choose_reason_api.update_null_choose_reason()
    logger.info("更新开盘啦入选原因")


# 更新一二级关系
def update_best_choose_plate_relation():
    first_index_df = sync_best_choose_first_index.choose_field_choose_first_index()
    kpl_all_concept_df = kpl_concept_common_service_api.get_kpl_all_concept()
    for first_index_df_one in first_index_df.itertuples():
        try:
            kpl_best_choose_sub_index_detail = selection_plate_api.best_choose_sub_index(first_index_df_one.plate_code)
            # 更新指数级别

            kpl_one_concept_df_first = kpl_all_concept_df.loc[
                kpl_all_concept_df['plate_code'] == first_index_df_one.plate_code]

            if data_frame_util.is_not_empty(kpl_one_concept_df_first):
                kpl_one_concept_df_first_exist = kpl_one_concept_df_first.loc[
                    kpl_one_concept_df_first['index_class'] == kpl_constant.FIRST_INDEX]
                if data_frame_util.is_not_empty(kpl_one_concept_df_first_exist):
                    update_query = {"plate_code": first_index_df_one.plate_code}
                    new_values = {"$set": {"first_plate_code": first_index_df_one.plate_code,
                                           "heat_score": first_index_df_one.heat_score,
                                           "plate_name": first_index_df_one.plate_name,
                                           "first_plate_name": first_index_df_one.plate_name}}
                    mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)
                else:
                    update_query = {"plate_code": first_index_df_one.plate_code}
                    new_values = {"$set": {
                        "first_plate_code": first_index_df_one.plate_code,
                        "first_plate_name": first_index_df_one.plate_name,
                        "plate_name": first_index_df_one.plate_name,
                        "index_class": kpl_constant.SUB_INDEX}}
                    mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)

            if data_frame_util.is_not_empty(kpl_best_choose_sub_index_detail):
                update_query = {"plate_code": {"$in": list(kpl_best_choose_sub_index_detail['plate_code'])}}
                new_values = {"$set": {"first_plate_code": first_index_df_one.plate_code,
                                       "first_plate_name": first_index_df_one.plate_name}}
                mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)
        except BaseException as e:
            logger.error("同步开盘啦精选板块指数关系异常:{},{}", first_index_df_one.plate_code, e)
    # 更新二级指数关系
    update_sub_index_relation(first_index_df, kpl_all_concept_df)


def update_sub_index_relation(first_index_df, kpl_all_concept_df):
    kpl_sub_concept_df_exist = kpl_all_concept_df.loc[
        kpl_all_concept_df['index_class'] == kpl_constant.SUB_INDEX]
    kpl_sub_concept_df_change = first_index_df.loc[
        first_index_df['plate_code'].isin(list(kpl_sub_concept_df_exist['plate_code']))]
    if data_frame_util.is_not_empty(kpl_sub_concept_df_change):
        update_query = {"plate_code": {"$in": list(kpl_sub_concept_df_change['plate_code'])}}
        new_values = {"$set": {"index_class": kpl_constant.FIRST_INDEX}}
        mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)


def update_null_name():
    query = {"plate_name": ''}
    kpl_best_choose_index_df = mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX, query)
    if data_frame_util.is_empty(kpl_best_choose_index_df):
        return
    else:
        kpl_best_choose_index_df_sub = kpl_best_choose_index_df.loc[
            kpl_best_choose_index_df["index_class"] == kpl_constant.SUB_INDEX]
        if data_frame_util.is_not_empty(kpl_best_choose_index_df_sub):
            for sub_one in kpl_best_choose_index_df_sub.itertuples():
                try:
                    first_plate_code = sub_one.first_plate_code
                    sub_plate_code = sub_one.plate_code
                    kpl_best_choose_sub_index_detail = selection_plate_api.best_choose_sub_index(first_plate_code)
                    sub_kpl_best_choose_sub_index_detail = kpl_best_choose_sub_index_detail.loc[
                        kpl_best_choose_sub_index_detail['plate_code'] == sub_plate_code]
                    if data_frame_util.is_not_empty(sub_kpl_best_choose_sub_index_detail):
                        plate_name = list(sub_kpl_best_choose_sub_index_detail['plate_name'])[0]
                        new_values = {"$set": {"plate_name": plate_name}}
                        update_query = {"plate_code": sub_plate_code}
                        mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)
                except BaseException as e:
                    logger.error("更新板块kpl概念名称出现异常:{},{}", sub_plate_code, e)
        kpl_best_choose_index_df_first = kpl_best_choose_index_df.loc[
            kpl_best_choose_index_df["index_class"] == kpl_constant.FIRST_INDEX]
        if data_frame_util.is_not_empty(kpl_best_choose_index_df_first):
            for first_one in kpl_best_choose_index_df_sub.itertuples():
                try:
                    first_plate_code = first_one.plate_code
                    first_index_df = sync_best_choose_first_index.choose_field_choose_first_index()
                    first_index_df_one = first_index_df.loc[first_index_df['plate_code'] == first_plate_code]
                    if data_frame_util.is_not_empty(first_index_df_one):
                        plate_name = list(first_index_df_one['plate_name'])[0]
                        new_values = {"$set": {"plate_name": plate_name}}
                        update_query = {"plate_code": first_plate_code}
                        mongodb_util.update_many(update_query, new_values, db_name_constant.KPL_BEST_CHOOSE_INDEX)
                except BaseException as e:
                    logger.error("更新板块kpl概念名称出现异常:{},{}", first_plate_code, e)

    return kpl_best_choose_index_df


if __name__ == '__main__':
    # update_null_name()
    # update_best_choose_plate_relation()

    # 同步第一和第二级别精选指数
    sync_all_plate_info()

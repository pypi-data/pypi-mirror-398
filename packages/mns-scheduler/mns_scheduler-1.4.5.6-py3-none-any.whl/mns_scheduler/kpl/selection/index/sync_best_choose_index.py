import sys
import os
import mns_common.api.kpl.selection.kpl_selection_plate_api as selection_plate_api
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
from datetime import datetime
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.msg.push_msg_api as push_msg_api
import time as sleep_time
import threading
import pandas as pd

import mns_common.api.kpl.constant.kpl_constant as kpl_constant

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

mongodb_util = MongodbUtil('27017')
# 定义一个全局锁，用于保护 result 变量的访问
result_lock = threading.Lock()
# 初始化 result 变量为一个空的 Pandas DataFrame
result = pd.DataFrame()

# 同步精选指数
file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
# 分页大小
MAX_PAGE_NUMBER = 10


# 获取精选一级指数
def choose_field_choose_first_index():
    data_df = selection_plate_api.best_choose()
    data_df['_id'] = data_df['plate_code']
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    data_df['sync_str_day'] = str_day
    data_df['sync_str_time'] = str_now_date
    data_df['index_class'] = kpl_constant.FIRST_INDEX
    return data_df


# 多线程分片同步
def multithread_shard_sync_index(first_kpl_df, page_number):
    global result
    for first_kpl_one in first_kpl_df.itertuples():
        try:
            kpl_best_choose_sub_index_detail = selection_plate_api.best_choose_sub_index(first_kpl_one.plate_code)
            if data_frame_util.is_not_empty(kpl_best_choose_sub_index_detail):
                # 保存第二级精选指数
                sync_best_choose_second_index(kpl_best_choose_sub_index_detail, first_kpl_one.plate_code)
                sub_plate_code_list = kpl_best_choose_sub_index_detail.to_string(index=False)
                # 更新第一级和第二级指数关联关系
                update_first_index_sub_index(first_kpl_one.plate_code, sub_plate_code_list)
                first_kpl_df.loc[
                    first_kpl_df['plate_code'] == first_kpl_one.plate_code, "sub_plate_code_list"] = sub_plate_code_list

        except BaseException as e:
            logger.error("处理一级精选指数异常:{}", e)
    with result_lock:
        # 使用锁来保护 result 变量的访问，将每页的数据添加到结果中
        result = pd.concat([result, first_kpl_df], ignore_index=True)


# 同步第一和第二级别精选指数  更新一级和二级之间的关联关系
def sync_best_choose_index():
    global result
    result = pd.DataFrame()  # 重新初始化 result 变量
    first_index_df = choose_field_choose_first_index()
    first_index_df.loc[:, "sub_plate_code_list"] = '-'

    count = first_index_df.shape[0]
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)

    threads = []

    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        page_df = first_index_df.iloc[begin_count:end_count]
        thread = threading.Thread(target=multithread_shard_sync_index, args=(page_df, page_number))
        threads.append(thread)
        thread.start()

        # 等待所有线程完成
    for thread in threads:
        thread.join()

    exist_code_df = mongodb_util.find_query_data_choose_field('kpl_best_choose_index',
                                                              {},
                                                              {"plate_code": 1})

    if data_frame_util.is_not_empty(exist_code_df):
        exist_code_list = list(exist_code_df['plate_code'])
        new_data_df = result.loc[~(result['plate_code'].isin(exist_code_list))]
    else:
        new_data_df = result.copy()

    if data_frame_util.is_empty(new_data_df):
        return None
    # 处理一级指数
    handle_new_kpl_index(new_data_df, kpl_constant.FIRST_INDEX, None)
    return result


# 处理新增指数数据
def handle_new_kpl_index(new_data_df, index_class, first_plate_code):
    for new_data_one in new_data_df.itertuples():
        try:
            concept_code = new_data_one.plate_code
            concept_name = new_data_one.plate_name
            msg = "概念代码:" + str(concept_code) + "," + "概念名称:" + concept_name + ",指数级别" + index_class
            title = "新增开盘啦精选概念:" + str(concept_code) + "-" + concept_name
            push_msg_api.push_msg_to_wechat(title, msg)
            sleep_time.sleep(1)
        except BaseException as e:
            logger.error("推送出现异常:{}", e)
    # 保存新数据
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    if first_plate_code is not None:
        new_data_df['first_plate_code'] = first_plate_code
    else:
        new_data_df['first_plate_code'] = new_data_one.plate_code

    new_data_df['create_day'] = str_day
    new_data_df['create_time'] = str_now_date
    new_data_df.loc[:, "create_day"] = str_day
    new_data_df.loc[:, "create_time"] = str_now_date
    new_data_df.loc[:, "valid"] = True
    new_data_df = new_data_df[["_id",
                               "plate_code",
                               "plate_name",
                               "heat_score",
                               "index_class",
                               "sync_str_day",
                               "sync_str_time",
                               "create_day",
                               "create_time",
                               "first_plate_code",
                               "valid"]]
    mongodb_util.insert_mongo(new_data_df, 'kpl_best_choose_index')


# 更新第一级精选指数 次级指数关系
def update_first_index_sub_index(first_plate_code, sub_plate_code_list):
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    new_values = {"$set": {"sub_plate_code_list": sub_plate_code_list,
                           "sync_str_day": str_day,
                           "sync_str_time": str_now_date}}
    query = {'plate_code': first_plate_code}
    mongodb_util.update_many(query, new_values, "kpl_best_choose_index")


# 同步二级精选指数
def sync_best_choose_second_index(kpl_best_choose_sub_index_detail, first_plate_code):
    kpl_best_choose_sub_index_detail['_id'] = kpl_best_choose_sub_index_detail['plate_code']
    kpl_best_choose_sub_index_detail['index_class'] = kpl_constant.SUB_INDEX
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    sync_str_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    kpl_best_choose_sub_index_detail['sync_str_day'] = str_day
    kpl_best_choose_sub_index_detail['sync_str_time'] = sync_str_date

    exist_code_df = mongodb_util.find_query_data_choose_field('kpl_best_choose_index',
                                                              {},
                                                              {"plate_code": 1})

    if data_frame_util.is_not_empty(exist_code_df):
        exist_code_list = list(exist_code_df['plate_code'])
        new_data_df = kpl_best_choose_sub_index_detail.loc[
            ~(kpl_best_choose_sub_index_detail['plate_code'].isin(exist_code_list))]
    else:
        new_data_df = kpl_best_choose_sub_index_detail.copy()
    if data_frame_util.is_empty(new_data_df):
        return None

    handle_new_kpl_index(new_data_df, kpl_constant.SUB_INDEX, first_plate_code)

import os
import sys
import mns_common.api.ths.concept.web.ths_concept_detail_web as ths_concept_detail_web
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.common_service_fun_api as common_service_fun_api
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
from datetime import datetime
from mns_common.utils.async_fun import async_fun
import mns_scheduler.concept.ths.common.ths_concept_sync_common_api as ths_concept_sync_common_api
import threading
import mns_scheduler.concept.ths.common.ths_concept_update_common_api as ths_concept_update_common_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.redis_msg.redis_msg_publish_service as redis_msg_publish_service
import mns_common.constant.redis_msg_constant as redis_msg_constant

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
mongodb_util = MongodbUtil('27017')
# 分页大小
MAX_PAGE_NUMBER = 2500


# 获取单只股票新增概念


def create_index():
    mongodb_util.create_index(db_name_constant.THS_STOCK_CONCEPT_DETAIL_APP, [("symbol", 1)])
    mongodb_util.create_index(db_name_constant.THS_STOCK_CONCEPT_DETAIL_APP, [("str_day", 1)])
    mongodb_util.create_index(db_name_constant.THS_STOCK_CONCEPT_DETAIL_APP, [("title", 1)])
    mongodb_util.create_index(db_name_constant.THS_STOCK_CONCEPT_DETAIL_APP, [("str_now_date", 1)])


# 同步新概念到详情表中
# @async_fun
def sync_new_concept_to_ths_detail(symbol_add_new_concept_df, str_day, str_now_time):
    for new_concept_one in symbol_add_new_concept_df.itertuples():
        try:
            web_concept_code = new_concept_one.concept_code
            query = {'web_concept_code': int(web_concept_code)}
            ths_concept_list = mongodb_util.find_query_data('ths_concept_list', query)
            if data_frame_util.is_empty(ths_concept_list):
                logger.error("无此同花顺概念:{}", new_concept_one.title)
            else:
                concept_code = list(ths_concept_list['symbol'])[0]
                concept_name = list(ths_concept_list['name'])[0]
                ths_concept_sync_common_api.save_ths_concept_detail(symbol_add_new_concept_df,
                                                                    concept_name, str_day,
                                                                    str_now_time, concept_code)

        except BaseException as e:
            logger.error("转换同花顺概念异常:{},{}", new_concept_one, e)
    # 项目之间推送消息
    redis_msg_publish_service.send_redis_msg(redis_msg_constant.THS_CONCEPT_MSG_TOPIC,
                                             redis_msg_constant.THS_NEW_CONCEPT_ADD_MSG)


# 保存数据到对比
@async_fun
def save_data_to_db(ths_concept_df):
    if data_frame_util.is_empty(ths_concept_df):
        return
    json_data = ths_concept_df.to_dict(orient='records')
    mongodb_util.save_mongo_json(json_data, db_name_constant.THS_STOCK_CONCEPT_DETAIL_APP)


# 对比数据库和接口概念详情的差值
def choose_new_concept_from_compare_db(ths_concept_df, symbol_ths_new_concept_exist_db):
    if data_frame_util.is_empty(symbol_ths_new_concept_exist_db):
        return ths_concept_df
    else:
        symbol_add_new_concept = ths_concept_df.loc[~(
            ths_concept_df['_id'].isin(list(symbol_ths_new_concept_exist_db['_id'])))]
        return symbol_add_new_concept


# 选择接口返回为新概念标识的数据
def choose_type_new_concept(ths_concept_df):
    filtered_df = ths_concept_df[
        ths_concept_df['label'].apply(lambda x: any(item['type'] == 'new' for item in x))]
    if data_frame_util.is_empty(filtered_df):
        return
    return ths_concept_df


# 同步新概念 多线程实现
def update_symbol_new_concept(symbol_df, page_number):
    for stock_one in symbol_df.itertuples():
        try:
            symbol_ths_concept_all_df = ths_concept_detail_web.get_one_symbol_all_ths_concepts(stock_one.symbol)
            logger.info("同步代码{},所有概念信息", stock_one.symbol)
            if data_frame_util.is_empty(symbol_ths_concept_all_df):
                continue

            now_date = datetime.now()
            # 开盘交易前不同步 资源开销过大
            if date_handle_util.is_close_time(now_date):
                ths_concept_update_common_api.update_ths_concept_choose_reason(symbol_ths_concept_all_df,
                                                                               stock_one.symbol)

            str_day = now_date.strftime('%Y-%m-%d')
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
            symbol_ths_concept_all_df.loc[:, 'str_day'] = str_day
            symbol_ths_concept_all_df.loc[:, 'str_now_date'] = str_now_date
            symbol_ths_concept_all_df.loc[:, 'symbol'] = stock_one.symbol
            symbol_ths_concept_all_df.loc[:, 'name'] = stock_one.name
            symbol_ths_concept_all_df.loc[:, 'index'] = 1
            symbol_ths_concept_all_df.loc[:, 'now_price'] = stock_one.now_price
            symbol_ths_concept_all_df.loc[:, 'chg'] = stock_one.chg
            symbol_ths_concept_all_df.loc[:, 'change'] = stock_one.now_price - stock_one.open
            symbol_ths_concept_all_df.loc[:, 'exchange'] = stock_one.exchange
            symbol_ths_concept_all_df.loc[:, 'amount'] = stock_one.amount
            symbol_ths_concept_all_df.loc[:, 'concept_create_day'] = str_day

            symbol_ths_concept_all_df['concept_code'] = symbol_ths_concept_all_df['cid'].apply(str)
            symbol_ths_concept_all_df['name'] = symbol_ths_concept_all_df['name'].replace(" ", "")

            symbol_ths_concept_all_df.loc[:, '_id'] = symbol_ths_concept_all_df['symbol'] + '_' + \
                                                      symbol_ths_concept_all_df['concept_code']

            query = {'symbol': stock_one.symbol}
            query_field = {"_id": 1}
            # 已经存在的数据
            symbol_ths_new_concept_exist_db = mongodb_util.find_query_data_choose_field('ths_stock_concept_detail_app',
                                                                                        query, query_field)
            # 与存在的概念对比 找出新增概念
            symbol_add_new_concept_db_df = choose_new_concept_from_compare_db(symbol_ths_concept_all_df,
                                                                              symbol_ths_new_concept_exist_db)
            # 接口中带new 标记的数据
            symbol_add_new_concept_api_df = choose_type_new_concept(symbol_ths_concept_all_df)

            symbol_add_new_concept_df = data_frame_util.merge_choose_data_no_drop(symbol_add_new_concept_api_df,
                                                                                  symbol_add_new_concept_db_df)
            if data_frame_util.is_empty(symbol_add_new_concept_df):
                continue

            symbol_add_new_concept_df.drop_duplicates('_id', keep='last', inplace=True)

            if data_frame_util.is_empty(symbol_ths_new_concept_exist_db):
                symbol_add_new_concept_df = symbol_add_new_concept_df
            else:
                symbol_add_new_concept_df = symbol_add_new_concept_df.loc[~(
                    symbol_add_new_concept_df['_id'].isin(list(symbol_ths_new_concept_exist_db['_id'])))]
            if data_frame_util.is_empty(symbol_add_new_concept_df):
                continue
            # 保存到概念详情集合中
            save_data_to_db(symbol_add_new_concept_df)
            sync_new_concept_to_ths_detail(symbol_add_new_concept_df, str_day, str_now_date)
            logger.info("symbol新增概念信息:{},{}", stock_one.symbol, stock_one.name)
        except BaseException as e:
            logger.error("发生异常:{},{}", e, stock_one.symbol)


def sync_symbol_all_concept(symbol):
    create_index()
    real_time_quotes_now = em_stock_info_api.get_a_stock_info()
    real_time_quotes_now = common_service_fun_api.classify_symbol(real_time_quotes_now)
    if symbol is not None:
        real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['symbol'] == symbol]
    count = real_time_quotes_now.shape[0]
    page_number = round(count / MAX_PAGE_NUMBER, 0) + 1
    page_number = int(page_number)
    threads = []
    # 创建多个线程来获取数据
    for page in range(page_number):  # 0到100页
        end_count = (page + 1) * MAX_PAGE_NUMBER
        begin_count = page * MAX_PAGE_NUMBER
        if symbol is None:
            page_df = real_time_quotes_now.loc[begin_count:end_count]
        else:
            page_df = real_time_quotes_now
        thread = threading.Thread(target=update_symbol_new_concept, args=(page_df, page_number))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()


if __name__ == '__main__':
    sync_symbol_all_concept(None)

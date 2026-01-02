import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.api.ths.concept.app.ths_concept_detail_app as ths_concept_detail_app
import mns_common.api.ths.wen_cai.ths_wen_cai_api as ths_wen_cai_api
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.api.ths.concept.web.ths_concept_detail_web as ths_concept_detail_web
import math
from loguru import logger
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util
import time
from datetime import datetime
import mns_scheduler.concept.ths.common.ths_concept_sync_common_api as ths_concept_sync_common_api
import mns_common.component.redis_msg.redis_msg_publish_service as redis_msg_publish_service
import mns_common.constant.redis_msg_constant as redis_msg_constant


def get_ths_concept_detail(concept_code, concept_name):
    real_time_quotes_all_stocks = em_stock_info_api.get_a_stock_info()
    # 1  通过入选理获取概念组成股票详情
    ths_concept_detail_by_explain = get_ths_concept_detail_by_explain(concept_code, real_time_quotes_all_stocks)
    # 2 app 分享链接获取概念组成详情
    ths_concept_detail_from_app = get_ths_concept_detail_from_app(concept_code, real_time_quotes_all_stocks)
    # 3 通过问财
    if concept_name is None or data_frame_util.is_string_empty(concept_name):
        ths_concept_list = ths_concept_common_service_api.get_all_ths_concept()
        ths_concept_one_df = ths_concept_list.loc[
            (ths_concept_list['symbol'] == int(concept_code))
            | (ths_concept_list['web_concept_code'] == int(concept_code))]
        if data_frame_util.is_not_empty(ths_concept_one_df):
            concept_name = list(ths_concept_one_df['name'])[0]
    # if data_frame_util.is_string_not_empty(concept_name) and concept_name is not None:
    #     concept_detail_by_wen_cai_df = get_ths_concept_detail_by_wen_cai(concept_name, real_time_quotes_all_stocks)
    # else:
    concept_detail_by_wen_cai_df = None
    # 4 通过web端
    ths_concept_detail_from_web_df = get_ths_concept_detail_from_web(concept_code, real_time_quotes_all_stocks)
    # 判断是否都为空
    all_are_none = all(
        df is None for df in [ths_concept_detail_by_explain, ths_concept_detail_from_app,
                              concept_detail_by_wen_cai_df, ths_concept_detail_from_web_df])
    if all_are_none:
        return None
    result_df = pd.concat([ths_concept_detail_by_explain, ths_concept_detail_from_app,
                           concept_detail_by_wen_cai_df, ths_concept_detail_from_web_df])

    result_df.drop_duplicates('symbol', keep='last', inplace=True)
    if data_frame_util.is_not_empty(ths_concept_detail_by_explain):
        ths_concept_detail_by_explain_new = ths_concept_detail_by_explain.loc[
            ths_concept_detail_by_explain['symbol'].isin(result_df['symbol'])]

        not_in_ths_concept_detail_by_explain = result_df.loc[~(
            result_df['symbol'].isin(ths_concept_detail_by_explain['symbol']))]
        result_df = pd.concat([ths_concept_detail_by_explain_new, not_in_ths_concept_detail_by_explain])
    result_df['concept_code'] = concept_code
    result_df['change'] = 0
    result_df['index'] = 0
    return result_df


# 通过入选理获取概念组成股票详情
def get_ths_concept_detail_by_explain(concept_code, real_time_quotes_all_stocks):
    page_size = 800

    de_list_symbols = company_common_service_new_api.get_de_list_company()
    real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
        ~(real_time_quotes_all_stocks['symbol'].isin(de_list_symbols))]

    max_page_number = math.ceil(real_time_quotes_all_stocks.shape[0] / page_size)
    page = 0

    result_df = None

    while page < max_page_number:
        try:

            begin_index = page * page_size
            end_index = (page + 1) * page_size
            page_df = real_time_quotes_all_stocks.iloc[begin_index: end_index]
            code_list = ','.join(page_df['symbol'].astype(str))
            all_ths_concept_detail = ths_concept_detail_app.get_concept_explain(concept_code, code_list)
            if data_frame_util.is_empty(result_df) and data_frame_util.is_not_empty(all_ths_concept_detail):
                result_df = all_ths_concept_detail
            elif data_frame_util.is_not_empty(result_df) and data_frame_util.is_not_empty(all_ths_concept_detail):
                result_df = pd.concat([all_ths_concept_detail, result_df])
        except BaseException as e:
            logger.error("通过ths概念入选理由列表获取详情异常:{},{}", concept_code, e)
        page = page + 1
    if data_frame_util.is_not_empty(result_df):
        result_df = result_df[result_df['explain'].astype(str).str.len() > 0]
    if data_frame_util.is_not_empty(result_df):
        result_df = result_df.rename(columns={
            "stockCode": "symbol",
            "explain": "long"})
        result_df = merge_data_common_fun(result_df, real_time_quotes_all_stocks)
        return result_df
    else:
        return None


# 通过分享链接获取
def get_ths_concept_detail_from_app(concept_code, real_time_quotes_all_stocks):
    ths_concept_detail_from_app = ths_concept_detail_app.get_ths_concept_detail_by_app(concept_code)
    if data_frame_util.is_not_empty(ths_concept_detail_from_app):
        ths_concept_detail_from_app['long'] = ''
        ths_concept_detail_from_app = ths_concept_detail_from_app[[
            'symbol',
            'long'
        ]]
        ths_concept_detail_from_app = merge_data_common_fun(ths_concept_detail_from_app,
                                                            real_time_quotes_all_stocks)
        return ths_concept_detail_from_app

    else:
        return None


# 3 通过问财
def get_ths_concept_detail_by_wen_cai(concept_name, real_time_quotes_all_stocks):
    concept_detail_by_wen_cai_df = ths_wen_cai_api.get_concept_detail_by_wen_cai(concept_name)
    if data_frame_util.is_not_empty(concept_detail_by_wen_cai_df):
        concept_detail_by_wen_cai_df = concept_detail_by_wen_cai_df[[
            'symbol',
            'explain'
        ]]

        concept_detail_by_wen_cai_df = concept_detail_by_wen_cai_df.rename(columns={
            "explain": "long"})
        concept_detail_by_wen_cai_df = merge_data_common_fun(concept_detail_by_wen_cai_df,
                                                             real_time_quotes_all_stocks)

    return concept_detail_by_wen_cai_df


# 通过web端 最近不可用
def get_ths_concept_detail_from_web(concept_code, real_time_quotes_all_stocks):
    ths_concept_detail_from_web_df = ths_concept_detail_web.stock_board_cons_ths(concept_code)
    if data_frame_util.is_not_empty(ths_concept_detail_from_web_df):
        ths_concept_detail_from_web_df = ths_concept_detail_from_web_df[[
            'symbol'
        ]]
        ths_concept_detail_from_web_df['long'] = ''

        ths_concept_detail_from_web_df = merge_data_common_fun(ths_concept_detail_from_web_df,
                                                               real_time_quotes_all_stocks)

    return ths_concept_detail_from_web_df


def merge_data_common_fun(result_df, real_time_quotes_all_stocks):
    real_time_quotes_ths_detail = real_time_quotes_all_stocks.loc[
        real_time_quotes_all_stocks['symbol'].isin(result_df['symbol'])]
    real_time_quotes_ths_detail = common_service_fun_api.total_mv_classification(real_time_quotes_ths_detail)
    real_time_quotes_ths_detail = real_time_quotes_ths_detail[[
        "symbol",
        "name",
        "now_price",
        "chg",
        "exchange",
        "amount",
        "flow_mv_sp",
        "total_mv_sp"]]

    query_field = {
        "concept_name": 1,
        "concept_code": 1,
        "company_type": 1,
        "concept_create_day": 1,
        "first_relevance_industry": 1,
        "second_relevance_industry": 1,
        "industry": 1
    }
    query_field_key = str(query_field)
    query_key = str({})
    company_df = company_common_service_new_api.get_company_info_by_field(query_key, query_field_key)
    company_ths_df = company_df.loc[company_df['_id'].isin(result_df['symbol'])]

    result_df['short'] = result_df['long']
    result_df = result_df.set_index(['symbol'], drop=True)
    company_ths_df = company_ths_df.set_index(['_id'], drop=True)
    real_time_quotes_ths_detail = real_time_quotes_ths_detail.set_index(['symbol'], drop=False)
    result_df = pd.merge(real_time_quotes_ths_detail, result_df,
                         how='outer',
                         left_index=True, right_index=True)
    result_df = pd.merge(result_df, company_ths_df,
                         how='outer',
                         left_index=True, right_index=True)
    return result_df


# 同步概念详情到db
def sync_ths_concept_detail_to_db(concept_code, concept_name):
    new_concept_symbol_detail_df = get_ths_concept_detail(concept_code, concept_name)
    if data_frame_util.is_empty(new_concept_symbol_detail_df):
        time.sleep(10)
        return None
    now_date = datetime.now()
    str_now_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
    time.sleep(1)
    str_day = now_date.strftime('%Y-%m-%d')
    new_concept_symbol_detail_df.loc[:, 'way'] = 'index_sync'
    ths_concept_sync_common_api.save_ths_concept_detail(new_concept_symbol_detail_df,
                                                        concept_name,
                                                        str_day,
                                                        str_now_time, concept_code)

    # 项目之前推送消息
    redis_msg_publish_service.send_redis_msg(redis_msg_constant.THS_CONCEPT_MSG_TOPIC,
                                             redis_msg_constant.THS_NEW_CONCEPT_ADD_MSG)


if __name__ == '__main__':
    sync_ths_concept_detail_to_db('886090', '智谱AI')
    # real_time_quotes_all_stocks_df = east_money_stock_api.get_real_time_quotes_all_stocks()
    # get_ths_concept_detail_by_explain('886084', real_time_quotes_all_stocks_df)
    # get_ths_concept_detail_from_web('886084', real_time_quotes_all_stocks_df)
    # get_ths_concept_detail('886084', '光纤概念')
    # get_ths_concept_detail_by_wen_cai('光纤概念', real_time_quotes_all_stocks_df)

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.company.company_common_service_api as company_common_service_api
from loguru import logger
from datetime import datetime
import time
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_scheduler.irm.api.sh_stock_sns_sse_info_api as sh_stock_sns_sse_info_api
import mns_scheduler.irm.api.sz_stock_sns_sse_info_api as sz_stock_sns_sse_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_scheduler.irm.stock_question_id_service as stock_question_id_service

mongodb_util = MongodbUtil('27017')


# 获取股票提问    互动易-提问 todo 深交所 可以拉取未回答的,但是最拉到最近三个月
def get_stock_irm_cninfo_sz_api(symbol):
    try:
        org_ask_id = stock_question_id_service.get_one_sz_symbol_org_id(symbol)
        # 获取一页
        stock_irm_cninfo_df = sz_stock_sns_sse_info_api.stock_irm_cninfo(symbol,
                                                                         org_ask_id,
                                                                         1,
                                                                         100)
        # 获取全页
        # stock_irm_cninfo_df = ak.stock_irm_cninfo(symbol)
    except Exception as e:
        logger.error("获取提问者异常:{},{}", symbol, e)
        return pd.DataFrame()
    if data_frame_util.is_empty(stock_irm_cninfo_df):
        return pd.DataFrame()
    stock_irm_cninfo_df = stock_irm_cninfo_df.rename(columns={"股票代码": "symbol",
                                                              "公司简称": "name",
                                                              "行业": "industry",
                                                              "行业代码": "industry_code",
                                                              "问题": "question",
                                                              '提问者': "questioner",
                                                              '来源': "source",
                                                              '提问时间': "question_time",
                                                              '更新时间': "answer_time",
                                                              "提问者编号": "questioner_no",
                                                              "问题编号": "question_no",
                                                              "回答ID": "answer_id",
                                                              "回答内容": "answer_content",
                                                              "回答者": "answer"
                                                              })
    stock_irm_cninfo_df['_id'] = stock_irm_cninfo_df['symbol'] + '_' + stock_irm_cninfo_df['question_no']
    stock_irm_cninfo_df = stock_irm_cninfo_df[[
        '_id',
        "symbol",
        "name",
        "question",
        "answer_content",
        "question_time",
        "answer_time",
        "questioner",
        "source"]]
    return stock_irm_cninfo_df


# 获取股票提问    互动易-提问 todo 上交所
def get_stock_irm_cninfo_sh_api(symbol):
    try:
        # 获取一页
        org_ask_id = stock_question_id_service.get_one_sh_symbol_org_id(symbol)

        stock_sns_sse_info_df = sh_stock_sns_sse_info_api.stock_sns_sse_info(org_ask_id,
                                                                             1,
                                                                             100)
        # 获取全页
        # stock_sns_sse_info_df = ak.stock_sns_sseinfo(symbol)
    except Exception as e:
        logger.error("获取提问者异常:{},{}", symbol, e)
        return pd.DataFrame()
    if data_frame_util.is_empty(stock_sns_sse_info_df):
        return pd.DataFrame()

    stock_sns_sse_info_df = stock_sns_sse_info_df.rename(columns={"股票代码": "symbol",
                                                                  "公司简称": "name",
                                                                  "问题": "question",
                                                                  "回答": "answer_content",
                                                                  '问题时间': "question_time",
                                                                  '回答时间': "answer_time",
                                                                  '用户名': "questioner",
                                                                  '问题来源': "source"
                                                                  })
    stock_sns_sse_info_df['question_time'] = stock_sns_sse_info_df['question_time'].apply(replace_date_format)
    stock_sns_sse_info_df['answer_time'] = stock_sns_sse_info_df['answer_time'].apply(replace_date_format)
    stock_sns_sse_info_df['_id'] = stock_sns_sse_info_df['symbol'] + '_' + stock_sns_sse_info_df['question_time']
    stock_sns_sse_info_df = stock_sns_sse_info_df[[
        "_id",
        "symbol",
        "name",
        "question",
        "answer_content",
        "question_time",
        "answer_time",
        "questioner",
        "source"]]
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    stock_sns_sse_info_df.loc[
        stock_sns_sse_info_df['answer_time'].str.contains('小时前', na=False), 'answer_time'] = str_now_date
    stock_sns_sse_info_df.loc[
        stock_sns_sse_info_df['answer_time'].str.contains('分钟前', na=False), 'answer_time'] = str_now_date
    stock_sns_sse_info_df.loc[
        stock_sns_sse_info_df['question_time'].str.contains('小时前', na=False), 'question_time'] = str_now_date
    stock_sns_sse_info_df.loc[
        stock_sns_sse_info_df['question_time'].str.contains('分钟前', na=False), 'answer_time'] = str_now_date

    return stock_sns_sse_info_df


# 格式化 时间
def replace_date_format(date_str):
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    last_day = date_handle_util.add_date(str_day, -1)

    return date_str.replace('年', '-').replace('月', '-').replace('日', '').replace('昨天', last_day)


# 同步所有互动问题
def sync_symbols_interactive_questions(symbol_list):
    real_time_quotes_all_stocks = em_stock_info_api.get_a_stock_info()
    de_list_company_symbols = company_common_service_api.get_de_list_company()
    real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
        ~(real_time_quotes_all_stocks['symbol'].isin(de_list_company_symbols))]
    real_time_quotes_all_stocks = common_service_fun_api.classify_symbol(real_time_quotes_all_stocks)
    real_time_quotes_all_stocks = real_time_quotes_all_stocks.sort_values(by=['amount'], ascending=False)
    fail_symbol_list = []
    if len(symbol_list) != 0:
        real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
            real_time_quotes_all_stocks['symbol'].isin(symbol_list)]

    real_time_quotes_all_stocks = real_time_quotes_all_stocks.reset_index(drop=True)
    for stock_one in real_time_quotes_all_stocks.itertuples():
        try:
            now_date = datetime.now()
            str_day = now_date.strftime('%Y-%m-%d')
            str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
            classification = stock_one.classification

            if classification in ['S', 'C']:
                stock_irm_cninfo_df = get_stock_irm_cninfo_sz_api(stock_one.symbol)
                time.sleep(1)
            elif classification in ['K', 'H']:
                stock_irm_cninfo_df = get_stock_irm_cninfo_sh_api(stock_one.symbol)
                time.sleep(1)

            else:
                continue
            if data_frame_util.is_empty(stock_irm_cninfo_df):
                continue
            stock_irm_cninfo_df['sync_time'] = str_now_date
            stock_irm_cninfo_df['str_day'] = str_day
            stock_irm_cninfo_df.drop_duplicates('_id', keep='last', inplace=True)
            stock_irm_cninfo_df.fillna("", inplace=True)

            stock_irm_cninfo_df['valid'] = True
            stock_irm_cninfo_df['answer_content'].fillna('')
            # 保存新增数据
            save_new_data(stock_irm_cninfo_df)
            logger.info("完成同步互动回答到:{}", stock_one.symbol)
        except Exception as e:
            time.sleep(5)
            fail_symbol_list.append(stock_one.symbol)
            logger.error("同步互动问题出现异常:{},{}", stock_one.symbol, e)


# 保存新增回答数据
def save_new_data(stock_irm_cninfo_df):
    if data_frame_util.is_empty(stock_irm_cninfo_df):
        return None
    else:
        irm_id_list = list(stock_irm_cninfo_df['_id'])
        query = {"_id": {"$in": irm_id_list}, 'answer_content': {"$ne": ''}}
        query_field = {"_id": 1}

        exist_df = mongodb_util.find_query_data_choose_field(db_name_constant.STOCK_INTERACTIVE_QUESTION, query,
                                                             query_field)
        if data_frame_util.is_empty(exist_df):
            new_df = stock_irm_cninfo_df
        else:
            new_df = stock_irm_cninfo_df.loc[~(stock_irm_cninfo_df['_id'].isin(list(exist_df['_id'])))]
        if data_frame_util.is_not_empty(new_df):
            mongodb_util.save_mongo(new_df, db_name_constant.STOCK_INTERACTIVE_QUESTION)


if __name__ == '__main__':
    get_stock_irm_cninfo_sz_api('000002')
    sync_symbols_interactive_questions([])
    # sync_symbols_interactive_questions([])
    # get_stock_irm_cninfo_sh_api('688778')
    # fail_symbol_list_01 = ['000638', '002886', '688778', '688766', '688733', '688778', '688793', '688787']
    # get_stock_irm_cninfo_sh_api('603633')
    # sync_symbols_interactive_questions(None)

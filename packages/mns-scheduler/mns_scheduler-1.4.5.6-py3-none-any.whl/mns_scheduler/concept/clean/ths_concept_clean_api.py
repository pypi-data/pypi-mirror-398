import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd
import mns_common.api.ths.concept.web.ths_concept_index_web as ths_concept_index_web
import time
from loguru import logger
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
import mns_common.api.ths.concept.app.ths_concept_index_app as ths_concept_index_app

mongodb_util = MongodbUtil('27017')


# 统计概念股票数量和行业分组信息
def update_ths_concept_info():
    ths_concept_list = mongodb_util.find_all_data(db_name_constant.THS_CONCEPT_LIST)
    for ths_concept_one in ths_concept_list.itertuples():
        try:
            update_one_concept_relevance_industry(ths_concept_one.symbol)
        except BaseException as e:
            logger.error("更新概念信息异常:{},{}", e, ths_concept_one.name)


# 更新一个概念行业相关
def update_one_concept_relevance_industry(concept_code):
    query = {'concept_code': concept_code}
    ths_stock_concept_detail_df = (mongodb_util
                                   .find_query_data(db_name_constant.THS_STOCK_CONCEPT_DETAIL, query))
    concept_count = ths_stock_concept_detail_df.shape[0]
    ths_concept_list = ths_concept_common_service_api.get_all_ths_concept()
    ths_concept_list_one_df = ths_concept_list.loc[ths_concept_list['symbol'] == concept_code]
    ths_concept_list_one_df['concept_count'] = concept_count

    ths_stock_concept_detail_df = ths_stock_concept_detail_df.reset_index(drop=True)
    if 'industry' in ths_stock_concept_detail_df.columns:
        del ths_stock_concept_detail_df['industry']

    company_info_df = company_common_service_api.get_company_info_industry()
    company_info_df = company_info_df[['_id', 'industry']]
    company_info_df = company_info_df.loc[
        company_info_df['_id'].isin(list(ths_stock_concept_detail_df['symbol']))]
    company_info_df = company_info_df.set_index(['_id'], drop=True)

    ths_stock_concept_detail_df = ths_stock_concept_detail_df.set_index(['symbol'], drop=False)
    ths_stock_concept_detail_df = pd.merge(ths_stock_concept_detail_df, company_info_df,
                                           how='outer',
                                           left_index=True, right_index=True)
    ths_stock_concept_detail_df.dropna(subset=['industry'], axis=0, inplace=True)

    grouped = ths_stock_concept_detail_df.groupby('industry')
    result_list = grouped.size()
    ths_concept_group = pd.DataFrame(result_list, columns=['number'])
    ths_concept_group['industry'] = ths_concept_group.index
    ths_concept_group = ths_concept_group.sort_values(by=['number'], ascending=False)
    if ths_concept_group.shape[0] >= 2:
        first_relevance_industry = list(ths_concept_group.iloc[0:1]['industry'])[0]
        first_relevance_industry_number = list(ths_concept_group.iloc[0:1]['number'])[0]
        second_relevance_industry = list(ths_concept_group.iloc[1:2]['industry'])[0]
        second_relevance_industry_number = list(ths_concept_group.iloc[1:2]['number'])[0]
    else:
        first_relevance_industry = list(ths_concept_group.iloc[0:1]['industry'])[0]
        first_relevance_industry_number = list(ths_concept_group.iloc[0:1]['number'])[0]
        second_relevance_industry = '无'
        second_relevance_industry_number = 0
    ths_concept_list_one_df['first_relevance_industry'] = first_relevance_industry
    ths_concept_list_one_df['second_relevance_industry'] = second_relevance_industry
    ths_concept_list_one_df['first_relevance_industry_number'] = first_relevance_industry_number
    ths_concept_list_one_df['second_relevance_industry_number'] = second_relevance_industry_number

    ths_stock_concept_detail_df['first_relevance_industry'] = first_relevance_industry
    ths_stock_concept_detail_df['second_relevance_industry'] = second_relevance_industry

    new_values_list = {"$set": {"first_relevance_industry": first_relevance_industry,
                                "second_relevance_industry": second_relevance_industry,
                                "first_relevance_industry_number": first_relevance_industry_number,
                                "second_relevance_industry_number": second_relevance_industry_number,
                                "concept_count": concept_count
                                }}

    update_query = {"symbol": concept_code}
    mongodb_util.update_one_query(update_query, new_values_list, db_name_constant.THS_CONCEPT_LIST)

    new_values_detail = {"$set": {"first_relevance_industry": first_relevance_industry,
                                  "second_relevance_industry": second_relevance_industry

                                  }}
    update_query_detail = {"concept_code": concept_code}
    mongodb_util.update_one_query(update_query_detail, new_values_detail, db_name_constant.THS_STOCK_CONCEPT_DETAIL)


# 更新空名字
def update_null_name():
    query = {"_id": {'$gte': 886025}}
    ths_concept_list = mongodb_util.find_query_data('ths_concept_list', query)
    ths_concept_list = ths_concept_list.sort_values(by=['_id'], ascending=False)

    for concept_one in ths_concept_list.itertuples():
        concept_code = concept_one.symbol
        name = concept_one.name
        exist_url = concept_one.url

        if name == '':
            concept_name = ths_concept_index_web.get_concept_name(concept_code)
            query_concept = {"symbol": concept_code}
            new_values = {'$set': {"name": concept_name}}
            mongodb_util.update_one_query(query_concept, new_values, 'ths_concept_list')

            new_values_detail = {'$set': {"concept_name": concept_name}}

            query_concept_detail = {"concept_code": concept_code}

            mongodb_util.update_many(query_concept_detail, new_values_detail, 'ths_stock_concept_detail')
            time.sleep(10)

        if exist_url == '' or pd.isna(exist_url):
            url = 'http://q.10jqka.com.cn/thshy/detail/code/' + str(concept_code)
            str_now_time = concept_one.str_day + " " + "00:00:00"
            query_concept = {"symbol": concept_code}
            new_values = {'$set': {"url": url, "str_now_time": str_now_time}}
            mongodb_util.update_one_query(query_concept, new_values, 'ths_concept_list')


if __name__ == '__main__':
    # update_one_concept_relevance_industry(886095)
    update_null_name()
    logger.info("开始")
    update_ths_concept_info()
    logger.info("结束")
    update_null_name()

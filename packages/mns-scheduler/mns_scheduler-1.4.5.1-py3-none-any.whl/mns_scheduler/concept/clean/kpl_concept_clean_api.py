import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
from loguru import logger
import mns_common.component.company.company_common_service_api as company_common_service_api

mongodb_util = MongodbUtil('27017')
import pandas as pd


# 开盘啦
def update_kpl_concept_info():
    query = {}
    kpl_best_choose_index_df = mongodb_util.find_query_data(db_name_constant.KPL_BEST_CHOOSE_INDEX, query)
    for kpl_concept_one in kpl_best_choose_index_df.itertuples():
        try:
            query_detail = {"plate_code": kpl_concept_one.plate_code}
            kpl_best_choose_index_detail_df = mongodb_util.find_query_data(
                db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL,
                query_detail)
            concept_count = kpl_best_choose_index_detail_df.shape[0]
            kpl_best_choose_index_one_df = kpl_best_choose_index_df.loc[
                kpl_best_choose_index_df['plate_code'] == kpl_concept_one.plate_code]
            kpl_best_choose_index_one_df['concept_count'] = concept_count

            kpl_best_choose_index_detail_df = kpl_best_choose_index_detail_df.reset_index(drop=True)

            if 'industry' in kpl_best_choose_index_detail_df.columns:
                del kpl_best_choose_index_detail_df['industry']

            company_info_df = company_common_service_api.get_company_info_industry()
            company_info_df = company_info_df[['_id', 'industry']]
            company_info_df = company_info_df.loc[
                company_info_df['_id'].isin(list(kpl_best_choose_index_detail_df['symbol']))]
            company_info_df = company_info_df.set_index(['_id'], drop=True)

            kpl_best_choose_index_detail_df = kpl_best_choose_index_detail_df.set_index(['symbol'], drop=False)
            kpl_best_choose_index_detail_df = pd.merge(kpl_best_choose_index_detail_df, company_info_df,
                                                       how='outer',
                                                       left_index=True, right_index=True)
            kpl_best_choose_index_detail_df.dropna(subset=['industry'], axis=0, inplace=True)

            grouped = kpl_best_choose_index_detail_df.groupby('industry')
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
            kpl_best_choose_index_one_df['first_relevance_industry'] = first_relevance_industry
            kpl_best_choose_index_one_df['second_relevance_industry'] = second_relevance_industry
            kpl_best_choose_index_one_df['first_relevance_industry_number'] = first_relevance_industry_number
            kpl_best_choose_index_one_df['second_relevance_industry_number'] = second_relevance_industry_number

            kpl_best_choose_index_detail_df['first_relevance_industry'] = first_relevance_industry
            kpl_best_choose_index_detail_df['second_relevance_industry'] = second_relevance_industry

            mongodb_util.save_mongo(kpl_best_choose_index_one_df, db_name_constant.KPL_BEST_CHOOSE_INDEX)
            mongodb_util.save_mongo(kpl_best_choose_index_detail_df, db_name_constant.KPL_BEST_CHOOSE_INDEX_DETAIL)

        except Exception as e:
            logger.error("更新开盘啦概念异常:{},{}", e, kpl_concept_one.plate_name)


if __name__ == '__main__':
    update_kpl_concept_info()

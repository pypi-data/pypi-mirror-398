import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.component.em.em_stock_info_api as em_stock_info_api
import akshare as ak
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
from functools import lru_cache
import mns_common.component.zt.zt_common_service_api as zt_common_service_api

mongodb_util = MongodbUtil('27017')


# 获取陆股通的列表
@lru_cache(maxsize=None)
def get_hk_ggt_component():
    stock_hk_ggt_components_em_df = ak.stock_hk_ggt_components_em()
    stock_hk_ggt_components_em_df = stock_hk_ggt_components_em_df.rename(columns={
        "序号": "index",
        "代码": "symbol",
        "名称": "name"
    })
    return stock_hk_ggt_components_em_df


# 获取em cookie
@lru_cache(maxsize=None)
def get_em_cookie():
    query = {"type": "em_cookie"}
    stock_account_info = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    cookie = list(stock_account_info['cookie'])[0]
    return cookie


def sync_hk_company_industry():
    hk_real_time_df = em_stock_info_api.get_hk_stock_info()

    hk_real_time_df = hk_real_time_df[[
        "symbol",
        "name",
        "chg",
        "total_mv",
        "flow_mv",
        "list_date",
        "industry",
        "amount",
        "now_price"
    ]]
    hk_real_time_df = hk_real_time_df.loc[(hk_real_time_df['total_mv'] != '-')]
    hk_real_time_df['total_mv'] = hk_real_time_df['total_mv'].astype(float)
    hk_real_time_df['flow_mv'] = hk_real_time_df['flow_mv'].astype(float)
    hk_real_time_df = hk_real_time_df.loc[hk_real_time_df['total_mv'] != 0]

    hk_real_time_df.loc[hk_real_time_df['industry'] == '-', 'industry'] = '其他'

    group_industry_df = zt_common_service_api.group_by_industry(hk_real_time_df, 'industry')
    group_industry_df['_id'] = group_industry_df['industry']
    mongodb_util.remove_all_data(db_name_constant.HK_COMPANY_INDUSTRY)
    mongodb_util.save_mongo(group_industry_df, db_name_constant.HK_COMPANY_INDUSTRY)


if __name__ == '__main__':
    sync_hk_company_industry()

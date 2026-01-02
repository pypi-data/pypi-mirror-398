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
import mns_common.api.hk.ths_hk_company_info_api as ths_hk_company_info_api
import pandas as pd

mongodb_util = MongodbUtil('27017')
from loguru import logger


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


@lru_cache(maxsize=None)
def get_ths_cookie():
    query = {"type": "ths_cookie"}
    stock_account_info = mongodb_util.find_query_data(db_name_constant.STOCK_ACCOUNT_INFO, query)
    cookie = list(stock_account_info['cookie'])[0]
    return cookie


# https://quote.eastmoney.com/center/gridlist.html#hk_stocks
def sync_hk_company_info():
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
    # 排除基金
    hk_real_time_df = hk_real_time_df.loc[hk_real_time_df['total_mv'] != '-']

    stock_hk_ggt_components_em_df = get_hk_ggt_component()
    stock_hk_ggt_components_symbol_list = list(stock_hk_ggt_components_em_df['symbol'])
    hk_real_time_df['hk_ggt'] = False
    hk_real_time_df.loc[hk_real_time_df['symbol'].isin(stock_hk_ggt_components_symbol_list), 'hk_ggt'] = True
    hk_real_time_df.loc[hk_real_time_df['industry'] == '-', 'industry'] = '其他'

    hk_real_time_df['_id'] = hk_real_time_df['symbol']

    hk_real_time_df.fillna(0, inplace=True)
    mongodb_util.remove_all_data(db_name_constant.COMPANY_INFO_HK)
    hk_real_time_df = hk_real_time_df.sort_values(by=['hk_ggt'], ascending=False)
    for stock_one in hk_real_time_df.itertuples():
        try:
            symbol = stock_one.symbol
            ths_cookie = get_ths_cookie()
            company_hk_df = ths_hk_company_info_api.get_hk_company_info(symbol, ths_cookie)

            company_hk_df = company_hk_df.rename(columns={
                "industry": "industry_detail",
                "list_date": "list_date_str",
            })

            hk_real_time_one_df = hk_real_time_df.loc[hk_real_time_df['symbol'] == symbol]

            company_hk_df = company_hk_df.set_index(['symbol'], drop=True)
            hk_real_time_one_df = hk_real_time_one_df.set_index(['symbol'], drop=False)
            company_hk_df = pd.merge(company_hk_df, hk_real_time_one_df, how='outer',
                                     left_index=True, right_index=True)

            mongodb_util.save_mongo(company_hk_df, db_name_constant.COMPANY_INFO_HK)
        except BaseException as e:
            logger.error("同步港股公司信息异常:{},{}", symbol, e)


if __name__ == '__main__':
    get_hk_ggt_component()
    sync_hk_company_info()

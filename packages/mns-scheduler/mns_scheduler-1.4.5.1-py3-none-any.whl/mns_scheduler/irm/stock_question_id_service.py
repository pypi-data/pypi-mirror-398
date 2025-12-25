import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

"""
"""

from functools import lru_cache
import pandas as pd
import requests
from bs4 import BeautifulSoup
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.company.company_common_service_api as company_common_service_api
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util
from datetime import datetime, timedelta

mongodb_util = MongodbUtil('27017')
from tqdm import tqdm


# 同步所有映射表
@lru_cache()
def sync_stock_uid() -> pd.DataFrame:
    """
    上证e互动-代码ID映射
    https://sns.sseinfo.com/list/company.do
    :return: 代码ID映射
    :rtype: str
    """
    url = "https://sns.sseinfo.com/allcompany.do"
    data = {
        "code": "0",
        "order": "2",
        "areaId": "0",
        "page": "1",
    }
    uid_list = list()
    code_list = list()
    for page in tqdm(range(1, 74), leave=False):
        data.update({"page": page})
        r = requests.post(url, data=data)
        data_json = r.json()
        soup = BeautifulSoup(data_json["content"], "lxml")
        soup.find_all("a", attrs={"rel": "tag"})
        uid_list.extend(
            [item["uid"] for item in soup.find_all("a", attrs={"rel": "tag"})]
        )
        code_list.extend(
            [
                item.find("img")["src"].split("?")[0].split("/")[-1].split(".")[0]
                for item in soup.find_all("a", attrs={"rel": "tag"})
            ]
        )
    code_uid_df = pd.DataFrame()
    code_uid_df['symbol'] = code_list
    code_uid_df['uid'] = uid_list
    code_uid_df['_id'] = uid_list
    return code_uid_df


# 获取上海问答id
@lru_cache()
def get_sh_stock_all_uid() -> pd.DataFrame:
    return mongodb_util.find_all_data(db_name_constant.SH_INFO_UID)


# 获取深圳问答id
@lru_cache()
def get_sz_stock_all_uid() -> pd.DataFrame:
    return mongodb_util.find_all_data(db_name_constant.SZ_INFO_UID)


# 获取深圳互动回答单个ID
def get_one_sz_symbol_org_id(symbol):
    sz_info_uid_df = get_sz_stock_all_uid()
    sz_info_uid_one_df = sz_info_uid_df.loc[sz_info_uid_df['symbol'] == symbol]
    if data_frame_util.is_not_empty(sz_info_uid_one_df):
        return list(sz_info_uid_one_df['uid'])[0]
    else:
        try:
            return fetch_sz_org_id(symbol)
        except BaseException as e:
            logger.error("获取组织代码异常:{},{}", symbol, e)
            return '0'


# 获取上海互动回答单个ID
def get_one_sh_symbol_org_id(symbol):
    sh_info_uid_df = get_sh_stock_all_uid()
    sh_info_uid_one_df = sh_info_uid_df.loc[sh_info_uid_df['symbol'] == symbol]
    if data_frame_util.is_not_empty(sh_info_uid_one_df):
        return list(sh_info_uid_one_df['uid'])[0]
    else:
        return '0'


# 深圳股票-互动易-组织代码 单个获取
def fetch_sz_org_id(symbol: str = "000001") -> str:
    """
    股票-互动易-组织代码
    https://irm.cninfo.com.cn/
    :return: 组织代码
    :rtype: str
    """
    url = "https://irm.cninfo.com.cn/newircs/index/queryKeyboardInfo"
    params = {"_t": "1691144074"}
    data = {"keyWord": symbol}
    r = requests.post(url, params=params, data=data)
    data_json = r.json()
    org_id = data_json["data"][0]["secid"]
    return org_id


# 同步上证互动uid
def sync_sh_stock_uid():
    code_uid_df = sync_stock_uid()
    mongodb_util.save_mongo(code_uid_df, db_name_constant.SH_INFO_UID)


# 同步深圳互动uid
def sync_sz_stock_uid(symbol_list):
    real_time_quotes_all_stocks = em_stock_info_api.get_a_stock_info()
    de_list_company_symbols = company_common_service_api.get_de_list_company()
    real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
        ~(real_time_quotes_all_stocks['symbol'].isin(de_list_company_symbols))]
    real_time_quotes_all_stocks = common_service_fun_api.classify_symbol(real_time_quotes_all_stocks)

    real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
        real_time_quotes_all_stocks['classification'].isin(['S', 'C'])]
    if len(symbol_list) != 0:
        real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
            real_time_quotes_all_stocks['symbol'].isin(symbol_list)]
    else:
        # 获取当前时间
        now_date = datetime.now()
        # 计算前7天的时间（timedelta 用于表示时间间隔）
        seven_days_ago = now_date - timedelta(days=30)
        str_day_number = int(seven_days_ago.strftime('%Y%m%d'))
        real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[
            (real_time_quotes_all_stocks['list_date'] >= str_day_number) | (
                    real_time_quotes_all_stocks['list_date'] == 19890604)]
    for stock_one in real_time_quotes_all_stocks.itertuples():
        try:
            symbol = stock_one.symbol
            uid = fetch_sz_org_id(symbol)
            result_dict = {'_id': symbol, 'symbol': symbol, 'uid': uid}
            result_dict_df = pd.DataFrame(result_dict, index=[1])
            mongodb_util.save_mongo(result_dict_df, db_name_constant.SZ_INFO_UID)
            logger.info("同步SZ互动ID:{}", stock_one.symbol)
        except Exception as e:
            logger.error("同步SZ互动ID异常:{},{}", stock_one.symbol, e)


if __name__ == '__main__':
    sz_symbol_org_id = get_one_sz_symbol_org_id('300085')
    sh_symbol_org_id = get_one_sh_symbol_org_id('600000')
    print(sz_symbol_org_id)
    print(sh_symbol_org_id)
    sync_sz_stock_uid([])
    # sync_sz_stock_uid([])
    # sync_sh_stock_uid([])

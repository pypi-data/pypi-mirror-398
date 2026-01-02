import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import akshare as ak
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.constant.db_name_constant as db_name_constant


# 同步退市股票
def sync_de_list_stock():
    sh_de_list_df = ak.stock_info_sh_delist(symbol="全部")
    sh_de_list_df = sh_de_list_df.rename(columns={"公司代码": "symbol",
                                                  "公司简称": "name",
                                                  "上市日期": "list_date",
                                                  "暂停上市日期": "de_list_date"
                                                  })

    sz_de_list_df = ak.stock_info_sz_delist(symbol="终止上市公司")
    sz_de_list_df = sz_de_list_df.rename(columns={"证券代码": "symbol",
                                                  "证券简称": "name",
                                                  "上市日期": "list_date",
                                                  "终止上市日期": "de_list_date"
                                                  })
    all_de_list_df = pd.concat([sz_de_list_df, sh_de_list_df])
    all_de_list_df['_id'] = all_de_list_df['symbol']
    all_de_list_df['list_date'] = all_de_list_df['list_date'].astype(str)
    all_de_list_df['de_list_date'] = all_de_list_df['de_list_date'].astype(str)
    mongodb_util.save_mongo(all_de_list_df, db_name_constant.DE_LIST_STOCK)
    remove_black_list(all_de_list_df)


# 移除黑名单
def remove_black_list(all_de_list_df):
    symbol_list = list(all_de_list_df['symbol'])
    remove_query = {'symbol': {"$in": symbol_list}}
    mongodb_util.remove_data(remove_query, db_name_constant.SELF_BLACK_STOCK)


if __name__ == '__main__':
    sync_de_list_stock()

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import pandas as pd
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_api as company_common_service_api

mongodb_util = MongodbUtil('27017')
# 高涨幅阈值
HIGH_CHG = 50


# 最近大涨股票
def calculate_recent_hot_stocks(stock_qfq_daily_60, symbol, str_day):
    company_df = company_common_service_api.get_company_info_industry_list_date()
    company_one_df = company_df.loc[company_df['_id'] == symbol]
    company_one_df['list_date_01'] = pd.to_datetime(company_one_df['list_date'], format='%Y%m%d')
    list_date = list(company_one_df['list_date_01'])[0]

    str_list_date = date_handle_util.no_slash_date(list_date.strftime('%Y-%m-%d'))
    # 排除上市第一天的数据
    stock_qfq_daily_60 = stock_qfq_daily_60.loc[stock_qfq_daily_60['date'] > str_list_date]

    stock_qfq_daily_05 = stock_qfq_daily_60.iloc[0:5]

    stock_qfq_daily_10 = stock_qfq_daily_60.iloc[0:10]

    stock_qfq_daily_20 = stock_qfq_daily_60.iloc[0:20]

    stock_qfq_daily_30 = stock_qfq_daily_60.iloc[0:30]
    sum_five_chg = round(sum(stock_qfq_daily_05['chg']), 2)
    sum_ten_chg = round(sum(stock_qfq_daily_10['chg']), 2)

    sum_twenty_chg = round(sum(stock_qfq_daily_20['chg']), 2)

    sum_thirty_chg = round(sum(stock_qfq_daily_30['chg']), 2)

    sum_sixty_chg = round(sum(stock_qfq_daily_60['chg']), 2)
    if (sum_sixty_chg >= HIGH_CHG
            or sum_ten_chg >= HIGH_CHG
            or sum_twenty_chg >= HIGH_CHG
            or sum_thirty_chg >= HIGH_CHG
            or sum_sixty_chg >= HIGH_CHG):
        query = {'symbol': symbol}
        company_info_df = mongodb_util.find_query_data(db_name_constant.COMPANY_INFO, query)
        name = list(company_info_df['name'])[0]
        hot_stocks_dict = {
            "_id": str_day + "_" + symbol,
            "symbol": symbol,
            "name": name,
            "str_day": str_day,
            "sum_five_chg": sum_five_chg,
            "sum_ten_chg": sum_ten_chg,
            "sum_twenty_chg": sum_twenty_chg,
            "sum_thirty_chg": sum_thirty_chg,
            "sum_sixty_chg": sum_sixty_chg,
        }
        hot_stocks_df = pd.DataFrame(hot_stocks_dict, index=[1])
        mongodb_util.save_mongo(hot_stocks_df, db_name_constant.RECENT_HOT_STOCKS)

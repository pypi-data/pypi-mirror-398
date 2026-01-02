import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import pandas as pd
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
import mns_scheduler.k_line.clean.week_month.normal_week_month_k_line_service as week_month_k_line_service
import mns_scheduler.k_line.clean.daily.daily_k_line_service as daily_k_line_service

mongodb_util = MongodbUtil('27017')


# 日线 周线 月线 成交量  筹码信息
def calculate_k_line_info(str_day, symbol, diff_days, stock_qfq_year_df):
    k_line_info = pd.DataFrame([[
        str_day,
        symbol, diff_days]],
        columns=['str_day',
                 'symbol',
                 'diff_days'
                 ])
    # 交易天数
    deal_days = k_line_common_service_api.get_deal_days(str_day, symbol)
    # 处理周线 月线
    k_line_info = week_month_k_line_service.handle_month_week_line(k_line_info, str_day, symbol,
                                                                   deal_days, stock_qfq_year_df)
    # 处理日线
    k_line_info = daily_k_line_service.handle_day_line(k_line_info, str_day, symbol, deal_days)
    return k_line_info

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.constant.db_name_constant as db_name_constant
import mns_scheduler.risk.financial_report_risk_check_api as financial_report_risk_check_api
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')


def fix_profit_black_list():
    period_time = "2024-12-31 00:00:00"
    period = 4
    report_type_list = [db_name_constant.EM_STOCK_ASSET_LIABILITY, db_name_constant.EM_STOCK_PROFIT]
    for report_type in report_type_list:
        query = {'REPORT_DATE': period_time}
        em_stock_profit_df_list = mongodb_util.find_query_data(report_type, query)
        for em_stock_one in em_stock_profit_df_list.itertuples():
            em_stock_one_df = em_stock_profit_df_list.loc[
                em_stock_profit_df_list['SECURITY_CODE'] == em_stock_one.SECURITY_CODE]

            financial_report_risk_check_api.financial_report_check(em_stock_one_df, period_time, period,
                                                                   report_type)


if __name__ == '__main__':
    fix_profit_black_list()

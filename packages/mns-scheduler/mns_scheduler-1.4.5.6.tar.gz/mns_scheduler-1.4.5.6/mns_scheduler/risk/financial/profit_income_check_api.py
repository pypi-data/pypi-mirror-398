import sys
import os
from datetime import datetime
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
import mns_common.component.common_service_fun_api as common_service_fun_api
from mns_common.constant.black_list_classify_enum import BlackClassify
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

# 利润为负的时候最小营业收入 主板 3.2亿
MIN_INCOME_MAIN = 320000000
# 利润为负的时候最小营业收入 科创 创业 1.2亿
MIN_INCOME_SUB = 120000000


# 营收利润check

def profit_income_check(new_report_df, period_time, report_type):
    new_report_one_df = new_report_df.loc[new_report_df['REPORT_DATE'] == period_time]
    symbol = list(new_report_one_df['SECURITY_CODE'])[0]
    name = list(new_report_one_df['SECURITY_NAME_ABBR'])[0]
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    notice_date = list(new_report_one_df['NOTICE_DATE'])[0]
    if report_type == db_name_constant.EM_STOCK_PROFIT:
        # 利润总额  净利润 扣除非经常性损益后的净利润  三者最小为负
        # 利润总额
        total_profit = list(new_report_one_df['TOTAL_PROFIT'])[0]
        #  净利润
        net_profit = list(new_report_one_df['NETPROFIT'])[0]
        # 营业利润
        operate_profit = list(new_report_one_df['OPERATE_PROFIT'])[0]
        # 持续经营净利润
        continued_profit = list(new_report_one_df['CONTINUED_NETPROFIT'])[0]
        # 归属于母公司股东的净利润
        parent_profit = list(new_report_one_df['PARENT_NETPROFIT'])[0]
        # 扣除非经常性损益后的净利润
        deduct_parent_profit = list(new_report_one_df['DEDUCT_PARENT_NETPROFIT'])[0]
        # 营业总收入
        total_operate_income = list(new_report_one_df['TOTAL_OPERATE_INCOME'])[0]
        if total_operate_income == 0:
            #  营业收入
            total_operate_income = list(new_report_one_df['OPERATE_INCOME'])[0]

            # 最小利润收入
        min_profit = min(total_profit, net_profit, operate_profit,
                         continued_profit, parent_profit, deduct_parent_profit)

        query = {'symbol': symbol, 'level_code': BlackClassify.FINANCIAL_PROBLEM_PROFIT.level_code}
        mongodb_util.remove_data(query, db_name_constant.SELF_BLACK_STOCK)

        if min_profit < 0:

            classification = common_service_fun_api.classify_symbol_one(symbol)
            if ((classification in ['S', 'H'] and total_operate_income < MIN_INCOME_MAIN)
                    | (classification in ['K', 'C'] and total_operate_income < MIN_INCOME_SUB)):
                id_key = symbol + "_" + period_time + "_" + BlackClassify.FINANCIAL_PROBLEM_PROFIT.level_code
                min_profit = round(min_profit / common_service_fun_api.TEN_THOUSAND, 1)
                total_operate_income = round(total_operate_income / common_service_fun_api.HUNDRED_MILLION, 1)

                black_list_service_api.save_black_stock(id_key,
                                                        symbol,
                                                        name,
                                                        str_day,
                                                        notice_date,
                                                        '年报:利润:' + '[' + str(min_profit) + '万]' + '收入:' + str(
                                                            total_operate_income) + '[' + '亿元]--' + '触发退市风险',
                                                        '年报:利润:' + '[' + str(min_profit) + '万]' + '收入:' + str(
                                                            total_operate_income) + '[' + '亿元]--' + '触发退市风险',
                                                        '',
                                                        BlackClassify.FINANCIAL_PROBLEM_PROFIT.up_level_code,
                                                        BlackClassify.FINANCIAL_PROBLEM_PROFIT.up_level_name,
                                                        BlackClassify.FINANCIAL_PROBLEM_PROFIT.level_code,
                                                        BlackClassify.FINANCIAL_PROBLEM_PROFIT.level_name)

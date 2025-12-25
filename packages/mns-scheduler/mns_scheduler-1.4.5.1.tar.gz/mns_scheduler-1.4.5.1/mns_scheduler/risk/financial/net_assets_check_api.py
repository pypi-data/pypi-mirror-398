from datetime import datetime
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api
from mns_common.constant.black_list_classify_enum import BlackClassify

mongodb_util = MongodbUtil('27017')
# 最大负债比
MAX_LIABILITY_RATIO = 90
# 最小净资产1.5亿
MIN_NET_ASSET = 150000000
# 排除校验负债比的行业
EXCLUDE_INDUSTRY = ['保险', '银行', '证券']


# 负债比校验| 净资产check
def net_assets_check(report_type, new_report_df, period_time):
    if report_type == db_name_constant.EM_STOCK_ASSET_LIABILITY:
        new_report_df = new_report_df.sort_values(by=['REPORT_DATE'], ascending=False)
        new_report_one_df = new_report_df.iloc[0:1]
        # 负债比
        liability_ratio = round(
            list(new_report_one_df['TOTAL_LIABILITIES'])[0] * 100 / list(new_report_one_df['TOTAL_ASSETS'])[0],
            2)
        # 净资产
        net_asset = round(list(new_report_one_df['TOTAL_ASSETS'])[0] - list(new_report_one_df['TOTAL_LIABILITIES'])[0],
                          2)

        symbol = list(new_report_one_df['SECURITY_CODE'])[0]
        name = list(new_report_one_df['SECURITY_NAME_ABBR'])[0]
        now_date = datetime.now()
        str_day = now_date.strftime('%Y-%m-%d')
        id_key = symbol + "_" + period_time + "_" + BlackClassify.FINANCIAL_PROBLEM_DEBT.level_code
        notice_date = list(new_report_one_df['NOTICE_DATE'])[0]
        query_company = {'_id': symbol, 'industry': {'$in': EXCLUDE_INDUSTRY}}
        query = {'symbol': symbol, 'level_code': BlackClassify.FINANCIAL_PROBLEM_DEBT.level_code}
        mongodb_util.remove_data(query, db_name_constant.SELF_BLACK_STOCK)

        if mongodb_util.exist_data_query(db_name_constant.COMPANY_INFO, query_company):
            return None

        if liability_ratio >= MAX_LIABILITY_RATIO and net_asset < MIN_NET_ASSET:

            black_list_service_api.save_black_stock(id_key,
                                                    symbol,
                                                    name,
                                                    str_day,
                                                    notice_date,
                                                    '负债过高:' + "[" + "负债比:" + str(
                                                        liability_ratio) + "]" + "," + "净资产:"
                                                    + str(round(net_asset / common_service_fun_api.HUNDRED_MILLION,
                                                                0)) + "亿",
                                                    '负债过高:' + "[" + str(liability_ratio) + "]",
                                                    '',
                                                    BlackClassify.FINANCIAL_PROBLEM_DEBT.up_level_code,
                                                    BlackClassify.FINANCIAL_PROBLEM_DEBT.up_level_name,
                                                    BlackClassify.FINANCIAL_PROBLEM_DEBT.level_code,
                                                    BlackClassify.FINANCIAL_PROBLEM_DEBT.level_name)
        # if net_asset < MIN_NET_ASSET:
        #     black_list_service_api.save_black_stock(id_key,
        #                                             symbol,
        #                                             name,
        #                                             str_day,
        #                                             notice_date,
        #                                             '净资产低:' + "[" + "负债比:" + str(
        #                                                 liability_ratio) + "]" + "," + "净资产:"
        #                                             + str(round(net_asset / common_service_fun_api.HUNDRED_MILLION,
        #                                                         0)) + "亿",
        #                                             '净资产低:' + "[" + str(liability_ratio) + "]",
        #                                             '',
        #                                             BlackClassify.FINANCIAL_PROBLEM_DEBT.up_level_code,
        #                                             BlackClassify.FINANCIAL_PROBLEM_DEBT.up_level_name,
        #                                             BlackClassify.FINANCIAL_PROBLEM_DEBT.level_code,
        #                                             BlackClassify.FINANCIAL_PROBLEM_DEBT.level_name)

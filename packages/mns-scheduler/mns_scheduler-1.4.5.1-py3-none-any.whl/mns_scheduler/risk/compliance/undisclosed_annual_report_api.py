from datetime import datetime
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
import mns_scheduler.finance.em.finance_common_api as finance_common_api
from loguru import logger
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import pandas as pd
from mns_common.constant.black_list_classify_enum import BlackClassify
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.utils.date_handle_util as date_handle_util

# 最迟出报告的交易天数
LATE_REPORT_DAYS = 3


# 未出财报检查
def un_disclosed_report_check(sync_time, now_year, period, period_time):
    un_report_asset_df = finance_common_api.find_un_report_symbol(period_time,
                                                                  db_name_constant.EM_STOCK_ASSET_LIABILITY)
    un_report_profit_df = finance_common_api.find_un_report_symbol(period_time,
                                                                   db_name_constant.EM_STOCK_PROFIT)
    un_report_df = pd.concat([un_report_asset_df, un_report_profit_df])
    if period == 4 or period == 1:
        month = sync_time[5:7]
        day = sync_time[8:10]
        day = int(day)
        month = int(month)
        if (month < 4) or (month == 4 and day < 20):
            return None
        last_report_day = str(now_year) + "-05-01"
    elif period == 2:
        last_report_day = str(now_year) + "-07-01"
    elif period == 3:
        last_report_day = str(now_year) + "-10-01"
    max_report_day = trade_date_common_service_api.get_before_trade_date(last_report_day, LATE_REPORT_DAYS)
    all_company_info = company_common_service_api.get_company_info_industry_list_date()
    if max_report_day >= sync_time:

        for un_asset_one in un_report_df.itertuples():
            symbol = un_asset_one.symbol
            company_info_one = all_company_info.loc[all_company_info['_id'] == symbol]
            list_date = list(company_info_one['list_date'])[0]
            list_date = str(list_date)
            list_date_time = date_handle_util.add_date_day(list_date[0:8], 0)
            list_date_str = list_date_time.strftime('%Y-%m-%d')
            if max_report_day < list_date_str:
                continue
            id_key = symbol + "_" + period_time + "_" + BlackClassify.UNDISCLOSED_REPORT.level_code
            name = un_asset_one.name
            now_date = datetime.now()
            str_day = now_date.strftime('%Y-%m-%d')
            try:

                black_list_service_api.save_black_stock(id_key,
                                                        symbol,
                                                        name,
                                                        str_day,
                                                        sync_time,
                                                        '未披露财务报告',
                                                        '未披露财务报告',
                                                        '',
                                                        BlackClassify.UNDISCLOSED_REPORT.up_level_code,
                                                        BlackClassify.UNDISCLOSED_REPORT.up_level_name,
                                                        BlackClassify.UNDISCLOSED_REPORT.level_code,
                                                        BlackClassify.UNDISCLOSED_REPORT.level_name)
            except Exception as e:
                logger.error("更新未出报告异常:{},{},{}", symbol, period_time, e)


if __name__ == '__main__':
    un_disclosed_report_check('2025-04-29', 2025, 4, '2024-12-31 00:00:00')

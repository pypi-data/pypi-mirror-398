import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.ths.concept.app.ths_concept_index_app as ths_concept_index_app
from datetime import datetime
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.utils.data_frame_util as data_frame_util
import pandas as pd
import mns_common.component.common_service_fun_api as common_service_fun_api


# 通过api 获取ths行业和指数
def get_ths_index_by_api(query_type):
    now_date = datetime.now()
    hour = now_date.hour
    minute = now_date.minute
    now_str_day = now_date.strftime('%Y-%m-%d')

    is_trade_day = trade_date_common_service_api.is_trade_day(now_str_day)

    if bool(1 - is_trade_day):
        last_trade_day = trade_date_common_service_api.get_before_trade_date(now_str_day, 1)
        begin_time = date_handle_util.no_slash_date(last_trade_day) + '093000'
        end_time = date_handle_util.no_slash_date(last_trade_day) + '150000'
    else:
        if hour < 9 or (hour == 9 and minute <= 25):
            last_trade_day = trade_date_common_service_api.get_before_trade_date(now_str_day, 2)
            begin_time = date_handle_util.no_slash_date(last_trade_day) + '093000'
            end_time = date_handle_util.no_slash_date(last_trade_day) + '150000'
        else:
            begin_time = date_handle_util.no_slash_date(now_str_day) + '093000'
            if hour == 9:
                hour = '0' + str(hour)
                end_time = date_handle_util.no_slash_date(now_str_day) + str(hour) + str(minute) + '00'
            elif (hour == 11 and minute >= 30) or (hour == 12):
                end_time = date_handle_util.no_slash_date(now_str_day) + '113000'
            elif hour >= 15:
                end_time = date_handle_util.no_slash_date(now_str_day) + '150000'
            else:
                end_time = date_handle_util.no_slash_date(now_str_day) + str(hour) + str(minute) + '00'

    df = ths_concept_index_app.get_ths_concept_his_info(begin_time, end_time, 500, query_type)
    if data_frame_util.is_empty(df):
        return pd.DataFrame()
    df['turnover'] = round(df['turnover'] / common_service_fun_api.HUNDRED_MILLION, 1)
    df['net_inflow_of_main_force'] = round(df['net_inflow_of_main_force'] / common_service_fun_api.TEN_THOUSAND, 1)
    df.fillna('', inplace=True)
    return df


if __name__ == '__main__':
    df_industry = get_ths_index_by_api(1)
    print(df_industry)

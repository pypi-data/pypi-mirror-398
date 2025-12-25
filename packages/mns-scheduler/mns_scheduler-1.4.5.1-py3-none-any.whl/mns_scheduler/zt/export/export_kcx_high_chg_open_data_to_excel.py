import sys
import os

from mns_common.db.MongodbUtil import MongodbUtil
import pandas as pd
import mns_common.utils.data_frame_util as data_frame_util

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
# 导出 K C X 板块高涨幅股票到excel


mongodb_util = MongodbUtil('27017')
choose_field = ["symbol",
                "name",
                "reason",
                "chg",
                "today_chg",
                "quantity_ratio",
                "amount_level",
                "disk_diff_amount_level",
                "sum_main_inflow_disk",
                "real_exchange",
                "flow_mv_level",
                "total_mv_level",
                "str_day",
                "diff_days",
                "industry",
                "ths_concept_name",
                "ths_concept_code",
                "first_sw_industry",
                "second_sw_industry",
                "third_sw_industry",
                "em_industry",
                "disk_ratio",
                "company_type",
                "reference_main_inflow",
                "exchange",
                "amount",
                "disk_diff_amount",
                "now_price",
                "high",
                "low",
                "open",
                "yesterday_price",
                "volume",
                "total_mv",
                "flow_mv",
                "outer_disk",
                "inner_disk",
                "classification",
                "str_now_date",
                "number",
                "yesterday_high_chg",
                "ths_concept_sync_day",
                "mv_circulation_ratio",
                "list_date",
                "real_flow_mv",
                "no_open_data"]

FILE_PATH = "D:\mns\mns-scheduler\mns_scheduler\m_review\kc_zt.xlsx"


def export_kc_zt_data(str_day):
    query = {"no_open_data": False, "yesterday_high_chg": False, "chg": {"$lte": 9}, "str_day": str_day}

    query_field = {"real_disk_diff_amount_exchange": 0, "max_real_main_inflow_multiple": 0, "main_inflow_multiple": 0,
                   "super_main_inflow_multiple": 0, "disk_diff_amount_exchange": 0}

    realtime_quotes_now_zt_new_kc_open_df = mongodb_util.find_query_data_choose_field(
        'realtime_quotes_now_zt_new_kc_open',
        query, query_field)

    realtime_quotes_now_zt_new_kc_open_df = realtime_quotes_now_zt_new_kc_open_df.loc[
        ~(realtime_quotes_now_zt_new_kc_open_df['name'].str.contains('N'))]

    realtime_quotes_now_zt_new_kc_open_df = realtime_quotes_now_zt_new_kc_open_df.loc[
        ~(realtime_quotes_now_zt_new_kc_open_df['name'].str.contains('ST'))]

    realtime_quotes_now_zt_new_kc_open_df = realtime_quotes_now_zt_new_kc_open_df.loc[
        ~(realtime_quotes_now_zt_new_kc_open_df['name'].str.contains('退'))]

    realtime_quotes_now_zt_new_kc_open_df.loc[:, 'disk_diff_amount_level'] = round(
        realtime_quotes_now_zt_new_kc_open_df[
            'disk_diff_amount'] / 10000, 2)

    realtime_quotes_now_zt_new_kc_open_df.loc[:, "reason"] = ""

    realtime_quotes_now_zt_new_kc_open_exist_df = pd.read_excel(
        FILE_PATH,
        converters={u'a1': str})

    final_result = data_frame_util.merge_choose_data_no_drop(realtime_quotes_now_zt_new_kc_open_exist_df,
                                                             realtime_quotes_now_zt_new_kc_open_df)

    final_result['_id'] = final_result['name'] + "_" + final_result['str_day']

    final_result.drop_duplicates('_id', keep='last', inplace=True)

    final_result = final_result.sort_values(by=['str_day'],
                                            ascending=False)

    final_result = final_result[choose_field]

    final_result.to_excel(FILE_PATH,
                          index=False,
                          header=True)


if __name__ == '__main__':
    export_kc_zt_data('2023-12-15')

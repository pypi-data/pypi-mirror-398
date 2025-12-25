import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
# from mns_common.db.MongodbUtil import MongodbUtil
# import mns_common.component.k_line.common.k_line_common_service_api as k_line_common_service_api
#
# mongodb_util = MongodbUtil('27017')
# # query = {"deal_days": {"$exists": False}}
# deal_days = 8
# fail_id_list = []
# while True:
#     query = {"deal_days": deal_days}
#     realtime_quotes_now_zt_new_kc_open_df = mongodb_util.find_query_data('realtime_quotes_now_zt_new_kc_open', query)
#
#     for stock_one in realtime_quotes_now_zt_new_kc_open_df.itertuples():
#         try:
#             str_day = stock_one.str_day
#             deal_days = k_line_common_service_api.get_deal_days(str_day, stock_one.symbol)
#
#             realtime_quotes_now_zt_new_kc_open_one = realtime_quotes_now_zt_new_kc_open_df.loc[
#                 (realtime_quotes_now_zt_new_kc_open_df['symbol'] == stock_one.symbol)
#                 & (realtime_quotes_now_zt_new_kc_open_df['str_day'] == stock_one.str_day)]
#
#             realtime_quotes_now_zt_new_kc_open_one['deal_days'] = deal_days
#
#             mongodb_util.save_mongo(realtime_quotes_now_zt_new_kc_open_one, 'realtime_quotes_now_zt_new_kc_open')
#         except Exception as e:
#             mongodb_util.insert_mongo(realtime_quotes_now_zt_new_kc_open_one, 'realtime_quotes_now_zt_new_kc_open_fail')
#             print(stock_one.symbol)
#     deal_days = deal_days + 1
#     if deal_days > 3479:
#         print(deal_days)
#         break

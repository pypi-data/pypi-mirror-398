import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
import mns_common.component.data.data_init_api as data_init_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.db_util as db_util
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')

# 保存高涨股票当天实时行情数据


choose_field = ["_id",
                "symbol",
                "name",
                "industry",
                "chg",
                "quantity_ratio",
                "amount_level",
                'sum_main_inflow_disk',
                "disk_ratio",
                "now_price",
                "real_disk_diff_amount_exchange",
                'max_real_main_inflow_multiple',

                "real_main_inflow_multiple",
                "real_super_main_inflow_multiple",
                "super_main_inflow_multiple",
                "main_inflow_multiple",
                "disk_diff_amount_exchange",
                "large_inflow_multiple",
                "today_main_net_inflow",
                "today_main_net_inflow_ratio",
                "super_large_order_net_inflow",
                "super_large_order_net_inflow_ratio",
                "large_order_net_inflow",
                "large_order_net_inflow_ratio",
                "reference_main_inflow",
                "disk_diff_amount",
                "mv_circulation_ratio",
                "real_exchange",
                "exchange",
                'real_exchange',
                "total_mv",
                "flow_mv",
                "volume",
                "high",
                "low",
                "open",
                "yesterday_price",
                "amount",
                "total_mv_sp",
                "flow_mv_sp",
                "outer_disk",
                "inner_disk",
                "classification",
                "number",
                "str_day",
                "str_now_date"
                ]


# 同步高涨幅股票实时行情数据
def sync_high_chg_real_time_quotes(str_day):
    mongo = db_util.get_db(str_day)

    realtime_quotes_db_name = db_name_constant.REAL_TIME_QUOTES_NOW + "_" + str_day
    high_chg_list = get_high_chg_symbol(str_day)
    if high_chg_list is None or len(high_chg_list) == 0:
        return

    for symbol in high_chg_list:
        try:
            query_all = {"symbol": symbol}
            real_time_quotes_now_high_chg_all = mongo.find_query_data(realtime_quotes_db_name, query_all)
            if real_time_quotes_now_high_chg_all.shape[0] == 0:
                return
            real_time_quotes_now_high_chg_all = company_common_service_new_api.amend_ths_industry(
                real_time_quotes_now_high_chg_all)
            real_time_quotes_now_high_chg_all.dropna(subset=['symbol'], axis=0,
                                                     inplace=True)
            real_time_quotes_now_high_chg_all = data_init_api.calculate_parameter_factor(
                real_time_quotes_now_high_chg_all)

            real_time_quotes_now_high_chg_all['amount_level'] = round(
                (real_time_quotes_now_high_chg_all['amount'] / common_service_fun_api.HUNDRED_MILLION), 2)
            real_time_quotes_now_high_chg_all['flow_mv_sp'] = round(
                (real_time_quotes_now_high_chg_all['flow_mv'] / common_service_fun_api.HUNDRED_MILLION), 2)
            real_time_quotes_now_high_chg_all['total_mv_sp'] = round(
                (real_time_quotes_now_high_chg_all['total_mv'] / common_service_fun_api.HUNDRED_MILLION), 2)

            save_realtime_quotes_now_zt_data(real_time_quotes_now_high_chg_all, str_day, symbol)
            logger.info("同步高涨幅股票实时行情数据信息:{},{}", str_day, symbol)
        except BaseException as e:
            logger.error("同步高涨幅股票实时行情数据发生异常:{}:{},{}", str_day, e, symbol)


# 获取 str_day 高涨幅列表 k线和涨停池中
def get_high_chg_symbol(str_day):
    query = {"date": date_handle_util.no_slash_date(str_day), "chg": {'$gte': common_service_fun_api.ZT_CHG}}
    # 今日高涨幅的list
    real_time_quotes_now_high_chg = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_DAILY, query)
    if real_time_quotes_now_high_chg.shape[0] == 0:
        return None
    high_chg_list = list(real_time_quotes_now_high_chg['symbol'])
    # 今日涨停股
    query_zt = {'str_day': str_day}
    zt_pool = mongodb_util.find_query_data(db_name_constant.STOCK_ZT_POOL, query_zt)
    if zt_pool.shape[0] > 0:
        zt_pool_list = list(zt_pool['symbol'])
        high_chg_list.extend(zt_pool_list)
    high_chg_list = list(set(high_chg_list))
    return high_chg_list


# 保存high chg 股票实时行情数据
def save_realtime_quotes_now_zt_data(realtime_quotes_now_zt, str_day, symbol):
    realtime_quotes_now_zt = common_service_fun_api.classify_symbol(realtime_quotes_now_zt.copy())
    # create_index()
    if 'wei_bi' in realtime_quotes_now_zt.columns and bool(1 - ("wei_bi" in choose_field)):
        choose_field.append("wei_bi")
    if 'up_speed' in realtime_quotes_now_zt.columns and bool(1 - ("up_speed" in choose_field)):
        choose_field.append("up_speed")
    if 'list_date' in realtime_quotes_now_zt.columns and bool(1 - ("list_date" in choose_field)):
        choose_field.append("list_date")
    realtime_quotes_now_zt.loc[:, 'str_day'] = str_day
    realtime_quotes_now_zt = realtime_quotes_now_zt[choose_field]
    remove_query = {"symbol": symbol, "str_day": str_day}
    result = mongodb_util.remove_data(remove_query, db_name_constant.ZT_STOCK_REAL_TIME_QUOTES).acknowledged
    if result:
        mongodb_util.insert_mongo(realtime_quotes_now_zt, db_name_constant.ZT_STOCK_REAL_TIME_QUOTES)


if __name__ == '__main__':
    sync_high_chg_real_time_quotes('2024-12-26')

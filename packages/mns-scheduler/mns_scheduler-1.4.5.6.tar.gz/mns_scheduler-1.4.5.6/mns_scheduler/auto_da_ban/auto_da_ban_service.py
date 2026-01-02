import sys
import os
import time

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.component.deal.deal_service_api as deal_service_api
from loguru import logger
from mns_common.utils.async_fun import async_fun
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.utils.date_handle_util as date_handle_util
import pandas as pd

mongodb_util = MongodbUtil('27017')
from datetime import datetime


def auto_da_ban_task():
    logger.info("打板任务启动")
    while True:
        try:
            now_date = datetime.now()
            now_str_day = now_date.strftime('%Y-%m-%d')
            if bool(1 - date_handle_util.is_trade_date(now_str_day)):
                logger.info("非交易日不执行:{}", now_str_day)
                break
            else:
                # 执行打板任务
                auto_da_ban()
        except BaseException as e:
            logger.error("自动打板定时任务异常:{}", e)


def auto_da_ban():
    now_date = datetime.now()
    now_str_day = now_date.strftime('%Y-%m-%d')
    over_night_da_ban_list = query_over_night_da_ban_list(now_str_day)
    if data_frame_util.is_empty(over_night_da_ban_list):
        return None
    for stock_one in over_night_da_ban_list.itertuples():
        try:
            symbol = stock_one.symbol
            buy_price = stock_one.zt_price
            buy_volume = stock_one.buy_volume
            xia_dan_to_qmt(symbol, buy_price, buy_volume, now_str_day)
        except BaseException as e:
            logger.error("隔夜委托出现异常:{},{}", symbol, e)


def xia_dan_to_qmt(symbol, buy_price, buy_volume, str_day):
    symbol_prefix = common_service_fun_api.add_after_prefix_one(symbol)

    deal_service_api.trade_buy(symbol_prefix, buy_price, buy_volume, 'qmt')

    # 异步更新信息
    handle_async_msg(str_day, symbol, symbol_prefix)


@async_fun
def handle_async_msg(str_day, symbol, symbol_prefix):
    order_list = deal_service_api.query_orders('qmt')
    order_list_df = pd.DataFrame(order_list)
    # order_status ==57 费单
    success_order_df = order_list_df.loc[
        (order_list_df['stock_code'] == symbol_prefix) & (order_list_df['order_status'] != 57)]
    # 多委托几个
    time.sleep(1)
    # 委托成功 更新状态
    if data_frame_util.is_not_empty(success_order_df):
        logger.info("隔夜委托成功:{}", symbol)
        query = {"str_day": str_day, "symbol": symbol}
        new_values = {"$set": {"valid": False}}
        mongodb_util.update_many(query, new_values, db_name_constant.OVER_NIGHT_DA_BAN)


def query_over_night_da_ban_list(str_day):
    query = {"str_day": str_day, "valid": True}
    return mongodb_util.find_query_data(db_name_constant.OVER_NIGHT_DA_BAN, query)


if __name__ == '__main__':
    while True:
        auto_da_ban()

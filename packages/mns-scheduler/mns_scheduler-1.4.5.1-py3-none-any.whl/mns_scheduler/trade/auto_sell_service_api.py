import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.utils.data_frame_util as data_frame_util
import mns_common.constant.db_name_constant as db_name_constant
import datetime
import mns_common.component.cache.cache_service as cache_service
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.deal.deal_service_api as deal_service_api
from loguru import logger
from mns_common.utils.async_fun import async_fun
import mns_common.component.price.trade_price_service_api as trade_price_service_api

mongodb_util = MongodbUtil('27017')
from mns_common.constant.price_enum import PriceEnum

AUTO_SELL_KEY = "AUTO_SELL_KEY"

# 当前跌幅卖出阈值
AUTO_SELL_CHG = -8
# 收益率阈值
AUTO_SELL_PROFIT_LOSS_CHG = -11.0


# 自动卖出
@async_fun
def auto_sell_stock(realtime_quotes_now):
    sell_flag = cache_service.get_cache(AUTO_SELL_KEY)
    if sell_flag is not None and bool(1 - sell_flag):
        return
    now_date = datetime.datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    query_exist = {'str_day': str_day, "valid": True}
    position_stock_df = mongodb_util.find_query_data(db_name_constant.POSITION_STOCK, query_exist)
    if data_frame_util.is_empty(position_stock_df):
        cache_service.set_cache(AUTO_SELL_KEY, False)
        return None
    else:
        cache_service.set_cache(AUTO_SELL_KEY, True)
        position_stock_symbol_list = list(position_stock_df['symbol'])
        realtime_quotes_now_position = realtime_quotes_now.loc[
            realtime_quotes_now['symbol'].isin(position_stock_symbol_list)]
        sell_stock_detail(realtime_quotes_now_position, position_stock_df, str_day, now_date)


def sell_stock_detail(realtime_quotes_now_position, position_stock_df, str_day, now_date):
    for stock_one in realtime_quotes_now_position.itertuples():
        try:

            symbol = stock_one.symbol
            sell_price = trade_price_service_api.get_trade_price(symbol, PriceEnum.SEll_PRICE_LIMIT.price_code)
            position_stock_df_one = position_stock_df.loc[position_stock_df['symbol'] == symbol]
            available_position = list(position_stock_df_one['available_position'])[0]
            if sell_signal(stock_one, now_date, position_stock_df_one):
                sell_result = deal_service_api.trade_sell(symbol, sell_price, available_position)
                if "message" in sell_result:
                    result_msg = sell_result['message']
                    if result_msg == 'success':
                        update_position_status(symbol, None, str_day)
                elif "entrust_no" in sell_result:
                    sell_entrust_no = sell_result['entrust_no']
                    if sell_entrust_no is not None:
                        update_position_status(symbol, sell_entrust_no, str_day)

        except BaseException as e:
            logger.error("自动卖出异常:{},{}", stock_one.symbol, e)


# 卖出信号 TODO 待优化
def sell_signal(stock_one, now_date, position_stock_df_one):
    chg = stock_one.chg
    wei_bi = stock_one.wei_bi

    hour = now_date.hour
    minute = now_date.minute
    # 跌停直接卖出
    if wei_bi == -100:
        return True
    # 开盘五分钟先看看
    if hour == 9 and minute <= 35:
        return False
    # 尾盘卖不出了
    if hour == 14 and minute >= 57:
        return False

    # 自动卖出涨幅
    if chg < AUTO_SELL_CHG:
        return True

    cost_price = list(position_stock_df_one['cost_price'])[0]
    now_price = stock_one.now_price
    # 收益率
    profit_loss_chg = round((now_price - cost_price) * 100 / cost_price, 2)
    # 收益卖出阈值
    if profit_loss_chg < AUTO_SELL_PROFIT_LOSS_CHG:
        return True
    return False


# 更新持仓状态
def update_position_status(symbol, sell_entrust_no, str_day):
    update_query = {'symbol': symbol, 'str_day': str_day}
    new_values = {"$set": {"valid": False, "sell_entrust_no": sell_entrust_no}}
    mongodb_util.update_many(update_query, new_values, db_name_constant.POSITION_STOCK)


import mns_common.component.em.em_stock_info_api as em_stock_info_api

if __name__ == '__main__':
    sell_price_01 = trade_price_service_api.get_trade_price('002336',PriceEnum.SEll_PRICE_LIMIT.price_code)
    while True:
         real_time_quotes_now = em_stock_info_api.get_a_stock_info()
         auto_sell_stock(real_time_quotes_now)

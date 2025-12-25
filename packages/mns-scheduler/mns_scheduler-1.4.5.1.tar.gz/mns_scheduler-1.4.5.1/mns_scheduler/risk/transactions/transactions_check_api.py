import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from datetime import datetime
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
from loguru import logger
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api
from mns_common.constant.black_list_classify_enum import BlackClassify
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.component.tfp.stock_tfp_api as stock_tfp_api

mongodb_util = MongodbUtil('27017')

# 主板 市值最小值 6亿 20个交易日低于5亿退市
MAIN_MARKET_MIN_MV = 600000000

# 创业 科创 北交所 市值最小值 4亿  20个交易日低于3亿退市
SUB_MARKET_MIN_MV = 400000000

# 最小面值 20个交易日低于1元退市
MIN_NOW_PRICE = 1.5

# 主板 120个交易日 参考600万 成交量低于500万股
MAIN_MARKET_MIN_VOLUME = 6000000

# 科创 创业 120个交易日 参考300万 成交量低于200万股
SUB_MARKET_MIN_VOLUME = 3000000

# 北交所 120个交易日 参考150万 成交量低于100万股
BJS_MARKET_MIN_VOLUME = 1500000


def transactions_check_task():
    # 获取当前日期和时间
    now = datetime.now()

    # 格式化输出
    now_day_str = now.strftime("%Y%m%d")

    now_day_number = float(now_day_str)

    real_time_quotes_now = em_stock_info_api.get_a_stock_info()
    real_time_quotes_now['list_date'] = real_time_quotes_now['list_date'].fillna(19890604)
    real_time_quotes_now = real_time_quotes_now.loc[real_time_quotes_now['list_date'] <= now_day_number]
    real_time_quotes_now = common_service_fun_api.classify_symbol(real_time_quotes_now)
    real_time_quotes_now = common_service_fun_api.exclude_ts_symbol(real_time_quotes_now)
    # 排除交易金额为0的
    real_time_quotes_now = common_service_fun_api.exclude_amount_zero_stock(real_time_quotes_now)

    de_list_symbol = company_common_service_new_api.get_de_list_company()

    real_time_quotes_now = real_time_quotes_now.loc[~(real_time_quotes_now['symbol'].isin(de_list_symbol))]

    query = {"up_level_code": BlackClassify.TRANSACTIONS.level_code}
    tag = mongodb_util.remove_data(query, db_name_constant.SELF_BLACK_STOCK)
    success = tag.acknowledged
    if success:

        for stock_one in real_time_quotes_now.itertuples():
            try:
                total_mv_check(stock_one)
                now_price_check(stock_one)
                volume_check(stock_one)
            except BaseException as e:
                logger.error("交易风险校验异常:{},{}", e, stock_one.symbol)


# 总市值check
def total_mv_check(stock_one):
    classification = stock_one.classification
    total_mv = stock_one.total_mv
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    key_id = stock_one.symbol + "_" + BlackClassify.MV_RISK.level_code
    tag = False
    if classification in ['S', 'H'] and total_mv < MAIN_MARKET_MIN_MV:
        tag = True
    elif classification in ['K', 'C', "X"] and total_mv < SUB_MARKET_MIN_MV:
        tag = True

    if tag:
        black_list_service_api.save_black_stock(
            key_id,
            stock_one.symbol,
            stock_one.name,
            str_day,
            str_now_date,
            BlackClassify.MV_RISK.level_name + ":" + str(
                round(total_mv / common_service_fun_api.HUNDRED_MILLION, 2)) + "亿",
            BlackClassify.MV_RISK.level_name + ":" + str(
                round(total_mv / common_service_fun_api.HUNDRED_MILLION, 2)) + "亿",
            "",
            BlackClassify.MV_RISK.up_level_code,
            BlackClassify.MV_RISK.up_level_name,
            BlackClassify.MV_RISK.level_code,
            BlackClassify.MV_RISK.level_name,
        )


# 当前面值check
def now_price_check(stock_one):
    now_price = stock_one.now_price
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')

    tfp_symbol_list = stock_tfp_api.get_stock_tfp_symbol_list_by_day(str_day)
    if stock_one.symbol in tfp_symbol_list:
        return

    key_id = stock_one.symbol + "_" + BlackClassify.CLOSE_PRICE_RISK.level_code
    if MIN_NOW_PRICE > now_price > 0:
        black_list_service_api.save_black_stock(
            key_id,
            stock_one.symbol,
            stock_one.name,
            str_day,
            str_now_date,
            BlackClassify.CLOSE_PRICE_RISK.level_name + ":当前价格" + str(now_price),
            BlackClassify.CLOSE_PRICE_RISK.level_name + ":当前价格" + str(now_price),
            "",
            BlackClassify.CLOSE_PRICE_RISK.up_level_code,
            BlackClassify.CLOSE_PRICE_RISK.up_level_name,
            BlackClassify.CLOSE_PRICE_RISK.level_code,
            BlackClassify.CLOSE_PRICE_RISK.level_name,
        )


#
def volume_check(stock_one):
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    trade_date_120 = trade_date_common_service_api.get_before_trade_date(str_day, 120)
    query = {'date': {"$gte": date_handle_util.no_slash_date(trade_date_120)}, 'symbol': stock_one.symbol}
    stock_qfq_daily_df = mongodb_util.find_query_data(db_name_constant.STOCK_QFQ_DAILY, query)
    if stock_qfq_daily_df.shape[0] < 120:
        return
    # volume 单位是100股
    sum_volume = sum(stock_qfq_daily_df['volume']) * 100
    key_id = stock_one.symbol + "_" + BlackClassify.AMOUNT_RISK.level_code
    tag = False
    classification = stock_one.classification
    if classification in ['S', 'H'] and sum_volume < MAIN_MARKET_MIN_VOLUME:
        tag = True

    elif classification in ['K', 'C'] and sum_volume < SUB_MARKET_MIN_VOLUME:
        tag = True

    elif classification in ['X'] and sum_volume < BJS_MARKET_MIN_VOLUME:
        tag = True

    if tag:
        black_list_service_api.save_black_stock(
            key_id,
            stock_one.symbol,
            stock_one.name,
            str_day,
            str_now_date,
            BlackClassify.AMOUNT_RISK.level_name + ":120个交易日成交量:" + str(
                round(sum_volume / common_service_fun_api.TEN_THOUSAND), 0) + "万股",
            BlackClassify.AMOUNT_RISK.level_name + ":120个交易日成交量:" + str(
                round(sum_volume / common_service_fun_api.TEN_THOUSAND), 0) + "万股",
            "",
            BlackClassify.AMOUNT_RISK.up_level_code,
            BlackClassify.AMOUNT_RISK.up_level_name,
            BlackClassify.AMOUNT_RISK.level_code,
            BlackClassify.AMOUNT_RISK.level_name,
        )


if __name__ == '__main__':
    transactions_check_task()

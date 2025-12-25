import sys
import os

import pandas as pd

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.akshare.k_line_api as k_line_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.api.xueqiu.xue_qiu_k_line_api as xue_qiu_k_line_api
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.component.common_service_fun_api as common_service_fun_api
from datetime import datetime, timedelta
import mns_common.api.msg.push_msg_api as push_msg_api
import numpy as np
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger
import threading

# source_type = 'xue_qiu'
source_type = 'xue_qiu'
error_no = 1


# 自定义报警处理函数
def custom_alert(current: int, threshold: int):
    push_msg_api.push_msg_to_wechat('获取k线数据异常', "当前次数:" + str(current) + "阈值:" + str(threshold))


# 定义一个带超时的函数调用
def call_with_timeout(func, *args, timeout=10, **kwargs):
    # 用于存储函数执行结果
    result = None
    exception = None

    # 定义一个线程目标函数
    def target():
        nonlocal result, exception
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            exception = e

    # 创建线程并启动
    thread = threading.Thread(target=target)
    thread.start()

    # 等待线程完成，最多等待 timeout 秒
    thread.join(timeout)

    # 如果线程仍然存活，说明函数超时了
    if thread.is_alive():
        raise TimeoutError(f"Function exceeded timeout of {timeout} seconds")

    # 如果函数抛出了异常，重新抛出
    if exception is not None:
        raise exception
    return result


def get_k_line_common_adapter(symbol, period, hq, end_date):
    global error_no
    df = pd.DataFrame()
    try:
        if source_type == 'em':

            df = call_with_timeout(get_em_k_line_api,
                                   symbol,
                                   period,
                                   hq,
                                   end_date,
                                   timeout=10)
        elif source_type == 'xue_qiu':
            df = call_with_timeout(get_xueqiu_k_line_api,
                                   symbol,
                                   period,
                                   hq,
                                   end_date,
                                   timeout=10)

        if data_frame_util.is_empty(df):
            error_no = error_no + 1
    except BaseException as e:
        logger.error("获取k线异常:{}", e)
        error_no = error_no + 1
    if error_no == 1000:
        push_msg_api.push_msg_to_wechat('获取k线数据异常', "当前次数:" + str(error_no))
    return df


# 应用带参数的装饰器
# @exception_counter(
#     threshold=1500,
#     alert_handler=custom_alert,
#     auto_reset=False
# )
def get_em_k_line_api(symbol, period, hq, end_date):
    # 检查symbol是否以'6'开头
    if symbol.startswith('6'):
        symbol_a = '1.' + symbol
    else:
        symbol_a = '0.' + symbol
    stock_hfq_df = k_line_api.stock_zh_a_hist(symbol=symbol_a,
                                              period=period,
                                              start_date=date_handle_util.no_slash_date('1990-12-19'),
                                              end_date=date_handle_util.no_slash_date(end_date),
                                              adjust=hq)

    stock_hfq_df.rename(columns={"日期": "date", "开盘": "open",
                                 "收盘": "close", "最高": "high",
                                 "最低": "low", "成交量": "volume",
                                 "成交额": "amount", "振幅": "pct_chg",
                                 "涨跌幅": "chg", "涨跌额": "change",
                                 "换手率": "exchange"}, inplace=True)
    stock_hfq_df['symbol'] = symbol
    stock_hfq_df['_id'] = symbol + '-' + stock_hfq_df['date']
    return stock_hfq_df


# period : year  quarter  month  week  day
# hq: qfq:before ,hfq:after, bfq:normal

def get_xueqiu_k_line_api(symbol, period, hq, end_date):
    if hq == 'qfq':
        adjust = 'before'
    elif hq == 'hfq':
        adjust = 'after'
    else:
        adjust = 'normal'

    period_time = 'day'
    if period == 'daily':
        period_time = 'day'
    elif period == 'weekly':
        period_time = 'week'
    elif period == 'monthly':
        period_time = 'month'

    cookie = cookie_info_service.get_xue_qiu_cookie()
    symbol_pre_fix = common_service_fun_api.add_pre_prefix_one(symbol)
    dt = datetime.strptime(end_date, '%Y-%m-%d')
    dt += timedelta(days=1)
    timestamp = str(int(dt.timestamp() * 1000))  # 转换为毫秒
    stock_k_line_df = xue_qiu_k_line_api.get_xue_qiu_k_line(symbol_pre_fix, period_time,
                                                            cookie, timestamp, adjust)

    stock_k_line_df['pct_chg'] = round(abs(stock_k_line_df['high'] - stock_k_line_df['low'] / stock_k_line_df['high']),
                                       2)
    stock_k_line_df.rename(columns={"chg": "change",
                                    "percent": "chg",
                                    "str_day": "date",
                                    "market_capital": "flow_mv",
                                    "turnoverrate": "exchange"}, inplace=True)
    stock_k_line_df = stock_k_line_df[[
        "date",
        "open",
        "close",
        "high",
        "low",
        "volume",
        "amount",
        "pct_chg",
        "chg",
        "change",
        "exchange"
    ]]
    stock_k_line_df['symbol'] = symbol
    stock_k_line_df['date'] = stock_k_line_df['date'].str.replace('-', '')
    stock_k_line_df['_id'] = symbol + '-' + stock_k_line_df['date']
    stock_k_line_df['last_price'] = round(((stock_k_line_df['close']) / (1 + stock_k_line_df['chg'] / 100)), 2)
    stock_k_line_df['max_chg'] = round(
        ((stock_k_line_df['high'] - stock_k_line_df['last_price']) / stock_k_line_df['last_price']) * 100, 2)
    stock_k_line_df['amount_level'] = round((stock_k_line_df['amount'] / common_service_fun_api.HUNDRED_MILLION), 2)
    stock_k_line_df['flow_mv'] = round(stock_k_line_df['amount'] * 100 / stock_k_line_df['exchange'], 2)
    stock_k_line_df['flow_mv_sp'] = round(stock_k_line_df['flow_mv'] / common_service_fun_api.HUNDRED_MILLION, 2)

    stock_k_line_df.replace([np.inf, -np.inf], 0, inplace=True)
    stock_k_line_df.fillna(0, inplace=True)
    stock_k_line_df['date'] = stock_k_line_df['date'].astype(str).str[:8]
    return stock_k_line_df


if __name__ == '__main__':
    while True:
        test_df = get_k_line_common_adapter('000001', 'day', 'qfq', '2025-05-25')
        print(test_df)

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from datetime import datetime
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import pandas as pd
import time

mongodb_util = MongodbUtil('27017')


def update_five_connected_boards_task(stock_zt_pool):
    stock_zt_pool_5_list = stock_zt_pool.loc[stock_zt_pool['connected_boards_numbers'] == 5]
    if data_frame_util.is_empty(stock_zt_pool_5_list):
        return None
    # 保存五板以上数据
    handle_five_connected_boards_symbol(stock_zt_pool_5_list)
    time.sleep(10)
    update_high_point_day()


# 连续五板涨停信息同步
def handle_five_connected_boards_symbol(stock_zt_pool_5_list):
    trade_date_list = mongodb_util.find_all_data('trade_date_list')
    str_day_list = list(trade_date_list['trade_date'])
    stock_zt_pool_5_list = stock_zt_pool_5_list.loc[stock_zt_pool_5_list['str_day'].isin(str_day_list)]
    for stock_one in stock_zt_pool_5_list.itertuples():
        try:
            str_day = stock_one.str_day
            # 上市时间
            list_date = str(stock_one.list_date)
            # 五板的时间
            date_str_day = date_handle_util.str_to_date(str_day, "%Y-%m-%d")

            list_date_time = date_handle_util.add_date_day(list_date[0:8], 0)

            delta = date_str_day - list_date_time
            days = delta.days
            new_stock = False
            if days <= 30:
                new_stock = True

            before_five_day = trade_date_common_service_api.get_before_trade_date(str_day, 5)
            stock_zt_pool_five = mongodb_util.find_query_data('stock_zt_pool', query={'symbol': stock_one.symbol,
                                                                                      'str_day': before_five_day})
            stock_zt_pool_five['new_stock'] = new_stock

            save_zt_data(stock_zt_pool_five, stock_one.symbol, str_day)
        except BaseException as e:
            logger.error("发生异常:{},{}", stock_one.symbol, str_day)


def save_zt_data(stock_zt_pool_five, symbol, str_day):
    try:
        stock_zt_pool_five['closure_funds_level'] = round((stock_zt_pool_five['closure_funds'] / 10000000), 2)
        stock_zt_pool_five['amount_level'] = round((stock_zt_pool_five['amount'] / 10000000), 2)

        stock_zt_pool_five = stock_zt_pool_five.rename(columns={
            "str_day": "before_five_day"})

        stock_zt_pool_five['five_boards_day'] = str_day

        high_point_day = calculate_high_point_day(symbol, str_day)

        stock_zt_pool_five.loc[:, "high_point_day"] = high_point_day

        stock_zt_pool_five = stock_zt_pool_five[[
            "_id",
            'symbol',
            "name",
            "now_price",
            "exchange",
            "five_boards_day",
            "before_five_day",
            "high_point_day",
            "industry",
            "flow_mv_level",
            "amount_level",
            "closure_funds_level",
            "flow_mv_sp",
            "total_mv_sp",
            "amount",
            "chg",
            "frying_plates_numbers",
            "statistics",
            "flow_mv",
            "total_mv",
            "closure_funds",
            "first_closure_time",
            "last_closure_time",
            "index",
            'new_stock',
            "connected_boards_numbers",
            "first_sw_industry",
            "second_sw_industry",
            "third_sw_industry",
            "mv_circulation_ratio",
            "list_date",
            "classification",
        ]]

        mongodb_util.save_mongo(stock_zt_pool_five, 'stock_zt_pool_five')
    except BaseException as e:
        logger.error("发生异常:{}", symbol + '-' + str_day)


# 计算最大连板数
def calculate_max_connected_boards_numbers(begin_day, end_day, symbol):
    query = {'symbol': symbol,
             '$and': [{'str_day': {'$gte': begin_day}}, {'str_day': {'$lte': end_day}}]}
    stock_zt_pool = mongodb_util.descend_query(query, 'stock_zt_pool', 'connected_boards_numbers', 1)
    if stock_zt_pool.shape[0] > 0:
        max_connected_boards_numbers = list(stock_zt_pool.connected_boards_numbers)[0]
    else:
        max_connected_boards_numbers = 0
    return max_connected_boards_numbers


# 计算涨停数目
def calculate_total_zt_num(begin_day, end_day, symbol):
    query = {'symbol': symbol,
             '$and': [{'str_day': {'$gte': begin_day}}, {'str_day': {'$lte': end_day}}]}
    return mongodb_util.count(query, 'stock_zt_pool')


# 计算最高点到第一板的最大涨幅
def calculate_max_chg(begin_day, end_day, symbol):
    query_max = {'symbol': symbol, "date": date_handle_util.no_slash_date(end_day)}
    max_stock_hfq_daily = mongodb_util.find_one_query('stock_qfq_daily', query_max)
    query_min = {'symbol': symbol, "date": {'$lte': date_handle_util.no_slash_date(begin_day)}}
    min_stock_hfq_daily = mongodb_util.descend_query(query_min, 'stock_qfq_daily', 'date', 1)
    if max_stock_hfq_daily.shape[0] > 0 and min_stock_hfq_daily.shape[0] > 0:
        max_price = max_stock_hfq_daily['high']
        min_price = min_stock_hfq_daily['last_price']
        max_chg = round(((max_price - min_price) / min_price) * 100, 2)
        max_chg = list(max_chg)[0]
    else:
        max_chg = 0
    min_price = list(min_price)[0]
    start_df = pd.DataFrame([[max_chg, min_price]], columns=['max_chg',
                                                             'start_price'])

    return start_df


# 找出最高点时间
def calculate_high_point_day(symbol, five_boards_day):
    query = {'symbol': symbol, 'date': {'$gte': date_handle_util.no_slash_date(five_boards_day)}}
    stock_hfq_daily_list = mongodb_util.ascend_query(query, 'stock_hfq_daily', 'date', 40)

    if stock_hfq_daily_list.shape[0] == 0:
        return five_boards_day

    max_index = stock_hfq_daily_list['high'].idxmax()
    max_row = stock_hfq_daily_list.iloc[max_index, :]

    date = max_row.date

    high_point_day_date = date_handle_util.str_to_date(date, '%Y%m%d')

    high_point_day = high_point_day_date.strftime('%Y-%m-%d')

    return high_point_day


# 计算最高点 (1+10%)的五次方 = 1.62  (1+10%)的六次方 =1.77
def update_high_point_day():
    stock_zt_pool_five_list = mongodb_util.find_all_data('stock_zt_pool_five')

    stock_zt_pool_five_list = stock_zt_pool_five_list.sort_values(by=['five_boards_day'], ascending=False)

    for stock_one in stock_zt_pool_five_list.itertuples():
        try:
            high_point_day = calculate_high_point_day(stock_one.symbol, stock_one.five_boards_day)
            start_df = calculate_max_chg(stock_one.before_five_day, high_point_day, stock_one.symbol)

            max_connected_boards_numbers = calculate_max_connected_boards_numbers(stock_one.before_five_day,
                                                                                  high_point_day, stock_one.symbol)

            int_date = int(stock_one.list_date)  # 转换为整数
            list_date_01 = datetime(year=int_date // 10000, month=(int_date // 100) % 100, day=int_date % 100)

            str_day_date = date_handle_util.str_to_date(stock_one.five_boards_day, '%Y-%m-%d')
            # 计算日期差值 距离现在上市时间
            diff_days = (str_day_date - list_date_01).days

            total_zt_num = calculate_total_zt_num(stock_one.before_five_day, high_point_day, stock_one.symbol)

            query = {"before_five_day": stock_one.before_five_day, "symbol": stock_one.symbol}
            new_values = {"$set": {"high_point_day": high_point_day,
                                   "max_chg": list(start_df['max_chg'])[0],
                                   "start_price": list(start_df['start_price'])[0],
                                   "max_connected_boards_numbers": max_connected_boards_numbers,
                                   "total_zt_num": total_zt_num,
                                   "diff_days": diff_days
                                   }}
            mongodb_util.update_many(query, new_values, 'stock_zt_pool_five')
        except BaseException as e:
            logger.error("更新 high_point_day 异常:{},{},{}", stock_one.symbol, stock_one.five_boards_day, e)


def fix_miss_high_symbol():
    sync_one_symbol('002901', '2022-09-27')
    sync_one_symbol('000716', '2022-08-24')
    sync_one_symbol('002693', '2022-10-13')
    sync_one_symbol('000948', '2022-10-12')
    sync_one_symbol('000638', '2022-10-11')
    sync_one_symbol('002093', '2022-10-10')
    sync_one_symbol('002907', '2022-10-17')
    sync_one_symbol('002528', '2022-10-12')
    sync_one_symbol('003023', '2022-09-21')
    sync_one_symbol('002093', '2022-10-10')
    sync_one_symbol('003005', '2022-09-28')
    sync_one_symbol('002965', '2022-05-27')

    sync_one_symbol('000032', '2022-10-26')
    sync_one_symbol('002045', '2022-08-10')

    sync_one_symbol('003042', '2022-10-31')

    sync_one_symbol('002896', '2022-07-18')

    sync_one_symbol('000759', '2022-09-08')
    sync_one_symbol('002579', '2022-08-05')

    sync_one_symbol('002992', '2022-07-06')

    sync_one_symbol('000582', '2022-04-07')

    sync_one_symbol('002053', '2022-03-07')


def group_industry():
    pipeline = [
        {'$match': {
            "classification": "S"}},
        {'$group': {'_id': "$first_sw_industry", 'count': {'$sum': 1}}}
    ]
    result = mongodb_util.aggregate(pipeline, 'stock_zt_pool_five')

    result = result.sort_values(by=['count'], ascending=True)
    print(result)


def group_flow_mv():
    pipeline = [
        {'$match': {
            "new_stock": False,
            "classification": {"$in": ["S", "H"]}}},
        {'$group': {'_id': "$flow_mv_level", 'count': {'$sum': 1}}}
    ]
    result = mongodb_util.aggregate(pipeline, 'stock_zt_pool_five')

    result = result.sort_values(by=['count'], ascending=False)
    print(result)


def sync_one_symbol(symbol, str_day):
    stock_zt_pool_five = mongodb_util.find_query_data('stock_zt_pool', query={'symbol': symbol,
                                                                              'str_day': str_day})
    stock_zt_pool_five['new_stock'] = False
    after_five_day = trade_date_common_service_api.get_further_trade_date(str_day, 5)
    save_zt_data(stock_zt_pool_five, symbol, after_five_day)

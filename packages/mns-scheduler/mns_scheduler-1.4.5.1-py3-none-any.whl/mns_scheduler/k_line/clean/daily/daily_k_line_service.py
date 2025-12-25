import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.date_handle_util as date_handle_util
import mns_scheduler.k_line.hot_stocks.recent_hot_stocks_clean_service as recent_hot_stocks_clean_service
import mns_scheduler.k_line.clean.daily.daily_k_line_clean_common_service as daily_k_line_clean_common_service
from mns_common.component.classify.symbol_classify_param import stock_type_classify_param
import mns_scheduler.k_line.clean.week_month.sub_new_week_month_k_line_service as sub_new_week_month_k_line_service

mongodb_util = MongodbUtil('27017')
# 普通股日线查询数据 60
NORMAL_DAILY_K_LINE_NUMBER = 60


def handle_day_line(k_line_info, str_day, symbol, deal_days):
    sub_stock_new_max_deal_days = stock_type_classify_param['sub_new_stock_max_deal_days']
    if deal_days > sub_stock_new_max_deal_days:
        return handle_day_line_normal(k_line_info, str_day, symbol, deal_days)

    else:
        # 交易日小于100天的
        return handle_day_line_sub_new(k_line_info, str_day, symbol, deal_days)

    # 处理日线


def handle_day_line_sub_new(k_line_info, str_day, symbol, deal_days):
    k_line_info['deal_days'] = deal_days
    query = {"symbol": symbol, 'date': {"$lt": date_handle_util.no_slash_date(str_day)}}
    stock_qfq_daily = mongodb_util.descend_query(query, 'stock_qfq_daily', 'date', deal_days)
    # 初始化数据
    k_line_info = daily_k_line_clean_common_service.init_day_line_data(k_line_info, stock_qfq_daily)
    if stock_qfq_daily.shape[0] == 0:
        return k_line_info

    # 当前交易日k线信息
    stock_qfq_daily_one = stock_qfq_daily.iloc[0:1]
    # 设置当天k线形态 下一个交易日判断当前交易日k线形态
    stock_qfq_daily_one = daily_k_line_clean_common_service.set_k_line_patterns(stock_qfq_daily_one.copy())
    # 设置历史k线列表
    stock_qfq_daily_one = daily_k_line_clean_common_service.set_history_list(stock_qfq_daily_one.copy(),
                                                                             stock_qfq_daily.copy())
    # 修改字段名称
    k_line_info = daily_k_line_clean_common_service.k_line_field_fix_name(k_line_info.copy(),
                                                                          stock_qfq_daily_one.copy())
    if stock_qfq_daily.shape[0] == 1:
        # 上市第二天的股票
        return k_line_info
    # 排除上市第一天的股票
    stock_qfq_daily = stock_qfq_daily.iloc[0:deal_days - 1]
    # 计算换手平均值 k线 5 10 20 30 60均线
    stock_qfq_daily = daily_k_line_clean_common_service.calculate_exchange_and_k_line_avg_param(stock_qfq_daily)
    # 计算30天最大涨幅
    k_line_info = daily_k_line_clean_common_service.calculate_30_day_max_chg(stock_qfq_daily, k_line_info)
    # 设置五日k线和
    k_line_info = daily_k_line_clean_common_service.set_sum_five_chg(k_line_info, deal_days)
    # 计算当前交易日开盘时的涨幅
    k_line_info = daily_k_line_clean_common_service.calculate_open_chg(stock_qfq_daily, k_line_info)
    # 计算 昨日最高点到开盘涨幅差值 and   # 昨日最高点到当日收盘涨幅之间的差值 and  # 昨日收盘到当日开盘涨幅之间的差值
    k_line_info = daily_k_line_clean_common_service.calculate_chg_diff_value(k_line_info)
    # 计算 月线
    k_line_info = sub_new_week_month_k_line_service.handle_month_line(k_line_info, stock_qfq_daily, deal_days)
    # 计算周线
    k_line_info = sub_new_week_month_k_line_service.handle_week_line(k_line_info, stock_qfq_daily, deal_days)

    # 排除最近有三板以上的股票 todo
    # 计算最近热门大涨的股票
    recent_hot_stocks_clean_service.calculate_recent_hot_stocks(stock_qfq_daily, symbol, str_day)
    # 修改 avg name
    k_line_info = daily_k_line_clean_common_service.fix_avg_slope_name(k_line_info, stock_qfq_daily)

    return k_line_info


def handle_day_line_normal(k_line_info, str_day, symbol, deal_days):
    # 取五天刚好包含一周 todo 选择60天的历史记录

    query = {"symbol": symbol, 'date': {"$lt": date_handle_util.no_slash_date(str_day)}}
    stock_qfq_daily = mongodb_util.descend_query(query, 'stock_qfq_daily', 'date', NORMAL_DAILY_K_LINE_NUMBER)
    if stock_qfq_daily.shape[0] == 0:
        return k_line_info
    # 初始化数据
    k_line_info = daily_k_line_clean_common_service.init_day_line_data(k_line_info, stock_qfq_daily)
    # 计算30天最大涨幅
    k_line_info = daily_k_line_clean_common_service.calculate_30_day_max_chg(stock_qfq_daily, k_line_info)
    # 计算换手平均值 k线 5 10 20 30 60均线
    stock_qfq_daily = daily_k_line_clean_common_service.calculate_exchange_and_k_line_avg_param(stock_qfq_daily)
    # 当前交易日k线信息
    stock_qfq_daily_one = stock_qfq_daily.iloc[0:1]
    # 设置当天k线形态 下一个交易日判断当前交易日k线形态
    stock_qfq_daily_one = daily_k_line_clean_common_service.set_k_line_patterns(stock_qfq_daily_one.copy())
    # 设置历史k线列表
    stock_qfq_daily_one = daily_k_line_clean_common_service.set_history_list(stock_qfq_daily_one.copy(),
                                                                             stock_qfq_daily.copy())
    # 修改字段名称
    k_line_info = daily_k_line_clean_common_service.k_line_field_fix_name(k_line_info.copy(),
                                                                          stock_qfq_daily_one.copy())
    # 设置五日k线和
    k_line_info = daily_k_line_clean_common_service.set_sum_five_chg(k_line_info, deal_days)
    # 计算当前交易日开盘时的涨幅
    k_line_info = daily_k_line_clean_common_service.calculate_open_chg(stock_qfq_daily, k_line_info)
    # 计算 昨日最高点到开盘涨幅差值 and   # 昨日最高点到当日收盘涨幅之间的差值 and  # 昨日收盘到当日开盘涨幅之间的差值
    k_line_info = daily_k_line_clean_common_service.calculate_chg_diff_value(k_line_info)

    # 排除最近有三板以上的股票 todo
    # 计算最近热门大涨的股票
    recent_hot_stocks_clean_service.calculate_recent_hot_stocks(stock_qfq_daily, symbol, str_day)
    # 修改 avg name
    k_line_info = daily_k_line_clean_common_service.fix_avg_slope_name(k_line_info, stock_qfq_daily)
    return k_line_info


# if __name__ == '__main__':
#     query1 = {"symbol": '301596', 'date': {"$lte": date_handle_util.no_slash_date('2024-05-31')}}
#     stock_qfq_daily_301596 = mongodb_util.descend_query(query1, 'stock_qfq_daily', 'date', 15)
#     stock_qfq_daily_301596.shape[0]
#     stock_qfq_daily1 = stock_qfq_daily_301596.iloc[0:14]

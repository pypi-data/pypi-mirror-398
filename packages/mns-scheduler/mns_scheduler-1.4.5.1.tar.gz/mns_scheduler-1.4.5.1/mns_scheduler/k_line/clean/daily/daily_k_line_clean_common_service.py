import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.component.k_line.patterns.k_line_patterns_service_api as k_line_patterns_service

# 计算五日线之和交易天数最小值
MIN_DEAL_DAYS = 6


# 初始化数据
def init_day_line_data(k_line_info, stock_qfq_daily):
    daily_num = stock_qfq_daily.shape[0]
    if daily_num == 0:
        k_line_info['max_chg_daily01'] = 0
        k_line_info['daily01'] = 0
        k_line_info['daily02'] = 0
        k_line_info['daily03'] = 0
        k_line_info['daily04'] = 0
        k_line_info['daily05'] = 0
    elif daily_num == 1:
        k_line_info['max_chg_daily01'] = stock_qfq_daily.iloc[0].max_chg
        k_line_info['daily01'] = stock_qfq_daily.iloc[0].chg
        k_line_info['daily02'] = 0
        k_line_info['daily03'] = 0
        k_line_info['daily04'] = 0
        k_line_info['daily05'] = 0
    elif daily_num == 2:
        k_line_info['max_chg_daily01'] = stock_qfq_daily.iloc[0].max_chg
        k_line_info['daily01'] = stock_qfq_daily.iloc[0].chg
        k_line_info['daily02'] = stock_qfq_daily.iloc[1].chg
        k_line_info['daily03'] = 0
        k_line_info['daily04'] = 0
        k_line_info['daily05'] = 0
    elif daily_num == 3:
        k_line_info['max_chg_daily01'] = stock_qfq_daily.iloc[0].max_chg
        k_line_info['daily01'] = stock_qfq_daily.iloc[0].chg
        k_line_info['daily02'] = stock_qfq_daily.iloc[1].chg
        k_line_info['daily03'] = stock_qfq_daily.iloc[2].chg
        k_line_info['daily04'] = 0
        k_line_info['daily05'] = 0
    elif daily_num == 4:
        k_line_info['max_chg_daily01'] = stock_qfq_daily.iloc[0].max_chg
        k_line_info['daily01'] = stock_qfq_daily.iloc[0].chg
        k_line_info['daily02'] = stock_qfq_daily.iloc[1].chg
        k_line_info['daily03'] = stock_qfq_daily.iloc[2].chg
        k_line_info['daily04'] = stock_qfq_daily.iloc[3].chg
        k_line_info['daily05'] = 0
    elif daily_num >= 5:
        k_line_info['max_chg_daily01'] = stock_qfq_daily.iloc[0].max_chg
        k_line_info['daily01'] = stock_qfq_daily.iloc[0].chg
        k_line_info['daily02'] = stock_qfq_daily.iloc[1].chg
        k_line_info['daily03'] = stock_qfq_daily.iloc[2].chg
        k_line_info['daily04'] = stock_qfq_daily.iloc[3].chg
        k_line_info['daily05'] = stock_qfq_daily.iloc[4].chg
    k_line_info.loc[:, 'exclude'] = False
    # 30日最大涨幅
    k_line_info.loc[:, 'amount_level_last'] = 0
    k_line_info.loc[:, 'exchange_last'] = 0
    k_line_info.loc[:, 'exchange_mean_last'] = 0
    k_line_info.loc[:, 'exchange_mean_last_02'] = 0
    k_line_info.loc[:, 'exchange_difference_last'] = 0
    k_line_info.loc[:, 'exchange_chg_percent_last'] = 0
    k_line_info.loc[:, 'pct_chg_mean_last'] = 0
    k_line_info.loc[:, 'pct_chg_difference_last'] = 0
    k_line_info.loc[:, 'close_difference_five_last'] = 0
    k_line_info.loc[:, 'close_difference_ten_last'] = 0
    k_line_info.loc[:, 'close_difference_twenty_last'] = 0
    k_line_info.loc[:, 'close_difference_thirty_last'] = 0
    k_line_info.loc[:, 'close_difference_sixty_last'] = 0
    k_line_info.loc[:, 'pct_chg_last'] = 0
    k_line_info.loc[:, 'max_chg_last'] = 0
    k_line_info.loc[:, 'chg_last'] = 0
    k_line_info.loc[:, 'close_last'] = 0
    k_line_info.loc[:, 'high_last'] = 0
    k_line_info.loc[:, 'low_last'] = 0

    k_line_info.loc[:, 'avg_five_last'] = 0
    k_line_info.loc[:, 'avg_ten_last'] = 0
    k_line_info.loc[:, 'avg_twenty_last'] = 0
    k_line_info.loc[:, 'avg_thirty_last'] = 0
    k_line_info.loc[:, 'avg_sixty_last'] = 0

    k_line_info.loc[:, 'slope_five_last'] = 0
    k_line_info.loc[:, 'slope_ten_last'] = 0
    k_line_info.loc[:, 'slope_twenty_last'] = 0
    k_line_info.loc[:, 'slope_thirty_last'] = 0
    k_line_info.loc[:, 'slope_sixty_last'] = 0

    k_line_info.loc[:, 'std_amount_ten'] = 0
    k_line_info.loc[:, 'mean_amount_ten'] = 0
    k_line_info.loc[:, 'std_amount_thirty'] = 0
    k_line_info.loc[:, 'mean_amount_thirty'] = 0

    k_line_info.loc[:, 'std_amount_sixty'] = 0
    k_line_info.loc[:, 'mean_amount_sixty'] = 0

    k_line_info.loc[:, 'sum_five_chg'] = 0

    k_line_info.loc[:, 'open_chg_last'] = 0

    k_line_info.loc[:, 'before_close'] = 0

    k_line_info.loc[:, 'diff_max_chg_from_open_last'] = 0

    k_line_info.loc[:, 'diff_max_chg_from_close_last'] = 0

    k_line_info.loc[:, 'diff_close_from_open_last'] = 0

    k_line_info.loc[:, 'max_chg_30'] = 0

    return k_line_info


# 计算30天最大涨幅
def calculate_30_day_max_chg(stock_qfq_daily, k_line_info):
    # 取30天的交易k线
    stock_qfq_daily_30 = stock_qfq_daily.iloc[0:29]

    deal_days = stock_qfq_daily_30.shape[0]

    if deal_days < 30:
        # 排除第一天
        stock_qfq_daily_30 = stock_qfq_daily_30[0: deal_days - 1]
    if deal_days == 0 or deal_days == 1:
        k_line_info['max_chg_30'] = 0
        return k_line_info

    stock_qfq_daily_30['date_time'] = pd.to_datetime(stock_qfq_daily_30['date'])
    # 找出最高点和最低点的行
    max_row = stock_qfq_daily_30[stock_qfq_daily_30['high'] == stock_qfq_daily_30['high'].max()]
    min_row = stock_qfq_daily_30[stock_qfq_daily_30['low'] == stock_qfq_daily_30['low'].min()]

    # 获取最高点和最低点的值以及对应的日期
    max_high = max_row['high'].values[0]
    min_low = min_row['low'].values[0]
    date_of_max_high = max_row['date_time'].values[0]
    date_of_min_low = min_row['date_time'].values[0]
    max_chg_30 = round((max_high - min_low) * 100 / min_low, 2)
    if date_of_max_high < date_of_min_low:
        max_chg_30 = -max_chg_30
    k_line_info['max_chg_30'] = max_chg_30
    return k_line_info


# 计算换手平均值 k线 5 10 20 30 60均线
def calculate_exchange_and_k_line_avg_param(stock_qfq_daily):
    stock_qfq_daily = stock_qfq_daily.sort_values(by=['date'], ascending=True)

    # 计算每个日期前10天的换手均值
    stock_qfq_daily['exchange_mean'] = round(
        stock_qfq_daily['exchange'].rolling(window=10, min_periods=1).mean(), 2)

    # stock_qfq_daily['exchange_mean_ewm'] = round(
    #     stock_qfq_daily['exchange'].ewm(span=10).mean(), 2)

    stock_qfq_daily['exchange_mean_yesterday'] = stock_qfq_daily['exchange_mean']

    # 昨日平均值 向当前移位
    stock_qfq_daily['exchange_mean_yesterday'] = stock_qfq_daily['exchange_mean_yesterday'].shift(1)

    # 今天换手相对于[昨日平均十日换手]的差值
    stock_qfq_daily['exchange_difference'] = round(
        stock_qfq_daily['exchange'] - stock_qfq_daily['exchange_mean_yesterday'], 2)

    # 今天换手相对于[昨日平均十日换手]的倍数
    stock_qfq_daily['exchange_chg_percent'] = round(
        stock_qfq_daily['exchange'] / stock_qfq_daily['exchange_mean_yesterday'], 2)

    # pct_chg

    # 计算每个日期的前10天的均值
    stock_qfq_daily['pct_chg_mean'] = round(stock_qfq_daily['pct_chg'].rolling(window=10, min_periods=1).mean(),
                                            2)

    stock_qfq_daily['pct_chg_mean_yesterday'] = stock_qfq_daily['pct_chg_mean']

    stock_qfq_daily['pct_chg_mean_yesterday'] = stock_qfq_daily['pct_chg_mean_yesterday'].shift(1)

    stock_qfq_daily['pct_chg_difference'] = round(
        stock_qfq_daily['pct_chg'] - stock_qfq_daily['pct_chg_mean_yesterday'],
        2)

    # 计算五日均线

    stock_qfq_daily['avg_five'] = round(stock_qfq_daily['close'].rolling(window=5, min_periods=1).mean(),
                                        2)
    # 计算十日均线
    stock_qfq_daily['avg_ten'] = round(stock_qfq_daily['close'].rolling(window=10, min_periods=1).mean(),
                                       2)
    # 计算二十日均线
    stock_qfq_daily['avg_twenty'] = round(stock_qfq_daily['close'].rolling(window=20, min_periods=1).mean(),
                                          2)

    # 计算三十日均线
    stock_qfq_daily['avg_thirty'] = round(stock_qfq_daily['close'].rolling(window=30, min_periods=1).mean(),
                                          2)

    # 计算六十日均线
    stock_qfq_daily['avg_sixty'] = round(stock_qfq_daily['close'].rolling(window=60, min_periods=1).mean(),
                                         2)

    # 收盘价格与均线差值
    stock_qfq_daily['close_difference_five'] = round(
        100 * (stock_qfq_daily['close'] - stock_qfq_daily['avg_five']) / stock_qfq_daily['avg_five'],
        2)

    stock_qfq_daily['close_difference_ten'] = round(
        100 * (stock_qfq_daily['close'] - stock_qfq_daily['avg_ten']) / stock_qfq_daily['avg_ten'],
        2)

    stock_qfq_daily['close_difference_twenty'] = round(
        100 * (stock_qfq_daily['close'] - stock_qfq_daily['avg_twenty']) / stock_qfq_daily['avg_twenty'],
        2)

    stock_qfq_daily['close_difference_thirty'] = round(
        100 * (stock_qfq_daily['close'] - stock_qfq_daily['avg_thirty']) / stock_qfq_daily['avg_thirty'],
        2)

    stock_qfq_daily['close_difference_sixty'] = round(
        100 * (stock_qfq_daily['close'] - stock_qfq_daily['avg_sixty']) / stock_qfq_daily['avg_sixty'],
        2)
    if (('slope_' + 'five' not in stock_qfq_daily.columns)
            or ('slope_' + 'ten' not in stock_qfq_daily.columns) \
            or ('slope_' + 'twenty' not in stock_qfq_daily.columns) \
            or ('slope_' + 'thirty' not in stock_qfq_daily.columns) \
            or ('slope_' + 'sixty' not in stock_qfq_daily.columns)):
        # 计算均线斜率
        stock_qfq_daily = calculate_slope(stock_qfq_daily, windows=['five', 'ten', 'twenty', 'thirty', 'sixty'])

    stock_qfq_daily = stock_qfq_daily[[
        "symbol",
        "name",
        "industry",
        "chg",
        "max_chg",
        "pct_chg",
        "pct_chg_mean",
        "exchange",
        "exchange_mean",
        "exchange_mean_yesterday",
        "exchange_difference",
        'exchange_chg_percent',
        "pct_chg_mean_yesterday",
        "pct_chg_difference",
        "close_difference_five",
        "close_difference_ten",
        "close_difference_twenty",
        "close_difference_thirty",
        "close_difference_sixty",
        "amount_level",
        "flow_mv",
        "flow_mv_sp",
        "volume",
        "amount",
        "change",
        "last_price",
        "open",
        "close",
        "high",
        "low",
        "avg_five",
        "avg_ten",
        "avg_twenty",
        'avg_thirty',
        'avg_sixty',
        "slope_five",
        "slope_ten",
        "slope_twenty",
        'slope_thirty',
        'slope_sixty',
        "classification",
        "_id",
        "date"
    ]]
    stock_qfq_daily = stock_qfq_daily.sort_values(by=['date'], ascending=False)
    stock_qfq_daily = stock_qfq_daily.fillna(0)

    return stock_qfq_daily


def fix_avg_slope_name(k_line_info, stock_qfq_daily):
    stock_qfq_daily_one = stock_qfq_daily.iloc[0:1]
    k_line_info['slope_five_last'] = stock_qfq_daily_one['slope_five']
    k_line_info['slope_ten_last'] = stock_qfq_daily_one['slope_ten']
    k_line_info['slope_twenty_last'] = stock_qfq_daily_one['slope_twenty']
    k_line_info['slope_thirty_last'] = stock_qfq_daily_one['slope_thirty']
    k_line_info['slope_sixty_last'] = stock_qfq_daily_one['slope_sixty']
    return k_line_info


# 计算均线
def calculate_moving_averages(data, windows=['five', 'ten', 'twenty', 'thirty', 'sixty']):
    for window in windows:
        data[f'avg_{window}', window] = data['close'].rolling(window=window).mean()
    return data


# 计算均线斜率
def calculate_slope(data, windows=['five', 'ten', 'twenty', 'thirty', 'sixty']):
    for window in windows:
        if 'slope_' + window in data.columns:
            continue
        data[f'slope_{window}'] = data[f'avg_{window}'].diff() / data[f'avg_{window}'].shift(1)
        data[f'slope_{window}'] = data[f'slope_{window}'] * 100
        data[f'slope_{window}'] = round(data[f'slope_{window}'], 2)
    return data


# 设置当天k线形态 下一个交易日判断当前交易日k线形态
def set_k_line_patterns(stock_qfq_daily_one):
    open = list(stock_qfq_daily_one['open'])[0]
    close = list(stock_qfq_daily_one['close'])[0]
    high = list(stock_qfq_daily_one['high'])[0]
    low = list(stock_qfq_daily_one['low'])[0]
    max_chg = list(stock_qfq_daily_one['max_chg'])[0]
    chg = list(stock_qfq_daily_one['chg'])[0]

    k_line_pattern = k_line_patterns_service.k_line_patterns_classify(open, close, high, low, max_chg, chg)
    stock_qfq_daily_one.loc[:, 'k_line_pattern'] = k_line_pattern.value
    return stock_qfq_daily_one


# 设置历史k线列表
def set_history_list(stock_qfq_daily_one, stock_qfq_daily):
    stock_qfq_daily = stock_qfq_daily[[
        "date",
        "exchange",
        "exchange_mean",
        "exchange_mean_yesterday",
        "exchange_difference",
        "exchange_chg_percent",
        "pct_chg_mean_yesterday",
        "pct_chg_difference",
        "pct_chg",
        "pct_chg_mean",
        "max_chg",
        "chg",
        "amount_level",
        "close_difference_five",
        "close_difference_ten",
        "close_difference_twenty",
        "close_difference_thirty",
        'open',
        'close',
        'high',
        'low'
    ]]
    # 删除index 转str
    stock_qfq_daily_one.loc[:, 'history_data'] = stock_qfq_daily.to_string(index=False)

    daily_num = stock_qfq_daily.shape[0]
    std_amount_ten = 0
    mean_amount_ten = 0
    std_amount_thirty = 0
    mean_amount_thirty = 0
    std_amount_sixty = 0
    mean_amount_sixty = 0

    if daily_num >= 10:
        stock_qfq_daily_ten = stock_qfq_daily.iloc[0:10]
        # 计算 10日 amount 的标准差
        std_amount_ten = round(stock_qfq_daily_ten['amount_level'].std(), 2)
        # 计算 10日amount 的平均值
        mean_amount_ten = round(stock_qfq_daily_ten['amount_level'].mean(), 2)

    if daily_num >= 30:
        stock_qfq_daily_thirty = stock_qfq_daily.iloc[0:30]
        # 计算 amount 的标准差
        std_amount_thirty = round(stock_qfq_daily_thirty['amount_level'].std(), 2)
        # 计算 amount 的平均值
        mean_amount_thirty = round(stock_qfq_daily_thirty['amount_level'].mean(), 2)
    if daily_num >= 60:
        std_amount_sixty = round(stock_qfq_daily['amount_level'].std(), 2)
        # 计算 amount 的平均值
        mean_amount_sixty = round(stock_qfq_daily['amount_level'].mean(), 2)

    # text = list(stock_qfq_daily_one['history_data'])[0]
    # history_data_df = pd.read_csv(StringIO(text), delim_whitespace=True)

    stock_qfq_daily_one.loc[:, 'std_amount_ten'] = std_amount_ten
    stock_qfq_daily_one.loc[:, 'mean_amount_ten'] = mean_amount_ten
    stock_qfq_daily_one.loc[:, 'std_amount_thirty'] = std_amount_thirty
    stock_qfq_daily_one.loc[:, 'mean_amount_thirty'] = mean_amount_thirty
    stock_qfq_daily_one.loc[:, 'std_amount_sixty'] = std_amount_sixty
    stock_qfq_daily_one.loc[:, 'mean_amount_sixty'] = mean_amount_sixty

    return stock_qfq_daily_one


# 修改字段名称
def k_line_field_fix_name(k_line_info, stock_qfq_daily_one):
    k_line_info['classification'] = stock_qfq_daily_one['classification']
    k_line_info['amount_level_last'] = stock_qfq_daily_one['amount_level']
    k_line_info['name'] = stock_qfq_daily_one['name']
    k_line_info['exchange_last'] = stock_qfq_daily_one['exchange']
    k_line_info['exchange_mean_last'] = stock_qfq_daily_one['exchange_mean']
    k_line_info['exchange_mean_last_02'] = stock_qfq_daily_one['exchange_mean_yesterday']
    k_line_info['exchange_difference_last'] = stock_qfq_daily_one['exchange_difference']
    k_line_info['exchange_chg_percent_last'] = stock_qfq_daily_one['exchange_chg_percent']
    k_line_info['pct_chg_mean_last'] = stock_qfq_daily_one['pct_chg_mean_yesterday']
    k_line_info['pct_chg_difference_last'] = stock_qfq_daily_one['pct_chg_difference']

    k_line_info['close_difference_five_last'] = stock_qfq_daily_one['close_difference_five']
    k_line_info['close_difference_ten_last'] = stock_qfq_daily_one['close_difference_ten']
    k_line_info['close_difference_twenty_last'] = stock_qfq_daily_one['close_difference_twenty']
    k_line_info['close_difference_thirty_last'] = stock_qfq_daily_one['close_difference_thirty']
    k_line_info['close_difference_sixty_last'] = stock_qfq_daily_one['close_difference_sixty']

    k_line_info['pct_chg_last'] = stock_qfq_daily_one['pct_chg']
    k_line_info['pct_chg_mean_last'] = stock_qfq_daily_one['pct_chg_mean']
    k_line_info['max_chg_last'] = stock_qfq_daily_one['max_chg']
    k_line_info['chg_last'] = stock_qfq_daily_one['chg']
    k_line_info['open_last'] = stock_qfq_daily_one['open']
    k_line_info['close_last'] = stock_qfq_daily_one['close']
    k_line_info['high_last'] = stock_qfq_daily_one['high']
    k_line_info['low_last'] = stock_qfq_daily_one['low']
    k_line_info['avg_five_last'] = stock_qfq_daily_one['avg_five']
    k_line_info['avg_ten_last'] = stock_qfq_daily_one['avg_ten']
    k_line_info['avg_twenty_last'] = stock_qfq_daily_one['avg_twenty']
    k_line_info['avg_thirty_last'] = stock_qfq_daily_one['avg_thirty']
    k_line_info['avg_sixty_last'] = stock_qfq_daily_one['avg_sixty']

    k_line_info['std_amount_ten'] = stock_qfq_daily_one['std_amount_ten']
    k_line_info['mean_amount_ten'] = stock_qfq_daily_one['mean_amount_ten']
    k_line_info['std_amount_thirty'] = stock_qfq_daily_one['std_amount_thirty']
    k_line_info['mean_amount_thirty'] = stock_qfq_daily_one['mean_amount_thirty']
    k_line_info['std_amount_sixty'] = stock_qfq_daily_one['std_amount_sixty']
    k_line_info['mean_amount_sixty'] = stock_qfq_daily_one['mean_amount_sixty']
    k_line_info['k_line_pattern'] = stock_qfq_daily_one['k_line_pattern']
    k_line_info['history_data'] = stock_qfq_daily_one['history_data']

    return k_line_info


# 设置五日k线和
def set_sum_five_chg(k_line_info, deal_days):
    k_line_info.loc[:, 'deal_days'] = deal_days
    # 排除上市第一天的k线
    k_line_info.loc[k_line_info['deal_days'] >= MIN_DEAL_DAYS, 'sum_five_chg'] = k_line_info['daily01'] \
                                                                                 + k_line_info['daily02'] \
                                                                                 + k_line_info['daily03'] \
                                                                                 + k_line_info['daily04'] \
                                                                                 + k_line_info['daily05']
    k_line_info.loc[k_line_info['deal_days'] < MIN_DEAL_DAYS, 'sum_five_chg'] = 0

    return k_line_info


# 计算当前交易日开盘时的涨幅
def calculate_open_chg(stock_qfq_daily, k_line_info):
    # 新股
    if stock_qfq_daily.shape[0] == 1:
        k_line_info['open_chg_last'] = k_line_info['daily01']
    else:
        # 获取前一个交易日的收盘价格
        k_line_info['before_close'] = round(
            k_line_info['close_last'] / (1 + k_line_info['daily01'] * 0.01), 2)
        k_line_info['open_chg_last'] = round((k_line_info['open_last'] / k_line_info['before_close'] - 1) * 100, 2)
    return k_line_info


# 计算涨幅差值
# 昨日最高点到开盘涨幅差值
# 昨日最高点到当日收盘涨幅之间的差值
# 昨日收盘到当日开盘涨幅之间的差值
def calculate_chg_diff_value(result):
    # 昨日最高点到开盘涨幅差值
    result['diff_max_chg_from_open_last'] = round(
        result['max_chg_last'] - result['open_chg_last'], 2)

    # 昨日最高点到当日收盘涨幅之间的差值
    result['diff_max_chg_from_close_last'] = round(
        result['max_chg_last'] - result['chg_last'], 2)

    # 昨日最高点到当日收盘涨幅之间的差值
    result['diff_close_from_open_last'] = round(
        result['chg_last'] - result['open_chg_last'], 2)

    return result

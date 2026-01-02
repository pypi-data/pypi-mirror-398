import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

# 每月最大交易天数
MAX_TRADE_DAYS_PER_MONTH = 23
# 每周最大交易天数
MAX_TRADE_DAYS_PER_WEEK = 5


def handle_month_line(k_line_info, stock_qfq_daily, deal_days):
    # 上市2-23天
    if 1 < deal_days <= MAX_TRADE_DAYS_PER_MONTH:
        month_01 = round(sum(stock_qfq_daily['chg']), 2)
        k_line_info['sum_month'] = month_01
        k_line_info['month_num'] = 1
        k_line_info['month01'] = month_01
        k_line_info['month01_date'] = list(stock_qfq_daily.iloc[0:1]['date'])[0]
        # 上市23-23*2天
    elif (deal_days > MAX_TRADE_DAYS_PER_MONTH) \
            and (deal_days <= MAX_TRADE_DAYS_PER_MONTH * 2):
        stock_qfq_daily_month_01 = stock_qfq_daily.iloc[0:MAX_TRADE_DAYS_PER_MONTH]
        month_01 = round(sum(stock_qfq_daily_month_01['chg']), 2)
        k_line_length = stock_qfq_daily.shape[0]
        stock_qfq_daily_month_02 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_MONTH: k_line_length]
        month_02 = round(sum(stock_qfq_daily_month_02['chg']), 2)
        k_line_info['sum_month'] = round(month_01 + month_02, 2)
        k_line_info['month_num'] = 2
        k_line_info['month01'] = month_01
        k_line_info['month02'] = month_02
        k_line_info['month01_date'] = list(stock_qfq_daily_month_01.iloc[0:1]['date'])[0]
        if k_line_length != MAX_TRADE_DAYS_PER_MONTH:
            k_line_info['month02_date'] = list(stock_qfq_daily_month_02.iloc[0:1]['date'])[0]
        else:
            k_line_info['month02_date'] = '19890729'
    elif deal_days > MAX_TRADE_DAYS_PER_MONTH * 2:
        stock_qfq_daily_month_01 = stock_qfq_daily.iloc[0:MAX_TRADE_DAYS_PER_MONTH]
        month_01 = round(sum(stock_qfq_daily_month_01['chg']), 2)
        stock_qfq_daily_month_02 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_MONTH:MAX_TRADE_DAYS_PER_MONTH * 2]
        month_02 = round(sum(stock_qfq_daily_month_02['chg']), 2)
        k_line_info['month01_date'] = list(stock_qfq_daily_month_01.iloc[0:1]['date'])[0]
        k_line_info['month02_date'] = list(stock_qfq_daily_month_02.iloc[0:1]['date'])[0]
        k_line_info['sum_month'] = round(month_01 + month_02, 2)
        k_line_info['month_num'] = 2
        k_line_info['month01'] = month_01
        k_line_info['month02'] = month_02

    return k_line_info


def handle_week_line(k_line_info, stock_qfq_daily, deal_days):
    if 1 < deal_days <= MAX_TRADE_DAYS_PER_WEEK:
        week_01 = round(sum(stock_qfq_daily['chg']), 2)
        k_line_info['sum_week'] = week_01
        k_line_info['week_num'] = 1
        k_line_info['week01'] = week_01
        k_line_info['week_last_day'] = list(stock_qfq_daily.iloc[0:1]['date'])[0]
    elif MAX_TRADE_DAYS_PER_WEEK < deal_days <= MAX_TRADE_DAYS_PER_WEEK * 2:
        stock_qfq_daily_week_01 = stock_qfq_daily.iloc[0:MAX_TRADE_DAYS_PER_WEEK]
        stock_qfq_daily_week_02 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK:MAX_TRADE_DAYS_PER_WEEK * 2]
        week_01 = round(sum(stock_qfq_daily_week_01['chg']), 2)
        week_02 = round(sum(stock_qfq_daily_week_02['chg']), 2)
        k_line_info['sum_week'] = week_01 + week_02
        k_line_info['week_num'] = 2
        k_line_info['week01'] = week_01
        k_line_info['week02'] = week_02
        k_line_info['week_last_day'] = list(stock_qfq_daily_week_01.iloc[0:1]['date'])[0]
    elif MAX_TRADE_DAYS_PER_WEEK < deal_days <= MAX_TRADE_DAYS_PER_WEEK * 3:
        stock_qfq_daily_week_01 = stock_qfq_daily.iloc[0:MAX_TRADE_DAYS_PER_WEEK]
        stock_qfq_daily_week_02 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK: MAX_TRADE_DAYS_PER_WEEK * 2]
        stock_qfq_daily_week_03 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK * 2: MAX_TRADE_DAYS_PER_WEEK * 3]
        week_01 = round(sum(stock_qfq_daily_week_01['chg']), 2)
        week_02 = round(sum(stock_qfq_daily_week_02['chg']), 2)
        week_03 = round(sum(stock_qfq_daily_week_03['chg']), 2)
        k_line_info['sum_week'] = week_01 + week_02 + week_03
        k_line_info['week_num'] = 3
        k_line_info['week01'] = week_01
        k_line_info['week02'] = week_02
        k_line_info['week03'] = week_03
        k_line_info['week_last_day'] = list(stock_qfq_daily_week_01.iloc[0:1]['date'])[0]

    elif MAX_TRADE_DAYS_PER_WEEK * 3 < deal_days:
        stock_qfq_daily_week_01 = stock_qfq_daily.iloc[0:MAX_TRADE_DAYS_PER_WEEK]
        stock_qfq_daily_week_02 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK:MAX_TRADE_DAYS_PER_WEEK * 2]
        stock_qfq_daily_week_03 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK * 2: MAX_TRADE_DAYS_PER_WEEK * 3]
        stock_qfq_daily_week_04 = stock_qfq_daily.iloc[MAX_TRADE_DAYS_PER_WEEK * 3: MAX_TRADE_DAYS_PER_WEEK * 4]
        week_01 = round(sum(stock_qfq_daily_week_01['chg']), 2)
        week_02 = round(sum(stock_qfq_daily_week_02['chg']), 2)
        week_03 = round(sum(stock_qfq_daily_week_03['chg']), 2)
        week_04 = round(sum(stock_qfq_daily_week_04['chg']), 2)
        k_line_info['sum_week'] = week_01 + week_02 + week_03 + week_04
        k_line_info['week_num'] = 4
        k_line_info['week01'] = week_01
        k_line_info['week02'] = week_02
        k_line_info['week03'] = week_03
        k_line_info['week04'] = week_04
        k_line_info['week_last_day'] = stock_qfq_daily_week_01.iloc[0:1]['date']
    return k_line_info

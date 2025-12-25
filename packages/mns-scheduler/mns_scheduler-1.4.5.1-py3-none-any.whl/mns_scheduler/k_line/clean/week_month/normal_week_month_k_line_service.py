import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.component.classify.symbol_classify_param import stock_type_classify_param
import mns_common.utils.data_frame_util as data_frame_util

# import functools

mongodb_util = MongodbUtil('27017')


# 处理月线 周线 todo 暂时简单计算周线之和
def handle_month_week_line(k_line_info, str_day, symbol, deal_days,
                           stock_qfq_year_df):
    sub_stock_new_max_deal_days = stock_type_classify_param['sub_new_stock_max_deal_days']
    if deal_days > sub_stock_new_max_deal_days:
        k_line_info = handle_month_line(k_line_info, str_day, symbol)
        k_line_info = handle_week_line(k_line_info, str_day, symbol)
        k_line_info = set_year_k_line(k_line_info, symbol, stock_qfq_year_df, str_day)
    else:
        k_line_info['week01'] = 0
        k_line_info['week02'] = 0
        k_line_info['week03'] = 0
        k_line_info['week04'] = 0
        k_line_info['sum_week'] = 0
        k_line_info['week_num'] = 0
        k_line_info['week_last_day'] = '19890729'

        k_line_info['sum_month'] = 0
        k_line_info['month_num'] = 0
        k_line_info['month01'] = 0
        k_line_info['month02'] = 0
        k_line_info['month01_date'] = '19890729'
        k_line_info['month02_date'] = '19890729'
        # 上市交易日不到100天的默认设置年线数据为0
        k_line_info['now_year_chg'] = 0
        k_line_info['now_year_open_from_high_chg'] = 0
        k_line_info['now_year_low_from_high_chg'] = 0

        k_line_info['last_year_chg'] = 0
        k_line_info['last_year_open_from_high_chg'] = 0
        k_line_info['last_year_low_from_high_chg'] = 0

    return k_line_info


# 年线数据设置
def set_year_k_line(k_line_info, symbol, stock_qfq_year_df, str_day):
    now_year = int(str_day[0:4])
    last_year = str(now_year - 1)
    stock_qfq_now_year_df = stock_qfq_year_df.loc[(stock_qfq_year_df['symbol'] == symbol)
                                                  & (stock_qfq_year_df['year'] == str(now_year))]
    if data_frame_util.is_empty(stock_qfq_now_year_df):
        k_line_info['now_year_chg'] = 0
        k_line_info['now_year_open_from_high_chg'] = 0
        k_line_info['now_year_low_from_high_chg'] = 0
    else:
        k_line_info['now_year_chg'] = list(stock_qfq_now_year_df['chg'])[0]
        k_line_info['now_year_open_from_high_chg'] = list(stock_qfq_now_year_df['open_to_high_pct'])[0]
        k_line_info['now_year_low_from_high_chg'] = list(stock_qfq_now_year_df['low_to_high_pct'])[0]

    stock_qfq_last_year_df = stock_qfq_year_df.loc[(stock_qfq_year_df['symbol'] == symbol)
                                                   & (stock_qfq_year_df['year'] == last_year)]

    if data_frame_util.is_empty(stock_qfq_last_year_df):
        k_line_info['last_year_chg'] = 0
        k_line_info['last_year_open_from_high_chg'] = 0
        k_line_info['last_year_low_from_high_chg'] = 0
    else:
        k_line_info['last_year_chg'] = list(stock_qfq_last_year_df['chg'])[0]
        k_line_info['last_year_open_from_high_chg'] = list(stock_qfq_last_year_df['open_to_high_pct'])[0]
        k_line_info['last_year_low_from_high_chg'] = list(stock_qfq_last_year_df['low_to_high_pct'])[0]

    return k_line_info

    # 处理月线


def handle_month_line(k_line_info, str_day, symbol):
    now_year = int(str_day[0:4])
    last_year = str(now_year - 1)

    now_month_begin_day = str_day[0:7] + '-01'

    last_year_begin_day = last_year + '-01-01'
    # now_year_begin_day = str(now_year) + '-01-01'

    query = {"symbol": symbol,
             'date': {"$gte": date_handle_util.no_slash_date(last_year_begin_day)}}
    stock_hfq_monthly_all = mongodb_util.find_query_data('stock_qfq_monthly', query)
    if data_frame_util.is_empty(stock_hfq_monthly_all):
        k_line_info['sum_month'] = 0

    else:
        stock_hfq_monthly_all = stock_hfq_monthly_all.sort_values(by=['date'], ascending=False)
        stock_hfq_monthly_all = stock_hfq_monthly_all.loc[
            stock_hfq_monthly_all['date'] <= date_handle_util.no_slash_date(now_month_begin_day)]

        # stock_hfq_monthly_last_year = stock_hfq_monthly_all.loc[
        #     stock_hfq_monthly_all['date'] < date_handle_util.no_slash_date(now_year_begin_day)]
        #
        # stock_hfq_monthly_now_year = stock_hfq_monthly_all.loc[
        #     stock_hfq_monthly_all['date'] > date_handle_util.no_slash_date(now_year_begin_day)]

        # 最近两个月k线
        before_two_month_stock_hfq_monthly = stock_hfq_monthly_all.iloc[0:2]
        month_num = before_two_month_stock_hfq_monthly.shape[0]
        k_line_info['month_num'] = month_num

        if month_num == 0:
            k_line_info['sum_month'] = 0
            k_line_info['month01'] = 0
            k_line_info['month02'] = 0
            k_line_info['month01_date'] = '19890729'
            k_line_info['month02_date'] = '19890729'
        elif month_num == 1:
            k_line_info['month01'] = before_two_month_stock_hfq_monthly.iloc[0].chg
            k_line_info['month02'] = 0
            k_line_info['month01_date'] = before_two_month_stock_hfq_monthly.iloc[0].date
            k_line_info['month02_date'] = '19890729'
            k_line_info['sum_month'] = before_two_month_stock_hfq_monthly.iloc[0].chg
        elif month_num == 2:
            k_line_info['month01'] = before_two_month_stock_hfq_monthly.iloc[0].chg
            k_line_info['month02'] = before_two_month_stock_hfq_monthly.iloc[1].chg
            k_line_info['month01_date'] = before_two_month_stock_hfq_monthly.iloc[0].date
            k_line_info['month02_date'] = before_two_month_stock_hfq_monthly.iloc[1].date
            close_price = before_two_month_stock_hfq_monthly.iloc[0].close
            open_price = before_two_month_stock_hfq_monthly.iloc[1].last_price
            sum_chg = round((close_price - open_price) * 100 / open_price, 2)
            k_line_info['sum_month'] = sum_chg
        #
        # last_year_month_number = stock_hfq_monthly_last_year.shape[0]
        # if last_year_month_number == 0:
        #     k_line_info['last_year_chg'] = 0
        # elif last_year_month_number == 1:
        #     k_line_info['last_year_chg'] = stock_hfq_monthly_last_year.iloc[0].chg
        # else:
        #     # chg_list = list(stock_hfq_monthly_last_year['chg'])
        #     # # 将列表中的每个元素加上1
        #     # updated_list = [round((x / 100) + 1, 2) for x in chg_list]
        #     #
        #     # # 使用 functools.reduce 将列表中的所有元素相乘
        #     # last_year_chg = functools.reduce(lambda x, y: x * y, updated_list)
        #     close_price = stock_hfq_monthly_last_year.iloc[0].close
        #     open_price = stock_hfq_monthly_last_year.iloc[last_year_month_number - 1].last_price
        #     last_year_chg = round((close_price - open_price) * 100 / open_price, 2)
        #     k_line_info['last_year_chg'] = last_year_chg
        #
        # now_year_month_number = stock_hfq_monthly_now_year.shape[0]
        # if now_year_month_number == 0:
        #     k_line_info['now_year_chg'] = 0
        # elif now_year_month_number == 1:
        #     k_line_info['now_year_chg'] = stock_hfq_monthly_now_year.iloc[0].chg
        # else:
        #     close_price = stock_hfq_monthly_now_year.iloc[0].close
        #     open_price = stock_hfq_monthly_now_year.iloc[now_year_month_number - 1].last_price
        #     last_year_chg = round((close_price - open_price) * 100 / open_price, 2)
        #     k_line_info['now_year_chg'] = last_year_chg

    return k_line_info


# 处理周线
def handle_week_line(k_line_info, str_day, symbol):
    month_begin_day = str_day[0:7] + '-01'
    query = {"symbol": symbol,
             '$and': [{'date': {"$gte": date_handle_util.no_slash_date(month_begin_day)}},
                      {'date': {"$lt": date_handle_util.no_slash_date(str_day)}}]}
    stock_hfq_weekly = mongodb_util.find_query_data('stock_qfq_weekly', query)
    week_num = stock_hfq_weekly.shape[0]
    if week_num > 0:
        stock_hfq_weekly = stock_hfq_weekly.sort_values(by=['date'], ascending=False)
        k_line_info['sum_week'] = round(sum(stock_hfq_weekly['chg']), 2)
    else:
        k_line_info['sum_week'] = 0
    k_line_info['week_num'] = week_num
    if week_num == 1:
        k_line_info['week01'] = stock_hfq_weekly.iloc[0].chg
        k_line_info['week02'] = 0
        k_line_info['week03'] = 0
        k_line_info['week04'] = 0
    elif week_num == 2:
        k_line_info['week01'] = stock_hfq_weekly.iloc[0].chg
        k_line_info['week02'] = stock_hfq_weekly.iloc[1].chg
        k_line_info['week03'] = 0
        k_line_info['week04'] = 0
    elif week_num == 3:
        k_line_info['week01'] = stock_hfq_weekly.iloc[0].chg
        k_line_info['week02'] = stock_hfq_weekly.iloc[1].chg
        k_line_info['week03'] = stock_hfq_weekly.iloc[2].chg
        k_line_info['week04'] = 0
    elif week_num >= 4:
        k_line_info['week01'] = stock_hfq_weekly.iloc[0].chg
        k_line_info['week02'] = stock_hfq_weekly.iloc[1].chg
        k_line_info['week03'] = stock_hfq_weekly.iloc[2].chg
        k_line_info['week04'] = stock_hfq_weekly.iloc[3].chg
    elif week_num == 0:
        k_line_info['week01'] = 0
        k_line_info['week02'] = 0
        k_line_info['week03'] = 0
        k_line_info['week04'] = 0
        k_line_info['week_last_day'] = month_begin_day
        k_line_info['sum_week'] = 0
        return k_line_info
    stock_hfq_weekly = stock_hfq_weekly.sort_values(by=['date'], ascending=False)
    stock_hfq_weekly_last = stock_hfq_weekly.iloc[0:1]
    k_line_info['week_last_day'] = list(stock_hfq_weekly_last['date'])[0]

    return k_line_info

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.common_service_fun_api as common_service_fun_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
import mns_common.api.kpl.constant.kpl_constant as kpl_constant
import mns_common.constant.db_name_constant as db_name_constant
from functools import lru_cache
from loguru import logger

mongodb_util = MongodbUtil('27017')


def set_kpl_plate_info(company_one_df, company_one, kpl_real_time_quotes):
    try:
        if data_frame_util.is_not_empty(kpl_real_time_quotes):
            kpl_real_time_quotes_one = kpl_real_time_quotes.loc[
                kpl_real_time_quotes['symbol'] == company_one.symbol]

            if data_frame_util.is_not_empty(kpl_real_time_quotes_one):
                company_one_df['kpl_plate_name'] = list(kpl_real_time_quotes_one['plate_name_list'])[0]
                company_one_df['kpl_most_relative_name'] = \
                    list(kpl_real_time_quotes_one['most_relative_name'])[
                        0]
            company_one_df = set_kpl_data(kpl_real_time_quotes_one, company_one_df, company_one)

        if bool(1 - ("kpl_plate_name" in company_one_df.columns)) or bool(
                1 - ("kpl_most_relative_name" in company_one_df.columns)):
            company_one_df['kpl_plate_name'] = ""
            company_one_df['kpl_most_relative_name'] = ""
    except BaseException as e:
        logger.warning("设置开盘啦数据异常:{},{}", company_one.symbol, e)
    return company_one_df

def set_kpl_data(kpl_real_time_quotes_one, company_one_df, company_one):
    if data_frame_util.is_not_empty(kpl_real_time_quotes_one):
        company_one_df['kpl_plate_name'] = list(kpl_real_time_quotes_one['plate_name_list'])[0]
        company_one_df['kpl_most_relative_name'] = list(kpl_real_time_quotes_one['most_relative_name'])[
            0]
        symbol = company_one.symbol

        query = {'symbol': symbol, "index_class": kpl_constant.FIRST_INDEX}
        kpl_best_choose_index_detail = mongodb_util.find_query_data('kpl_best_choose_index_detail', query)
        if data_frame_util.is_not_empty(kpl_best_choose_index_detail):
            kpl_best_choose_index_detail = kpl_best_choose_index_detail[[
                "plate_code",
                "plate_name",
                "first_plate_code",
                "first_plate_name",
                "index_class"
            ]]

            # 去除空格
            kpl_best_choose_index_detail['plate_name'] = kpl_best_choose_index_detail['plate_name'].str.replace(' ', '')
            # 去除空格
            kpl_best_choose_index_detail['first_plate_name'] = kpl_best_choose_index_detail[
                'first_plate_name'].str.replace(' ', '')

            company_one_df.loc[:, 'kpl_plate_list_info'] = kpl_best_choose_index_detail.to_string(index=False)
    return company_one_df


# 获取可转债信息
@lru_cache(maxsize=None)
def get_kzz_debt_info():
    query = {}
    kzz_debt_info_df = mongodb_util.find_query_data(db_name_constant.KZZ_DEBT_INFO, query)
    kzz_debt_info_df = kzz_debt_info_df[[
        'symbol',
        'name',
        'stock_code',
        'apply_date',
        'list_date',
        'due_date'
    ]]
    return kzz_debt_info_df


def set_kzz_debt(company_one_df, symbol):
    kzz_debt_info_df_all = get_kzz_debt_info()
    kzz_debt_info_df = kzz_debt_info_df_all.loc[kzz_debt_info_df_all['stock_code'] == symbol]

    if data_frame_util.is_not_empty(kzz_debt_info_df):
        kzz_debt_info_df_list = kzz_debt_info_df.to_dict(orient='records')
        company_one_df['kzz_debt_list'] = [kzz_debt_info_df_list]
    return company_one_df


# 获取最近年报收入
def set_recent_year_income(symbol, company_one_df):
    query = {'symbol': symbol, "REPORT_TYPE": "年报"}
    em_stock_profit = mongodb_util.descend_query(query, db_name_constant.EM_STOCK_PROFIT, 'REPORT_DATE', 1)
    if data_frame_util.is_not_empty(em_stock_profit):
        company_one_df['operate_profit'] = list(em_stock_profit['OPERATE_PROFIT'])[0]
        company_one_df['operate_date_name'] = list(em_stock_profit['REPORT_DATE_NAME'])[0]
        total_operate_income = list(em_stock_profit['TOTAL_OPERATE_INCOME'])[0]
        # 金融机构大多收入计入在这个字段中
        if total_operate_income == 0:
            total_operate_income = list(em_stock_profit['OPERATE_INCOME'])[0]

        company_one_df['total_operate_income'] = total_operate_income
    else:
        company_one_df['operate_profit'] = 0
        company_one_df['total_operate_income'] = 0
        company_one_df['operate_date_name'] = '暂无年报'
    company_one_df['operate_profit'] = round(
        company_one_df['operate_profit'] / common_service_fun_api.HUNDRED_MILLION, 2)
    company_one_df['total_operate_income'] = round(
        company_one_df['total_operate_income'] / common_service_fun_api.HUNDRED_MILLION, 2)
    return company_one_df


# 计算真实流通比例
def set_calculate_circulation_ratio(symbol, now_str_day, company_one_df):
    query = {"symbol": symbol}
    stock_gdfx_free_top_1 = mongodb_util.descend_query(query, 'stock_gdfx_free_top_10', "period", 1)
    if stock_gdfx_free_top_1.shape[0] == 0:
        mv_circulation_ratio = 1
        qfii_number = 0
        qfii_type = 'A股'
        share_holder_sync_day = now_str_day
    else:
        period_time = list(stock_gdfx_free_top_1['period'])[0]

        query_free = {'symbol': symbol, 'period': period_time}
        stock_gdfx_free_top_10 = mongodb_util.find_query_data('stock_gdfx_free_top_10', query_free)

        stock_gdfx_free_top_10['shares_number_str'] = stock_gdfx_free_top_10['shares_number'].astype(str)

        stock_gdfx_free_top_10['id_key'] = stock_gdfx_free_top_10['symbol'] + '_' + stock_gdfx_free_top_10[
            'period'] + '_' + stock_gdfx_free_top_10.shares_number_str

        stock_gdfx_free_top_10.drop_duplicates('id_key', keep='last', inplace=True)

        # 排除香港结算公司 大于5%减持不用发公告  香港中央结算    HKSCC
        stock_gdfx_free_top_10['is_hk'] = stock_gdfx_free_top_10['shareholder_name'].apply(
            lambda shareholder_name: "HK" if shareholder_name.startswith('香港中央结算') or shareholder_name.startswith(
                'HKSCC') else "A")

        # 持股大于5% 减持需要发公告
        # 排除香港结算公司不发公共 小于5%减持不用发公告
        # 香港中央结算    HKSCC
        stock_free_top_greater_than_5 = stock_gdfx_free_top_10.loc[
            (stock_gdfx_free_top_10['circulation_ratio'] >= 5) & (stock_gdfx_free_top_10['is_hk'] == 'A')]

        stock_free_qfii = stock_gdfx_free_top_10.loc[stock_gdfx_free_top_10['shareholder_nature'] == 'QFII']

        share_holder_sync_day = list(stock_gdfx_free_top_10['create_day'])[0]

        # qfii 数量
        qfii_number = stock_free_qfii.shape[0]
        # qfii 类型
        qfii_type = set_qfii_type(qfii_number, stock_free_qfii.copy())

        circulation_ratio = sum(stock_free_top_greater_than_5['circulation_ratio'])
        mv_circulation_ratio = round((100 - circulation_ratio) / 100, 2)
        # 防止错误数据
        if mv_circulation_ratio < 0:
            mv_circulation_ratio = 1

    company_one_df['mv_circulation_ratio'] = mv_circulation_ratio
    company_one_df['qfii_type'] = qfii_type
    company_one_df['qfii_number'] = qfii_number
    company_one_df['share_holder_sync_day'] = share_holder_sync_day

    return company_one_df


# 设置QFII持股
def set_qfii_type(qfii_number, stock_free_qfii):
    if qfii_number > 0:
        stock_free_qfii['new_change'] = stock_free_qfii['change']
        stock_free_qfii.loc[stock_free_qfii['change_ratio'] == 0, 'new_change'] = 0
        stock_free_qfii.loc[stock_free_qfii['change'] == '新进', 'new_change'] = \
            stock_free_qfii['shares_number']
        stock_free_qfii['new_change'] = stock_free_qfii['new_change'].astype(float)

        stock_free_qfii_new_in = stock_free_qfii.loc[stock_free_qfii['change'] == '新进']
        if data_frame_util.is_not_empty(stock_free_qfii_new_in):
            qfii_type = 1
            return qfii_type

        stock_free_qfii_add = stock_free_qfii.loc[
            (~stock_free_qfii['change'].isin(['不变', '新进'])) & (stock_free_qfii['new_change'] > 0)]

        if data_frame_util.is_not_empty(stock_free_qfii_add):
            qfii_type = 2
            return qfii_type

        stock_free_qfii_not_change = stock_free_qfii.loc[stock_free_qfii['change'] == '不变']

        if data_frame_util.is_not_empty(stock_free_qfii_not_change):
            qfii_type = 3
            return qfii_type

        stock_free_qfii_reduce = stock_free_qfii.loc[
            (~stock_free_qfii['change'].isin(['不变', '新进'])) & (stock_free_qfii['new_change'] < 0)]

        if data_frame_util.is_not_empty(stock_free_qfii_reduce):
            qfii_type = 4
            return qfii_type
    else:
        return 0

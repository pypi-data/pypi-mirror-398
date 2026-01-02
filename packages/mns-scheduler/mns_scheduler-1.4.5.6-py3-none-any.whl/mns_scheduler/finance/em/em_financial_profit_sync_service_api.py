import sys
import os

import pandas as pd

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import akshare as ak
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')
import mns_common.constant.db_name_constant as db_name_constant
import mns_scheduler.finance.em.finance_common_api as finance_common_api
from loguru import logger


# 利润表
#  "_id" : ObjectId("6644085f608b7737dee21a3a"),
#     "SECUCODE" : "600519.SH",
#     "SECURITY_CODE" : "600519",
#     "SECURITY_NAME_ABBR" : "贵州茅台",
#     "ORG_CODE" : "10002602",
#     "ORG_TYPE" : "通用",
#     "REPORT_DATE" : "2023-12-31 00:00:00",
#     "REPORT_TYPE" : "年报",
#     "REPORT_DATE_NAME" : "2023年报",
#     "SECURITY_TYPE_CODE" : "058001001",
#     "NOTICE_DATE" : "2024-04-03 00:00:00",
#     "UPDATE_DATE" : "2024-04-03 00:00:00",
#     "CURRENCY" : "CNY",
#     "TOTAL_OPERATE_INCOME" : 150560330316.45,  营业总收入
#     "TOTAL_OPERATE_INCOME_YOY" : 18.0365792459, 总运营收入修正
#     "OPERATE_INCOME" : 147693604994.14,  营业收入
#     "OPERATE_INCOME_YOY" : 19.0119185529, 营业收入修正
#     "INTEREST_INCOME" : 2866725322.31, 利息收入
#     "INTEREST_INCOME_YOY" : 利息收入修正
#     "EARNED_PREMIUM" : NaN,
#     "EARNED_PREMIUM_YOY" : NaN,
#     "FEE_COMMISSION_INCOME" : NaN,
#     "FEE_COMMISSION_INCOME_YOY" : NaN,
#     "OTHER_BUSINESS_INCOME" : NaN,
#     "OTHER_BUSINESS_INCOME_YOY" : NaN,
#     "TOI_OTHER" : NaN,
#     "TOI_OTHER_YOY" : NaN,
#     "TOTAL_OPERATE_COST" : 46960889468.54, 营业总成本
#     "TOTAL_OPERATE_COST_YOY" : 18.1456266222,
#     "OPERATE_COST" : 11867273851.78, 营业成本
#     "OPERATE_COST_YOY" : 17.5737925437,
#     "INTEREST_EXPENSE" : 113500129.93, 利息支出
#     "INTEREST_EXPENSE_YOY" : 7.4972611642,
#     "FEE_COMMISSION_EXPENSE" : 68578.57,  手续费及佣金支出
#     "FEE_COMMISSION_EXPENSE_YOY" : -52.0903684752,
#     "RESEARCH_EXPENSE" : 157371873.01, 研发费用
#     "RESEARCH_EXPENSE_YOY" : 16.4116440028,
#     "SURRENDER_VALUE" : NaN,
#     "SURRENDER_VALUE_YOY" : NaN,
#     "NET_COMPENSATE_EXPENSE" : NaN,
#     "NET_COMPENSATE_EXPENSE_YOY" : NaN,
#     "NET_CONTRACT_RESERVE" : NaN,
#     "NET_CONTRACT_RESERVE_YOY" : NaN,
#     "POLICY_BONUS_EXPENSE" : NaN,
#     "POLICY_BONUS_EXPENSE_YOY" : NaN,
#     "REINSURE_EXPENSE" : NaN,
#     "REINSURE_EXPENSE_YOY" : NaN,
#     "OTHER_BUSINESS_COST" : NaN,
#     "OTHER_BUSINESS_COST_YOY" : NaN,
#     "OPERATE_TAX_ADD" : 22234175898.6, 税金及附加
#     "OPERATE_TAX_ADD_YOY" : 20.2119055043,
#     "SALE_EXPENSE" : 4648613585.82, 销售费用
#     "SALE_EXPENSE_YOY" : 40.9642928475,
#     "MANAGE_EXPENSE" : 9729389252.31, 管理费用
#     "MANAGE_EXPENSE_YOY" : 7.9580889133,
#     "ME_RESEARCH_EXPENSE" : NaN,
#     "ME_RESEARCH_EXPENSE_YOY" : NaN,
#     "FINANCE_EXPENSE" : -1789503701.48, 财务费用
#     "FINANCE_EXPENSE_YOY" : -28.5742355094,
#     "FE_INTEREST_EXPENSE" : 12624628.35, 利息费用
#     "FE_INTEREST_EXPENSE_YOY" : 5.0021902771,
#     "FE_INTEREST_INCOME" : 1942301920.98, 利息收入
#     "FE_INTEREST_INCOME_YOY" : 31.6437955552,
#     "ASSET_IMPAIRMENT_LOSS" : NaN,
#     "ASSET_IMPAIRMENT_LOSS_YOY" : NaN,
#     "CREDIT_IMPAIRMENT_LOSS" : NaN,
#     "CREDIT_IMPAIRMENT_LOSS_YOY" : NaN,
#     "TOC_OTHER" : NaN,
#     "TOC_OTHER_YOY" : NaN,
#     "FAIRVALUE_CHANGE_INCOME" : 3151962.5, :公允价值变动收益
#     "FAIRVALUE_CHANGE_INCOME_YOY" : NaN,
#     "INVEST_INCOME" : 34025967.82, 投资收益
#     "INVEST_INCOME_YOY" : -46.7011782268,
#     "INVEST_JOINT_INCOME" : NaN,
#     "INVEST_JOINT_INCOME_YOY" : NaN,
#     "NET_EXPOSURE_INCOME" : NaN,
#     "NET_EXPOSURE_INCOME_YOY" : NaN,
#     "EXCHANGE_INCOME" : NaN,
#     "EXCHANGE_INCOME_YOY" : NaN,
#     "ASSET_DISPOSAL_INCOME" : -479736.97, 资产处置收益
#     "ASSET_DISPOSAL_INCOME_YOY" : -324.9796785895,
#     "ASSET_IMPAIRMENT_INCOME" : NaN,
#     "ASSET_IMPAIRMENT_INCOME_YOY" : NaN,
#     "CREDIT_IMPAIRMENT_INCOME" : 37871293.26, 信用减值损失(新)
#     "CREDIT_IMPAIRMENT_INCOME_YOY" : 357.8638477375,
#     "OTHER_INCOME" : 34644873.86, 其他收益
#     "OTHER_INCOME_YOY" : 41.3767542405,
#     "OPERATE_PROFIT_OTHER" : NaN,
#     "OPERATE_PROFIT_OTHER_YOY" : NaN,
#     "OPERATE_PROFIT_BALANCE" : 0.0,
#     "OPERATE_PROFIT_BALANCE_YOY" : NaN,
#     "OPERATE_PROFIT" : 103708655208.38, 营业利润
#     "OPERATE_PROFIT_YOY" : 18.0123117479,
#     "NONBUSINESS_INCOME" : 86779655.95, 加:营业外收入
#     "NONBUSINESS_INCOME_YOY" : 22.4796849672,
#     "NONCURRENT_DISPOSAL_INCOME" : NaN,
#     "NONCURRENT_DISPOSAL_INCOME_YOY" : NaN,
#     "NONBUSINESS_EXPENSE" : 132881174.52, 减:营业外支出
#     "NONBUSINESS_EXPENSE_YOY" : -46.6092621953,
#     "NONCURRENT_DISPOSAL_LOSS" : NaN,
#     "NONCURRENT_DISPOSAL_LOSS_YOY" : NaN,
#     "EFFECT_TP_OTHER" : NaN,
#     "EFFECT_TP_OTHER_YOY" : NaN,
#     "TOTAL_PROFIT_BALANCE" : 0.0,
#     "TOTAL_PROFIT_BALANCE_YOY" : NaN,
#     "TOTAL_PROFIT" : 103662553689.81, 利润总额
#     "TOTAL_PROFIT_YOY" : 18.1993076599,
#     "INCOME_TAX" : 26141077412.01, 减:所得税
#     "INCOME_TAX_YOY" : 17.0909328034,
#     "EFFECT_NETPROFIT_OTHER" : NaN,
#     "EFFECT_NETPROFIT_OTHER_YOY" : NaN,
#     "EFFECT_NETPROFIT_BALANCE" : NaN,
#     "EFFECT_NETPROFIT_BALANCE_YOY" : NaN,
#     "UNCONFIRM_INVEST_LOSS" : NaN,
#     "UNCONFIRM_INVEST_LOSS_YOY" : NaN,
#     "NETPROFIT" : 77521476277.8, 净利润
#     "NETPROFIT_YOY" : 18.5778097415,
#     "PRECOMBINE_PROFIT" : NaN,
#     "PRECOMBINE_PROFIT_YOY" : NaN,
#     "CONTINUED_NETPROFIT" : 77521476277.8, 持续经营净利润
#     "CONTINUED_NETPROFIT_YOY" : 18.5778097415,
#     "DISCONTINUED_NETPROFIT" : NaN,
#     "DISCONTINUED_NETPROFIT_YOY" : NaN,
#     "PARENT_NETPROFIT" : 74734071550.75, 归属于母公司股东的净利润
#     "PARENT_NETPROFIT_YOY" : 19.1598992892,
#     "MINORITY_INTEREST" : 2787404727.05,  少数股东损益
#     "MINORITY_INTEREST_YOY" : 4.8459336455,
#     "DEDUCT_PARENT_NETPROFIT" : 74752564425.52, 扣除非经常性损益后的净利润
#     "DEDUCT_PARENT_NETPROFIT_YOY" : 19.0462109566,
#     "NETPROFIT_OTHER" : NaN,
#     "NETPROFIT_OTHER_YOY" : NaN,
#     "NETPROFIT_BALANCE" : NaN,
#     "NETPROFIT_BALANCE_YOY" : NaN,
#     "BASIC_EPS" : 59.49,  基本每股收益
#     "BASIC_EPS_YOY" : 19.1468055277,
#     "DILUTED_EPS" : 59.49,  稀释每股收益
#     "DILUTED_EPS_YOY" : 19.1468055277,
#     "OTHER_COMPRE_INCOME" : 4715179.82, 其他综合收益
#     "OTHER_COMPRE_INCOME_YOY" : 110.40766101,
#     "PARENT_OCI" : 4715179.82, 归属于母公司股东的其他综合收益
#     "PARENT_OCI_YOY" : 110.40766101,
#     "MINORITY_OCI" : NaN,
#     "MINORITY_OCI_YOY" : NaN,
#     "PARENT_OCI_OTHER" : NaN,
#     "PARENT_OCI_OTHER_YOY" : NaN,
#     "PARENT_OCI_BALANCE" : NaN,
#     "PARENT_OCI_BALANCE_YOY" : NaN,
#     "UNABLE_OCI" : NaN,
#     "UNABLE_OCI_YOY" : NaN,
#     "CREDITRISK_FAIRVALUE_CHANGE" : NaN,
#     "CREDITRISK_FAIRVALUE_CHANGE_YOY" : NaN,
#     "OTHERRIGHT_FAIRVALUE_CHANGE" : NaN,
#     "OTHERRIGHT_FAIRVALUE_CHANGE_YOY" : NaN,
#     "SETUP_PROFIT_CHANGE" : NaN,
#     "SETUP_PROFIT_CHANGE_YOY" : NaN,
#     "RIGHTLAW_UNABLE_OCI" : NaN,
#     "RIGHTLAW_UNABLE_OCI_YOY" : NaN,
#     "UNABLE_OCI_OTHER" : NaN,
#     "UNABLE_OCI_OTHER_YOY" : NaN,
#     "UNABLE_OCI_BALANCE" : NaN,
#     "UNABLE_OCI_BALANCE_YOY" : NaN,
#     "ABLE_OCI" : 4715179.82,
#     "ABLE_OCI_YOY" : 110.40766101,
#     "RIGHTLAW_ABLE_OCI" : NaN,
#     "RIGHTLAW_ABLE_OCI_YOY" : NaN,
#     "AFA_FAIRVALUE_CHANGE" : NaN,
#     "AFA_FAIRVALUE_CHANGE_YOY" : NaN,
#     "HMI_AFA" : NaN,
#     "HMI_AFA_YOY" : NaN,
#     "CASHFLOW_HEDGE_VALID" : NaN,
#     "CASHFLOW_HEDGE_VALID_YOY" : NaN,
#     "CREDITOR_FAIRVALUE_CHANGE" : NaN,
#     "CREDITOR_FAIRVALUE_CHANGE_YOY" : NaN,
#     "CREDITOR_IMPAIRMENT_RESERVE" : NaN,
#     "CREDITOR_IMPAIRMENT_RESERVE_YOY" : NaN,
#     "FINANCE_OCI_AMT" : NaN,
#     "FINANCE_OCI_AMT_YOY" : NaN,
#     "CONVERT_DIFF" : 4715179.82,
#     "CONVERT_DIFF_YOY" : 110.40766101,
#     "ABLE_OCI_OTHER" : NaN,
#     "ABLE_OCI_OTHER_YOY" : NaN,
#     "ABLE_OCI_BALANCE" : NaN,
#     "ABLE_OCI_BALANCE_YOY" : NaN,
#     "OCI_OTHER" : NaN,
#     "OCI_OTHER_YOY" : NaN,
#     "OCI_BALANCE" : NaN,
#     "OCI_BALANCE_YOY" : NaN,
#     "TOTAL_COMPRE_INCOME" : 77526191457.62, 综合收益总额
#     "TOTAL_COMPRE_INCOME_YOY" : 18.5809573963,
#     "PARENT_TCI" : 74738786730.57, 归属于母公司股东的综合收益总额
#     "PARENT_TCI_YOY" : 19.1631595692,
#     "MINORITY_TCI" : 2787404727.05,  归属于少数股东的综合收益总额
#     "MINORITY_TCI_YOY" : 4.8459336455,
#     "PRECOMBINE_TCI" : NaN,
#     "PRECOMBINE_TCI_YOY" : NaN,
#     "EFFECT_TCI_BALANCE" : NaN,
#     "EFFECT_TCI_BALANCE_YOY" : NaN,
#     "TCI_OTHER" : NaN,
#     "TCI_OTHER_YOY" : NaN,
#     "TCI_BALANCE" : NaN,
#     "TCI_BALANCE_YOY" : NaN,
#     "ACF_END_INCOME" : NaN,
#     "ACF_END_INCOME_YOY" : NaN,
#     "OPINION_TYPE" : "标准无保留意见" 审计意见(境内)
# https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#lrb-0
def get_em_profit_api(symbol):
    sec_code = finance_common_api.get_sec_code(symbol)
    try:
        stock_profit_sheet_by_report_em = ak.stock_profit_sheet_by_report_em(sec_code)
    except Exception as e:
        logger.error("同步利润表异常:{},{}", symbol, e)
    if data_frame_util.is_empty(stock_profit_sheet_by_report_em.copy()):
        return None
    stock_profit_sheet_by_report_em = check_columns(stock_profit_sheet_by_report_em)
    stock_profit_sheet_by_report_em = stock_profit_sheet_by_report_em[[
        "SECUCODE",
        "SECURITY_CODE",
        "SECURITY_NAME_ABBR",
        "ORG_CODE",
        "ORG_TYPE",
        "REPORT_DATE",
        "REPORT_TYPE",
        "REPORT_DATE_NAME",
        "SECURITY_TYPE_CODE",
        "NOTICE_DATE",
        "UPDATE_DATE",
        "CURRENCY",
        "TOTAL_OPERATE_INCOME",
        "OPERATE_INCOME",
        "INTEREST_INCOME",
        "TOTAL_OPERATE_COST",
        "OPERATE_COST",
        "INTEREST_EXPENSE",
        "FEE_COMMISSION_EXPENSE",
        "RESEARCH_EXPENSE",
        "OPERATE_TAX_ADD",
        "SALE_EXPENSE",
        "MANAGE_EXPENSE",
        "FINANCE_EXPENSE",
        "FE_INTEREST_EXPENSE",
        "FE_INTEREST_INCOME",
        "FAIRVALUE_CHANGE_INCOME",
        "INVEST_INCOME",
        "ASSET_DISPOSAL_INCOME",
        "CREDIT_IMPAIRMENT_INCOME",
        "OTHER_INCOME",
        "OPERATE_PROFIT",
        "NONBUSINESS_INCOME",
        "NONBUSINESS_EXPENSE",
        "TOTAL_PROFIT",
        "INCOME_TAX",
        "NETPROFIT",
        "CONTINUED_NETPROFIT",
        "PARENT_NETPROFIT",
        'MINORITY_INTEREST',
        'DEDUCT_PARENT_NETPROFIT',
        'BASIC_EPS',
        'DILUTED_EPS',
        'OTHER_COMPRE_INCOME',
        'PARENT_OCI',
        'TOTAL_COMPRE_INCOME',
        'PARENT_TCI',
        'MINORITY_TCI',
        'OPINION_TYPE'
    ]]
    stock_profit_sheet_by_report_em['_id'] = (stock_profit_sheet_by_report_em['SECURITY_CODE']
                                              + "_" + stock_profit_sheet_by_report_em['REPORT_DATE'])

    query = {'SECURITY_CODE': symbol}
    exist_profit_em_df = mongodb_util.find_query_data(db_name_constant.EM_STOCK_PROFIT, query)
    if data_frame_util.is_not_empty(exist_profit_em_df):
        new_profit_df = stock_profit_sheet_by_report_em.loc[
            ~(stock_profit_sheet_by_report_em['_id'].isin(list(exist_profit_em_df['_id'])))]
    else:
        new_profit_df = stock_profit_sheet_by_report_em
    if data_frame_util.is_empty(new_profit_df):
        return pd.DataFrame()
    new_profit_df = new_profit_df.fillna(0)
    return new_profit_df


def check_columns(profit_df):
    if 'TOTAL_OPERATE_INCOME' not in profit_df.columns:
        profit_df = profit_df.assign(TOTAL_OPERATE_INCOME=0)

    if 'FAIRVALUE_CHANGE_INCOME' not in profit_df.columns:
        profit_df = profit_df.assign(FAIRVALUE_CHANGE_INCOME=0)

    if 'INTEREST_INCOME' not in profit_df.columns:
        profit_df = profit_df.assign(INTEREST_INCOME=0)
    if 'TOTAL_OPERATE_COST' not in profit_df.columns:
        profit_df = profit_df.assign(TOTAL_OPERATE_COST=0)
    if 'OPERATE_COST' not in profit_df.columns:
        profit_df = profit_df.assign(OPERATE_COST=0)
    if 'INTEREST_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(INTEREST_EXPENSE=0)
    if 'FEE_COMMISSION_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(FEE_COMMISSION_EXPENSE=0)
    if 'RESEARCH_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(RESEARCH_EXPENSE=0)
    if 'SALE_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(SALE_EXPENSE=0)
    if 'MANAGE_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(MANAGE_EXPENSE=0)
    if 'FINANCE_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(FINANCE_EXPENSE=0)
    if 'FE_INTEREST_EXPENSE' not in profit_df.columns:
        profit_df = profit_df.assign(FE_INTEREST_EXPENSE=0)
    if 'FE_INTEREST_INCOME' not in profit_df.columns:
        profit_df = profit_df.assign(FE_INTEREST_INCOME=0)
    if 'CREDIT_IMPAIRMENT_INCOME' not in profit_df.columns:
        profit_df = profit_df.assign(CREDIT_IMPAIRMENT_INCOME=0)
    if 'ACCOUNTS_RECE' not in profit_df.columns:
        profit_df = profit_df.assign(ACCOUNTS_RECE=0)
    if 'LOAN_ADVANCE' not in profit_df.columns:
        profit_df = profit_df.assign(LOAN_ADVANCE=0)
    if 'MONETARYFUNDS' not in profit_df.columns:
        profit_df = profit_df.assign(MONETARYFUNDS=0)
    return profit_df


import mns_common.component.em.em_stock_info_api as em_stock_info_api

if __name__ == '__main__':
    get_em_profit_api('688302')
    em_df = em_stock_info_api.get_a_stock_info()
    for em_one in em_df.itertuples():
        try:
            get_em_profit_api(em_one.symbol)
        except Exception as e:
            logger.error("同步利润表异常:{},{}", em_one.symbol, e)

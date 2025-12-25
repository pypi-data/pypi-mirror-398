import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import akshare as ak
from mns_common.db.MongodbUtil import MongodbUtil
import mns_scheduler.finance.em.finance_common_api as finance_common_api
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')
from loguru import logger
import mns_common.utils.data_frame_util as data_frame_util


#
# {
#     "_id" : ObjectId("6644358f8eb1db9684c8b75d"),
#     "SECUCODE" : "600519.SH",
#     "SECURITY_CODE" : "600519",
#     "SECURITY_NAME_ABBR" : "贵州茅台",
#     "ORG_CODE" : "10002602",
#     "ORG_TYPE" : "通用",
#     "REPORT_DATE" : "2024-03-31 00:00:00",
#     "REPORT_TYPE" : "一季报",
#     "REPORT_DATE_NAME" : "2024一季报",
#     "SECURITY_TYPE_CODE" : "058001001",
#     "NOTICE_DATE" : "2024-04-27 00:00:00",
#     "UPDATE_DATE" : "2024-04-27 00:00:00",
#     "CURRENCY" : "CNY",
#     "ACCEPT_DEPOSIT_INTERBANK" : 8381544929.17,
#     "ACCOUNTS_PAYABLE" : 4022842219.54, 其中:应付账款
#     "ACCOUNTS_RECE" : 73124662.68, 应收账款
#     "ACCRUED_EXPENSE" : NaN,
#     "ADVANCE_RECEIVABLES" : NaN,
#     "AGENT_TRADE_SECURITY" : NaN,
#     "AGENT_UNDERWRITE_SECURITY" : NaN,
#     "AMORTIZE_COST_FINASSET" : NaN,
#     "AMORTIZE_COST_FINLIAB" : NaN,
#     "AMORTIZE_COST_NCFINASSET" : NaN,
#     "AMORTIZE_COST_NCFINLIAB" : NaN,
#     "APPOINT_FVTPL_FINASSET" : NaN,
#     "APPOINT_FVTPL_FINLIAB" : NaN,
#     "ASSET_BALANCE" : 0.0,
#     "ASSET_OTHER" : NaN,
#     "ASSIGN_CASH_DIVIDEND" : NaN,
#     "AVAILABLE_SALE_FINASSET" : NaN,
#     "BOND_PAYABLE" : NaN,
#     "BORROW_FUND" : NaN,
#     "BUY_RESALE_FINASSET" : 7111997692.87, 买入返售金融资产
#     "CAPITAL_RESERVE" : 1374964415.72, 资本公积
#     "CIP" : 2813289076.98, 在建工程
#     "CONSUMPTIVE_BIOLOGICAL_ASSET" : NaN,
#     "CONTRACT_ASSET" : NaN,
#     "CONTRACT_LIAB" : 9523298229.75, 合同负债
#     "CONVERT_DIFF" : NaN,
#     "CREDITOR_INVEST" : 5335437085.68, 债权投资
#     "CURRENT_ASSET_BALANCE" : 0.0,
#     "CURRENT_ASSET_OTHER" : NaN,
#     "CURRENT_LIAB_BALANCE" : 0.0,
#     "CURRENT_LIAB_OTHER" : NaN,
#     "DEFER_INCOME" : NaN,
#     "DEFER_INCOME_1YEAR" : NaN,
#     "DEFER_TAX_ASSET" : 4477172963.01, 递延所得税资产
#     "DEFER_TAX_LIAB" : 80835441.75, 递延所得税负债
#     "DERIVE_FINASSET" : NaN,
#     "DERIVE_FINLIAB" : NaN,
#     "DEVELOP_EXPENSE" : 222425799.33, 开发支出
#     "DIV_HOLDSALE_ASSET" : NaN,
#     "DIV_HOLDSALE_LIAB" : NaN,
#     "DIVIDEND_PAYABLE" : NaN,
#     "DIVIDEND_RECE" : NaN,
#     "EQUITY_BALANCE" : 0.0,
#     "EQUITY_OTHER" : NaN,
#     "EXPORT_REFUND_RECE" : NaN,
#     "FEE_COMMISSION_PAYABLE" : NaN,
#     "FIN_FUND" : NaN,
#     "FINANCE_RECE" : NaN,
#     "FIXED_ASSET" : 19541551054.14, 固定资产
#     "FIXED_ASSET_DISPOSAL" : NaN,
#     "FVTOCI_FINASSET" : NaN,
#     "FVTOCI_NCFINASSET" : NaN,
#     "FVTPL_FINASSET" : NaN,
#     "FVTPL_FINLIAB" : NaN,
#     "GENERAL_RISK_RESERVE" : 1061529724.0, 一般风险准备
#     "GOODWILL" : NaN,
#     "HOLD_MATURITY_INVEST" : NaN,
#     "HOLDSALE_ASSET" : NaN,
#     "HOLDSALE_LIAB" : NaN,
#     "INSURANCE_CONTRACT_RESERVE" : NaN,
#     "INTANGIBLE_ASSET" : 8517877019.46, 无形资产
#     "INTEREST_PAYABLE" : NaN,
#     "INTEREST_RECE" : NaN,
#     "INTERNAL_PAYABLE" : NaN,
#     "INTERNAL_RECE" : NaN,
#     "INVENTORY" : 46852227606.93, 存货
#     "INVEST_REALESTATE" : 3959373.06, 投资性房地产
#     "LEASE_LIAB" : 280265260.71, 租赁负债
#     "LEND_FUND" : 105060937860.99,  拆出资金
#     "LIAB_BALANCE" : 0.0,
#     "LIAB_EQUITY_BALANCE" : NaN,
#     "LIAB_EQUITY_OTHER" : NaN,
#     "LIAB_OTHER" : NaN,
#     "LOAN_ADVANCE" : 2603796544.91, 发放贷款及垫款
#     "LOAN_PBC" : NaN,
#     "LONG_EQUITY_INVEST" : NaN,
#     "LONG_LOAN" : NaN,
#     "LONG_PAYABLE" : NaN,
#     "LONG_PREPAID_EXPENSE" : 157773820.24, 长期待摊费用
#     "LONG_RECE" : NaN,
#     "LONG_STAFFSALARY_PAYABLE" : NaN,
#     "MINORITY_EQUITY" : 8804982639.98, 少数股东权益
#     "MONETARYFUNDS" : 74197126391.43,   货币资金
#     "NONCURRENT_ASSET_1YEAR" : NaN,
#     "NONCURRENT_ASSET_BALANCE" : 0.0,
#     "NONCURRENT_ASSET_OTHER" : NaN,
#     "NONCURRENT_LIAB_1YEAR" : 56128002.7, 一年内到期的非流动负债
#     "NONCURRENT_LIAB_BALANCE" : 0.0,
#     "NONCURRENT_LIAB_OTHER" : NaN,
#     "NOTE_ACCOUNTS_PAYABLE" : 4022842219.54,  应付票据及应付账款
#     "NOTE_ACCOUNTS_RECE" : 213804940.68,应收票据及应收账款 总
#     "NOTE_PAYABLE" : NaN,
#     "NOTE_RECE" : 140680278.0, 应收票据
#     "OIL_GAS_ASSET" : NaN,
#     "OTHER_COMPRE_INCOME" : -8109798.54, 其他综合收益
#     "OTHER_CREDITOR_INVEST" : NaN,
#     "OTHER_CURRENT_ASSET" : 61062481.87, 其他流动资产
#     "OTHER_CURRENT_LIAB" : 1145591991.93, 其他流动负债
#     "OTHER_EQUITY_INVEST" : NaN,
#     "OTHER_EQUITY_OTHER" : NaN,
#     "OTHER_EQUITY_TOOL" : NaN,
#     "OTHER_NONCURRENT_ASSET" : 154011277.63, 其他非流动资产
#     "OTHER_NONCURRENT_FINASSET" : 4004528610.65, 其他非流动金融资产
#     "OTHER_NONCURRENT_LIAB" : NaN,
#     "OTHER_PAYABLE" : NaN,
#     "OTHER_RECE" : NaN,
#     "PARENT_EQUITY_BALANCE" : 0.0,
#     "PARENT_EQUITY_OTHER" : NaN,
#     "PERPETUAL_BOND" : NaN,
#     "PERPETUAL_BOND_PAYBALE" : NaN,
#     "PREDICT_CURRENT_LIAB" : NaN,
#     "PREDICT_LIAB" : NaN,
#     "PREFERRED_SHARES" : NaN,
#     "PREFERRED_SHARES_PAYBALE" : NaN,
#     "PREMIUM_RECE" : NaN,
#     "PREPAYMENT" : 41204652.37, 预付款项
#     "PRODUCTIVE_BIOLOGY_ASSET" : NaN,
#     "PROJECT_MATERIAL" : NaN,
#     "RC_RESERVE_RECE" : NaN,
#     "REINSURE_PAYABLE" : NaN,
#     "REINSURE_RECE" : NaN,
#     "SELL_REPO_FINASSET" : NaN,
#     "SETTLE_EXCESS_RESERVE" : NaN,
#     "SHARE_CAPITAL" : 1256197800.0, 实收资本（或股本）
#     "SHORT_BOND_PAYABLE" : NaN,
#     "SHORT_FIN_PAYABLE" : NaN,
#     "SHORT_LOAN" : NaN,
#     "SPECIAL_PAYABLE" : NaN,
#     "SPECIAL_RESERVE" : NaN,
#     "STAFF_SALARY_PAYABLE" : 764260631.72, 应付职工薪酬
#     "SUBSIDY_RECE" : NaN,
#     "SURPLUS_RESERVE" : 38998763095.13, 盈余公积
#     "TAX_PAYABLE" : 7015986396.93, 应交税费
#     "TOTAL_ASSETS" : 285524543268.38, 资产总计
#     "TOTAL_CURRENT_ASSETS" : 237376996384.72,  流动资产合计
#     "TOTAL_CURRENT_LIAB" : 36626674015.39, 流动负债合计
#     "TOTAL_EQUITY" : 248536768550.53, 股东权益合计
#     "TOTAL_LIAB_EQUITY" : 285524543268.38, 负债和股东权益总计
#     "TOTAL_LIABILITIES" : 36987774717.85, 负债合计
#     "TOTAL_NONCURRENT_ASSETS" : 48147546883.66, 非流动资产合计
#     "TOTAL_NONCURRENT_LIAB" : 361100702.46, 非流动负债合计
#     "TOTAL_OTHER_PAYABLE" : 5717021613.65, 其他应付款合计
#     "TOTAL_OTHER_RECE" : 26297328.18, 其他应收款合计
#     "TOTAL_PARENT_EQUITY" : 239731785910.55, 归属于母公司股东权益总计
#     "TRADE_FINASSET" : NaN,
#     "TRADE_FINASSET_NOTFVTPL" : 3812337429.4, 交易性金融资产
#     "TRADE_FINLIAB" : NaN,
#     "TRADE_FINLIAB_NOTFVTPL" : NaN,
#     "TREASURY_SHARES" : NaN,
#     "UNASSIGN_RPOFIT" : 197048440674.24, 未分配利润
#     "UNCONFIRM_INVEST_LOSS" : NaN,
#     "USERIGHT_ASSET" : 315724258.57, 使用权资产
#     "ACCEPT_DEPOSIT_INTERBANK_YOY" : 6.5949245759,
#     "ACCOUNTS_PAYABLE_YOY" : 52.3685299106,
#     "ACCOUNTS_RECE_YOY" : 25.1911350968,
#     "ACCRUED_EXPENSE_YOY" : NaN,
#     "ADVANCE_RECEIVABLES_YOY" : NaN,
#     "AGENT_TRADE_SECURITY_YOY" : NaN,
#     "AGENT_UNDERWRITE_SECURITY_YOY" : NaN,
#     "AMORTIZE_COST_FINASSET_YOY" : NaN,
#     "AMORTIZE_COST_FINLIAB_YOY" : NaN,
#     "AMORTIZE_COST_NCFINASSET_YOY" : NaN,
#     "AMORTIZE_COST_NCFINLIAB_YOY" : NaN,
#     "APPOINT_FVTPL_FINASSET_YOY" : NaN,
#     "APPOINT_FVTPL_FINLIAB_YOY" : NaN,
#     "ASSET_BALANCE_YOY" : NaN,
#     "ASSET_OTHER_YOY" : NaN,
#     "ASSIGN_CASH_DIVIDEND_YOY" : NaN,
#     "AVAILABLE_SALE_FINASSET_YOY" : NaN,
#     "BOND_PAYABLE_YOY" : NaN,
#     "BORROW_FUND_YOY" : NaN,
#     "BUY_RESALE_FINASSET_YOY" : NaN,
#     "CAPITAL_RESERVE_YOY" : 0.0,
#     "CIP_YOY" : 16.3686330752,
#     "CONSUMPTIVE_BIOLOGICAL_ASSET_YOY" : NaN,
#     "CONTRACT_ASSET_YOY" : NaN,
#     "CONTRACT_LIAB_YOY" : 14.3255118595,
#     "CONVERT_DIFF_YOY" : NaN,
#     "CREDITOR_INVEST_YOY" : 285.3261659949,
#     "CURRENT_ASSET_BALANCE_YOY" : NaN,
#     "CURRENT_ASSET_OTHER_YOY" : NaN,
#     "CURRENT_LIAB_BALANCE_YOY" : NaN,
#     "CURRENT_LIAB_OTHER_YOY" : NaN,
#     "DEFER_INCOME_1YEAR_YOY" : NaN,
#     "DEFER_INCOME_YOY" : NaN,
#     "DEFER_TAX_ASSET_YOY" : 28.901621248,
#     "DEFER_TAX_LIAB_YOY" : -50.2942934041,
#     "DERIVE_FINASSET_YOY" : NaN,
#     "DERIVE_FINLIAB_YOY" : NaN,
#     "DEVELOP_EXPENSE_YOY" : 2.5846179105,
#     "DIV_HOLDSALE_ASSET_YOY" : NaN,
#     "DIV_HOLDSALE_LIAB_YOY" : NaN,
#     "DIVIDEND_PAYABLE_YOY" : NaN,
#     "DIVIDEND_RECE_YOY" : NaN,
#     "EQUITY_BALANCE_YOY" : NaN,
#     "EQUITY_OTHER_YOY" : NaN,
#     "EXPORT_REFUND_RECE_YOY" : NaN,
#     "FEE_COMMISSION_PAYABLE_YOY" : NaN,
#     "FIN_FUND_YOY" : NaN,
#     "FINANCE_RECE_YOY" : NaN,
#     "FIXED_ASSET_DISPOSAL_YOY" : NaN,
#     "FIXED_ASSET_YOY" : 0.2675488842,
#     "FVTOCI_FINASSET_YOY" : NaN,
#     "FVTOCI_NCFINASSET_YOY" : NaN,
#     "FVTPL_FINASSET_YOY" : NaN,
#     "FVTPL_FINLIAB_YOY" : NaN,
#     "GENERAL_RISK_RESERVE_YOY" : 0.0,
#     "GOODWILL_YOY" : NaN,
#     "HOLD_MATURITY_INVEST_YOY" : NaN,
#     "HOLDSALE_ASSET_YOY" : NaN,
#     "HOLDSALE_LIAB_YOY" : NaN,
#     "INSURANCE_CONTRACT_RESERVE_YOY" : NaN,
#     "INTANGIBLE_ASSET_YOY" : 1.0527955969,
#     "INTEREST_PAYABLE_YOY" : NaN,
#     "INTEREST_RECE_YOY" : NaN,
#     "INTERNAL_PAYABLE_YOY" : NaN,
#     "INTERNAL_RECE_YOY" : NaN,
#     "INVENTORY_YOY" : 16.9761008245,
#     "INVEST_REALESTATE_YOY" : -13.4284669865,
#     "LEASE_LIAB_YOY" : -16.5811741118,
#     "LEND_FUND_YOY" : -0.3509101173,
#     "LIAB_BALANCE_YOY" : NaN,
#     "LIAB_EQUITY_BALANCE_YOY" : NaN,
#     "LIAB_EQUITY_OTHER_YOY" : NaN,
#     "LIAB_OTHER_YOY" : NaN,
#     "LOAN_ADVANCE_YOY" : -38.6288828825,
#     "LOAN_PBC_YOY" : NaN,
#     "LONG_EQUITY_INVEST_YOY" : NaN,
#     "LONG_LOAN_YOY" : NaN,
#     "LONG_PAYABLE_YOY" : NaN,
#     "LONG_PREPAID_EXPENSE_YOY" : 8.0142948307,
#     "LONG_RECE_YOY" : NaN,
#     "LONG_STAFFSALARY_PAYABLE_YOY" : NaN,
#     "MINORITY_EQUITY_YOY" : 7.5367435942,
#     "MONETARYFUNDS_YOY" : 2.4104551404,
#     "NONCURRENT_ASSET_1YEAR_YOY" : NaN,
#     "NONCURRENT_ASSET_BALANCE_YOY" : NaN,
#     "NONCURRENT_ASSET_OTHER_YOY" : NaN,
#     "NONCURRENT_LIAB_1YEAR_YOY" : -37.7830800373,
#     "NONCURRENT_LIAB_BALANCE_YOY" : NaN,
#     "NONCURRENT_LIAB_OTHER_YOY" : NaN,
#     "NOTE_ACCOUNTS_PAYABLE_YOY" : 52.3685299106,
#     "NOTE_ACCOUNTS_RECE_YOY" : 266.0390657824,
#     "NOTE_PAYABLE_YOY" : NaN,
#     "NOTE_RECE_YOY" : NaN,
#     "OIL_GAS_ASSET_YOY" : NaN,
#     "OTHER_COMPRE_INCOME_YOY" : 18.9797836371,
#     "OTHER_CREDITOR_INVEST_YOY" : NaN,
#     "OTHER_CURRENT_ASSET_YOY" : -23.5699370064,
#     "OTHER_CURRENT_LIAB_YOY" : 16.8415197677,
#     "OTHER_EQUITY_INVEST_YOY" : NaN,
#     "OTHER_EQUITY_OTHER_YOY" : NaN,
#     "OTHER_EQUITY_TOOL_YOY" : NaN,
#     "OTHER_NONCURRENT_ASSET_YOY" : NaN,
#     "OTHER_NONCURRENT_FINASSET_YOY" : NaN,
#     "OTHER_NONCURRENT_LIAB_YOY" : NaN,
#     "OTHER_PAYABLE_YOY" : NaN,
#     "OTHER_RECE_YOY" : NaN,
#     "PARENT_EQUITY_BALANCE_YOY" : NaN,
#     "PARENT_EQUITY_OTHER_YOY" : NaN,
#     "PERPETUAL_BOND_PAYBALE_YOY" : NaN,
#     "PERPETUAL_BOND_YOY" : NaN,
#     "PREDICT_CURRENT_LIAB_YOY" : NaN,
#     "PREDICT_LIAB_YOY" : NaN,
#     "PREFERRED_SHARES_PAYBALE_YOY" : NaN,
#     "PREFERRED_SHARES_YOY" : NaN,
#     "PREMIUM_RECE_YOY" : NaN,
#     "PREPAYMENT_YOY" : -56.3999888135,
#     "PRODUCTIVE_BIOLOGY_ASSET_YOY" : NaN,
#     "PROJECT_MATERIAL_YOY" : NaN,
#     "RC_RESERVE_RECE_YOY" : NaN,
#     "REINSURE_PAYABLE_YOY" : NaN,
#     "REINSURE_RECE_YOY" : NaN,
#     "SELL_REPO_FINASSET_YOY" : NaN,
#     "SETTLE_EXCESS_RESERVE_YOY" : NaN,
#     "SHARE_CAPITAL_YOY" : 0.0,
#     "SHORT_BOND_PAYABLE_YOY" : NaN,
#     "SHORT_FIN_PAYABLE_YOY" : NaN,
#     "SHORT_LOAN_YOY" : NaN,
#     "SPECIAL_PAYABLE_YOY" : NaN,
#     "SPECIAL_RESERVE_YOY" : NaN,
#     "STAFF_SALARY_PAYABLE_YOY" : 71.7783411719,
#     "SUBSIDY_RECE_YOY" : NaN,
#     "SURPLUS_RESERVE_YOY" : 19.9219406872,
#     "TAX_PAYABLE_YOY" : 2.2341617814,
#     "TOTAL_ASSETS_YOY" : 10.501055862,
#     "TOTAL_CURRENT_ASSETS_YOY" : 8.7885311339,
#     "TOTAL_CURRENT_LIAB_YOY" : 16.5392858116,
#     "TOTAL_EQUITY_YOY" : 9.7469071685,
#     "TOTAL_LIAB_EQUITY_YOY" : 10.501055862,
#     "TOTAL_LIABILITIES_YOY" : 15.8503242759,
#     "TOTAL_NONCURRENT_ASSETS_YOY" : 19.7986394071,
#     "TOTAL_NONCURRENT_LIAB_YOY" : -27.5773258656,
#     "TOTAL_OTHER_PAYABLE_YOY" : 35.5651942454,
#     "TOTAL_OTHER_RECE_YOY" : -20.5943342049,
#     "TOTAL_PARENT_EQUITY_YOY" : 9.8298140667,
#     "TRADE_FINASSET_NOTFVTPL_YOY" : NaN,
#     "TRADE_FINASSET_YOY" : NaN,
#     "TRADE_FINLIAB_NOTFVTPL_YOY" : NaN,
#     "TRADE_FINLIAB_YOY" : NaN,
#     "TREASURY_SHARES_YOY" : NaN,
#     "UNASSIGN_RPOFIT_YOY" : 8.225033105,
#     "UNCONFIRM_INVEST_LOSS_YOY" : NaN,
#     "USERIGHT_ASSET_YOY" : -18.2349946142,
#     "OPINION_TYPE" : null, 审计意见(境内)
#     "OSOPINION_TYPE" : NaN,
#     "LISTING_STATE" : "0"
# }

# 资产负债表
# https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/Index?type=web&code=sh600519#zcfzb-0
def get_em_asset_liability_api(symbol):
    sec_code = finance_common_api.get_sec_code(symbol)
    try:
        stock_balance_sheet_by_report_em_df = ak.stock_balance_sheet_by_report_em(sec_code)
    except Exception as e:
        logger.error("同步资产表异常:{},{}", symbol, e)
        return None
    if data_frame_util.is_empty(stock_balance_sheet_by_report_em_df):
        return None
    stock_balance_sheet_by_report_em_df = check_columns(stock_balance_sheet_by_report_em_df)
    stock_balance_sheet_by_report_em_df = stock_balance_sheet_by_report_em_df[[
        'SECUCODE',
        'SECURITY_CODE',
        'SECURITY_NAME_ABBR',
        'ORG_CODE',
        'ORG_TYPE',
        'REPORT_DATE',
        'REPORT_TYPE',
        'REPORT_DATE_NAME',
        'SECURITY_TYPE_CODE',
        'NOTICE_DATE',
        'UPDATE_DATE',
        'CURRENCY',
        'ACCOUNTS_PAYABLE',
        'ACCOUNTS_RECE',
        'BUY_RESALE_FINASSET',
        'CAPITAL_RESERVE',
        'CIP',
        'CONTRACT_LIAB',
        'CREDITOR_INVEST',
        'DEFER_TAX_ASSET',
        'DEFER_TAX_LIAB',
        'DEVELOP_EXPENSE',
        'FIXED_ASSET',
        'GENERAL_RISK_RESERVE',
        'INTANGIBLE_ASSET',
        'INVENTORY',
        'INVEST_REALESTATE',
        'LEASE_LIAB',
        'LEND_FUND',
        'LOAN_ADVANCE',
        'LONG_PREPAID_EXPENSE',
        'MINORITY_EQUITY',
        'MONETARYFUNDS',
        'NONCURRENT_LIAB_1YEAR',
        'NOTE_ACCOUNTS_PAYABLE',
        'NOTE_ACCOUNTS_RECE',
        'NOTE_RECE',
        'OTHER_COMPRE_INCOME',
        'OTHER_CURRENT_ASSET',
        'OTHER_CURRENT_LIAB',
        'OTHER_NONCURRENT_ASSET',
        'OTHER_NONCURRENT_FINASSET',
        'PREPAYMENT',
        'SHARE_CAPITAL',
        'STAFF_SALARY_PAYABLE',
        'SURPLUS_RESERVE',
        'TAX_PAYABLE',
        'TOTAL_ASSETS',
        'TOTAL_CURRENT_ASSETS',
        'TOTAL_CURRENT_LIAB',
        'TOTAL_EQUITY',
        'TOTAL_LIAB_EQUITY',
        'TOTAL_LIABILITIES',
        'TOTAL_NONCURRENT_ASSETS',
        'TOTAL_NONCURRENT_LIAB',
        'TOTAL_OTHER_PAYABLE',
        'TOTAL_OTHER_RECE',
        'TOTAL_PARENT_EQUITY',
        'TRADE_FINASSET_NOTFVTPL',
        'UNASSIGN_RPOFIT',
        'USERIGHT_ASSET',
        'OPINION_TYPE'
    ]]
    stock_balance_sheet_by_report_em_df['_id'] = (stock_balance_sheet_by_report_em_df['SECURITY_CODE']
                                                  + "_" + stock_balance_sheet_by_report_em_df['REPORT_DATE'])

    query = {'SECURITY_CODE': symbol}
    exist_asset_em_df = mongodb_util.find_query_data(db_name_constant.EM_STOCK_ASSET_LIABILITY, query)
    if data_frame_util.is_not_empty(exist_asset_em_df):
        new_asset_df = stock_balance_sheet_by_report_em_df.loc[
            ~(stock_balance_sheet_by_report_em_df['_id'].isin(list(exist_asset_em_df['_id'])))]
    else:
        new_asset_df = stock_balance_sheet_by_report_em_df
    if data_frame_util.is_empty(new_asset_df):
        return None
    new_asset_df.fillna(0, inplace=True)
    return new_asset_df


def check_columns(new_asset_df):
    if 'CONTRACT_LIAB' not in new_asset_df.columns:
        new_asset_df['CONTRACT_LIAB'] = 0

    if 'DEVELOP_EXPENSE' not in new_asset_df.columns:
        new_asset_df['DEVELOP_EXPENSE'] = 0

    if 'INVENTORY' not in new_asset_df.columns:
        new_asset_df['INVENTORY'] = 0

    if 'NONCURRENT_LIAB_1YEAR' not in new_asset_df.columns:
        new_asset_df['NONCURRENT_LIAB_1YEAR'] = 0

    if 'NOTE_ACCOUNTS_PAYABLE' not in new_asset_df.columns:
        new_asset_df['NOTE_ACCOUNTS_PAYABLE'] = 0

    if 'NOTE_ACCOUNTS_RECE' not in new_asset_df.columns:
        new_asset_df['NOTE_ACCOUNTS_RECE'] = 0

    if 'OTHER_CURRENT_ASSET' not in new_asset_df.columns:
        new_asset_df['OTHER_CURRENT_ASSET'] = 0

    if 'OTHER_CURRENT_LIAB' not in new_asset_df.columns:
        new_asset_df['OTHER_CURRENT_LIAB'] = 0

    if 'OTHER_NONCURRENT_ASSET' not in new_asset_df.columns:
        new_asset_df['OTHER_NONCURRENT_ASSET'] = 0
    if 'OTHER_NONCURRENT_FINASSET' not in new_asset_df.columns:
        new_asset_df['OTHER_NONCURRENT_FINASSET'] = 0
    if 'PREPAYMENT' not in new_asset_df.columns:
        new_asset_df['PREPAYMENT'] = 0
    if 'TOTAL_CURRENT_ASSETS' not in new_asset_df.columns:
        new_asset_df['TOTAL_CURRENT_ASSETS'] = 0
    if 'TOTAL_CURRENT_LIAB' not in new_asset_df.columns:
        new_asset_df['TOTAL_CURRENT_LIAB'] = 0
    if 'TOTAL_NONCURRENT_ASSETS' not in new_asset_df.columns:
        new_asset_df['TOTAL_NONCURRENT_ASSETS'] = 0
    if 'TOTAL_NONCURRENT_LIAB' not in new_asset_df.columns:
        new_asset_df['TOTAL_NONCURRENT_LIAB'] = 0
    if 'TOTAL_OTHER_PAYABLE' not in new_asset_df.columns:
        new_asset_df['TOTAL_OTHER_PAYABLE'] = 0
    if 'TOTAL_OTHER_RECE' not in new_asset_df.columns:
        new_asset_df['TOTAL_OTHER_RECE'] = 0
    if 'ACCOUNTS_RECE' not in new_asset_df.columns:
        new_asset_df['ACCOUNTS_RECE'] = 0

    if 'LOAN_ADVANCE' not in new_asset_df.columns:
        new_asset_df['LOAN_ADVANCE'] = 0
    if 'MONETARYFUNDS' not in new_asset_df.columns:
        new_asset_df['MONETARYFUNDS'] = 0
    return new_asset_df


if __name__ == '__main__':
    get_em_asset_liability_api('832876')

    stock_cash_flow_sheet_by_report_em_df = ak.stock_cash_flow_sheet_by_report_em(symbol="SH600519")
    print(stock_cash_flow_sheet_by_report_em_df)

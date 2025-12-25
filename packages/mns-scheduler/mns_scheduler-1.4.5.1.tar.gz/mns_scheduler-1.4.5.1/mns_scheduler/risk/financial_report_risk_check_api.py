import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_scheduler.risk.financial.net_assets_check_api as net_assets_check_api
import mns_scheduler.risk.financial.annual_report_audit_check_api as annual_report_audit_check_api
import mns_scheduler.risk.financial.profit_income_check_api as profit_income_check_api


# 1.无保留意见/标准报告：报告没问题。（没有发现造假，但也不能保证为真）
#
# 2.带强调事项段的无保留意见：报告没问题，但是有亏损获对其可持续经营有重大疑虑（可能造假，至少是在粉饰报表）
#
# 3.保留意见报告：有问题，财务造假
#
# 4.否定意见报告：有很大问题
#
# 5.无法表示意见报告：不让查
#


#### 退市新规 ####
# 1 股价类:连续20个交易日估价低于1元
# 2 市值类: 主板小于5亿、创业板3亿
# 3 财务类: (1) 利润总额 净利润 扣非净利润三者最小值为负 且营业收入小于3亿 创业板营业收入小于1元
#          (2) 资不抵债


# 财报审核
def financial_report_check(new_report_df, period_time, period, report_type):
    # 年报审核
    if period == 4:
        # 年报审计意见
        annual_report_audit_check_api.annual_report_audit_check(new_report_df, period_time)
        # 年报收入利润check
        profit_income_check_api.profit_income_check(new_report_df, period_time, report_type)

    # 负债过高
    net_assets_check_api.net_assets_check(report_type, new_report_df, period_time)

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_scheduler.k_line.month_week_daily.daily_week_month_line_sync as daily_week_month_line_sync
from datetime import datetime
import mns_scheduler.zt.zt_pool.em_zt_pool_sync_api as em_zt_pool_sync_api
import mns_scheduler.zt.high_chg.sync_high_chg_pool_service as sync_high_chg_pool_service
import mns_scheduler.zt.open_data.kcx_high_chg_open_data_sync as kcx_high_chg_open_data_sync
import mns_scheduler.zt.high_chg.sync_high_chg_real_time_quotes_service as sync_high_chg_real_time_quotes_service


def sync_now_day_high_chg():
    real_time_quotes_now_es = em_stock_info_api.get_a_stock_info()
    real_time_quotes_now_es_high_chg = real_time_quotes_now_es.loc[
        real_time_quotes_now_es['chg'] > common_service_fun_api.ZT_CHG]
    now_date = datetime.now()

    str_now_day = now_date.strftime('%Y-%m-%d')
    # 同步qfq k线
    daily_week_month_line_sync.sync_all_daily_data('daily', 'qfq', 'stock_qfq_daily', str_now_day,
                                                   list(real_time_quotes_now_es_high_chg['symbol']))


    # 同步当前涨停
    em_zt_pool_sync_api.save_zt_info(str_now_day)

    # 同步涨幅列表
    sync_high_chg_pool_service.sync_stock_high_chg_pool_list(str_now_day, None)

    # 同步kcx 集合竞价数据
    kcx_high_chg_open_data_sync.sync_all_kc_zt_data(str_now_day, None)
    # 同步实时行情数据
    sync_high_chg_real_time_quotes_service.sync_high_chg_real_time_quotes(str_now_day)


if __name__ == '__main__':
    sync_now_day_high_chg()


import warnings
# 忽略所有警告
warnings.filterwarnings("ignore")
from loguru import logger
from datetime import datetime
import mns_scheduler.dt.stock_dt_pool_sync as stock_dt_pool_sync_api
import mns_scheduler.zb.stock_zb_pool_sync as stock_zb_pool_sync_api
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
import mns_scheduler.k_line.month_week_daily.daily_week_month_line_sync as daily_week_month_line_sync_api
import mns_scheduler.db.col_move_service as col_move_service
import mns_scheduler.zt.open_data.kcx_high_chg_open_data_sync as kcx_high_chg_open_data_sync
import mns_scheduler.zt.export.export_kcx_high_chg_open_data_to_excel as export_kcx_high_chg_open_data_to_excel
import mns_scheduler.zt.connected_boards.zt_five_boards_sync_api as zt_five_boards_sync_api
import mns_scheduler.zt.zt_pool.em_zt_pool_sync_api as em_zt_pool_sync_api
import mns_scheduler.k_line.clean.k_line_info_clean_task as k_line_info_clean_service

import mns_scheduler.open.sync_one_day_open_data_to_db_service as sync_one_day_open_data_to_db_service
import mns_scheduler.zt.high_chg.sync_high_chg_pool_service as sync_high_chg_pool_service
import mns_scheduler.zt.high_chg.sync_high_chg_real_time_quotes_service as sync_high_chg_real_time_quotes_service
import mns_scheduler.zt.zt_pool.ths_zt_pool_sync_api as ths_zt_pool_sync_api
import mns_scheduler.trade.tfp.stock_tfp_info_sync as stock_tfp_info_sync


# 定时同步每日交易行情数据(前复权)
def stock_daily_sync_qfq():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d')
    logger.info('同步每日行情数据(前复权):' + str_now_date)
    daily_week_month_line_sync_api.sync_all_daily_data('daily',
                                                       'qfq', 'stock_qfq_daily', str_now_date)


# 同步当日k c x 高涨幅数据
def realtime_quotes_now_zt_kc_data_sync():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    if trade_date_common_service_api.is_trade_day(str_day):
        # 同步当日kcx 高涨幅 当天交易数据和开盘数据
        kcx_high_chg_open_data_sync.sync_all_kc_zt_data(str_day, None)
        # 同步当日开盘数据
        sync_one_day_open_data_to_db_service.sync_one_day_open_data(str_day)
        # 涨停数据同步到excel
        export_kcx_high_chg_open_data_to_excel.export_kc_zt_data(str_day)


# 同步涨停池
def sync_stock_zt_pool():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    if trade_date_common_service_api.is_trade_day(str_day):
        logger.info('同步当天涨停池股开始')
        em_stock_zt_pool = em_zt_pool_sync_api.save_zt_info(str_day)
        zt_five_boards_sync_api.update_five_connected_boards_task(em_stock_zt_pool)
        logger.info('同步ths股票涨停池')
        ths_zt_pool_df = ths_zt_pool_sync_api.ths_zt_pool(str_day, None)
        ths_zt_pool_sync_api.save_ths_zt_pool(ths_zt_pool_df, str_day)
        logger.info('同步当天涨停池股票完成')


# 保存今天高涨幅数据
def sync_toady_stock_zt_pool():
    logger.info('同步今天涨幅大于9.5的symbol')
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    # 同步高涨幅实时行情
    sync_high_chg_real_time_quotes_service.sync_high_chg_real_time_quotes(str_day)
    # 同步高涨幅列表
    sync_high_chg_pool_service.sync_stock_high_chg_pool_list(str_day, None)


# 计算下一个交易日k线数据
def generate_new_day_k_line_info():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    # 生成下一个交易日日期k线数据 number=2 获取下一个交易日 日期
    if trade_date_common_service_api.is_trade_day(str_day):
        dis_number = 2
    else:
        dis_number = 1
    next_trade_day = trade_date_common_service_api.get_further_trade_date(str_day, dis_number)
    k_line_info_clean_service.sync_k_line_info_task(next_trade_day)
    logger.info('计算当日k线信息完成:{}', str_day)


# 同步一天k线 涨停 数据
def sync_daily_data_info():
    # 同步k线数据
    try:
        stock_daily_sync_qfq()
    except BaseException as e:
        logger.error("同步当日k线数据异常:{}", e)

    # 同步当日k c x 高涨幅数据
    try:
        realtime_quotes_now_zt_kc_data_sync()
    except BaseException as e:
        logger.error("同步当日kcx高涨幅数据异常:{}", e)

    # 同步涨停池数据信息
    try:
        sync_stock_zt_pool()
    except BaseException as e:
        logger.error("同步涨停数据信息异常:{}", e)

    # 同步今日高涨幅数据 依赖涨停股票池的数据
    try:
        sync_toady_stock_zt_pool()
    except BaseException as e:
        logger.error("同步今日高涨幅数据异常:{}", e)

    # 计算当日k线数据
    try:
        generate_new_day_k_line_info()
    except BaseException as e:
        logger.error("计算当日k线数据异常:{}", e)

# 跌停信息
def sync_stock_dt_pool():
    now_date = datetime.now()
    str_now_day = now_date.strftime('%Y-%m-%d')
    if trade_date_common_service_api.is_trade_day(str_now_day):
        stock_dt_pool_sync_api.sync_stock_dt_pool(str_now_day)
        logger.info("同步跌停信息任务执行成功:{}", str_now_day)


# 炸板信息
def sync_stock_zb_pool():
    now_date = datetime.now()
    str_now_day = now_date.strftime('%Y-%m-%d')
    if trade_date_common_service_api.is_trade_day(str_now_day):
        stock_zb_pool_sync_api.sync_stock_zb_pool(str_now_day)
        logger.info("同步炸板信息任务执行成功:{}", str_now_day)
    # 同步停复牌信息
    sync_stock_tfp()


# 同步停复牌信息
def sync_stock_tfp():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    stock_tfp_info_sync.sync_stock_tfp(str_day)




#  当天实时数据备份
def col_data_move():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    logger.info('当天实时数据备份:{}', str_day)
    if trade_date_common_service_api.is_trade_day(str_day):
        col_move_service.sync_col_move(str_day)

if __name__ == '__main__':
    col_data_move()
    sync_daily_data_info()
    sync_stock_zt_pool()
    sync_stock_dt_pool()
    sync_stock_zb_pool()


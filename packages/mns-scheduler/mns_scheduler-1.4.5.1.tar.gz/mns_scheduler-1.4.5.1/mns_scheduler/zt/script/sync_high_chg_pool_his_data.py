import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.utils.date_handle_util as date_handle_util
from mns_common.db.MongodbUtil import MongodbUtil
import mns_scheduler.zt.high_chg.sync_high_chg_pool_service as sync_high_chg_pool_service
from loguru import logger
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api

mongodb_util = MongodbUtil('27017')


def sync_his_zt_pool_data(begin_day, end_day):
    sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(begin_day), 0)

    end_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(end_day), 0)

    str_now_day = begin_day

    while sync_date <= end_date:
        try:
            is_trade_day = trade_date_common_service_api.is_trade_day(str_now_day)
            if is_trade_day:
                sync_high_chg_pool_service.sync_stock_high_chg_pool_list(str_now_day, None)
                logger.error("同步高涨幅列表完成:{}", str_now_day)
            sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day), 1)
            str_now_day = sync_date.strftime('%Y-%m-%d')
        except Exception as e:
            sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_now_day), 1)
            str_now_day = sync_date.strftime('%Y-%m-%d')
            logger.error("更新高涨幅数据异常:{},{}", str_now_day, e)


if __name__ == '__main__':
    sync_high_chg_pool_service.sync_stock_high_chg_pool_list('2025-05-23', None)

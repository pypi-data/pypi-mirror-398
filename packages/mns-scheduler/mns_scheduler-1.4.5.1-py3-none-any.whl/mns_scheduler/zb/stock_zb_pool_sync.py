from datetime import datetime
from loguru import logger
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.api.akshare.stock_zb_pool as stock_zb_pool_api
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.component.company.company_common_service_api as company_common_service_api

mongodb_util = MongodbUtil('27017')


def sync_stock_zb_pool(str_now_day):
    try:
        if str_now_day is None:
            now_date_time = datetime.now()
            str_now_day = now_date_time.strftime('%Y-%m-%d')
        logger.info('同步所有炸板股:' + str_now_day)
        stock_em_zb_pool_df_data = stock_zb_pool_api.stock_zb_pool_df(
            date_handle_util.no_slash_date(str_now_day))
        if stock_em_zb_pool_df_data is None:
            return
        stock_em_zb_pool_df_data = company_common_service_api.merge_company_info(stock_em_zb_pool_df_data, str_now_day)
        mongodb_util.save_mongo(stock_em_zb_pool_df_data, 'stock_zb_pool')
        return stock_em_zb_pool_df_data
    except BaseException as e:
        logger.error("实时股票炸板股信息数据同步异常:{},{}", str_now_day, e)
        return None


if __name__ == '__main__':
    sync_stock_zb_pool('2025-12-11')

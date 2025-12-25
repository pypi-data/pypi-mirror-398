import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_scheduler.company_info.task.company_industry_info_task as company_industry_info_task
import mns_scheduler.company_info.task.company_business_info_task as company_business_info_task
import mns_scheduler.company_info.task.company_base_info_task as company_base_info_task
import mns_scheduler.company_info.task.company_hold_info_task as company_hold_info_task
import mns_scheduler.company_info.task.company_announce_info_task as company_announce_info_task
from mns_scheduler.company_info.common.company_common_query_service import get_company_info
from datetime import datetime
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger


def sync_all_company_task():
    # 同步公司行业信息
    company_industry_info_task.sync_company_industry_info_task([])
    logger.info("[全量]同步公司[行业]信息完成")
    # 同步公司业务信息
    company_business_info_task.sync_company_business_task([])
    logger.info("[全量]同步公司[业务]信息完成")
    # 同步公司基本信息
    company_base_info_task.sync_company_base_info_task([])
    logger.info("[全量]同步公司[基本]信息完成")
    # 同步公司控股信息
    company_hold_info_task.sync_all_company_hold_info_task([])
    logger.info("[全量]同步公司[控股]信息完成")
    # 同步公司公告信息
    company_announce_info_task.sync_company_announce_task([])
    logger.info("[全量]同步公司[公告]信息完成")


def sync_new_stock_company_task():
    all_company_info_df = get_company_info()

    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    # 去掉横线并转换为整数
    now_day = int(str_day.replace('-', ''))

    new_company_info_df = all_company_info_df.loc[
        (all_company_info_df['list_date'] == 19890604) | (all_company_info_df['list_date'] >= now_day)]
    if data_frame_util.is_empty(new_company_info_df):
        return
    symbol_list = list(new_company_info_df['symbol'])
    # 同步公司行业信息
    company_industry_info_task.sync_company_industry_info_task(symbol_list)
    logger.info("[新股]同步公司[行业]信息完成")
    # 同步公司业务信息
    company_business_info_task.sync_company_business_task(symbol_list)
    logger.info("[新股]同步公司[业务]信息完成")
    # 同步公司基本信息
    company_base_info_task.sync_company_base_info_task(symbol_list)
    logger.info("[新股]同步公司[基本]信息完成")
    # 同步公司控股信息
    company_hold_info_task.sync_all_company_hold_info_task(symbol_list)
    logger.info("[新股]同步公司[控股]信息完成")
    # 同步公司公告信息
    company_announce_info_task.sync_company_announce_task(symbol_list)
    logger.info("[新股]同步公司[公告]信息完成")


if __name__ == '__main__':
    sync_new_stock_company_task()
    sync_all_company_task()

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
from datetime import datetime
import mns_common.constant.extra_income_db_name as extra_income_db_name
import mns_common.component.cookie.cookie_info_service as cookie_info_service
import mns_common.api.em.real_time.east_money_stock_us_api as east_money_stock_us_api
import mns_common.api.em.real_time.east_money_debt_api as east_money_debt_api
import mns_common.api.em.real_time.east_money_etf_api as east_money_etf_api
import mns_common.api.em.real_time.east_money_stock_hk_api as east_money_stock_hk_api
import mns_common.api.em.real_time.east_money_stock_hk_gtt_api as east_money_stock_hk_gtt_api
import mns_common.api.em.real_time.east_money_stock_a_v2_api as east_money_stock_a_v2_api

mongodb_util = MongodbUtil('27017')


def sync_all_em_stock_info():
    logger.info("同步东方财富a,etf,kzz,us,hk,信息开始")
    # 同步东方财富A股股票信息
    sync_stock_info()
    # 同步东方财富A股可转债信息
    sync_kzz_info()
    # 同步东方财富A股ETF信息
    sync_etf_info()
    # 同步东方财富港股信息
    sync_hk_stock_info()
    # 同步东方财富港股通信息
    sync_hk_ggt_stock_info()
    # 同步东方财富美股信息
    sync_us_stock_info()

    logger.info("同步东方财富a,etf,kzz,us,hk,信息完成")


# 同步东方财富A股可转债信息
def sync_kzz_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富可转债信息")
    try:
        em_kzz_info = east_money_debt_api.get_kzz_real_time_quotes(30, 6)
        em_kzz_info['_id'] = em_kzz_info['symbol']
        em_kzz_info['sync_time'] = str_now_date
        mongodb_util.save_mongo(em_kzz_info, extra_income_db_name.EM_KZZ_INFO)
    except BaseException as e:
        logger.error("同步东方财富可转债信息异常:{}", e)


# 同步东方财富A股ETF信息
def sync_etf_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富ETF信息")
    try:
        em_etf_info = east_money_etf_api.get_etf_real_time_quotes(30, 6)
        em_etf_info['_id'] = em_etf_info['symbol']
        em_etf_info['sync_time'] = str_now_date
        mongodb_util.save_mongo(em_etf_info, extra_income_db_name.EM_ETF_INFO)
    except BaseException as e:
        logger.error("同步东方财富ETF信息异常:{}", e)


# 同步东方财富A股股票信息
def sync_stock_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富股票信息")
    try:
        em_etf_info = east_money_stock_a_v2_api.get_stock_real_time_quotes(60)
        em_etf_info['_id'] = em_etf_info['symbol']
        em_etf_info['sync_time'] = str_now_date
        mongodb_util.save_mongo(em_etf_info, extra_income_db_name.EM_A_STOCK_INFO)
    except BaseException as e:
        logger.error("同步东方财富ETF信息异常:{}", e)


# 同步东方财富港股信息
def sync_hk_stock_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富港股信息")

    em_cookie = cookie_info_service.get_em_cookie()

    try:
        em_hk_info = east_money_stock_hk_api.get_hk_real_time_quotes(30, em_cookie)
        em_hk_info['_id'] = em_hk_info['symbol']
        em_hk_info['sync_time'] = str_now_date
        mongodb_util.save_mongo(em_hk_info, extra_income_db_name.EM_HK_STOCK_INFO)
    except BaseException as e:
        logger.error("同步东方财富ETF信息异常:{}", e)


# 同步东方财富港股通信息
def sync_hk_ggt_stock_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富港股信息")
    em_cookie = cookie_info_service.get_em_cookie()

    try:
        em_hk_gtt_info = east_money_stock_hk_gtt_api.get_ggt_real_time_quotes(em_cookie, 30, 6)
        em_hk_gtt_info['_id'] = em_hk_gtt_info['symbol']
        em_hk_gtt_info['sync_time'] = str_now_date
        mongodb_util.save_mongo(em_hk_gtt_info, extra_income_db_name.EM_HK_GGT_STOCK_INFO)
    except BaseException as e:
        logger.error("同步东方财富ETF信息异常:{}", e)


# 同步东方财富美股信息 todo 增加稳定接口
def sync_us_stock_info():
    now_date = datetime.now()
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    logger.error("同步东方财富美股信息")
    em_cookie = cookie_info_service.get_em_cookie()
    us_stock_info = east_money_stock_us_api.get_us_stock_real_time_quotes(em_cookie, None)
    us_stock_info['_id'] = us_stock_info['symbol']
    us_stock_info['sync_time'] = str_now_date
    mongodb_util.save_mongo(us_stock_info, extra_income_db_name.EM_US_STOCK_INFO)


if __name__ == '__main__':
    sync_stock_info()
    # em_cookie = cookie_info_service.get_em_cookie()
    # em_us_stock_info = east_money_stock_us_api.get_us_stock_real_time_quotes(em_cookie, None)
    # em_us_stock_info['_id'] = em_us_stock_info['symbol']
    # mongodb_util.save_mongo(em_us_stock_info, db_name_constant.EM_US_STOCK_INFO)

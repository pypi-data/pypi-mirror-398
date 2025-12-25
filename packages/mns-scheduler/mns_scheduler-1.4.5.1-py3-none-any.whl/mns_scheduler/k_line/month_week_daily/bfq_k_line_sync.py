import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_scheduler.k_line.common.k_line_common_api as k_line_common_api
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api



mongodb_util = MongodbUtil('27017')


def sync_bfq_k_line_data(period='daily',
                         hq='hfq',
                         hq_col='stock_hfq_daily',
                         end_date='2222-01-01',
                         symbol=None):

    stock_hfq_df = k_line_common_api.get_k_line_common_adapter(symbol, period, hq, end_date)



    classification = common_service_fun_api.classify_symbol_one(symbol)
    stock_hfq_df['classification'] = classification
    stock_hfq_df = stock_hfq_df.sort_values(by=['date'], ascending=False)
    insert_data(stock_hfq_df, hq_col, symbol)
    logger.info(period + 'k线同步-' + hq + '-' + symbol)
    return stock_hfq_df


def sync_all_bfq_k_line(period='daily',
                        hq='hfq',
                        hq_col='stock_hfq_daily',
                        end_date='22220101',
                        symbol='300085'):
    real_time_quotes_now_es = em_stock_info_api.get_a_stock_info()

    symbol_list = list(real_time_quotes_now_es['symbol'])
    # 退市公司
    de_list_company = company_common_service_new_api.get_de_list_company()
    symbol_list.extend(de_list_company)
    symbol_list = set(symbol_list)
    if symbol is not None:
        symbol_list = [symbol]
    for symbol in symbol_list:
        try:
            sync_bfq_k_line_data(period,
                                 hq,
                                 hq_col,
                                 end_date,
                                 symbol)
        except BaseException as e:
            logger.warning("同步不复权k线:{},{}", symbol, e)


def insert_data(stock_hfq_df, hq_col, symbol):
    query = {'symbol': symbol}
    tag = mongodb_util.remove_data(query, hq_col)
    success = tag.acknowledged
    if success:
        mongodb_util.insert_mongo(stock_hfq_df, hq_col)


if __name__ == '__main__':
    sync_all_bfq_k_line('daily',
                        'qfq',
                        'stock_bfq_daily',
                        '2025-05-25',
                        '000001')

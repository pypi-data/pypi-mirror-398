import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

from loguru import logger
import mns_common.component.em.em_stock_info_api as em_stock_info_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.api.xueqiu.xue_qiu_k_line_api as xue_qiu_k_line_api
import mns_common.component.cookie.cookie_info_service as cookie_info_service
from datetime import datetime
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')


def sync_year_k_line():
    timestamp = str(int(datetime.now().timestamp() * 1000))

    col_name = db_name_constant.STOCK_QFQ_YEAR
    real_time_quotes_all_stocks_df = em_stock_info_api.get_a_stock_info()
    real_time_quotes_all_stocks_df = common_service_fun_api.classify_symbol(real_time_quotes_all_stocks_df)
    real_time_quotes_all_stocks_df = common_service_fun_api.add_pre_prefix(real_time_quotes_all_stocks_df)
    for stock_one in real_time_quotes_all_stocks_df.itertuples():
        symbol = stock_one.symbol
        try:
            symbol_prefix = stock_one.symbol_prefix

            year_k_line_df_copy = xue_qiu_k_line_api.get_xue_qiu_k_line(symbol_prefix, 'year',
                                                                        cookie_info_service.get_xue_qiu_cookie(),
                                                                        timestamp,
                                                                        'before')
            if data_frame_util.is_empty(year_k_line_df_copy):
                logger.warning("返回数据为空:{}", symbol)
                continue

            year_k_line_df = year_k_line_df_copy.copy()
            year_k_line_df = year_k_line_df[[
                'volume',
                'open',
                'high',
                'low',
                'close',
                'chg',
                'percent',
                'turnoverrate',
                'amount',
                'str_day'
            ]]
            year_k_line_df['year'] = year_k_line_df['str_day'].str[:4]

            year_k_line_df["open_to_high_pct"] = (
                    (year_k_line_df["high"] - year_k_line_df["open"]) / year_k_line_df["open"] * 100).round(2)

            year_k_line_df["low_to_high_pct"] = (
                    (year_k_line_df["high"] - year_k_line_df["low"]) / year_k_line_df["low"] * 100).round(2)
            year_k_line_df = year_k_line_df.rename(columns={
                "percent": "chg",
                "chg": "chg_price",
                "turnoverrate": "exchange"
            })
            year_k_line_df['symbol'] = symbol
            year_k_line_df['_id'] = symbol + '_' + year_k_line_df['year']
            mongodb_util.save_mongo(year_k_line_df, col_name)
            logger.info("同步年线数据完成:{},{}", symbol, stock_one.name)
        except BaseException as e:
            logger.error("同步年线数据异常:{},{}", symbol, e)


if __name__ == '__main__':
    sync_year_k_line()

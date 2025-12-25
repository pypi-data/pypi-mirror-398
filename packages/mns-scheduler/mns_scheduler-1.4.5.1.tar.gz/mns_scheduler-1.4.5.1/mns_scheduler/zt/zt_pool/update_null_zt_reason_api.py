import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
import mns_common.api.ths.zt.ths_stock_zt_pool_api as ths_stock_zt_pool_api
import mns_common.utils.data_frame_util as data_frame_util
from loguru import logger
import time


def update_null_zt_reason(str_day):
    query = {"str_day": str_day, "$or": [{"zt_reason": "0"},
                                         {"zt_reason": ""},
                                         {"zt_reason": float('nan')},

                                         {"zt_analysis": "0"},
                                         {"zt_analysis": ""},
                                         {"zt_analysis": float('nan')},

                                         ]}
    stock_zt_pool_df_null_zt_reason = mongodb_util.find_query_data('stock_zt_pool', query)
    if data_frame_util.is_empty(stock_zt_pool_df_null_zt_reason):
        return None
    no_reason_list = list(stock_zt_pool_df_null_zt_reason['symbol'])
    repeat_number = 0
    # 循环10次
    while len(no_reason_list) > 0 and repeat_number < 10:

        for stock_zt_one in stock_zt_pool_df_null_zt_reason.itertuples():
            try:
                # 涨停原因
                stock_zt_pool_df_one_df = stock_zt_pool_df_null_zt_reason.loc[
                    stock_zt_pool_df_null_zt_reason['symbol'] == stock_zt_one.symbol]
                # 涨停分析
                zt_result_dict = ths_stock_zt_pool_api.zt_analyse_reason(stock_zt_one.symbol)
                time.sleep(5)

                zt_analysis = zt_result_dict['zt_analyse_detail']
                zt_reason = zt_result_dict['zt_reason']

                stock_zt_pool_df_one_df['zt_analysis'] = zt_analysis
                stock_zt_pool_df_one_df['zt_reason'] = zt_reason

                mongodb_util.save_mongo(stock_zt_pool_df_one_df, 'stock_zt_pool')
                if stock_zt_one.symbol in no_reason_list:
                    no_reason_list.remove(stock_zt_one.symbol)
            except BaseException as e:
                logger.error("出现异常:{},{}", stock_zt_one.symbol, e)
                continue
        repeat_number = repeat_number + 1
    return stock_zt_pool_df_null_zt_reason


if __name__ == '__main__':
    update_null_zt_reason('2025-12-08')

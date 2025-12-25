import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger
import mns_common.utils.date_handle_util as date_handle_util
mongodb_util = MongodbUtil('27017')

from mns_scheduler.db.script.sync.remote_mongo_util import RemoteMongodbUtil


remote_mongodb_util = RemoteMongodbUtil('27017')


def fix_error_deal_days(db_name):
    realtime_quotes_now_zt_new_kc_open_df = mongodb_util.find_query_data(db_name, {})
    realtime_quotes_now_zt_new_kc_open_df['id_key'] = realtime_quotes_now_zt_new_kc_open_df['_id']
    for stock_one in realtime_quotes_now_zt_new_kc_open_df.itertuples():
        try:
            symbol = stock_one.symbol
            str_day = stock_one.str_day
            query = {'symbol': symbol, 'date': {"$lt": date_handle_util.no_slash_date(str_day)}}
            deal_days = mongodb_util.count(query, 'stock_qfq_daily')
            new_values = {"$set": {"deal_days": deal_days}}
            id_key = stock_one.id_key
            update_query = {'_id': id_key}
            mongodb_util.update_many(update_query, new_values, db_name)
            logger.info("更新到:{},{}", symbol, str_day)
        except BaseException as e:
            logger.error("出现异常:{},{},{}", symbol, str_day, e)


if __name__ == '__main__':
    # db_name_0 = 'realtime_quotes_now_zt_new_kc_open'
    db_name_01 = 'stock_high_chg_pool'
    # fix_error_deal_days(db_name_0)
    fix_error_deal_days(db_name_01)

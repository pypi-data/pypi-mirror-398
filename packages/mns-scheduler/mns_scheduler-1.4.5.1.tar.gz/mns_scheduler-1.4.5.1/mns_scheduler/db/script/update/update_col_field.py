import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
from mns_common.db.MongodbUtil import MongodbUtil
from loguru import logger

mongodb_util_27017 = MongodbUtil('27017')
mongodb_util_27019 = MongodbUtil('27019')


def update_col_data():
    query = {"$and": [{'trade_date': {'$lte': '2024-05-23'}},
                      {'trade_date': {'$gte': '2022-07-02'}}]}
    trade_date_list_df = mongodb_util_27017.find_query_data('trade_date_list', query)
    trade_date_list_df = trade_date_list_df.sort_values(by=['trade_date'], ascending=True)
    for trade_one in trade_date_list_df.itertuples():
        col_name = 'realtime_quotes_now_' + trade_one.trade_date
        new_values = {'$unset': {
            'classification': '',
            'medium_order_net_inflow': '',
            'small_order_net_inflow': '',
            'str_day': '',
            'list_date': '',
            'amount_level': '',
            'name': '', 'industry': '', 'concept': ''}}

        mongodb_util_27019.update_many({}, new_values, col_name)
        logger.info("完成集合数据更新:{}", col_name)


if __name__ == '__main__':
    update_col_data()

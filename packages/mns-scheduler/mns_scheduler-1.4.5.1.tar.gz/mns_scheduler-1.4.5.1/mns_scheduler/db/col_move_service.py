import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import mns_common.utils.date_handle_util as date_handle_util
import os
from loguru import logger
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
mongodb_util_21019 = MongodbUtil('27019')


def create_db_index(str_day):
    try:
        mongodb_util_21019.create_index('realtime_quotes_now_' + str_day, [("symbol", 1)])
        mongodb_util_21019.create_index('realtime_quotes_now_' + str_day, [("number", 1)])
        mongodb_util_21019.create_index('realtime_quotes_now_' + str_day, [("symbol", 1), ("number", 1)])
        mongodb_util_21019.create_index('realtime_quotes_now_' + str_day, [("str_now_date", 1)])
        logger.info("创建索引成功:{}", str_day)
    except BaseException as e:
        logger.warning("创建索引异常:{}", e)


# mongodump --host 127.0.0.1:27018  -d patience    -o H:\back
def get_mongodb_util(str_day):
    sync_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_day), 0)
    month = sync_date.month
    day = sync_date.day
    if month < 8:
        return '127.0.0.1:27018'
    elif month == 8 and day < 15:
        return '127.0.0.1:27018'
    else:
        return '127.0.0.1:27017'


def db_export(db, str_day):
    col = 'realtime_quotes_now_' + str_day
    cmd = 'F:/mongo/bin/mongodump.exe --host ' + db + ' -d patience -c ' + col + ' -o D:/back'
    os.system(cmd)
    logger.info("export finished:{}", str_day)


def db_import(db, str_day):
    col = 'realtime_quotes_now_' + str_day
    create_db_index(str_day)
    cmd = 'F:/mongo/bin/mongorestore.exe --host ' + db + ' -d patience -c ' + col + ' D:/back/patience/' + col + '.bson'
    os.system(cmd)

    path = 'D:\\back\\patience\\realtime_quotes_now_' + str_day + '.bson'
    cmd_del = 'del /F /S /Q ' + path
    os.system(cmd_del)

    logger.info("import finished:{}", str_day)


def trans_one_day_trade_data(str_day, db1, db2):
    db_export(db1, str_day)
    db_import(db2, str_day)


def sync_col_move(str_day):
    query_trade_day = {"trade_date": str_day}
    if mongodb_util.exist_data_query('trade_date_list', query_trade_day):
        try:
            db_export('127.0.0.1:27017', str_day)
            db_import('127.0.0.1:27019', str_day)
            delete_exist_data(str_day)
        except BaseException as e:
            logger.error("备份数据出现错误:{}", e)


def delete_exist_data(str_day):
    query_trade_day = {"trade_date": str_day}
    if mongodb_util.exist_data_query('trade_date_list', query_trade_day):
        # 删除27017中最早一天的实时数据
        query = {"tag": False}
        trade_date_one = mongodb_util.ascend_query(query, 'trade_date_list', 'trade_date', 1)
        trade_date = list(trade_date_one['trade_date'])[0]
        db_name = 'realtime_quotes_now_' + trade_date
        mongodb_util.drop_collection(db_name)

        query_date = {'trade_date': trade_date}
        new_values = {"$set": {"tag": True}}
        mongodb_util.update_many(query_date, new_values, 'trade_date_list')

        return trade_date_one


def db_export_col(db, col):
    cmd = 'F:/mongo/bin/mongodump.exe --host ' + db + ' -d patience -c ' + col + ' -o H:/back'
    os.system(cmd)
    logger.info("export finished:{}")
    os.system(cmd)

    logger.info("export finished:{}", col)


# D:\software\mongodb-tools\mongodb-database-tools-windows-x86_64-100.5.2\bin
def db_import_col(db, col):
    cmd = 'F:/mongo/bin/mongodump.exe --host ' + db + ' -d patience -c ' + col + ' H:/back/patience/' + col + '.bson'
    os.system(cmd)

    logger.info("import finished:{}", col)


# -u "username" -p "password"
if __name__ == '__main__':
    query_trade = {"$and": [{"trade_date": {"$gte": "2024-09-24"}}, {"trade_date": {"$lte": "2024-10-22"}}]}

    trade_date_list = mongodb_util.find_query_data('trade_date_list', query_trade)
    for trade_one in trade_date_list.itertuples():
        trade_date_move = trade_one.trade_date
        sync_col_move(trade_date_move)

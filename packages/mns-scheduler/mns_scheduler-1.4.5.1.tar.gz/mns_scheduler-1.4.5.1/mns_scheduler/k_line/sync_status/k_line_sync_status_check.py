import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
from datetime import datetime
import mns_common.component.trade_date.trade_date_common_service_api as trade_date_common_service_api
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant
import mns_common.utils.date_handle_util as date_handle_util
import mns_common.api.msg.push_msg_api as push_msg_api

mongodb_util = MongodbUtil('27017')

min_k_line_count = 5200


# check下一个交易日k线同步状态
def check_k_line_sync_count():
    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    hour = now_date.hour
    # 是否是交易日
    if trade_date_common_service_api.is_trade_day(str_day):
        if hour > 15:
            qfq_day = str_day
            k_line_day = trade_date_common_service_api.get_further_trade_date(str_day, 2)
        else:
            qfq_day = trade_date_common_service_api.get_last_trade_day(str_day)
            k_line_day = str_day
    else:
        qfq_day = trade_date_common_service_api.get_last_trade_day(str_day)
        k_line_day = trade_date_common_service_api.get_further_trade_date(str_day, 1)

    # check 当日k线同步状态
    query_qfq = {'date': date_handle_util.no_slash_date(qfq_day)}
    qfq_k_line_count = mongodb_util.count(query_qfq, db_name_constant.STOCK_QFQ_DAILY)
    if qfq_k_line_count < min_k_line_count:
        title = '当日k线同步数量不对'
        msg = '当日k线同步数量不对,当前k线数量:' + str(qfq_k_line_count)
        push_msg_api.push_msg_to_wechat(title, msg)

    query_last_trade = {'str_day': k_line_day}
    last_trade_day_k_line_count = mongodb_util.count(query_last_trade, 'k_line_info')
    if last_trade_day_k_line_count < min_k_line_count:
        title = '下一个交易日策略k线数量不对'
        msg = '下一个交易日策略k线数量不对,当前数量:' + str(last_trade_day_k_line_count)
        push_msg_api.push_msg_to_wechat(title, msg)


if __name__ == '__main__':
    check_k_line_sync_count()

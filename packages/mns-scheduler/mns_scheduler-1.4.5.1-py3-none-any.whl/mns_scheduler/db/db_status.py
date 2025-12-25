import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.msg.push_msg_api as push_msg_api
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')
from loguru import logger
import mns_common.utils.ip_util as ip_util


def db_status_check():
    try:
        query = {'symbol': '000001'}
        mongodb_util.find_query_data('company_info', query)
    except BaseException as e:
        ip = ip_util.get_host_ip()
        push_msg_api.push_msg_to_wechat("数据库挂了", "地址:" + ip + "-" + "数据库挂了")
        logger.error("出现异常:{}", e)


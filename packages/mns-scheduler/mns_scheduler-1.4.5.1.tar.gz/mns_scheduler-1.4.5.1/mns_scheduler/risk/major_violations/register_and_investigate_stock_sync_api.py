import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import pandas as pd
from datetime import datetime
import mns_common.component.self_choose.black_list_service_api as black_list_service_api
import mns_common.utils.date_handle_util as date_handle_util
from loguru import logger
import mns_common.constant.db_name_constant as db_name_constant
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util
from mns_common.constant.black_list_classify_enum import BlackClassify

mongodb_util = MongodbUtil('27017')
import mns_common.component.company.company_common_service_new_api as company_common_service_new_api


# 立案调查股票
# http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search&lastPage=index

def sync_investigate_stocks_api(page_num, page_size, search_key, begin_day, end_day):
    url = ('http://www.cninfo.com.cn/new/hisAnnouncement/query?'
           'pageNum=' + str(page_num) +
           '&pageSize=' + str(page_size) +
           '&column=szse&tabName=fulltext&plate=&stock=&searchkey=' + search_key +
           '&secid=&category=&trade=&seDate=' + begin_day +
           '~' + end_day +
           '&sortName=&sortType=&isHLtitle=true')

    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post(url, headers=headers)
    data_json = r.json()
    total_record_num = data_json['totalRecordNum']
    data_list = data_json['announcements']
    data_df = pd.DataFrame(data_list)
    result = {'total_record_num': total_record_num,
              'data_df': data_df}
    return result


def sync_all_investigate_stocks(page_size, search_key, begin_day, end_day):
    page_num = 1
    data_result_df = None
    while True:
        result = sync_investigate_stocks_api(page_num, page_size, search_key, begin_day, end_day)
        data_df = result['data_df']
        if data_result_df is None:
            data_result_df = data_df
        else:
            data_result_df = pd.concat([data_df, data_result_df])

        if data_df.shape[0] < page_size:
            break
        page_num = page_num + 1
    return data_result_df


# 立案调查的股票
def sync_register_and_investigate_stocks():
    before_days = 60
    const_num = 30
    init_date = datetime.now()
    str_day = init_date.strftime('%Y-%m-%d')
    # 过去30天新增风险股票
    begin_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_day), -before_days)
    begin_day = begin_date.strftime('%Y-%m-%d')
    search_key = '立案'

    end_date = date_handle_util.add_date_day(date_handle_util.no_slash_date(str_day), 1)
    end_day = end_date.strftime('%Y-%m-%d')
    new_high_risk_stocks_df = sync_all_investigate_stocks(const_num, search_key, begin_day, end_day)
    if data_frame_util.is_empty(new_high_risk_stocks_df):
        return None
    new_high_risk_stocks_df = new_high_risk_stocks_df.sort_values(by=['announcementTime'], ascending=False)
    de_list_company_symbols = company_common_service_new_api.get_de_list_company()
    for high_risk_stocks_one in new_high_risk_stocks_df.itertuples():
        try:
            symbol = high_risk_stocks_one.secCode
            if symbol in de_list_company_symbols:
                continue
            announcement_id = high_risk_stocks_one.announcementId

            key_id = symbol + "_" + str(announcement_id)
            query_exist = {"_id": key_id}
            if mongodb_util.exist_data_query(db_name_constant.SELF_BLACK_STOCK,
                                             query_exist):
                continue
            else:
                announcement_time = high_risk_stocks_one.announcementTime
                # 将毫秒转换为秒
                seconds = announcement_time // 1000
                # 使用datetime模块从秒转换为日期
                announce_date = datetime.fromtimestamp(seconds)
                announce_str_day = announce_date.strftime('%Y-%m-%d')
                announce_time = announce_date.strftime('%Y-%m-%d %H:%M:%S')
                announce_url = ('http://www.cninfo.com.cn/new/disclosure/detail?stockCode=' + str(symbol) +
                                '&announcementId=' + str(announcement_id) +
                                '&orgId=' + str(high_risk_stocks_one.orgId) +
                                '&announcementTime=' + announce_str_day)

                black_list_service_api.save_black_stock(
                    key_id,
                    symbol,
                    high_risk_stocks_one.secName,
                    announce_str_day,
                    announce_time,
                    high_risk_stocks_one.announcementTitle,
                    high_risk_stocks_one.announcementTitle,
                    announce_url,
                    BlackClassify.MAJOR_VIOLATIONS.up_level_code,
                    BlackClassify.MAJOR_VIOLATIONS.up_level_name,
                    BlackClassify.REGISTER_INVESTIGATE.level_code,
                    BlackClassify.REGISTER_INVESTIGATE.level_name,
                )
        except Exception as e:
            logger.error("保存风险警示股票异常:{},{}", symbol, e)


if __name__ == '__main__':
    sync_register_and_investigate_stocks()
    # result_df = sync_all_investigate_stocks(30, '立案', '2023-01-01', '2024-06-15')
    # result_df = result_df.sort_values(by=['announcementTime'], ascending=False)
    # print(result_df)

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
# !/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Date: 2023/8/4 19:20
Desc: 上证e互动-提问与回答
https://sns.sseinfo.com/
"""
import warnings
import pandas as pd
import requests
from bs4 import BeautifulSoup
from mns_common.db.MongodbUtil import MongodbUtil

mongodb_util = MongodbUtil('27017')


def stock_sns_sse_info(org_ask_id,
                       page,
                       page_size) -> pd.DataFrame:
    """
    上证e互动-提问与回答
    https://sns.sseinfo.com/company.do?uid=65
    :param symbol: 股票代码
    :type symbol: str
    :return: 提问与回答
    :rtype: str
    """

    url = "https://sns.sseinfo.com/ajax/userfeeds.do"
    params = {
        "typeCode": "company",
        "type": "11",
        "pageSize": str(page_size),
        "uid": org_ask_id,
        "page": str(page),
    }
    big_df = pd.DataFrame()
    page = 1
    warnings.warn("正在下载中")
    params.update({"page": page})
    r = requests.post(url, params=params)
    if len(r.text) < 300:
        return None
    r = requests.post(url, params=params)
    soup = BeautifulSoup(r.text, "lxml")
    content_list = [
        item.get_text().strip()
        for item in soup.find_all("div", attrs={"class": "m_feed_txt"})
    ]
    date_list = [
        item.get_text().strip().split("\n")[0]
        for item in soup.find_all("div", attrs={"class": "m_feed_from"})
    ]
    source_list = [
        item.get_text().strip().split("\n")[2]
        for item in soup.find_all("div", attrs={"class": "m_feed_from"})
    ]
    q_list = [
        item.split(")")[1]
        for index, item in enumerate(content_list)
        if index % 2 == 0
    ]
    stock_name = [
        item.split("(")[0].strip(":")
        for index, item in enumerate(content_list)
        if index % 2 == 0
    ]
    stock_code = [
        item.split("(")[1].split(")")[0]
        for index, item in enumerate(content_list)
        if index % 2 == 0
    ]
    a_list = [item for index, item in enumerate(content_list) if index % 2 != 0]
    d_q_list = [item for index, item in enumerate(date_list) if index % 2 == 0]
    d_a_list = [item for index, item in enumerate(date_list) if index % 2 != 0]
    s_q_list = [item for index, item in enumerate(source_list) if index % 2 == 0]
    s_a_list = [item for index, item in enumerate(source_list) if index % 2 != 0]
    author_name = [
        item["title"] for item in soup.find_all("a", attrs={"rel": "face"})
    ]
    temp_df = pd.DataFrame(
        [
            stock_code,
            stock_name,
            q_list,
            a_list,
            d_q_list,
            d_a_list,
            s_q_list,
            s_a_list,
            author_name,
        ]
    ).T
    temp_df.columns = [
        "股票代码",
        "公司简称",
        "问题",
        "回答",
        "问题时间",
        "回答时间",
        "问题来源",
        "回答来源",
        "用户名",
    ]
    big_df = pd.concat([big_df, temp_df], ignore_index=True)
    return big_df


if __name__ == "__main__":
    stock_sns_sse_info_df = stock_sns_sse_info('308', '2', '100')
    print(stock_sns_sse_info_df)

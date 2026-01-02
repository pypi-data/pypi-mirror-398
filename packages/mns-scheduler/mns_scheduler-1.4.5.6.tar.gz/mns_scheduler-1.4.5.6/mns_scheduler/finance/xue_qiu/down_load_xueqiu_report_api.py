import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import requests
import pandas as pd
from loguru import logger


# report_type income 利润表
# cash_flow 现金流量
# balance 资产负债


def get_xue_qiu_report(symbol, report_type, cookie, count, period_type):
    # 请求 URL
    url = (f"https://stock.xueqiu.com/v5/stock/finance/cn/{report_type}.json?symbol={symbol}&type={period_type}"
           f"&is_detail=true&count={count}")

    # 请求头（关键是 cookies）
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "origin": "https://xueqiu.com",
        "referer": f"https://xueqiu.com/snowman/S/{symbol}/detail",
        "sec-fetch-mode": "cors",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        # ⚠ 替换为你浏览器访问雪球后的 Cookie（需含 xq_a_token）
        "cookie": cookie,
    }

    # 发送请求
    response = requests.get(url, headers=headers)

    # 检查结果
    if response.status_code == 200:
        data = response.json()

        # 提取财报数据列表
        raw_list = data['data']['list']
        processed_list = []

        for entry in raw_list:
            flat_entry = {}
            for key, value in entry.items():
                if isinstance(value, list) and len(value) == 2:
                    # 处理列表字段：提取两个值，空则填 0
                    v0 = value[0] if value[0] is not None else 0
                    v1 = value[1] if value[1] is not None else 0
                    flat_entry[key] = v0
                    flat_entry[key + "_chg"] = round(v1 * 100, 2)
                elif value is None:
                    # 整个字段为空，设置为 0 和 0（变化量）
                    flat_entry[key] = 0
                else:
                    flat_entry[key] = value
            processed_list.append(flat_entry)

        # 转换为 DataFrame
        df = pd.DataFrame(processed_list)
        return df

    else:
        logger.error("请求失败，状态码:{}", response.status_code)
        return pd.DataFrame()


import mns_common.component.cookie.cookie_info_service as cookie_info_service

if __name__ == '__main__':
    cash_flow_df = get_xue_qiu_report('SZ301662', 'cash_flow', cookie_info_service.get_xue_qiu_cookie(), 1, 'all')
    income_df = get_xue_qiu_report('SZ301662', 'income', cookie_info_service.get_xue_qiu_cookie(), 1, 'all')
    balance_df = get_xue_qiu_report('SZ301662', 'balance', cookie_info_service.get_xue_qiu_cookie(), 1, 'all')
    pass

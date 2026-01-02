import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

import akshare as ak

# 当天龙虎榜股票
stock_lhb_detail_em_df = ak.stock_lhb_detail_em(start_date="20240520", end_date="20240522")
print(stock_lhb_detail_em_df)

# 000560 某只股票当天龙虎榜详情
stock_lhb_stock_detail_em_df = ak.stock_lhb_stock_detail_em(symbol="600383", date="20240521", flag="买入")
stock_lhb_stock_detail_em_df = ak.stock_lhb_stock_detail_em(symbol="600383", date="20240521", flag="卖出")
print(stock_lhb_stock_detail_em_df)

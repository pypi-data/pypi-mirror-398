import sys
import os

import mns_common.api.kpl.selection.kpl_selection_plate_api as selection_plate_api
from mns_common.db.MongodbUtil import MongodbUtil
from datetime import datetime
import mns_common.utils.data_frame_util as data_frame_util

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)

mongodb_util = MongodbUtil('27017')
choose_field = [
    '_id',
    'symbol',
    'name',
    'plate_code',
    'plate_name',
    'first_plate_code',
    'first_plate_name',
    'index_class',
    'most_relative_name',
    'plate_name_list',
    'you_zi',
    'now_price',
    'chg',
    'amount',
    'exchange',
    'speed',
    'real_flow_mv',
    'main_flow_in',
    'main_flow_out',
    'main_flow_net',
    # 卖流占比
    'sell_radio',
    'chg_from_chg',
    'connected_boards',
    'dragon_index',
    'closure_funds',
    'max_closure_funds',
    'total_mv',
    'flow_mv',
    'most_relative_name',
    "sync_str_day",
    "sync_str_time",
    "index_class",
    "create_day",
    "create_time"
]


# 更新次级指数详细组成
def save_one_plate_detail_data(plate_code, plate_name, index_class, first_plate_code,
                               first_plate_name):
    kpl_best_choose_index_detail = selection_plate_api.best_choose_stock(plate_code)
    if data_frame_util.is_empty(kpl_best_choose_index_detail):
        return None
    kpl_best_choose_index_detail = kpl_best_choose_index_detail[[
        'symbol',
        'name',
        'plate_name_list',
        'you_zi',
        'now_price',
        'chg',
        'amount',
        'exchange',
        'speed',
        'real_flow_mv',
        'main_flow_in',
        'main_flow_out',
        'main_flow_net',
        # 卖流占比
        'sell_radio',
        'chg_from_chg',
        'connected_boards',
        'dragon_index',
        'closure_funds',
        'max_closure_funds',
        'total_mv',
        'flow_mv',
        'most_relative_name'
    ]].copy()
    kpl_best_choose_index_detail['_id'] = kpl_best_choose_index_detail['symbol'] + "-" + plate_code

    kpl_best_choose_index_detail['plate_code'] = plate_code

    kpl_best_choose_index_detail['plate_name'] = plate_name

    kpl_best_choose_index_detail['first_plate_code'] = first_plate_code

    kpl_best_choose_index_detail['first_plate_name'] = first_plate_name

    now_date = datetime.now()
    str_day = now_date.strftime('%Y-%m-%d')
    str_now_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    kpl_best_choose_index_detail['sync_str_day'] = str_day
    kpl_best_choose_index_detail['sync_str_time'] = str_now_date
    kpl_best_choose_index_detail['index_class'] = index_class

    query = {"plate_code": plate_code}

    exist_code_df = mongodb_util.find_query_data_choose_field('kpl_best_choose_index_detail',
                                                              query,
                                                              {
                                                                  "create_day": 1,
                                                                  "symbol": 1,
                                                                  "create_time": 1})

    if data_frame_util.is_empty(exist_code_df):
        new_df = kpl_best_choose_index_detail
    else:
        del exist_code_df['_id']
        exist_symbol_list = list(exist_code_df['symbol'])
        new_df = kpl_best_choose_index_detail.loc[~(kpl_best_choose_index_detail['symbol'].isin(exist_symbol_list))]
    if data_frame_util.is_not_empty(new_df):
        # 这个时间和sync时间一样
        new_df['create_day'] = str_day
        new_df['create_time'] = str_now_date
        new_df = new_df[choose_field]
        new_df['grade'] = 1
        new_df['remark'] = ''
        new_df['remark_flag'] = ''
        new_df['long'] = ''
        mongodb_util.insert_mongo(new_df, 'kpl_best_choose_index_detail')

        # 保存到当日新增概念列表
        new_df['concept_type'] = 'kpl'
        mongodb_util.save_mongo(new_df, 'today_new_concept_list')

    # if data_frame_util.is_not_empty(exist_code_df):
    #     exist_df = kpl_best_choose_index_detail.loc[(kpl_best_choose_index_detail['symbol'].isin(exist_symbol_list))]
    #     exist_df = exist_df.set_index(['symbol'], drop=False)
    #     exist_code_df = exist_code_df.set_index(['symbol'], drop=True)
    #
    #     exist_df = pd.merge(exist_df, exist_code_df, how='outer',
    #                         left_index=True, right_index=True)
    #     mongodb_util.save_mongo(exist_df, 'kpl_best_choose_index_detail')

import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.utils.data_frame_util as data_frame_util

mongodb_util = MongodbUtil('27017')


# 修改行业分类的股票
def get_fix_symbol_industry():
    return pd.DataFrame([
        ['688480', '赛恩斯', '760103', '环境治理'],

        ['603260', '合盛硅业', '220316', '有机硅'],
        ['300559', '佳发教育', '461102', '培训教育'],

        ['600338', '西藏珠峰', '240303', '铅锌'],

        ['688507', '索辰科技', '710402', '横向通用软件'],
        ['301387', '光大同创', '270504', '消费电子零部件及组装'],
        ['300295', '三六五网', '430301', '物业管理'],
        ['300947', '德必集团', '430301', '物业管理'],
        ['300483', '首华燃气', '410301', '燃气Ⅲ'],
        ['300215', '电科院', '410110', '电能综合服务'],
        # 持有上海微电子装备有限公司10%的股份 国产光刻机 主要炒作在芯片概念 不在房地产

        ['300836', '佰奥智能', '640701', '机器人'],
        ['300293', '蓝英装备', '640701', '机器人'],
        ['301112', '信邦智能', '640704', '其他自动化设备'],



        ['000670', '盈方微', '270401', '其他电子'],

        ['300803', '指南针', '490101', '证券'],
        ['300085', '银之杰', '490101', '证券'],
        ['300380', '安硕信息', '490101', '证券'],
        ['600446', '金证股份', '490101', '证券'],
        ['688318', '财富趋势', '490101', '证券'],
        ['600570', '恒生电子', '490101', '证券'],
        ['837592', '华信永道', '490101', '证券'],
        ['830799', '艾融软件', '490101', '证券'],
        ['300033', '同花顺', '490101', '证券'],
        ['300399', '天利科技', '490201', '保险'],

        ['002131', '利欧股份', '720501', '营销代理'],

        ['300042', '朗科科技', '270108', '半导体设备'],
        # EDA软件
        ['301269', '华大九天', '270108', '半导体设备'],
        ['688206', '概伦电子', '270108', '半导体设备'],
        ['301095', '广立微', '270108', '半导体设备'],
        ['600895', '张江高科', '270108', '半导体设备'],

        ['688630', '芯碁微装', '270108', '半导体设备'],
        ['001309', '德明利', '270104', '数字芯片设计'],
        ['688795', '摩尔线程', '270104', '数字芯片设计'],

    ],
        columns=['symbol',
                 'name',
                 'new_industry_code',  # 三级行业代码
                 'new_industry'])


# 修改二级行业分类的股票
def get_fix_second_industry_info():
    return pd.DataFrame([
        ['110200', '渔业', "农林牧渔", "110000", '农业综合Ⅱ', '110900'],

        ['110300', '林业', "农林牧渔", "110000", '农业综合Ⅱ', '110900'],

        ['450700', '旅游零售Ⅱ', '社会服务', '460000', '旅游及景区', '461000'],

        ['220700', '化工新材料Ⅱ', '基础化工', '220000', '非金属材料Ⅱ', '220900'],

        ['330700', '其他家电Ⅱ', '家用电器', '330000', '小家电', '330300'],

        ['250100', '建筑材料', '建筑材料', '610000', '装修建材', '610300'],

        ['460600', '体育Ⅱ', '综合', '510000', '综合Ⅱ', '510100'],

        ['770300', '医疗美容', '美容护理', '770000', '化妆品', '770200'],

    ],
        columns=['original_second_industry_code',
                 'original_second_industry_name',
                 'first_sw_industry',
                 'first_industry_code',
                 'second_sw_industry',  # 二级级行业代码
                 'second_industry_code'])


def fix_second_industry(company_info):
    fix_second_industry_df = get_fix_second_industry_info()
    del fix_second_industry_df['original_second_industry_name']
    fix_second_company_df = company_info.loc[
        company_info['second_industry_code'].isin(fix_second_industry_df['original_second_industry_code'])]

    no_fix_second_company_df = company_info.loc[~(
        company_info['second_industry_code'].isin(fix_second_industry_df['original_second_industry_code']))]

    fix_second_company_df = fix_second_company_df.set_index(['second_industry_code'], drop=True)
    del fix_second_company_df['second_sw_industry']
    del fix_second_company_df['first_industry_code']
    del fix_second_company_df['first_sw_industry']
    fix_second_industry_df = fix_second_industry_df.set_index(['original_second_industry_code'], drop=True)

    fix_second_company_df = pd.merge(fix_second_company_df, fix_second_industry_df, how='outer',
                                     left_index=True, right_index=True)

    return pd.concat([no_fix_second_company_df, fix_second_company_df])


# 修改行业名
def get_fix_industry_name_df():
    return pd.DataFrame([

        # 交通运输 1
        ['物流', '物流'],
        ['铁路公路', '铁路公路'],
        ['航运港口', '航运港口'],
        ['航空机场', '航空机场'],

        # 传媒 2
        ['数字媒体', '数字媒体'],
        ['电视广播Ⅱ', '电视广播'],
        ['游戏Ⅱ', '游戏'],
        ['出版', '出版'],
        ['影视院线', '影视院线'],
        ['广告营销', '广告营销'],

        # 公用事业 3
        ['燃气Ⅱ', '燃气'],
        ['电力', '电力'],

        # 农林牧渔 4
        ['养殖业', '养殖业'],
        ['农产品加工', '农产品加工'],
        ['饲料', '饲料'],
        ['渔业', '渔业'],  # merge  to 农业综合
        ['动物保健Ⅱ', '动物保健'],
        ['种植业', '种植业'],
        # ['林业Ⅱ', '林业'],  # merge  农业综合
        ['农业综合Ⅱ', '农业综合'],  #

        # 医药生物 5
        ['化学制药', '化学制药'],
        ['生物制品', '生物制品'],
        ['中药Ⅱ', '中药'],
        ['医疗器械', '医疗器械'],
        ['医疗服务', '医疗服务'],
        ['医药商业', '医药商业'],

        # 商贸零售 6
        ['一般零售', '一般零售'],
        ['互联网电商', '互联网电商'],
        ['贸易Ⅱ', '贸易'],  #
        ['专业连锁Ⅱ', '零售专业连锁'],  # 专业连锁 综合Ⅱ
        # ['旅游零售Ⅱ', '旅游零售'],  # merge旅游及景区

        # 国防 7
        ['军工电子Ⅱ', '军工电子'],
        ['地面兵装Ⅱ', '地面兵装'],
        ['航天装备Ⅱ', '航天装备'],
        ['航空装备Ⅱ', '航空装备'],
        ['航海装备Ⅱ', '航海装备'],

        # 基础化工 8
        ['化学制品', '化学制品'],
        ['化学原料', '化学原料'],
        ['化学纤维', '化学纤维'],
        ['农化制品', '化肥农药'],
        ['塑料', '塑料'],
        ['橡胶', '橡胶'],
        ['非金属材料Ⅱ', '非金属材料'],

        # 家用电器 9
        ['白色家电', '白色家电'],  # merge 家用电器
        ['照明设备Ⅱ', '照明设备'],  # merge 家用电器
        # ['其他家电Ⅱ', '其他家电'],  # merge  小家电
        ['家电零部件Ⅱ', '家电零部件'],  # merge 家用电器
        ['小家电', '小家电'],  # merge '家用电器'
        ['黑色家电', '黑色家电'],  # merge 家用电器
        ['厨卫电器', '厨卫电器'],  # merge   家用电器

        # 建筑材料  10
        ['装修建材', '装修建材'],  #
        ['建筑建材', '装修建材'],  #
        ['玻璃玻纤', '玻璃玻纤'],
        ['水泥', '水泥'],

        # 建筑装饰 11
        ['基础建设', '基础建设'],
        ['房屋建设Ⅱ', '房屋建设'],
        ['工程咨询服务Ⅱ', '工程咨询服务'],
        ['专业工程', '建筑专业工程'],
        ['装修装饰Ⅱ', '装修装饰'],

        # 房地产 12
        ['房地产开发', '房地产'],
        ['房地产服务', '房地产'],

        # 有色金属 13
        ['能源金属', '能源金属'],
        ['小金属', '小金属'],
        ['贵金属', '贵金属'],  #
        ['金属新材料', '金属新材料'],
        ['工业金属', '工业金属'],  # 铅锌  铝  铜

        # 机械设备 14
        ['自动化设备', '自动化设备'],
        ['轨交设备Ⅱ', '轨交设备'],
        ['通用设备', '通用设备'],
        ['专用设备', '专用设备'],
        ['工程机械', '工程机械'],

        # 汽车 15
        ['汽车零部件', '汽车零部件'],
        ['汽车服务', '汽车服务'],
        ['乘用车', '乘用车'],  # = merge 汽车整车
        ['商用车', '商用车'],
        ['摩托车及其他', '摩托车及其他'],

        # 煤炭 16
        ['焦炭Ⅱ', '焦炭'],  # merge  to 煤炭
        ['煤炭开采', '煤炭开采'],  # merge 煤炭

        # 环保 17
        ['环境治理', '环境治理'],  # merge, 环保
        ['环保设备Ⅱ', '环保设备'],  # merge '环保'

        # 电力设备 18
        ['电网设备', '电网设备'],
        ['电池', '电池'],
        ['电机Ⅱ', '电机'],  #
        ['光伏设备', '光伏设备'],
        ['风电设备', '风电设备'],
        ['其他电源设备Ⅱ', '其他电源设备'],

        # 电子 19
        ['半导体', '半导体'],
        ['电子化学品Ⅱ', '电子化学品'],
        ['光学光电子', '光学光电子'],
        ['消费电子', '消费电子'],
        ['元件', '元件'],
        ['其他电子Ⅱ', '其他电子'],  #

        # 石油石化 20
        ['炼化及贸易', '石油行业'],  # merge 石油行业
        ['油服工程', '采掘行业'],  # merge '采掘行业'
        ['油气开采Ⅱ', '石油行业'],  # merge  to 石油行业

        # 社会服务 21
        ['专业服务', '社会专业服务'],
        ['旅游及景区', '旅游及景区'],
        ['酒店餐饮', '旅游酒店'],
        ['教育', '教育'],
        # ['体育Ⅱ', '体育'],

        # 纺织服装 22
        ['服装家纺', '纺织服装'],  # merge 纺织服装
        ['纺织制造', '纺织服装'],  # merge 纺织服装
        ['饰品', '饰品'],

        # 综合 23
        ['综合Ⅱ', '综合'],

        # 美容护理 24
        ['化妆品', '化妆美容'],  # merge  to 化妆美容
        # ['医疗美容', '化妆美容'],  # merge  化妆美容
        ['个护用品', '个护用品'],

        # 计算机 25
        ['计算机设备', '计算机设备'],
        ['IT服务Ⅱ', 'IT服务'],
        ['软件开发', '软件开发'],

        # 轻工制造 26
        ['造纸', '造纸'],
        ['包装印刷', '包装印刷'],  #
        ['文娱用品', '文娱用品'],  #
        ['家居用品', '家居用品'],

        # 通信 27
        ['通信服务', '通信服务'],
        ['通信设备', '通信设备'],

        #  钢铁 28
        ['普钢', '普钢'],  #
        ['特钢Ⅱ', '特钢'],
        ['冶钢原料', '冶钢原料'],

        # 银行 29
        ['国有大型银行Ⅱ', '银行'],  # merge  to 银行
        ['城商行Ⅱ', '银行'],  #
        ['农商行Ⅱ', '银行'],  # merge   银行
        ['股份制银行Ⅱ', '银行'],  # merge  to 银行

        # 非银金融  30
        ['证券Ⅱ', '证券'],
        ['保险Ⅱ', '保险'],
        ['多元金融', '多元金融'],

        # 食品饮料 31
        ['饮料乳品', '饮料乳品'],  # merge 食品饮料
        ['食品加工', '食品加工'],  # merge 食品饮料
        ['调味发酵品Ⅱ', '调味发酵品'],  # merge  to  食品饮料
        ['休闲食品', '休闲食品'],  # merge '食品饮料'
        ['白酒Ⅱ', '白酒'],
        ['非白酒', '非白酒']

    ], columns=['second_sw_industry', 'industry'])


# 第三行业作为行业
def fix_industry_use_sw_third(company_info_df):
    # 细分工业金属行业
    company_info = company_info_df.copy()
    company_info.loc[company_info.third_industry_code == '240303', 'industry'] = '铅锌'
    company_info.loc[company_info.third_industry_code == '240301', 'industry'] = '铝'
    company_info.loc[company_info.third_industry_code == '240302', 'industry'] = '铜'

    company_info.loc[company_info.third_industry_code == '240303', 'second_sw_industry'] = '铅锌'
    company_info.loc[company_info.third_industry_code == '240301', 'second_sw_industry'] = '铝'
    company_info.loc[company_info.third_industry_code == '240302', 'second_sw_industry'] = '铜'

    company_info.loc[company_info.third_industry_code == '240303', 'second_industry_code'] = '240303'
    company_info.loc[company_info.third_industry_code == '240301', 'second_industry_code'] = '240301'
    company_info.loc[company_info.third_industry_code == '240302', 'second_industry_code'] = '240302'

    # 细分专业设备
    company_info.loc[company_info.third_industry_code == '640203', 'industry'] = '能源及重型设备'
    company_info.loc[company_info.third_industry_code == '640204', 'industry'] = '楼宇设备'
    company_info.loc[company_info.third_industry_code == '640206', 'industry'] = '纺织服装设备'
    company_info.loc[company_info.third_industry_code == '640207', 'industry'] = '农用机械'
    company_info.loc[company_info.third_industry_code == '640208', 'industry'] = '印刷包装机械'

    company_info.loc[company_info.third_industry_code == '640203', 'second_sw_industry'] = '能源及重型设备'
    company_info.loc[company_info.third_industry_code == '640204', 'second_sw_industry'] = '楼宇设备'
    company_info.loc[company_info.third_industry_code == '640206', 'second_sw_industry'] = '纺织服装设备'
    company_info.loc[company_info.third_industry_code == '640207', 'second_sw_industry'] = '农用机械'
    company_info.loc[company_info.third_industry_code == '640208', 'second_sw_industry'] = '印刷包装机械'

    company_info.loc[company_info.third_industry_code == '640203', 'second_industry_code'] = '640203'
    company_info.loc[company_info.third_industry_code == '640204', 'second_industry_code'] = '640204'
    company_info.loc[company_info.third_industry_code == '640206', 'second_industry_code'] = '640206'
    company_info.loc[company_info.third_industry_code == '640207', 'second_industry_code'] = '640207'
    company_info.loc[company_info.third_industry_code == '640208', 'second_industry_code'] = '640208'

    # todo 细分
    company_info.loc[company_info.third_industry_code == '640209', 'industry'] = '专用设备'
    company_info.loc[company_info.third_industry_code == '640209', 'second_sw_industry'] = '专用设备'
    company_info.loc[company_info.third_industry_code == '640209', 'second_industry_code'] = '640208'

    company_info.loc[company_info.third_industry_code == '260205', 'industry'] = '专用设备'
    company_info.loc[company_info.third_industry_code == '260205', 'second_sw_industry'] = '专用设备'
    company_info.loc[company_info.third_industry_code == '260205', 'second_industry_code'] = '260205'

    # 细分通用设备
    company_info.loc[company_info.third_industry_code == '640101', 'industry'] = '机床工具'
    company_info.loc[company_info.third_industry_code == '640103', 'industry'] = '磨具磨料'
    company_info.loc[company_info.third_industry_code == '640105', 'industry'] = '制冷空调设备'
    company_info.loc[company_info.third_industry_code == '640106', 'industry'] = '通用设备'
    company_info.loc[company_info.third_industry_code == '640107', 'industry'] = '仪器仪表'
    company_info.loc[company_info.third_industry_code == '640108', 'industry'] = '金属制品'

    company_info.loc[company_info.third_industry_code == '640101', 'second_sw_industry'] = '机床工具'
    company_info.loc[company_info.third_industry_code == '640103', 'second_sw_industry'] = '磨具磨料'
    company_info.loc[company_info.third_industry_code == '640105', 'second_sw_industry'] = '制冷空调设备'
    company_info.loc[company_info.third_industry_code == '640106', 'second_sw_industry'] = '通用设备'
    company_info.loc[company_info.third_industry_code == '640107', 'second_sw_industry'] = '仪器仪表'
    company_info.loc[company_info.third_industry_code == '640108', 'second_sw_industry'] = '金属制品'

    company_info.loc[company_info.third_industry_code == '640101', 'second_industry_code'] = '640101'
    company_info.loc[company_info.third_industry_code == '640103', 'second_industry_code'] = '640103'
    company_info.loc[company_info.third_industry_code == '640105', 'second_industry_code'] = '640105'
    company_info.loc[company_info.third_industry_code == '640106', 'second_industry_code'] = '640106'
    company_info.loc[company_info.third_industry_code == '640107', 'second_industry_code'] = '640107'
    company_info.loc[company_info.third_industry_code == '640108', 'second_industry_code'] = '640108'

    return company_info


def find_sw_third_industry(new_third_industry_code):
    sw_third_industry = mongodb_util.find_query_data('sw_industry', query={"_id": new_third_industry_code})
    first_sw_industry_name = list(sw_third_industry['first_sw_industry'])[0]
    second_sw_industry_name = list(sw_third_industry['second_sw_industry'])[0]

    first_sw_industry = mongodb_util.find_query_data('sw_industry', query={'first_sw_industry': first_sw_industry_name,
                                                                           "second_sw_industry": 0,
                                                                           "third_sw_industry": 0
                                                                           })

    second_sw_industry = mongodb_util.find_query_data('sw_industry',
                                                      query={'second_sw_industry': second_sw_industry_name,
                                                             "third_sw_industry": 0
                                                             })

    sw_third_industry['first_industry_code'] = first_sw_industry['_id']
    sw_third_industry['second_industry_code'] = second_sw_industry['_id']
    return sw_third_industry


# 修改行业信息
def fix_industry_data(new_third_industry_code, company_info):
    sw_industry = find_sw_third_industry(new_third_industry_code)
    company_info['first_sw_industry'] = list(sw_industry['first_sw_industry'])[0]
    company_info['first_industry_code'] = list(sw_industry['industry_code'])[0]
    company_info['second_sw_industry'] = list(sw_industry['second_sw_industry'])[0]
    company_info['second_industry_code'] = list(sw_industry['second_industry_code'])[0]
    company_info['third_sw_industry'] = list(sw_industry['third_sw_industry'])[0]
    company_info['third_industry_code'] = list(sw_industry['industry_code'])[0]
    return company_info


# 手动修改股票行业代码
def fix_symbol_industry(company_info, symbol):
    fix_symbol_df = get_fix_symbol_industry()
    fix_symbol_df_one = fix_symbol_df.loc[fix_symbol_df['symbol'] == symbol]
    if data_frame_util.is_not_empty(fix_symbol_df_one):
        new_third_industry_code = list(fix_symbol_df_one['new_industry_code'])[0]
        company_info = fix_industry_data(new_third_industry_code, company_info)

    return company_info


def filed_sort(company_info):
    return company_info[[
        "_id",
        "name",
        "industry",
        "first_sw_industry",
        "first_industry_code",
        "second_sw_industry",
        "second_industry_code",
        "third_sw_industry",
        "third_industry_code",
        "ths_concept_name",
        "ths_concept_code",
        "ths_concept_sync_day",
        "em_industry",
        "em_concept",
        "business_nature",
        "actual_controller_name",
        "actual_controller_rate",
        "final_controller_name",
        "final_controller_rate",
        "mv_circulation_ratio",
        'qfii_type',
        'qfii_number',
        'share_holder_sync_day',
        "flow_mv_sp",
        "total_mv_sp",
        "now_price",
        "total_share",
        "flow_share",
        "total_mv",
        "flow_mv",
        "flow_mv_level",
        "holder_controller_name",
        "holder_controller_rate",
        "area",
        "list_date",
        "deal_days",
        "pe_ttm",
        "pb",
        "ROE",
        "classification",
        "base_business",
        "intro",
        "address",
        "market_id",
        "symbol",
        "amount",
        "sync_date",
        "ths_concept_list_info",
        'ths_concept_name_list_str',
        'ths_concept_count',
        'ths_concept_most_relative_name',
        'ths_concept_most_relative_code',
        'ths_concept_list',
        "kpl_plate_name",
        "kpl_most_relative_name",
        "kpl_plate_list_info",
        'operate_profit',
        'total_operate_income',
        'operate_date_name',
        'kzz_debt_list',
        'hk_stock_code',
        'hk_stock_name',
        'main_business_list',
        'most_profitable_business',
        'most_profitable_business_rate',
        'most_profitable_business_profit',
    ]]


if __name__ == '__main__':
    industry_df_test = get_fix_industry_name_df()
    print(industry_df_test)

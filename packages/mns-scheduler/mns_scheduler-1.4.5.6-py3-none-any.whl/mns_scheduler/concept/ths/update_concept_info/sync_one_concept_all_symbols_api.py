import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import datetime
import mns_scheduler.concept.ths.detaill.ths_concept_detail_api as ths_concept_detail_api
import mns_common.component.concept.ths_concept_common_service_api as ths_concept_common_service_api
from loguru import logger


# 通过概念指数同步所有概念下的股票组成

# 同步概念下所有股票组成
def update_concept_all_detail_info():
    new_concept_list = ths_concept_common_service_api.get_all_ths_concept()
    new_concept_list = new_concept_list.sort_values(by=['symbol'], ascending=False)

    for one_concept in new_concept_list.itertuples():
        try:
            ths_concept_detail_api.sync_ths_concept_detail_to_db(one_concept.symbol, one_concept.name)
        except BaseException as e:
            logger.error("同步概念下所有股票组成异常:{},{}，｛｝", one_concept.symbol, one_concept.name, e)


if __name__ == '__main__':
    now_date = datetime.datetime.now()
    begin_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    print('同步开始:' + begin_date)
    update_concept_all_detail_info()
    now_date = datetime.datetime.now()
    end_date = now_date.strftime('%Y-%m-%d %H:%M:%S')
    print('同步结束:' + end_date)

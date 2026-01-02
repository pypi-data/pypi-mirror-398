import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.company.company_common_service_api as company_common_service_api
import mns_common.component.common_service_fun_api as common_service_fun_api


def get_company_info():
    em_company_info_df = em_stock_info_api.get_a_stock_info()
    em_company_info_df = em_company_info_df[['symbol',
                                             'name',
                                             "now_price",
                                             'total_mv',
                                             'flow_mv',
                                             'pe_ttm',
                                             'sz_sh',
                                             'area',
                                             'pb',
                                             'list_date',
                                             'ROE',
                                             'total_share',
                                             'flow_share',
                                             'industry',
                                             'amount',
                                             "hk_stock_code",
                                             "hk_stock_name",
                                             'concept']]

    em_company_info_df = em_company_info_df.sort_values(by=['list_date'], ascending=False)

    de_listed_stock_list = company_common_service_api.get_de_list_company()
    em_company_info_df = em_company_info_df.loc[~(
        em_company_info_df['symbol'].isin(de_listed_stock_list))]
    em_company_info_df = common_service_fun_api.exclude_ts_symbol(em_company_info_df)

    return em_company_info_df


if __name__ == '__main__':
    get_company_info()

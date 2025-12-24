import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import pandas as pd
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.component.zt.zt_common_service_api as zt_common_service_api


def handle_industry_index(real_time_quotes_now):
    industry_today_main_net_inflow_group = common_service_fun_api.group_by_industry_sum(real_time_quotes_now,
                                                                                        'industry',
                                                                                        'today_main_net_inflow')

    industry_today_main_net_inflow_group = industry_today_main_net_inflow_group.set_index(['industry'], drop=False)

    industry_amount_group = common_service_fun_api.group_by_industry_sum(real_time_quotes_now,
                                                                         'industry',
                                                                         'amount')
    industry_amount_group = industry_amount_group.set_index(['industry'], drop=True)
    industry_group = pd.merge(industry_today_main_net_inflow_group, industry_amount_group, how='outer',
                              left_index=True, right_index=True)

    # zt_sum sum
    zt_sum_group = zt_common_service_api.group_industry_zt_by_field(real_time_quotes_now, 'industry')
    # k c x 涨停乘以2
    zt_sum_group['industry_zt_num'] = zt_sum_group['industry_sh_zt_number'] + zt_sum_group[
        'industry_kc_zt_number'] * 2 + zt_sum_group['industry_kc_high_chg_number']
    zt_sum_group = zt_sum_group.set_index(['industry'], drop=True)

    industry_group = pd.merge(industry_group, zt_sum_group, how='outer',
                              left_index=True, right_index=True)

    disk_diff_amount_group = common_service_fun_api.group_by_industry_sum(real_time_quotes_now,
                                                                          'industry',
                                                                          'disk_diff_amount')
    disk_diff_amount_group = disk_diff_amount_group.set_index(['industry'], drop=True)
    industry_group = pd.merge(industry_group, disk_diff_amount_group, how='outer',
                              left_index=True, right_index=True)

    industry_group = industry_calculate_index(industry_group, real_time_quotes_now)
    return industry_group


def industry_calculate_index(industry_group, real_time_quotes_now):
    industry_group['industry_index'] = 0
    industry_group.drop_duplicates('industry', keep='last', inplace=True)
    top_up_industry_new = industry_group.copy()
    for industry_one in top_up_industry_new.itertuples():
        real_time_quotes_now_industry = real_time_quotes_now.loc[
            real_time_quotes_now['industry'] == industry_one.industry]
        industry_index = common_service_fun_api.calculate_index(real_time_quotes_now_industry.copy())
        top_up_industry_new.loc[top_up_industry_new["industry"] == industry_one.industry, ['industry_index']] \
            = industry_index

    return top_up_industry_new

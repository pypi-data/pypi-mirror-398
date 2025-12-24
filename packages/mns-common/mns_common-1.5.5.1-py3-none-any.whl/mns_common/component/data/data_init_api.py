import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 13
project_path = file_path[0:end]
sys.path.append(project_path)
from loguru import logger
import mns_common.component.common_service_fun_api as common_service_fun_api


def calculate_parameter_factor(real_time_quotes_now):
    # 单位亿
    real_time_quotes_now['amount_level'] = round(
        (real_time_quotes_now['amount'] / common_service_fun_api.HUNDRED_MILLION), 3)
    if bool(1 - ("disk_diff_amount_exchange" in real_time_quotes_now.columns)) or bool(
            1 - ("disk_diff_amount" in real_time_quotes_now.columns)):
        try:
            if 'average_price' in real_time_quotes_now.columns:
                # 外盘与内盘的金额差额 100 为1手
                real_time_quotes_now['disk_diff_amount'] = round(
                    (real_time_quotes_now['outer_disk'] - real_time_quotes_now['inner_disk']) * real_time_quotes_now[
                        "average_price"] * 100,
                    2)
            else:
                # 外盘与内盘的金额差额
                real_time_quotes_now['disk_diff_amount'] = round(
                    (real_time_quotes_now['outer_disk'] - real_time_quotes_now['inner_disk']) * real_time_quotes_now[
                        "now_price"] * 100,
                    2)
        except BaseException as e:
            real_time_quotes_now['disk_diff_amount'] = 0
            logger.error("出现异常:{}", e)
    # 使用 平均价和内外盘差值之积除流通市值之比 和 内外盘差值/流通股 误差很小
    # # 内外盘为手       flow_share 单位为股 所以要乘100
    # real_time_quotes_now['disk_diff_share'] = round(
    #     (real_time_quotes_now['outer_disk'] - real_time_quotes_now['inner_disk']) * 100, 2)
    # # 计算千分比 百分比太小
    # real_time_quotes_now['disk_diff_share_exchange'] = (real_time_quotes_now['disk_diff_share']
    # / real_time_quotes_now[
    #     'flow_share']) * 1000
    real_time_quotes_now['mv_circulation_ratio'] = real_time_quotes_now['mv_circulation_ratio'].fillna(1)

    real_time_quotes_now['mv_circulation_ratio'] = real_time_quotes_now['mv_circulation_ratio'].replace('', 1)

    real_time_quotes_now['disk_diff_amount_exchange'] = round(
        (real_time_quotes_now['disk_diff_amount'] / real_time_quotes_now['flow_mv']) * 1000, 2)

    real_time_quotes_now.loc[:, 'large_order_net_inflow_ratio'] = round(
        (real_time_quotes_now['large_order_net_inflow'] / real_time_quotes_now['amount']) * 100, 2)

    real_time_quotes_now.loc[:, 'reference_main_inflow'] = round(
        (real_time_quotes_now['flow_mv'] * (1 / 1000)), 2)

    real_time_quotes_now.loc[:, 'main_inflow_multiple'] = round(
        (real_time_quotes_now['today_main_net_inflow'] / real_time_quotes_now['reference_main_inflow']), 2)

    real_time_quotes_now.loc[:, 'super_main_inflow_multiple'] = round(
        (real_time_quotes_now['super_large_order_net_inflow'] / real_time_quotes_now['reference_main_inflow']), 2)
    real_time_quotes_now['large_inflow_multiple'] = round(
        (real_time_quotes_now['large_order_net_inflow'] / real_time_quotes_now['reference_main_inflow']), 2)

    if 'real_disk_diff_amount_exchange' not in real_time_quotes_now.columns:
        real_time_quotes_now.loc[:, 'real_disk_diff_amount_exchange'] = round(
            (real_time_quotes_now['disk_diff_amount_exchange'] / real_time_quotes_now['mv_circulation_ratio']), 2)

    if 'real_main_inflow_multiple' not in real_time_quotes_now.columns:
        real_time_quotes_now.loc[:, 'real_main_inflow_multiple'] = round(
            (real_time_quotes_now['main_inflow_multiple'] / real_time_quotes_now['mv_circulation_ratio']), 2)

    if 'real_super_main_inflow_multiple' not in real_time_quotes_now.columns:
        real_time_quotes_now.loc[:, 'real_super_main_inflow_multiple'] = round(
            (real_time_quotes_now['super_main_inflow_multiple'] / real_time_quotes_now['mv_circulation_ratio']), 2)

    if 'real_exchange' not in real_time_quotes_now.columns:
        real_time_quotes_now.loc[:, 'real_exchange'] = round(
            (real_time_quotes_now['exchange'] / real_time_quotes_now['mv_circulation_ratio']), 2)

    real_time_quotes_now.loc[:, 'max_real_main_inflow_multiple'] = real_time_quotes_now[
        ['real_main_inflow_multiple', 'real_super_main_inflow_multiple']].max(axis=1)

    real_time_quotes_now.loc[:, 'sum_main_inflow_disk'] = real_time_quotes_now['max_real_main_inflow_multiple'] + \
                                                          real_time_quotes_now['real_disk_diff_amount_exchange']

    real_time_quotes_now.loc[:, "real_flow_mv"] = round(
        (real_time_quotes_now['flow_mv'] * real_time_quotes_now['mv_circulation_ratio']), 2)

    real_time_quotes_now.loc[:, 'reference_main_inflow'] = round(
        (real_time_quotes_now['flow_mv'] * (1 / 1000)), 2)

    real_time_quotes_now.loc[:, ['flow_mv_level']] \
        = ((real_time_quotes_now["flow_mv"] / common_service_fun_api.HUNDRED_MILLION) // 10) + 1

    real_time_quotes_now.loc[:, ['total_mv_level']] \
        = ((real_time_quotes_now["total_mv"] / common_service_fun_api.HUNDRED_MILLION) // 10) + 1

    return real_time_quotes_now

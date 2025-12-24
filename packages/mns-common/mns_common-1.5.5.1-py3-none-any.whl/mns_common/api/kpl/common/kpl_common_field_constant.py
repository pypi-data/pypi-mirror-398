import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 16
project_path = file_path[0:end]
sys.path.append(project_path)


def rename_kpl_plate_detail(kpl_plate_detail_df):
    kpl_plate_detail_df = kpl_plate_detail_df.rename(columns={0: "symbol",
                                                              1: "name",
                                                              2: "you_zi",
                                                              4: "plate_name_list",
                                                              5: "now_price",
                                                              6: "chg",
                                                              7: "amount",
                                                              8: "real_exchange",
                                                              9: "speed",
                                                              10: "real_flow_mv",
                                                              11: "main_flow_in",
                                                              12: "main_flow_out",
                                                              13: "main_flow_net",
                                                              18: "sell_radio",

                                                              20: "chg_from_chg",

                                                              21: "quantity_ratio",
                                                              23: "connected_boards",
                                                              24: "dragon_index",
                                                              25: "exchange",
                                                              28: "closure_funds",
                                                              29: "max_closure_funds",
                                                              33: "pct_chg",
                                                              37: "total_mv",
                                                              38: "flow_mv",
                                                              39: "most_relative_name",
                                                              40: "leader_up_number",
                                                              42: "last_reason_organ_add",
                                                              62: "pe"
                                                              })
    kpl_plate_detail_df[["symbol",
                         "name",
                         "you_zi",
                         "plate_name_list",
                         "now_price",
                         "chg",
                         "amount",
                         "real_exchange",
                         "speed",
                         "real_flow_mv",
                         "main_flow_in",
                         "main_flow_out",
                         "main_flow_net",
                         "sell_radio",
                         "chg_from_chg",
                         "quantity_ratio",
                         "connected_boards",
                         "dragon_index",
                         "exchange",
                         "closure_funds",
                         "max_closure_funds",
                         "pct_chg",
                         "total_mv",
                         "flow_mv",
                         "most_relative_name",
                         "leader_up_number",
                         "last_reason_organ_add",
                         "pe"]]
    return kpl_plate_detail_df


# 指数名称改名
def rename_plate_index(plate_index_df):
    plate_index_df = plate_index_df.rename(columns={
        0: "plate_code",
        1: "plate_name",
        2: "heat_score",
        3: "chg",
        4: "speed",
        5: "amount",
        6: "main_net_inflow",
        7: "main_inflow_in",
        8: "main_inflow_out",
        9: "quantity_ratio",
        10: "flow_mv",
        12: "super_order_net",
        13: "total_mv",
        14: "last_reason_organ_add",
        15: "ava_pe_now",
        16: "ava_pe_next"
    })
    plate_index_df = plate_index_df[[
        "plate_code",
        "plate_name",
        "heat_score",
        "chg",
        "speed",
        "amount",
        "main_net_inflow",
        "main_inflow_in",
        "main_inflow_out",
        "quantity_ratio",
        "flow_mv",
        "super_order_net",
        "total_mv",
        "last_reason_organ_add",
        "ava_pe_now",
        "ava_pe_next"
    ]]
    return plate_index_df

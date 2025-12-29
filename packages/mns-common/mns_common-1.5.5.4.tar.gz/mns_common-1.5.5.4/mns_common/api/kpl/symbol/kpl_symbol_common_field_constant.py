import sys
import os

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)

SYNC_FIELD = [
    'symbol',
    'name',
    'you_zi',
    '_',
    'plate_name_list',
    'now_price',
    'chg',
    'amount',
    'real_exchange',
    'speed',
    'real_flow_mv',
    'main_flow_in',
    'main_flow_out',
    'main_flow_net',
    '_',
    '_',
    '_',
    '_',
    '_',
    # 卖流占比
    'sell_radio',

    'chg_from_chg',
    'quantity_ratio',
    '_',
    'connected_boards',
    'dragon_index',
    'exchange',
    '_',
    '_',
    'closure_funds',
    'max_closure_funds',
    '_',
    '_',
    '_',
    'pct_chg',
    '_',
    '_',
    '_',
    'total_mv',
    'flow_mv',
    'most_relative_name',
    '_',
    '_',
    'last_reason_organ_add',
    '_',

    '_',
    '_',
    '_',
    '_',
    '_',
    '_',

    '_',
    '_',

    '_',
    '_',

    '_',
    '_',
    '_',
    '_',
    '_',
    '_'

]

CHOOSE_FIELD = [
    'symbol',
    'name',
    'you_zi',
    'plate_name_list',
    'now_price',
    'chg',
    'amount',
    'exchange',
    'real_exchange',
    'speed',
    'real_flow_mv',
    'main_flow_in',
    'main_flow_out',
    'main_flow_net',
    # 卖流占比
    'sell_radio',
    'chg_from_chg',
    'quantity_ratio',
    'connected_boards',
    'dragon_index',
    'closure_funds',
    'max_closure_funds',
    'pct_chg',
    'total_mv',
    'flow_mv',
    'most_relative_name',
    'last_reason_organ_add'

]


def rename_kpl_real_time_quotes(kpl_real_time_quotes):
    return kpl_real_time_quotes.rename(columns={0: "symbol",
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
                                                26: "closure_funds",
                                                27: "max_closure_funds",
                                                33: "pct_chg",
                                                37: "total_mv",
                                                38: "flow_mv",
                                                39: "most_relative_name",
                                                42: "last_reason_organ_add"
                                                })

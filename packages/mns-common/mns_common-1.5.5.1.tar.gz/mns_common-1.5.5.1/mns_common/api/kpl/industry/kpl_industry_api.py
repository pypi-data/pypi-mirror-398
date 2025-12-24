import sys
import os
file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 14
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.kpl.common.kpl_common_api as kpl_common_api


def get_industry_index():
    return kpl_common_api.get_plate_index(kpl_common_api.INDUSTRY)


def industry_index_detail(industry_code):
    return kpl_common_api.plate_detail_info(industry_code)


if __name__ == '__main__':
    industry_df = get_industry_index()

    df = industry_index_detail('881129')
    print(df)

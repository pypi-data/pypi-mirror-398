import sys
import os
file_path = os.path.abspath(__file__)
end = file_path.index('mns') +14
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.api.kpl.common.kpl_common_api as kpl_common_api


def get_concept_index():
    return kpl_common_api.get_plate_index(kpl_common_api.CONCEPT)


def concept_index_detail(concept_code):
    return kpl_common_api.plate_detail_info(concept_code)


if __name__ == '__main__':
    df_concept = get_concept_index()
    print(df_concept)
    df_concept_detail = concept_index_detail('801476')
    print(df_concept_detail)

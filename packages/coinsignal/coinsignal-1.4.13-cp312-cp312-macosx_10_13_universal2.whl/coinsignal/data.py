# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements data reading and transformation functions:
# • Reading raw market data from CSV files
# • Handling static and dynamic symbol selection
# • Transforming symbol-based data maps into feature maps
# --------------------------------------------------------------------------------


import _ext.data as _data


DEFAULT_DATA_PARAMS_DICT = {
    'static_symbols': [],
    'dynamic_symbols': {
        'rule': '',
        'count': 0
    },
    'sources': []
}


def read_data_to_features_map(data_dir, date, look_back_days, look_ahead_days, data_params_dict):
    features_map, read_data_errors = _data.read_data_to_features_map(data_dir, date, look_back_days, look_ahead_days, data_params_dict)
    return features_map, read_data_errors

def transform_features_map_to_full_features_df(features_map):
    full_features_df = _data.transform_features_map_to_full_features_df(features_map)
    return full_features_df
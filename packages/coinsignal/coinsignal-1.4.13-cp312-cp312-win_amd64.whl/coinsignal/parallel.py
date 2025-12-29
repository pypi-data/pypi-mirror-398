# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements parallel processing for feature preparation:
# • Parallelizing data reading, feature and label calculations, sampling
# • Progress tracking for parallel processing across multiple dates
# --------------------------------------------------------------------------------


import _ext.parallel as _parallel


def prepare_sub_full_features_df(data_dir, date, look_back_days, look_ahead_days, constants_dict, data_params_dict, feature_params_dict, return_params_dict, sampler_params_dict, N, n_completed, progress_update_event):
    df, mft_df, mft_feature_plan, errors = _parallel.prepare_sub_full_features_df(data_dir, date, look_back_days, look_ahead_days, constants_dict, data_params_dict, feature_params_dict, return_params_dict, sampler_params_dict, N, n_completed, progress_update_event)
    return df, mft_df, mft_feature_plan, errors

def prepare_full_features_df(data_dir, start_date, end_date, look_back_days, look_ahead_days, constants_dict, data_params_dict, feature_params_dict, return_params_dict, sampler_params_dict):
    full_features_df, mft_full_features_df, mft_feature_plan, read_data_errors = _parallel.prepare_full_features_df(prepare_sub_full_features_df, data_dir, start_date, end_date, look_back_days, look_ahead_days, constants_dict, data_params_dict, feature_params_dict, return_params_dict, sampler_params_dict)
    return full_features_df, mft_full_features_df, mft_feature_plan, read_data_errors
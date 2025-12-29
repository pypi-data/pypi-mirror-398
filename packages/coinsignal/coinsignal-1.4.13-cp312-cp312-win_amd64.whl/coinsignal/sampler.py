# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements data sampling functions:
# • Sampling data on time using time intervals
# • Sampling data on move using smoothed price change
# • Sampling data on return using weighted random sampling
# --------------------------------------------------------------------------------


import _ext.sampler as _sampler


DEFAULT_SAMPLER_PARAMS_DICT = {
    'sampling_time': 0,
    'is_time_random': False,
    'sampling_bp': 0,
    'rolling_step': 0
}


def sample_data(features_map, sampler_params_dict):
    features_map = _sampler.sample_data(features_map, sampler_params_dict)
    return features_map
# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements feature engineering functions:
# • Adding various features based on trade and reference exchange-market pairs
# --------------------------------------------------------------------------------


import _ext.feature as _feature


DEFAULT_FEATURE_PARAMS_DICT = {
    'features':
    {
        'time': [],
        'macd': [],
        'rsi': [],
        'price_move_range': [],
        'price_trend': [],
        'price_volume_corr': [],
        'ohlcv': [],
        'volatility': [],
        'high_low_time': [],
        'volume': [],
        'basis': [],
        'fixedstart': [],
        'funding_rate': [],
        'funding_time': [],
        'index': []
    },
    'is_validating': False
}


def add_features(features_map, feature_params_dict):
    features_map = _feature.add_features(features_map, feature_params_dict)
    return features_map
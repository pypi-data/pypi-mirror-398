# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module implements the main model training and evaluation pipeline:
# • Handling data splitting, scaling, auxiliary model processing, cross-validation,
# • Training and evaluating models with various metrics
# --------------------------------------------------------------------------------


import _ext.model as _model


DEFAULT_MODEL_PARAMS_DICT = {
    'group_count': 5,
    'train_ratio': 0.8,
    'valid_sub_ratio': 0.25,
    'test_isolate_time': 0,
    'is_random_start': False,
    'weight_limit': 1,
    'is_sign_balanced': False,
    'is_cv': True,
    'cv_split_count': 4,
    'cv_eval_train_metric': True,
    'cv_selection_metric': 'mse',
    'num_boost_round': 1000,
    'log_evaluation_period': 50,
    'evaluate_rounds': [400, 700, 1000],
    'X_scaler_sub_params': {
        'name': '',
        'vlimits': None,
        'qlimits': [0, 1],
        'inner_scale': 1,
        'outer_scale': 1
    },
    'y_scaler_sub_params': {
        'name': '',
        'vlimits': None,
        'qlimits': [0, 1],
        'inner_scale': 1,
        'outer_scale': 1
    },
    'auxiliary_model_sub_params': {
        'name': '',
        'model_dir': '',
        'vlimits': None,
        'qlimits': [0, 1],
        'sampling_modes': ['train', 'evaluate']
    },
    'loss_sub_params': {
        'name': '',
        'dof': 10,
        'scale': 1,
        'fee': 0.0001
    },
    'training_sub_params': {
        'boosting_type': 'gbdt',
        'num_leaves': 25,
        'max_depth': 5,
        'learning_rate': 0.005,
        'reg_alpha': 1,
        'reg_lambda': 1,
        'min_gain_to_split': 0.1,
        'extra_trees': True,
        'objective': 'regression',
        'metric': '',
        'num_class': 1,
        'verbose': -1
    }
}


def run_model(full_features_df, model_params_dict):
    model_evaluations = _model.run_model(full_features_df, model_params_dict)
    return model_evaluations
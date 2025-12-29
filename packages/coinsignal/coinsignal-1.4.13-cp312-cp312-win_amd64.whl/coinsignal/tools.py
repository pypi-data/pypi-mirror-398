# --------------------------------------------------------------------------------
# Copyright (c) 2025 Zehao Yang
#
# Author: Zehao Yang
#
# This module provides utility functions and helper classes:
# • I/O utilities for logging and progress tracking
# • Configuration loading and parameter updating
# • Rolling statistics calculations and various data processing helpers
# • Plotting functions for model performance visualization
# --------------------------------------------------------------------------------


import os
import sys
import yaml
import hashlib
import numpy as np
from datetime import datetime
import _ext.tools as _tools


class RegressionIO:
    def __init__(self, log_file):
        self.sys_stdout = sys.stdout
        self.ios = [sys.stdout, open(log_file, 'a', encoding='utf-8')]

    def write(self, text):
        current_time = get_current_time()
        if text not in ['\n', '\r']:
            text = f'[{current_time}] {text}'
        for io in self.ios:
            io.write(text)

    def flush(self):
        for io in self.ios:
            io.flush()

    def close(self):
        for io in self.ios[1:]:
            io.close()

    def __enter__(self):
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.sys_stdout
        self.close()
        return False


def get_current_dir(current_file):
    current_dir = os.path.dirname(os.path.abspath(current_file))
    return current_dir

def get_current_time():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return current_time

def write_log(log_file, log):
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(log)

def load_config(current_dir):
    with open(f'{current_dir}/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    config['start_date'] = str(config['start_date'])
    config['end_date'] = str(config['end_date'])
    return config

def initialize_random_seed(random_seed):
    if random_seed is None:
        random_seed = int(hashlib.md5(f'{datetime.now().timestamp()}_{os.urandom(8).hex()}'.encode()).hexdigest()[:8], 16)
    np.random.seed(random_seed)
    return random_seed

def update_params_dict(params_dict, default_params_dict):
    new_params_dict = {}
    for key in default_params_dict:
        if isinstance(default_params_dict[key], dict):
            new_params_dict[key] = update_params_dict(params_dict.get(key, {}), default_params_dict[key])
        else:
            new_params_dict[key] = params_dict.get(key, default_params_dict[key])
    return new_params_dict

def make_results_dirs(output_dir, model_name, horizons):
    model_dir = f'{output_dir}/{model_name}'
    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(f'{model_dir}/results', exist_ok=True)
    for horizon in horizons:
        ret_col = f'ret-{horizon}'
        os.makedirs(f'{model_dir}/results/{ret_col}', exist_ok=True)
        os.makedirs(f'{model_dir}/results/{ret_col}/models', exist_ok=True)
        os.makedirs(f'{model_dir}/results/{ret_col}/plots', exist_ok=True)

def copy_scripts(current_dir, output_dir, model_name, random_seed, scripts_folder='scripts'):
    model_dir = f'{output_dir}/{model_name}'
    os.makedirs(f'{model_dir}/{scripts_folder}', exist_ok=True)
    file_and_folders = [f for f in os.listdir(current_dir) if not f.startswith('.')]
    for f in file_and_folders:
        if os.path.isfile(f'{current_dir}/{f}'):
            with open(f'{current_dir}/{f}', 'r', encoding='utf-8') as file:
                text = file.read()
                if f == 'config.yaml':
                    row = [row for row in text.split('\n') if row.startswith('random_seed:')][0]
                    text = text.replace(row, f'random_seed: {random_seed}')
            with open(f'{model_dir}/{scripts_folder}/{f}', 'w', encoding='utf-8') as file:
                file.write(text)
        else:
            copy_scripts(f'{current_dir}/{f}', output_dir, model_name, random_seed, f'{scripts_folder}/{f}')

def validate_and_save_features(output_dir, model_name, full_features_df, mft_full_features_df, mft_feature_plan):
    comparison_df = _tools.validate_and_save_features(output_dir, model_name, full_features_df, mft_full_features_df, mft_feature_plan)
    return comparison_df

def summarize_and_save_results(output_dir, model_name, model_evaluations):
    _tools.summarize_and_save_results(output_dir, model_name, model_evaluations)
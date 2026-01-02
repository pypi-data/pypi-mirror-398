# coding: utf-8

# Copyright 2020,2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging


import math
import os
from ibm_cloud_sdk_core.authenticators import NoAuthAuthenticator, CloudPakForDataAuthenticator, IAMAuthenticator, BearerTokenAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.validation import *
from ibm_aigov_facts_client.utils.constants import *
from mlflow.utils.file_utils import read_file_lines
from functools import reduce
from ibm_aigov_facts_client.supporting_classes.cp4d_authenticator import CP4DAuthenticator


_logger = logging.getLogger(__name__)


def exists(name):
    return os.path.exists(name)


def is_directory(name):
    return os.path.isdir(name)


def is_file(name):
    return os.path.isfile(name)


def _check_root_dir(root_directory):
    """
    Run checks before running directory operations.
    """
    if not exists(root_directory):
        raise Exception("'%s' does not exist." % root_directory)
    if not is_directory(root_directory):
        raise Exception("'%s' is not a directory." % root_directory)


def check_if_any_values_exist(tags, values=[], key=None):
    if key is None:
        key = PRE_AUTOLOG_KEY
    d = tags.get(key)
    if d:
        is_exist = any(True if val in d else False for val in values)
    else:
        is_exist = False
    return is_exist




def check_tags_exist(tags, values=[], key=None):
    
    is_exist = False

    if key is None:
        for i in AUTO_FRAMEWORK_KEYS:
            d = tags.get(i)
            if d:
                is_exist = any(True if val in d else False for val in values)
                if is_exist:
                    return d
                else:
                    is_exist = False
    else:
        d = tags.get(key)
        if d:
            is_exist = all(True if val in d else False for val in values)
            if is_exist:
                return d
        else:
            is_exist = False
    return is_exist


def check_if_values_exist(tags, values=[], key=None):
    if key is None:
        key = PRE_AUTOLOG_KEY
    d = tags.get(key)
    if d:
        is_exist = any(True if val in d else False for val in values)
    else:
        is_exist = False
    return is_exist


def check_if_autolog_published(tags, key=None):
    is_published=False
    is_published = tags.get(PUBLISH_TAG or key)
    if is_published:
        is_published=True
        return is_published


def check_if_any_values_exist_custom(tags, values=[], key=None):
    if key is None:
        key = POST_AUTOLOG_KEY
    d = tags.get(key)
    if d:
        is_exist = any(True if val in d else False for val in values)
    else:
        is_exist = False
    return is_exist

def check_if_key_exist(data,key):
    is_exist=False
    d = data.get(key)
    if d and d!='None':
        is_exist = True
    return is_exist

def check_get_val(data,key):
    d = data.get(key)
    return d

def check_if_keys_exist(tags, keys=[]):
    is_exist = all(k in tags for k in keys)
    return is_exist


def check_if_any_keys_exist(tags, keys=[]):
    is_exist = any(k in tags for k in keys)
    return is_exist


def check_framework_custom(tags, values=[], key=None):
    if key is None:
        key = PRE_AUTOLOG_KEY
    d = tags.get(key)
    if d:
        is_exist = any(True if val in d else False for val in values)
    else:
        is_exist = False
    return is_exist


def check_current_framework(tags, key=None):
    if key is None:
        key = PRE_AUTOLOG_KEY
    val = tags.get(key)
    return val


def check_if_auth_used(authenticator):
    is_auth_used = False
    if type(authenticator) in [CloudPakForDataAuthenticator, CP4DAuthenticator, IAMAuthenticator, BearerTokenAuthenticator,MCSPV2Authenticator]:
            is_auth_used = True
    return is_auth_used


def roundup(x):
    return int(math.floor(x / 100.0)) * 100


def check_num_range(x):
    if x % 10 == 0:
        x = x-1
        final_num = roundup(x)
    else:
        final_num = roundup(x)
    return final_num


def check_epochs_count(params, tag_name):
    return params.get(tag_name)


def get_epochs_num_to_match(params, tag_name):
    epochs_count = check_epochs_count(params, tag_name)
    if tag_name == 'steps':
        num_to_match = check_num_range(int(epochs_count))+1
    else:
        num_to_match = int(epochs_count)-1

    return num_to_match

def check_if_earlystop_defined(params):
    early_stop_used=check_if_key_exist(params,EARLY_STOP_TAG)
    return early_stop_used

def check_earlystop_epoch(metrics):
    early_stop_epoch=check_if_key_exist(metrics,EARLY_STOP_EPOCH_TAG)
    return early_stop_epoch

def check_if_earlystoprounds_defined(params):
    early_stop_rounds_used=check_if_key_exist(params,EARLY_STOP_ROUND_TAG)
    return early_stop_rounds_used

def check_earlystop_epoch_rounds(metrics):
    early_stop_rounds=check_if_key_exist(metrics,EARLY_STOP_ROUND_METRIC_TAG)
    return early_stop_rounds

def list_all(root, filter_func=lambda x: True, full_path=False):
    if not is_directory(root):
        raise Exception("Invalid parent directory '%s'" % root)
    matches = [x for x in os.listdir(
        root) if filter_func(os.path.join(root, x))]
    return [os.path.join(root, m) for m in matches] if full_path else matches


def find(root, name, full_path=False):
    path_name = os.path.join(root, name)
    return list_all(root, lambda x: x == path_name, full_path)


def get_run_data(run_id):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    # _check_root_dir(root_dir)
    run_data = client.get_run(run_id).data
    run_info = client.get_run(run_id).info

    return run_data, run_info


def check_exp(run_id):
    _, run_info = get_run_data(run_id)
    exp_id = run_info.experiment_id

    return exp_id


def get_exp_name(run_id):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    _, run_info = get_run_data(run_id)
    exp_name = client.get_experiment(run_info.experiment_id).name
    return exp_name


def get_metric_from_line_custom(metric_name, line):
    metric_parts = line.strip().split(" ")
    ts = int(metric_parts[0])
    val = float(metric_parts[1])
    step = int(metric_parts[2]) if len(metric_parts) == 3 else 0
    return dict(key=metric_name, value=val, step=step)


def get_metric_from_file_custom(parent_path, metric_name):
    metric_objs = [
        get_metric_from_line_custom(metric_name, line)
        for line in read_file_lines(parent_path, metric_name)
    ]
    max_step = max(metric_objs, key=lambda x: x['step'])['step']
    if len(metric_objs) == 0:
        raise ValueError(
            "Metric '%s' is malformed. No data found." % metric_name)
    return metric_objs, max_step


def rename_tags(tags):
    renamed_tags = {k.replace("mlflow", "facts")if k.startswith(
        "mlflow.") else k: v for k, v in tags.items()}
    return renamed_tags


def format_metrics(metrics):
    metrics = reduce(
        lambda x, y: x+y, metrics)
    sorted_metrics = sorted(metrics, key=lambda k: k['step'])
    return sorted_metrics


def check_framework_support(tags, values=[], key=None):
    is_exist = False
    if key is None:
        for i in AUTO_FRAMEWORK_KEYS:
            d = tags.get(i)
            if d:
                is_exist = any(True if val in d else False for val in values)
                if is_exist:
                    return d
                else:
                    is_exist = False
    else:
        d = tags.get(key)
        if d:
            is_exist = all(True if val in d else False for val in values)
            if is_exist:
                return d
        else:
            is_exist = False
    return is_exist


def check_root_dir(self):
    """
    Run checks before running directory operations.
    """
    if not exists(self.root_directory):
        raise Exception("'%s' does not exist." % self.root_directory)
    if not is_directory(self.root_directory):
        raise Exception("'%s' is not a directory." % self.root_directory)


def set_custom_tag_autolog(run_id, flag=False):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    try:
        client.set_tag(run_id, PUBLISH_TAG, flag)
    except:
        client.set_tag(run_id, PUBLISH_TAG, flag)
        raise ClientError("Could not mark run as published to factsheet")
    
def set_custom_tag_new(run_id, tag_name, tag_value):
    from mlflow.tracking import MlflowClient
    client = MlflowClient()
    try:
        client.set_tag(run_id, tag_name, tag_value)
    except:
        client.set_tag(run_id, tag_name, tag_value)
        raise ClientError("Could not mark run as published to factsheet")    
    
def check_if_manual_export(run_id):
   manual_export=False
   data,_= get_run_data(run_id)
   published_flag=data.tags.get(PUBLISH_TAG)
   if published_flag:
     manual_export=True
   return manual_export

def get_estimator(tags):

    final_est=None

    est_name=tags.get(EST_TAG)
    if est_name:
        final_est=est_name
    else:
        for i in AUTO_FRAMEWORK_KEYS:
            est = tags.get(i)
            if est:
                final_est=est

    return final_est


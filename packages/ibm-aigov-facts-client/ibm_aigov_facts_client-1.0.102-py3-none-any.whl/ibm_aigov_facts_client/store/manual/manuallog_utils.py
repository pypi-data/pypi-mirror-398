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
import os
import mlflow
from ibm_aigov_facts_client.utils.client_errors import *
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

from ibm_aigov_facts_client.store.autolog.autolog_utils import *
from ibm_aigov_facts_client.custom import custom_file_store
from ibm_aigov_facts_client.utils.manual_store_utils import *
from ibm_aigov_facts_client.utils.constants import DEFAULT_DB_FILE_PATH,DEFAULT_LOCAL_FILE_PATH



def get_experiment(experiment_name):
    exp_exist = mlflow.get_experiment_by_name(experiment_name)
    return exp_exist


def create_experiment(experiment_name:str=None):
    client = mlflow.tracking.MlflowClient()
    if experiment_name is None:
        exp_id = client.create_experiment("Default")
    else: 
        exp_id = client.create_experiment(experiment_name)
    return exp_id


def set_experiment(experiment_name):
    mlflow.set_experiment(experiment_name)


def get_experiment_by_name(experiment_name):
    exp = mlflow.get_experiment_by_name(experiment_name)
    return exp


def clean_default_exp():
    client = mlflow.tracking.MlflowClient()
    default_experiment = get_experiment_by_name("Default")
    #if (default_experiment is not None) and (default_experiment.lifecycle_stage != "deleted"):
    #    client.delete_experiment("0")


def start_trace(experiment_id: str = None):

    check_if_active_run_exist = mlflow.active_run()
    if check_if_active_run_exist is not None:
        mlflow.end_run()

    try:
        if experiment_id:
            mlflow.start_run(experiment_id=experiment_id)
        else:
            mlflow.start_run()
    except:
        raise ClientError("Can not initiate tracing....")


def end_trace():
    try:
        check_if_active_run_exist = mlflow.active_run()
        if check_if_active_run_exist is None:
            return("No active run found")
        else:
            mlflow.end_run()
    except:
        raise ClientError("Can not end tracing....")


def log_metric_data(key: str, value: float, step: Optional[int] = None) -> None:
    mlflow.log_metric(key, value, step)


def log_metrics_data(metrics: Dict[str, float], step: Optional[int] = None) -> None:
    #mlflow.log_metrics(metrics, step)
    for key, value in metrics.items():
        mlflow.log_metric(key,value,step or 0)


def log_param_data(key: str, value: Any) -> None:
    mlflow.log_param(key, value)


def log_params_data(params: Dict[str, Any]) -> None:
    #mlflow.log_params(params)
    for key, value in params.items():
        mlflow.log_param(key,value)


def log_tag_data(key: str, value: Any) -> None:
    mlflow.set_tag(key, value)


def log_tags_data(tags: Dict[str, Any]) -> None:
    #mlflow.set_tags(tags)
    for key, value in tags.items():
        mlflow.set_tag(key,value)


def clean_tags(run_id):
    data, _ = get_run_data(run_id)
    get_sys_tags = {k: v for k, v in data.tags.items() if k.startswith(
        "mlflow.")}
    custom_file_store.FactSheetStore().clean_tags(get_sys_tags, run_id)


def get_active_run():
    run = mlflow.active_run()
    return run


def is_databricks_uri(uri):
    """
    Databricks URIs look like 'databricks' (default profile) or 'databricks://profile'
    or 'databricks://secret_scope:secret_key_prefix'.
    """
    scheme = urllib.parse.urlparse(uri).scheme
    return scheme == "databricks" or uri == "databricks"

def is_local_uri(uri):
    """Returns true if this is a local file path (/foo or file:/foo)."""
    scheme = urllib.parse.urlparse(uri).scheme
    return uri != "databricks" and (scheme == "" or scheme == "file")

def is_http_uri(uri):
    scheme = urllib.parse.urlparse(uri).scheme
    return scheme == "http" or scheme == "https"

def clean_uri():
    uri = mlflow.get_tracking_uri()
    is_db_uri=is_databricks_uri(uri)
    is_local= is_local_uri(uri)
    #is_http=is_http_uri(uri)
    if is_db_uri:
        mlflow.set_tracking_uri(DEFAULT_DB_FILE_PATH)
    elif not is_db_uri and not is_local:
        mlflow.set_tracking_uri(DEFAULT_LOCAL_FILE_PATH.format(os.path.abspath(os.getcwd())))
    else:
        mlflow.set_tracking_uri(DEFAULT_LOCAL_FILE_PATH.format(os.path.abspath(os.getcwd())))
        

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
import urllib.parse

from ibm_aigov_facts_client.utils.store_utils import *
from ibm_aigov_facts_client.custom import custom_file_store

from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.logging_utils import *

from ibm_aigov_facts_client.utils.constants import DEFAULT_DB_FILE_PATH,DEFAULT_LOCAL_FILE_PATH


_logger = logging.getLogger(__name__)


def get_experiment(experiment_name):
    exp_exist = mlflow.get_experiment_by_name(experiment_name)
    return exp_exist


def create_experiment(experiment_name=None):
    #client = mlflow.tracking.MlflowClient()
    if experiment_name is None:
        exp_id = mlflow.create_experiment("Default")
    else:
        exp_id = mlflow.create_experiment(experiment_name)
    return exp_id


def set_experiment(experiment_name):
    mlflow.set_experiment(experiment_name)


def get_experiment_by_name(experiment_name):
    exp = mlflow.get_experiment_by_name(experiment_name)
    return exp


def enable_autolog():
    try:
        mlflow.autolog(log_models=False, silent=True)
        _logger.info("Autolog enabled Successfully")
    except:
        raise ClientError(
            "Something went wrong when initiating Autolog")


def clean_default_exp():

    client = mlflow.tracking.MlflowClient()
    default_experiment = get_experiment_by_name("Default")
    #if (default_experiment is not None) and (default_experiment.lifecycle_stage != "deleted"):
    #    client.delete_experiment("0")


def clean_tags(tags, run_id):
    get_sys_tags = {k: v for k, v in tags.items() if k.startswith(
        "mlflow.")}
    custom_file_store.FactSheetStore().clean_tags(get_sys_tags, run_id)


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
        


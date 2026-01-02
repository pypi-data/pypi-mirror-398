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
import uuid
import mlflow
import pandas as pd
from ibm_aigov_facts_client.client import fact_trace, autolog, manual_log

from ibm_aigov_facts_client.custom import CUSTOM_TAG_GUID,DEFAULT_LOCAL_FILE_AND_ARTIFACT_PATH

from mlflow.entities import RunTag
from ..utils.client_errors import *
from ..utils.utils import *

_logger = logging.getLogger(__name__)


class GenerateExpId:

    def __init__(self, root_directory=None):
        self.root_directory = local_file_uri_to_path(
            root_directory or default_root_dir())
        self.generate_id = None
        self.EXP_GUID = None
        self.guid_tag = None
        self.experiment = None
        self.autolog = fact_trace.FactsClientAdapter._autolog

    def generate_guid(self, cur_exp):
        if not exists(self.root_directory):
            new_guid = self.get_new_guid()
        else:
            chk_exp_exists = mlflow.get_experiment_by_name(cur_exp.name)
            if chk_exp_exists is not None:
                check_runs = mlflow.search_runs([cur_exp.experiment_id])
                if not check_runs.empty and "tags.GUID" in check_runs:
                    new_guid = self.get_cur_exp_guid(check_runs)
                else:
                    new_guid = self.get_new_guid()
            else:
                new_guid = self.get_new_guid()

        return new_guid

    def get_exp_guid(self, experiment_name):
        check_if_exp_exists = mlflow.get_experiment_by_name(experiment_name)

        if check_if_exp_exists is not None:
            
            check_runs = mlflow.search_runs(
                [check_if_exp_exists.experiment_id])
            if not check_runs.empty and "tags.GUID" in check_runs:
                cur_guid = self.get_cur_exp_guid(check_runs)
            else:
                cur_guid=self.get_new_guid()
        else:
            raise ClientError("Could not locate experiment GUID")
        return cur_guid

    def get_cur_exp_guid(self, cur_runs):
        cur_id = cur_runs[(~cur_runs["tags.GUID"].isnull()) & (
            cur_runs["tags.GUID"] != "")]["tags.GUID"].unique()[0]
        return cur_id

    def get_new_guid(self):
        new_id = uuid.uuid4().hex
        return new_id

    def gen_new_tag(self):
        if self.autolog:
            self.experiment = autolog.AutoLog._cur_exp
        else:
            self.experiment = manual_log.ManualLog._cur_exp

        self.EXP_GUID = self.generate_guid(self.experiment)
        if self.EXP_GUID is not None or not "":
            self.guid_tag = RunTag(key=CUSTOM_TAG_GUID, value=self.EXP_GUID)
        else:
            raise ClientError("Error generating new tag")
        return self.guid_tag, self.EXP_GUID

    def gen_tag(self, tag):
        tag_obj = RunTag(key=list(tag.keys())[0], value=list(tag.values())[0])
        return tag_obj


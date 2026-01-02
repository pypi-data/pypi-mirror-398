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
from datetime import datetime
from ibm_aigov_facts_client.store.abstract_payload_store import AbstractPayloadStore

from ibm_aigov_facts_client.client import fact_trace, autolog, manual_log
from ibm_aigov_facts_client.custom import custom_exp
from ibm_aigov_facts_client.custom import custom_file_store
from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.manual_store_utils import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.store.manual.manuallog_utils import clean_tags


_logger = logging.getLogger(__name__)


class GetFinalPayloadGeneral(AbstractPayloadStore):
    def __init__(self, run_id=None, current_data=None, root_directory=None):

        self.current_data = current_data
        self.run_id = run_id
        self.root_dir = root_directory
        self.custom_tag = None
        self.exp_guid = None
        self.parent_path = None
        self.metric_files = None

        super().__init__()

    def set_guid_tag(self, run_id):
        self.custom_tag, self.exp_guid = custom_exp.GenerateExpId().gen_new_tag()
        custom_file_store.FactSheetStore().set_tag(run_id, self.custom_tag)

    def gen_payload(self, run_data, root_dir=None):

        experiments = []
        runs = {}
        tmp_payload = {}
        artifacts = []

        # if (fact_trace.FactsClientAdapter._autolog):
        #     tmp_payload["name"] = autolog.AutoLog._cur_exp.name
        #     tmp_payload["experiment_id"] = custom_exp.GenerateExpId(
        #     ).get_exp_guid(autolog.AutoLog._cur_exp.name)
        # else:
        #     tmp_payload["name"] = manual_log.ManualLog._cur_exp.name

        cur_run_exp_name = get_exp_name(self.run_id)
        if (fact_trace.FactsClientAdapter._autolog):

            if (cur_run_exp_name != autolog.AutoLog._cur_exp.name):

                tmp_payload["name"] = cur_run_exp_name
                tmp_payload["experiment_id"] = custom_exp.GenerateExpId(
                ).get_exp_guid(cur_run_exp_name)
            else:
                tmp_payload["name"] = autolog.AutoLog._cur_exp.name
                tmp_payload["experiment_id"] = custom_exp.GenerateExpId(
                ).get_exp_guid(autolog.AutoLog._cur_exp.name)
        else:

            if (cur_run_exp_name != manual_log.ManualLog._cur_exp.name):

                tmp_payload["name"] = cur_run_exp_name
                tmp_payload["experiment_id"] = custom_exp.GenerateExpId(
                ).get_exp_guid(cur_run_exp_name)
            else:
                tmp_payload["name"] = manual_log.ManualLog._cur_exp.name
                tmp_payload["experiment_id"] = custom_exp.GenerateExpId(
                ).get_exp_guid(manual_log.ManualLog._cur_exp.name)
        
        runs["run_id"] = self.run_id
        runs["created_date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if run_data.metrics and "data" not in run_data.metrics:
            runs["metrics"] = [{"key": k, "value": v}
                               for (k, v) in run_data.metrics.items()]

        elif run_data.metrics and "data" in run_data.metrics:
            runs["metrics"] = run_data.metrics["data"]
        else:
            runs["metrics"] = []

        if run_data.params:
            runs["params"] = [{"key": k, "value": v}
                              for (k, v) in run_data.params.items()]
        else:
            runs["params"] = []

        if run_data.tags:
            runs["tags"] = [{"key": k, "value": v}
                            for (k, v) in run_data.tags.items()]
        else:
            runs["tags"] = []

        runs["artifacts"] = artifacts

        experiments.append(runs)

        tmp_payload["runs"] = experiments

        return tmp_payload

    def clean_sys_tags(self,data,run_id):
        clean_tags(run_id)
        changed_tags = rename_tags(data.tags)
        data.tags.clear()
        data.tags.update(changed_tags)
        return data

    def get_payload_and_publish(self, root_dir, exp_id, run_id):
        self.run_id = run_id
        self.exp_id = exp_id
        self.root_dir = root_dir
        self.set_guid_tag(self.run_id)
        run_data, _ = get_run_data(run_id)
        updated_run_data=self.clean_sys_tags(run_data,self.run_id)
        self.final_payload = self.gen_payload(updated_run_data)
        return self.final_payload

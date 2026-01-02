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

from datetime import datetime

from ibm_aigov_facts_client.store.abstract_payload_manual import AbstractPayloadStore


from ibm_aigov_facts_client.client import fact_trace, autolog, manual_log
from ibm_aigov_facts_client.custom import custom_exp
from ibm_aigov_facts_client.store.manual.manuallog_utils import clean_tags

from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.manual_store_utils import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.validation import *


_logger = logging.getLogger(__name__)


class GetFinalPayloadBST(AbstractPayloadStore):
    def __init__(self, run_id=None, current_data=None, root_directory=None, subfolder_name=SUBFOLDER_DEFAULT):

        #self.current_data = current_data
        self.run_id = None
        self.exp_id = None
        self.root_dir = None
        self.custom_tag = None
        self.exp_guid = None
        self.parent_path = None
        self.metric_files = None
        self.final_payload = None
        self.subfolder = subfolder_name

        super().__init__()

    def get_metrics_files(self, exp_id, run_id, root_dir):
        validate_run_id(run_id)
        run_dir = get_run_dir(exp_id, run_id, root_dir)
        source_dirs = find(run_dir, self.subfolder, full_path=True)
        if len(source_dirs) == 0:
            return self.root_dir, []
        file_names = []
        for root, _, files in os.walk(source_dirs[0]):
            for name in files:
                abspath = os.path.join(root, name)
                file_names.append(os.path.relpath(abspath, source_dirs[0]))
        if sys.platform == "win32":
            # Turn metric relative path into metric name.
            # Metrics can have '/' in the name. On windows, '/' is interpreted as a separator.
            # When the metric is read back the path will use '\' for separator.
            # We need to translate the path into posix path.
            from mlflow.utils.file_utils import relative_path_to_artifact_path

            file_names = [relative_path_to_artifact_path(
                x) for x in file_names]
        return source_dirs[0], file_names

    def gen_payload(self, run_data, root_dir=None):

        experiments = []
        runs = {}
        tmp_payload = {}
        artifacts = []

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

        parent_path, metric_files = self.get_metrics_files(
            self.exp_id, self.run_id, self.root_dir)

        run_data, _ = get_run_data(run_id)

        check_early_stop_rounds_bst=check_if_earlystoprounds_defined(run_data.params)

        if(run_data.params.get(BST_EPOCHS_TAG) != None):
            check_epochs = run_data.params.get(BST_EPOCHS_TAG)

            allmetrics = []
            for metric_file in metric_files:
                final_metrics, num_max_step = get_metric_from_file_custom(
                    parent_path, metric_file)
                allmetrics.append(final_metrics)

            max_step_count = []
            for val in allmetrics:
                for row in val:
                    max_step_count.append(row["step"])
            
            
            if check_early_stop_rounds_bst:
                check_stop_rounds=run_data.metrics.get(EARLY_STOP_ROUND_METRIC_TAG)
                if check_stop_rounds:
                    if (max(max_step_count) == int(check_stop_rounds)+1):
                        allmetrics = format_metrics(allmetrics)
                        run_data.metrics.clear()
                        run_data.metrics['data'] = allmetrics
                        updated_run_data=self.clean_sys_tags(run_data,self.run_id)
                        self.final_payload = self.gen_payload(updated_run_data)
                    else:
                        raise ClientError("Error generating payload info")
            else:

                if (max(max_step_count) == int(check_epochs)-1):
                    allmetrics = format_metrics(allmetrics)
                    run_data.metrics.clear()
                    run_data.metrics['data'] = allmetrics
                    updated_run_data=self.clean_sys_tags(run_data,self.run_id)
                    self.final_payload = self.gen_payload(updated_run_data)
                else:
                    raise ClientError("Error generating payload info")
        return self.final_payload
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
import time

from ibm_aigov_facts_client.store.autolog import general_payload_store, dl_payload_store, bst_payload_store, spark_payload_store, dl_payload_store_custom, bst_payload_store_custom, bst_payload_store_custom_lgbm
from mlflow.store.tracking.file_store import FileStore
from ibm_aigov_facts_client.client import fact_trace
from ibm_aigov_facts_client.custom import custom_exp
from ibm_aigov_facts_client.utils.logging_utils import *

from ..utils.utils import *
from ..utils.store_utils import *
from ..utils.constants import *

_logger = logging.getLogger(__name__)


class FactSheetStore(FileStore):
    """FileStore provided through entrypoints system"""
    _cur_runid = None

    def __init__(self, root_directory=None, artifact_uri=None, **kwargs):
        if root_directory is None:
            self.root_directory = local_file_uri_to_path(
                root_directory or default_root_dir())
        self.is_plugin = True
        self.exp_guid = None
        self.parent_run_id = None
        self.autolog = fact_trace.FactsClientAdapter._autolog
        self.enable_push_framework = fact_trace.FactsClientAdapter._enable_push_framework
        super().__init__(self.root_directory, artifact_uri)

    def set_tag(self, run_id, custom_tag):
        super().set_tag(run_id, custom_tag)

    def clean_tags(self, tags, run_id):
        for k, val in tags.items():
            updated_key = k.replace("mlflow", "facts")
            updated_tag = custom_exp.GenerateExpId().gen_tag(
                {updated_key: val})
            super().set_tag(run_id, updated_tag)
            super().delete_tag(run_id, k)

    # def get_path_metric(self, run_id):
    #     parent_path, metric_files = super()._get_run_files(
    #         super()._get_run_info(run_id), "metric")

    #     return parent_path, metric_files

    def _get_resource_files(self, root_dir, subfolder_name):
        source_dirs = find(root_dir, subfolder_name, full_path=True)
        if len(source_dirs) == 0:
            return root_dir, []
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

    def get_path_metric(self, run_id):
        run_info = super()._get_run_info(run_id)
        run_dir = super()._get_run_dir(run_info.experiment_id, run_info.run_id)
        parent_path, metric_files = self._get_resource_files(
            run_dir, "metrics")

        return parent_path, metric_files

    def log_batch(self, run_id, metrics, params, tags):

        if self.autolog:
            is_special_new = self.enable_push_framework
            if (is_special_new == True):
                for framework in IS_SPECIAL_FRAMEWORKS:
                    set_custom_tag_new(run_id, 'facts.autologging', framework)

            super().log_batch(run_id, metrics, params, tags)
            currentRun = super().get_run(run_id)
            FactSheetStore._cur_runid = run_id
            currentData = currentRun.data

            check_spark_tag = check_tags_exist(
                currentData.tags, SPARK_FRAMEWORKS)
            check_tensorflow_tag = check_tags_exist(
                currentData.tags, DL_FRAMEWORKS)
            check_estimator_cls_tag = check_if_keys_exist(
                currentData.tags, SPARK_ESTIMATOR_CLS)
            check_hyp_tag_exist = check_if_key_exist(
                currentData.params, SPARK_HYP_TAG)
            check_hyp_tag_val = currentData.params.get(SPARK_HYP_TAG)
            check_bst_tag = check_tags_exist(
                currentData.tags, BST_FRAMEWORKS)
            check_framework_val = check_get_val(
                currentData.tags, PRE_AUTOLOG_KEY)

            frameworks_to_check = SUPPORTED_FRAMEWORKS + IS_SPECIAL_FRAMEWORKS
            check_valid_framework = check_framework_support(
                currentData.tags, frameworks_to_check)

            # Adding sleep of 1 sec to fix multiple asset creation problem
            time.sleep(1)

            if (check_valid_framework):

                check_if_published = check_if_autolog_published(
                    currentData.tags, PUBLISH_TAG)

                if not check_spark_tag:
                    if (check_tensorflow_tag or check_bst_tag):

                        if check_valid_framework == "pytorch":
                            clear_up_handler()

                        check_early_stop_dl = check_if_earlystop_defined(
                            currentData.params)

                        check_early_stop_rounds_val_bst = check_get_val(
                            currentData.params, EARLY_STOP_ROUND_TAG)
                        check_if_early_stop_happened_bst = check_if_key_exist(
                            currentData.metrics, EARLY_STOP_ROUND_METRIC_TAG)

                        if currentData.tags and check_framework_val == XGB_TAG and check_early_stop_rounds_val_bst != 'None' and check_if_early_stop_happened_bst and not check_spark_tag and not check_if_published:
                            parent_path, metric_files = self.get_path_metric(
                                run_id)
                            return bst_payload_store_custom.GetFinalPayloadBST(run_id, currentData, self.root_directory).get_final_payload_and_publish(parent_path, metric_files)

                        elif currentData.tags and check_framework_val == LGBM_TAG and check_early_stop_rounds_val_bst != 'None' and check_if_early_stop_happened_bst and not check_spark_tag and not check_if_published:
                            parent_path, metric_files = self.get_path_metric(
                                run_id)
                            return bst_payload_store_custom_lgbm.GetFinalPayloadBST(run_id, currentData, self.root_directory).get_final_payload_and_publish(parent_path, metric_files)

                        elif currentData.tags and check_bst_tag and check_early_stop_rounds_val_bst == 'None' and currentData.metrics and not check_spark_tag and not check_if_published:
                            parent_path, metric_files = self.get_path_metric(
                                run_id)
                            return bst_payload_store.GetFinalPayloadBST(run_id, currentData, self.root_directory).get_final_payload_and_publish(parent_path, metric_files)

                        if currentData.tags and check_tensorflow_tag and check_early_stop_dl and currentData.metrics and not check_spark_tag and not check_if_published:
                            parent_path, metric_files = self.get_path_metric(
                                run_id)
                            return dl_payload_store_custom.GetFinalPayloadDl(run_id, currentData, self.root_directory).get_final_payload_and_publish(parent_path, metric_files)

                        elif currentData.tags and check_tensorflow_tag and not check_early_stop_dl and currentData.metrics and not check_spark_tag and not check_if_published:
                            parent_path, metric_files = self.get_path_metric(
                                run_id)
                            return dl_payload_store.GetFinalPayloadDl(run_id, currentData, self.root_directory).get_final_payload_and_publish(parent_path, metric_files)

                    elif currentData.tags and currentData.params and currentData.metrics and not check_spark_tag and not check_if_published and not check_tensorflow_tag and not check_bst_tag:
                        return general_payload_store.GetFinalPayloadGeneral(run_id, currentData, self.root_directory).get_final_payload_and_publish()

                elif check_spark_tag and (check_hyp_tag_exist and check_hyp_tag_val != 'None'):
                    if check_spark_tag and currentData.params and currentData.tags and check_estimator_cls_tag:
                        self.parent_run_id = run_id
                        if self.parent_run_id is not None:
                            get_run_data = super().get_run(self.parent_run_id).data
                            check_param_tag = {
                                k: v for k, v in get_run_data.params.items() if k.startswith("best_")}
                            if check_param_tag:
                                return spark_payload_store.GetFinalPayloadSpark(self.parent_run_id, get_run_data, self.root_directory).get_final_payload_and_publish()

                elif check_spark_tag and currentData.params and currentData.tags and check_estimator_cls_tag and not check_hyp_tag_exist:
                    # for run with best scores only
                    # get_run_data_params = super().get_run(run_id).data.params
                    # check_if_hyp = get_run_data_params.get(SPARK_HYP_TAG)
                    # if check_if_hyp:
                    #     pass
                    # else:
                    return spark_payload_store.GetFinalPayloadSpark(run_id, currentData, self.root_directory).get_final_payload_and_publish()
                else:
                    pass

            else:
                raise ClientError("Framework not supported for autologging. Current supported ones are {}. If you are using push frameworks like {}, please use enable_push_framework during client initialization.".format(SUPPORTED_FRAMEWORKS, IS_SPECIAL_FRAMEWORKS))
      
        else:
            pass

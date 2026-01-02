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

import mlflow
import pandas as pd
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from mlflow.utils.file_utils import local_file_uri_to_path
from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.store_utils import _check_root_dir
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.client.autolog import AutoLog
from ibm_aigov_facts_client.client import fact_trace


MAX_RESULTS = 100

_logger = logging.getLogger(__name__)

class Experiments:
    """
        Utility to explore current experiments.

    """

    def __init__(self, root_directory=None):
        self.root_directory = local_file_uri_to_path(
            root_directory or default_root_dir())
        self.client = MlflowClient()
        self._autolog=fact_trace.FactsClientAdapter._autolog
    # def print_experiment_info(self, experiments):
    #     for e in experiments:
    #         return ("- experiment_id: {}, name: {}, lifecycle_stage: {}"
    #                 .format(e.experiment_id, e.name, e.lifecycle_stage))

    # def print_single_experiment_info(self, experiment):
    #     print("- experiment_id: {}, name: {}, lifecycle_stage: {}, tags: {}, location: {} "
    #           .format(experiment.experiment_id, experiment.name, experiment.lifecycle_stage, experiment.tags, experiment.artifact_location))

    def list_experiments(self, max_results: int = MAX_RESULTS)-> "pd.DataFrame":
        """
            List all active experiments.

            :return: `DataFrame` object.
            :rtype: Pandas.DataFrame

            A way you might use me is:

            >>> client.experiments.list_experiments()


        """
        try:
            _check_root_dir(self.root_directory)
            #exp_data = self.client.list_experiments(
            #    view_type=ViewType.ACTIVE_ONLY, max_results=max_results, page_token=None)

            exp_data = self.client.search_experiments(
                view_type=ViewType.ACTIVE_ONLY, max_results=max_results, page_token=None)
            # for exp in exp_data:
                # self.print_single_experiment_info(exp)

            info = {
                    "experiment_id": [],
                    "name": [],
                    "tags": [],
                    "location": [],
                }

            for i, exp in enumerate(exp_data):
                info["experiment_id"].append(exp.experiment_id)
                info["name"].append(exp.name)
                info["tags"].append(exp.tags)
                info["location"].append(exp.artifact_location)
            data = {}
            data.update(info)

        except:
            raise ClientError("Could not list experiments")
        return pd.DataFrame(data)

    def get_current_experiment_id(self):
        """
        Shows current experiment id.

        :return: `str`

        A way you might use me is:

        >>> client.experiments.get_current_experiment_id()
        """
        try:
            if self._autolog:
                cur_exp_id= AutoLog._cur_exp.experiment_id
            else:
                cur_exp_id=mlflow.active_run().info.experiment_id
        except:
            raise ClientError("No active experiment found, please reinitiate client")
        return cur_exp_id

    # def get_experiment(self, experiment_id: str):
    #     """
    #         Get any specific experiment by Id.

    #         :param str experiment_id: Id of the experiment.

    #         A way you might use me is:

    #         >>> client.experiments.get_experiment("1")

    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         exp_info = self.client.get_experiment(experiment_id)
    #         self.print_single_experiment_info(exp_info)
    #     except:
    #         raise ClientError(
    #             "Could not find experiment with id {}".format(experiment_id))

    # def get_experiment_by_name(self, experiment_name: str):
    #     """
    #         Get any specific experiment by name.

    #         :param str experiment_name: Name of the experiment.

    #         A way you might use me is:

    #         >>> client.experiments.get_experiment_by_name("Test")

    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         exp_info = self.client.get_experiment_by_name(experiment_name)
    #         self.print_single_experiment_info(exp_info)
    #     except:
    #         raise ClientError(
    #             "Could not find experiment with name {}".format(experiment_name))

    # def rename_experiment(self, experiment_id: str, new_name: str) -> None:
    #     """
    #         Update experiment name.The new name must be unique.

    #         :param str experiment_id: Id of the experiment.

    #         A way you might use me is:

    #         >>> client.experiments.rename_experiment(experiment_id, "New Exp")

    #     """

    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.rename_experiment(experiment_id, new_name)
    #         return ("Renamed experiment with id {} successfully to {}".format(experiment_id, new_name))
    #     except:
    #         raise ClientError(
    #             "Could not rename experiment with id {}".format(experiment_id))

    # def delete_experiment(self, experiment_id: str) -> None:
    #     """
    #         Delete experiment by Id.

    #         :param str experiment_id: Id of the experiment.

    #         A way you might use me is:

    #         >>> client.experiments.delete_experiment("1")

    #     """

    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.delete_experiment(experiment_id)
    #         return ("Deleted experiment with id {} successfully".format(experiment_id))
    #     except:
    #         raise ClientError(
    #             "Could not delete experiment with id {}".format(experiment_id))

    # def restore_experiment(self, experiment_id: str) -> None:
    #     """
    #         Restore experiment by Id.

    #         :param str experiment_id: Id of the experiment.

    #         A way you might use me is:

    #         >>> client.experiments.restore_experiment("1")

    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.restore_experiment(experiment_id)
    #         return ("Restored experiment with id {} successfully".format(experiment_id))
    #     except:
    #         raise ClientError(
    #             "Could not restore experiment with id {}".format(experiment_id))

    # def set_experiment_tag(self, experiment_id: str, key: str, value: Any) -> None:
    #     """
    #         Set custom tag for any experiment.

    #         :param str experiment_id: Id of the experiment.
    #         :param str key: Name of the tag
    #         :param value: Tag value (converted to string)

    #         A way you might use me is:

    #         >>> client.set_experiment_tag(experiment_id, "nlp.framework", "Scikit NLP")

    #     """

    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.set_experiment_tag(experiment_id, key, value)
    #         return ("Set experiment tag successfully for experiment id: {}".format(experiment_id))
    #     except:
    #         raise ClientError(
    #             "Could not set experiment tag for experiment {}".format(experiment_id))

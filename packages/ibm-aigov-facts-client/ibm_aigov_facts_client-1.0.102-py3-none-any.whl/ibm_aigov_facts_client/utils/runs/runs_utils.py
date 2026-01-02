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
import pandas as pd   # pylint: disable=unused-import
import numpy as np
import time
from mlflow.tracking import MlflowClient
from mlflow.entities import Experiment, Run, RunInfo, RunStatus, Param, RunTag, Metric, ViewType
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from mlflow.utils.file_utils import local_file_uri_to_path
from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.store_utils import _check_root_dir
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.validation import *
from ibm_aigov_facts_client.utils.manual_store_utils import *
from ibm_aigov_facts_client.utils.constants import *

from ibm_aigov_facts_client.custom.custom_file_store import *
from ibm_aigov_facts_client.client import fact_trace

SEARCH_MAX_RESULTS_PANDAS = 10000
SEARCH_MAX_RESULTS = 1000


class Runs:

    """
        Utilities to explore runs within any experiment.

    """

    def __init__(self, root_directory=None):
        self.root_directory = local_file_uri_to_path(
            root_directory or default_root_dir())
        self.client = MlflowClient()
        self._autolog=fact_trace.FactsClientAdapter._autolog

    def list_runs_by_experiment(self, experiment_id: str, order_by: Optional[List[str]] = None) -> "pd.DataFrame":
        """
            List all runs under any experiment

            :param str experiment_id: ID of the experiment.
            :param order_by: List of order_by clauses. Currently supported values are ``metric.key``, ``parameter.key``, ``tag.key``.For example, ``order_by=["tag.release ASC", "metric.training_score DESC"]``

            :return: `DataFrame` object that satisfy the search expressions.
            :rtype: Pandas.DataFrame

            A way you might use me is:  

            >>> client.runs.list_runs_by_experiment("1")

            >>> client.runs.list_runs_by_experiment("1", order_by=["metric.training_score DESC"]))


        """
        try:
            _check_root_dir(self.root_directory)
            #list_data = self.client.list_run_infos(
            #    experiment_id, ViewType.ACTIVE_ONLY, SEARCH_MAX_RESULTS, order_by, page_token=None)
            list_data = self.client.search_runs(
                experiment_ids=[experiment_id], run_view_type=ViewType.ACTIVE_ONLY, max_results=SEARCH_MAX_RESULTS, order_by=order_by, page_token=None)
            
            info = {
                "run_id": [],
                "experiment_id": [],
                "published": [],
                "artifact_uri": [],
                "start_time": [],
                "end_time": [],
            }

            for i, run in enumerate(list_data):
                #info["run_id"].append(run.run_id)
                #info["experiment_id"].append(run.experiment_id)
                info["run_id"].append(run.info.run_id)
                info["experiment_id"].append(run.info.experiment_id)
                # info["status"].append(run.status)
                #status=  self.client.get_run(run.run_id)
                #info["published"].append(status.data.tags.get("facts.publish"))
                #info["artifact_uri"].append(run.artifact_uri)
                info["published"].append(run.data.tags.get("facts.publish"))
                info["artifact_uri"].append(run.info.artifact_uri)
                #info["start_time"].append(pd.to_datetime(
                #    run.start_time, unit="ms", utc=True))
                info["start_time"].append(pd.to_datetime(
                    run.info.start_time, unit="ms", utc=True))
                #info["end_time"].append(pd.to_datetime(
                #    run.end_time, unit="ms", utc=True))
                info["end_time"].append(pd.to_datetime(
                    run.info.end_time, unit="ms", utc=True))
            data = {}
            data.update(info)

        except:
            raise ClientError("Could not list experiments")
        return pd.DataFrame(data)

    def get_current_run_id(self):
        """
            Shows current active run id.

            :return: `str`

            A way you might use me is:

            >>> client.runs.get_current_run_id()
        """
        try:
            if self._autolog:
                cur_run_id=FactSheetStore._cur_runid
            else:
                cur_run_id=mlflow.active_run().info.run_id
        except:
            raise ClientError("No active run found")
        return cur_run_id
    # def search_runs_by_experiment(self, experiment_ids: List[str], filter_string: str = "",
    #                               run_view_type: int = ViewType.ACTIVE_ONLY,
    #                               order_by: Optional[List[str]] = None,) -> Union[List, "pd.DataFrame"]:
    #     """
    #         Search experiments fitting search criteria.

    #         :param experiment_ids: List of experiment IDs, or a single int or string id.
    #         :param str filter_string: Filter query string, defaults to searching all runs.
    #         :param int run_view_type: ACTIVE_ONLY : `1` , DELETED_ONLY: `2`, or ALL: `3` runs
    #         :param order_by: List of columns to order by (e.g., `metrics.mae`). The ``order_by`` column can contain an optional ``DESC`` or ``ASC`` value. The default is ``ASC``. The default ordering is to sort by ``start_time DESC``, then ``run_id``.

    #         :return: `DataFrame` contains Run objects satisfy the search expressions.
    #         :rtype: Pandas.DataFrame

    #         A way you might use me is:

    #         >>> client.runs.search_runs(experiment_id, order_by=["metrics.m DESC"])

    #         >>> filter_string = "tags.facts.estimator_name ILIKE '%sklearn%'"
    #         runs = client.search_runs(experiment_id, run_view_type=ViewType.ACTIVE_ONLY,filter_string=filter_string)

    #     """

    #     try:
    #         _check_root_dir(self.root_directory)

    #         data = self.client.search_runs(
    #             experiment_ids, filter_string, run_view_type, SEARCH_MAX_RESULTS_PANDAS, order_by)
    #     except:
    #         raise ClientError("Could not find any results")
    #     info = {
    #         "run_id": [],
    #         "experiment_id": [],
    #         # "status": [],
    #         "artifact_uri": [],
    #         "start_time": [],
    #         "end_time": [],
    #     }

    #     params, metrics, tags = ({}, {}, {})
    #     PARAM_NULL, METRIC_NULL, TAG_NULL = (None, np.nan, None)

    #     for i, run in enumerate(data):
    #         info["run_id"].append(run.info.run_id)
    #         info["experiment_id"].append(run.info.experiment_id)
    #        # info["status"].append(run.info.status)
    #         info["artifact_uri"].append(run.info.artifact_uri)
    #         info["start_time"].append(pd.to_datetime(
    #             run.info.start_time, unit="ms", utc=True))
    #         info["end_time"].append(pd.to_datetime(
    #             run.info.end_time, unit="ms", utc=True))

    #         # Params
    #         param_keys = set(params.keys())
    #         for key in param_keys:
    #             if key in run.data.params:
    #                 params[key].append(run.data.params[key])
    #             else:
    #                 params[key].append(PARAM_NULL)
    #         new_params = set(run.data.params.keys()) - param_keys
    #         for p in new_params:
    #             # Fill in null values for all previous runs
    #             params[p] = [PARAM_NULL] * i
    #             params[p].append(run.data.params[p])

    #         # Metrics
    #         metric_keys = set(metrics.keys())
    #         for key in metric_keys:
    #             if key in run.data.metrics:
    #                 metrics[key].append(run.data.metrics[key])
    #             else:
    #                 metrics[key].append(METRIC_NULL)
    #         new_metrics = set(run.data.metrics.keys()) - metric_keys
    #         for m in new_metrics:
    #             metrics[m] = [METRIC_NULL] * i
    #             metrics[m].append(run.data.metrics[m])

    #         # Tags
    #         tag_keys = set(tags.keys())
    #         for key in tag_keys:
    #             if key in run.data.tags:
    #                 tags[key].append(run.data.tags[key])
    #             else:
    #                 tags[key].append(TAG_NULL)
    #         new_tags = set(run.data.tags.keys()) - tag_keys
    #         for t in new_tags:
    #             tags[t] = [TAG_NULL] * i
    #             tags[t].append(run.data.tags[t])

    #     data = {}
    #     data.update(info)
    #     for key in metrics:
    #         data["metrics." + key] = metrics[key]
    #     for key in params:
    #         data["params." + key] = params[key]
    #     for key in tags:
    #         data["tags." + key] = tags[key]

    #     return pd.DataFrame(data)

    # def get_run_details(self, run_id: str) -> "pd.DataFrame":
    #     """
    #         Fetch run data from store as a collection of run parameters, tags, and metrics.In the case where multiple metrics with the same key are logged for the run, it contains the most recently logged value at the largest step for each metric.

    #         :param str run_id: Unique identifier for the run.

    #         :return: A single run object, if the run exists. Otherwise, raises an exception.
    #         :rtype: Pandas.DataFrame

    #         A way you might use me is:

    #         >>> client.runs.get_run_details("run_id")
    #     """

    #     try:
    #         _check_root_dir(self.root_directory)
    #         details = self.client.get_run(run_id)

    #         allmetrics = []
    #         for metric_file in metric_files:
    #             final_metrics, num_max_step = get_metric_from_file_custom(
    #                 parent_path, metric_file)
    #         allmetrics.append(final_metrics)

    #         info = {
    #             "run_id": [],
    #             "experiment_id": [],
    #             # "status": [],
    #             "artifact_uri": [],
    #             "start_time": [],
    #             "end_time": [],
    #         }

    #         params, metrics, tags = ({}, {}, {})
    #         PARAM_NULL, METRIC_NULL, TAG_NULL = (None, np.nan, None)

    #         info["run_id"].append(details.info.run_id)
    #         info["experiment_id"].append(details.info.experiment_id)
    #         # info["status"].append(details.info.status)
    #         info["artifact_uri"].append(details.info.artifact_uri)
    #         info["start_time"].append(pd.to_datetime(
    #             details.info.start_time, unit="ms", utc=True))
    #         info["end_time"].append(pd.to_datetime(
    #             details.info.end_time, unit="ms", utc=True))

    #         # Params
    #         param_keys = set(params.keys())
    #         for key in param_keys:
    #             if key in details.data.params:
    #                 params[key].append(details.data.params[key])
    #             else:
    #                 params[key].append(PARAM_NULL)
    #         new_params = set(details.data.params.keys()) - param_keys
    #         for p in new_params:
    #             # Fill in null values for all previous runs
    #             params[p] = [PARAM_NULL] * 0
    #             params[p].append(details.data.params[p])

    #         # Metrics
    #         metric_keys = set(metrics.keys())
    #         for key in metric_keys:
    #             if key in details.data.metrics:
    #                 metrics[key].append(details.data.metrics[key])
    #             else:
    #                 metrics[key].append(METRIC_NULL)
    #         new_metrics = set(details.data.metrics.keys()) - metric_keys
    #         for m in new_metrics:
    #             metrics[m] = [METRIC_NULL] * 0
    #             metrics[m].append(details.data.metrics[m])

    #         # Tags
    #         tag_keys = set(tags.keys())
    #         for key in tag_keys:
    #             if key in details.data.tags:
    #                 tags[key].append(details.data.tags[key])
    #             else:
    #                 tags[key].append(TAG_NULL)
    #         new_tags = set(details.data.tags.keys()) - tag_keys
    #         for t in new_tags:
    #             tags[t] = [TAG_NULL] * 0
    #             tags[t].append(details.data.tags[t])

    #         data = {}
    #         data.update(info)
    #         for key in metrics:
    #             data["metrics." + key] = metrics[key]
    #         for key in params:
    #             data["params." + key] = params[key]
    #         for key in tags:
    #             data["tags." + key] = tags[key]

    #     except:
    #         raise ClientError("Cloud not get run details")
    #     return pd.DataFrame(data)

    def log_metric(self, run_id: str, key: str, value: float, step: Optional[int] = None) -> None:
        """
            Log a metric against the run ID.

            :param str run_id: The unique id for run.
            :param str key: Metric name.
            :param float value: Metric value (float).
            :param int step: Integer training step (iteration) at which was the metric calculated. Defaults to 0.

            :returns: None

            A way you might use me is:  

            >>> client.runs.log_metric(run_id, "mae", .77)

        """
        try:
            _check_root_dir(self.root_directory)
            self.client.log_metric(
                run_id, key, value, int(time.time()*1000), step or 0)

            return ("Successfully logged metric {} under run {}".format(key, run_id))
        except:
            raise ClientError("Could not log metric")

    def log_data(self, run_id, data, folder):
        if len(data) == 0:
            return

        validate_run_id(run_id)
        _, run_info = get_run_data(run_id)

        if folder == METRICS_FOLDER_NAME:
            for val in data:
                validate_metric(val.key, val.value,
                                val.timestamp, val.step)

            for metric in data:
                metric_path = os.path.join(get_run_dir(
                    run_info.experiment_id, run_info.run_id, self.root_directory), METRICS_FOLDER_NAME, metric.key)
                make_containing_dirs(metric_path)
                append_to(metric_path, "%s %s %s\n" %
                          (metric.timestamp, metric.value, metric.step))

        if folder == PARAMS_FOLDER_NAME:
            for val in data:
                validate_param(val.key, val.value)

            for param in data:
                param_path = os.path.join(get_run_dir(
                    run_info.experiment_id, run_info.run_id, self.root_directory), PARAMS_FOLDER_NAME, param.key)
                write_value = writeable_value(param.value)
                if os.path.exists(param_path):
                    validate_new_param_value(param_path=param_path,
                                             param_key=param.key,
                                             run_id=run_info.run_id,
                                             new_value=write_value)
                make_containing_dirs(param_path)
                write_to(param_path, write_value)

        if folder == TAGS_FOLDER_NAME:
            for val in data:
                validate_tag(val.key, val.value)
            for tag in data:
                tag_path = os.path.join(get_run_dir(
                    run_info.experiment_id, run_info.run_id, self.root_directory), TAGS_FOLDER_NAME, tag.key)
                write_value = writeable_value(tag.value)
                make_containing_dirs(tag_path)
                write_to(tag_path, write_value)

    def log_metrics(self, run_id: str, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
            Log multiple metrics for the given run.

            :param str run_id: The unique id for run.
            :param dict metrics: Dictionary of metric_name: String -> value: Float.
            :param int step: Integer training step (iteration) at which was the metric calculated. Defaults to 0.

            :returns: None

            A way you might use me is:  

            >>> client.runs.log_metrics(run_id, {"mse": 2000.00, "rmse": 50.00})

        """

        try:
            _check_root_dir(self.root_directory)
            metrics_data = [Metric(key, value, int(
                time.time()*1000), step or 0) for key, value in metrics.items()]

            self.log_data(run_id, metrics_data, METRICS_FOLDER_NAME)
            return ("Successfully set metrics under run {}".format(run_id))
        except:
            raise ClientError("Could not log metrics")

    def log_param(self, run_id: str, key: str, value: Any) -> None:
        """
            Log a param against the run ID.

            :param str run_id: The unique id for run.
            :param str key: Param name.
            :param value: Param value.Value is converted to a string.

            :returns: None

            A way you might use me is:  

            >>> client.runs.log_param(run_id, "c", 1)

        """
        try:
            _check_root_dir(self.root_directory)
            self.client.log_param(
                run_id, key, value)

            return ("Successfully logged param {} under run {}".format(key, run_id))
        except:
            raise ClientError("Could not log param")

    def log_params(self, run_id, params: Dict[str, Any]) -> None:
        """
            Log multiple params for the given run.

            :param str run_id: The unique id for run.
            :param dict params: Dictionary of String -> value: (String, but will be string-ified if not)

            :returns: None

            A way you might use me is:  

            >>> client.runs.log_params(run_id, {"n_estimators": 3, "random_state": 42})

        """
        try:
            _check_root_dir(self.root_directory)
            params_data = [Param(key, str(value))
                           for key, value in params.items()]
            self.log_data(run_id, params_data, PARAMS_FOLDER_NAME)
            return ("Successfully set params under run {}".format(run_id))
        except:
            raise ClientError("Could not log params")

    def set_tags(self, run_id: str, tags: Dict[str, Any]) -> None:
        """
            Log multiple tags for the given run.

            :param str run_id: The unique id for run.
            :param dict tags: Dictionary of tags names: String -> value: (String, but will be string-ified if not)

            :returns: None

            A way you might use me is:  

            >>> client.runs.set_tags(run_id, {"engineering": "ML Platform",
            "release.candidate": "RC1"})

        """
        try:
            _check_root_dir(self.root_directory)
            tags_data = [RunTag(key, str(value))
                         for key, value in tags.items()]
            self.log_data(run_id, tags_data, TAGS_FOLDER_NAME)
            return ("Successfully set tags under run {}".format(run_id))
        except:
            raise ClientError("Could not set tags")

    # def delete_tag(self, run_id: str, key: str) -> None:
    #     """
    #         Delete a tag from a run. This is irreversible.

    #         :param str run_id: String ID of the run
    #         :param str key: Name of the tag

    #          A way you might use me is:

    #         >>> client.runs.delete_tag(run_id, "release.candidate")
    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.delete_tag(run_id, key)
    #         return ("Successfully deleted tag from run {}".format(run_id))
    #     except:
    #         raise ClientError("Could not delete tag")

    # def delete_run(self, run_id: str) -> None:
    #     """
    #         Deletes a run with the given ID.

    #         :param str run_id: The unique run id to delete.

    #         A way you might use me is:

    #         >>> client.runs.delete_run("run_id")

    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.delete_run(run_id)
    #         return ("Deleted experiment with run id {} successfully".format(run_id))
    #     except:
    #         raise ClientError("Could not delete experiment")

    # def restore_run(self, run_id: str) -> None:
    #     """
    #         Restore a run with the given ID.

    #         :param str run_id: The unique run id to restore.

    #         A way you might use me is:

    #         >>> client.runs.restore_run("run_id")

    #     """
    #     try:
    #         _check_root_dir(self.root_directory)
    #         self.client.restore_run(run_id)
    #         return ("Restored run with id {} successfully".format(run_id))
    #     except:
    #         raise ClientError("Could not restore experiment")

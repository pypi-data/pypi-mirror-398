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
from ..utils.client_errors import *
from ..utils.logging_utils import *
from ibm_aigov_facts_client.store.manual.manuallog_utils import *
from ..utils.utils import *

_logger = logging.getLogger(__name__)


class ManualLog:

    """
    Enables user to trace experiments from external machine learning engines manually.
    """

    _cur_exp = None

    def __init__(self, experiment_name=None, set_as_current_exp=None, root_dir=None):
        clean_uri()
        self.experiment_name = experiment_name
        self.run_id=None

        self.root_directory = local_file_uri_to_path(
            root_dir or default_root_dir())
        self.trash_folder = os.path.join(self.root_directory, TRASH_FOLDER)
        self.set_as_current_exp = set_as_current_exp

        #needed for pytorch as it overwrites logger
        clear_up_handler()

        if not self.set_as_current_exp:
            self.__create_experiment()
            clean_default_exp()
        else:
            self.__check_set_experiment()

    def __create_experiment(self):

        if exists(self.root_directory):
            existing_exp = get_experiment_by_name(self.experiment_name)

            if existing_exp is None:
                exp_id = create_experiment(self.experiment_name)
                set_experiment(self.experiment_name)
                _logger.info("Experiment successfully created with ID {} and name {}".format(
                    exp_id, self.experiment_name))
            else:
                raise UnexpectedValue(
                    "Experiment with same name already exists")
        else:
            mkdir(self.root_directory)
            mkdir(self.trash_folder)

            create_experiment()
            clean_default_exp()

            exp_id = create_experiment(self.experiment_name)
            set_experiment(self.experiment_name)
            _logger.info("Experiment successfully created with ID {} and name {}".format(
                exp_id, self.experiment_name))

        ManualLog._cur_exp = get_experiment_by_name(
            self.experiment_name)

    def __check_set_experiment(self):
        existing_experiment = get_experiment_by_name(
            self.experiment_name)
        if existing_experiment is not None:
            set_experiment(self.experiment_name)
            _logger.info("Successfully set {} as current experiment".format(
                self.experiment_name))
            ManualLog._cur_exp = get_experiment_by_name(self.experiment_name)
        else:
            try:
                _logger.info(" Experiment {} does not exist, creating new experiment".format(
                    self.experiment_name))
                self.__create_experiment()
                clean_default_exp()
            except:
                raise ClientError(
                    "Something went wrong when setting current experiment")

    def start_trace(self, experiment_id: str = None):
        """
            Start a tracing session when using manual log option. By default it uses the current experiment used in client initialization.

            :param str experiment_id: (Optional) ID of experiment. This will start logging session under specific experiment so runs will be under specific experiment.
            
            A way you might use me is:

            >>> client.manual_log.start_trace()
            >>> client.manual_log.start_trace(experiment_id="1")

        """
        if experiment_id:
            start_trace(experiment_id=experiment_id)
        else:
            start_trace()

        run = get_active_run()
        if run:
            self.run_id=run.info.run_id
            clean_tags(self.run_id)
        #set_guid_tag(run.info.run_id)
        _logger.info ("Manual tracing initiated successfully under run {}".format(self.run_id))

    def log_metric(self, key: str, value: float, step: Optional[int] = None) -> None:
        """
            Log a metric against active run.

            :param str key: Metric name.
            :param float value: Metric value (float).
            :param int step: Integer training step (iteration) at which was the metric calculated. Defaults to 0.

            :returns: None

            A way you might use me is:

            >>> client.manual_log.log_metric("mae", .77)

        """
        try:
            log_metric_data(key, value, step)
            _logger.info ("logged metric {} successfully under run {}".format(key,self.run_id))
        except:
            raise ClientError("Could not log metric {}".format(key))

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """
            Log multiple metrics under active run.

            :param dict metrics: Dictionary of metric_name: String -> value: Float.
            :param int step: Integer training step (iteration) at which was the metric calculated. Defaults to 0.

            :returns: None

            A way you might use me is:

            >>> client.manual_log.log_metrics({"mse": 2000.00, "rmse": 50.00})

        """
        try:
            log_metrics_data(metrics, step)
            _logger.info ("logged metrics {} successfully under run {}".format(list(metrics.keys()),self.run_id))
        except:
            raise ClientError("Could not log metrics")

    def log_param(self, key: str, value: Any) -> None:
        """
            Log a param against active run.

            :param str key: Param name.
            :param value: Param value.Value is converted to a string.

            :returns: None

            A way you might use me is:

            >>> client.manual_log.log_param("c", 1)

        """

        try:
            log_param_data(key, value)
            _logger.info ("logged param {} successfully under run {}".format(key,self.run_id))
        except:
            raise ClientError("Could not log param {}".format(key))

    def log_params(self, params: Dict[str, Any]) -> None:
        """
            Log multiple params under active run.

            :param dict params: Dictionary of String -> value: (String, but will be string-ified if not)

            :returns: None

            A way you might use me is:

            >>> client.manual_log.log_params({"n_estimators": 3, "random_state": 42})

        """
        try:
            log_params_data(params)
            _logger.info ("logged params {} successfully under run {}".format(list(params.keys()),self.run_id))
        except:
            raise ClientError("Could not log params")

    def set_tag(self, key: str, value: Any) -> None:
        """
            Log tag for active run.

            :param str key: Param name.
            :param value: Param value.Value is converted to a string.

            :returns: None

            A way you might use me is:

            >>> client.manual_log.set_tag("engineering", "ML Platform")

        """
        try:
            log_tag_data(key, value)
            _logger.info ("logged tag {} successfully under run {}".format(key,self.run_id))
        except:
            raise ClientError("Could not log tag {}".format(key))

    def set_tags(self, tags: Dict[str, Any]) -> None:
        """
            Log multiple tags for active run.

            :param dict tags: Dictionary of tags names: String -> value: (String, but will be string-ified if not)

            :returns: None

            A way you might use me is:

            >>> client.manual_log.set_tags({"engineering": "ML Platform",
            "release.candidate": "RC1"})

        """
        try:
            log_tags_data(tags)
            _logger.info ("logged tags {} successfully under run {}".format(list(tags.keys()),self.run_id))
        except:
            raise ClientError("Could not log tags")

    def end_trace(self):
        """
            End an active session.

            A way you might use me is:

            >>> client.manual_log.end_trace()
        """
        end_trace()
        _logger.info ("Manual tracing ended successfully for run {}".format(self.run_id))

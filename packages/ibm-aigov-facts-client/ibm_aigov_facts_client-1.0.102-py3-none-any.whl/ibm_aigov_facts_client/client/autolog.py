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
from ibm_aigov_facts_client.store.autolog.autolog_utils import *

from ..utils.utils import *
from ..utils.client_errors import *
from ..utils.logging_utils import *

from ..utils.constants import *


_logger = logging.getLogger(__name__)


class AutoLog:

    _cur_exp = None

    def __init__(self,  experiment_name=None, set_as_current_exp=None, root_dir=None):

        clean_uri()
        
        self.experiment_name = experiment_name
        self.root_directory = local_file_uri_to_path(
            root_dir or default_root_dir())
        self.trash_folder = os.path.join(self.root_directory, TRASH_FOLDER)

        self.set_as_current_exp = set_as_current_exp

        clear_up_handler()

        if not self.set_as_current_exp:
            self.create_experiment()
            clean_default_exp()
        else:
            self.check_set_experiment()

    def create_experiment(self):

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

        AutoLog._cur_exp = get_experiment_by_name(
            self.experiment_name)
        enable_autolog()

    def check_set_experiment(self):
        existing_experiment = get_experiment_by_name(
            self.experiment_name)
        if existing_experiment is not None:
            set_experiment(self.experiment_name)
            _logger.info("Successfully set {} as current experiment".format(
                self.experiment_name))
            AutoLog._cur_exp = get_experiment_by_name(self.experiment_name)
            enable_autolog()
        else:
            try:
                _logger.info("Experiment {} does not exist, creating new experiment".format(
                    self.experiment_name))
                self.create_experiment()
                clean_default_exp()
            except:
                raise ClientError(
                    "Something went wrong when setting current experiment")

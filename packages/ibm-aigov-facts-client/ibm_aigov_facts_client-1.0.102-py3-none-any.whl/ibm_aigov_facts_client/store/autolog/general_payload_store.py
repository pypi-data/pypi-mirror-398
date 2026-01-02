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
import functools
from ibm_aigov_facts_client.store.abstract_payload_store import AbstractPayloadStore

from ibm_aigov_facts_client.client import fact_trace
from ibm_aigov_facts_client.custom import custom_file_store
from ibm_aigov_facts_client.custom import custom_exp
from ibm_aigov_facts_client.export import export_facts

from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.store_utils import *
from ibm_aigov_facts_client.store.autolog.decorators import *


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


    def publish_to_facts(self, run_id, current_data):
        export_facts.ExportFactsAutolog(run_id=run_id, guid=self.exp_guid).add_payload(
            payload=current_data)

    @clean_payload.format_tags()
    def get_final_payload_and_publish(self, parent_path=None, metric_files=None):

        self.set_guid_tag(self.run_id)

        check_auth = check_if_auth_used(
            fact_trace.FactsClientAdapter._authenticator)

        if check_auth:
            _logger.info(
                "logging results to factsheet for run_id {}".format(self.run_id))
            self.publish_to_facts(
                self.run_id, self.current_data)
        elif type(fact_trace.FactsClientAdapter._authenticator) in [NoAuthAuthenticator]:
            pass
        else:
            _logger.error(
                "You are not authorized to push to factsheet service")
            raise

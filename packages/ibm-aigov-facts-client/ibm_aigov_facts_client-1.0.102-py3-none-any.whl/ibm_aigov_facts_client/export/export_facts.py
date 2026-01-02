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


from ibm_aigov_facts_client.utils.utils import validate_type
from ibm_cloud_sdk_core import BaseService, DetailedResponse

from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator, CloudPakForDataAuthenticator, IAMAuthenticator, MCSPV2Authenticator 
from ibm_aigov_facts_client.base_classes.auth import FactsheetServiceClientAutolog
from ibm_aigov_facts_client.client import fact_trace, autolog, manual_log
from typing import Any, Dict

from ibm_aigov_facts_client.store.manual import bst_payload_manual, dl_payload_manual, spark_payload_manual, general_payload_manual
from ibm_aigov_facts_client.custom import custom_file_store, custom_exp

from ibm_aigov_facts_client.utils.utils import *
from ibm_aigov_facts_client.utils.manual_store_utils import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.logging_utils import *
from ..utils.config import *

from datetime import datetime


_logger = logging.getLogger(__name__)


class ExportFacts(FactsheetServiceClientAutolog):
    """ Export updated payloads for any run
    """

    def __init__(self, facts_service_client: 'fact_trace.FactsClientAdapter', **kwargs) -> None:
        validate_type(facts_service_client,
                      'facts_service_client', BaseService, True)
        self._factsheet_service_client = facts_service_client
        if fact_trace.FactsClientAdapter._autolog:
            self.experiment_name = autolog.AutoLog._cur_exp.name
        else:
            self.experiment_name = manual_log.ManualLog._cur_exp.name
        self.guid = None
        self.container_type = fact_trace.FactsClientAdapter._container_type
        self.container_id = fact_trace.FactsClientAdapter._container_id
        self.authenticator = fact_trace.FactsClientAdapter._authenticator
        self.external=fact_trace.FactsClientAdapter._external
        self.is_cp4d=fact_trace.FactsClientAdapter._is_cp4d
        self.final_payload = {}
        self.root_directory = None

        super().__init__(factsheet_auth_client=self._factsheet_service_client)

    def check_tags(self, run_id):
        run_data, _ = get_run_data(run_id)
        check_spark_tag = check_if_any_values_exist_custom(
            run_data.tags, SPARK_FRAMEWORKS)
        check_tensorflow_tag = check_if_any_values_exist_custom(
            run_data.tags, DL_FRAMEWORKS)
        check_estimator_cls_tag = check_if_keys_exist(
            run_data.tags, SPARK_ESTIMATOR_CLS)
        check_bst_tag = check_if_any_values_exist_custom(
            run_data.tags, BST_FRAMEWORKS)

        return check_bst_tag, check_spark_tag, check_tensorflow_tag, check_estimator_cls_tag

    def export_payload(self, run_id: str, root_directory: str = None) -> DetailedResponse:
        
        """
        Export single run to factsheet service. 

        :param str run_id: Id of run to be exported
        :param str root_directory: (Optional) Absolute path for directory containing   experiments and runs.
        :return: A `DetailedResponse` containing the factsheet response result
        :rtype: DetailedResponse

        A way you might use me is:

        >>> client.export_facts.export_payload(<RUN_ID>)

        """

        self.root_directory = local_file_uri_to_path(
            root_directory or default_root_dir())
        exp_id = check_exp(run_id)

        if check_if_auth_used(self.authenticator):
            if self.is_cp4d:
                self.token=self.authenticator.get_cp4d_auth_token()
            elif aws_env() in {'aws_dev', 'aws_test', 'aws_mumbai'}:
                self.token = self.authenticator.token_manager.get_token() if isinstance(
                    self.authenticator, MCSPV2Authenticator) else self.authenticator.bearer_token       
            else:
                self.token = self.authenticator.token_manager.get_token() if isinstance(
                    self.authenticator, IAMAuthenticator) else self.authenticator.bearer_token

            if self.token:
                run_data, _ = get_run_data(run_id)
                check_cur_framework = check_framework_support_manual(
                    run_data.tags, SUPPORTED_FRAMEWORKS+IS_SPECIAL_FRAMEWORKS)

                if check_cur_framework:
                    bst_tag, spark_tag, tf_tag, est_cls_tag = self.check_tags(
                        run_id)

                    if tf_tag:
                        if check_cur_framework == "pytorch":
                            clear_up_handler()

                        payload = dl_payload_manual.GetFinalPayloadDl().get_payload_and_publish(
                            self.root_directory, exp_id, run_id)

                    elif bst_tag:
                        payload = bst_payload_manual.GetFinalPayloadBST().get_payload_and_publish(
                            self.root_directory, exp_id, run_id)

                    elif spark_tag and est_cls_tag:
                        payload = spark_payload_manual.GetFinalPayloadSpark().get_payload_and_publish(
                            self.root_directory, exp_id, run_id)
                    else:
                        payload = general_payload_manual.GetFinalPayloadGeneral().get_payload_and_publish(
                            self.root_directory, exp_id, run_id)

                    self.final_payload["notebook_experiment"] = payload
                    _logger.info(
                        "Initiating logging to factsheet for run_id......{}".format(run_id))
                    super().add_payload(run_id=run_id,
                                        token=self.token,
                                        container_type=self.container_type,
                                        container_id=self.container_id, payload=self.final_payload,external=self.external,is_cp4d=self.is_cp4d)

                else:
                    raise ClientError("Invalid framework of support used")

            else:
                raise AuthorizationError(
                    "Could not authenticate, invalid token")

 

    def prepare_model_meta(self, wml_client: object, meta_props: Dict[str, Any], experiment_name: str = None) -> Dict:
        """
        Add current experiment attributes to model meta properties 

        :param object wml_client: Watson Machine learning client object.
        :param dict meta_props: Current model meta properties.
        :param str experiment_name: (Optional) Explicit name any experiment to be used.  
        :return: A `Dict` containing the updated meta properties.
        :rtype: Dict

        A way you might use me is:

        >>> client.export_facts.prepare_model_meta(wml_client=<wml_client>,meta_props=<wml_model_meta_props>)

        """

        if wml_client is None:
            raise MissingValue("client", "WML Client object is missing")

        if meta_props is None:
            raise MissingValue(
                "meta_props", "WML model meta properties missing")

        if experiment_name is None and fact_trace.FactsClientAdapter._autolog:
            experiment_name = autolog.AutoLog._cur_exp.name
            guid = custom_exp.GenerateExpId().get_exp_guid(
                self.experiment_name)
        elif experiment_name is None and not fact_trace.FactsClientAdapter._autolog:
            experiment_name = manual_log.ManualLog._cur_exp.name
            guid = custom_exp.GenerateExpId().get_exp_guid(
                experiment_name)
        else:
            experiment_name = experiment_name
            guid = custom_exp.GenerateExpId().get_exp_guid(experiment_name)

        meta_props[wml_client._models.ConfigurationMetaNames.CUSTOM] = {
            "experiment_id": guid, "experiment_name": experiment_name}

        return meta_props


class ExportFactsAutolog(FactsheetServiceClientAutolog):
    """
    Generate and export payload to factsheet as part of autolog
    """

    def __init__(self, run_id, guid) -> None:
        self.final_payload = {}
        self.token = None
        self.experiment = None
        self.run_id = run_id
        self.guid = guid
        self.container_type = fact_trace.FactsClientAdapter._container_type
        self.container_id = fact_trace.FactsClientAdapter._container_id
        self.authenticator = fact_trace.FactsClientAdapter._authenticator
        self.external=fact_trace.FactsClientAdapter._external
        self.is_cp4d=fact_trace.FactsClientAdapter._is_cp4d

        super().__init__()

    def gen_payload(self, payload, **kwargs):
        experiments = []
        runs = {}
        tmp_payload = {}
        artifacts = []

        tmp_payload["name"] = autolog.AutoLog._cur_exp.name
        tmp_payload["experiment_id"] = self.guid

        runs["run_id"] = self.run_id
        runs["created_date"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        if payload.metrics and "data" not in payload.metrics:
            runs["metrics"] = [{"key": k, "value": v}
                               for (k, v) in payload.metrics.items()]

        elif payload.metrics and "data" in payload.metrics:
            runs["metrics"] = payload.metrics["data"]
        else:
            runs["metrics"] = []

        if payload.params:
            runs["params"] = [{"key": k, "value": v}
                              for (k, v) in payload.params.items()]
        else:
            runs["params"] = []
        if payload.tags:
            runs["tags"] = [{"key": k, "value": v}
                            for (k, v) in payload.tags.items()]
        else:
            runs["tags"] = []

        runs["artifacts"] = artifacts

        experiments.append(runs)

        tmp_payload["runs"] = experiments

        return tmp_payload

    def add_payload(self, payload=None, **kwargs) -> 'DetailedResponse':
        if type(self.authenticator) in [CloudPakForDataAuthenticator,CP4DAuthenticator, IAMAuthenticator, BearerTokenAuthenticator]:
            if self.is_cp4d:
                self.token=self.authenticator.get_cp4d_auth_token()
            else:
                self.token = self.authenticator.token_manager.get_token() if isinstance(
                    self.authenticator, IAMAuthenticator) else self.authenticator.bearer_token
        

            self.final_payload["notebook_experiment"] = self.gen_payload(
                payload)
            
            super().add_payload(run_id=self.run_id,
                                token=self.token,
                                container_type=self.container_type,
                                container_id=self.container_id, payload=self.final_payload,external=self.external,is_cp4d=self.is_cp4d)

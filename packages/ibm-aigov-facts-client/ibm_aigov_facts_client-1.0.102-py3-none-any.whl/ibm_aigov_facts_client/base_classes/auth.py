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

from typing import Any, Dict
import json
#import requests

import ibm_aigov_facts_client._wrappers.requests as requests

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


from ibm_cloud_sdk_core import BaseService, DetailedResponse
from ibm_cloud_sdk_core.authenticators.authenticator import Authenticator
from ibm_aigov_facts_client.client import fact_trace

from ..utils.constants import *
from ..utils.enums import ContainerType

from ..utils.client_errors import *
from ..utils.store_utils import set_custom_tag_autolog
from ..utils.config import *
from ibm_aigov_facts_client.utils.asset_context import AssetContext


_logger = logging.getLogger(__name__)

##############################################################################
# Auth Service
##############################################################################


class FactsAuthClient(BaseService):
    """IBM Facts Auth Client."""

    DEFAULT_SERVICE_URL = None

    def __init__(self,
                 authenticator: Authenticator = None,
                 ) -> None:
        """
        Construct a new client for Facts Client Utility.
        :param Authenticator authenticator: The authenticator specifies the authentication mechanism.
               Get up to date information from https://github.com/IBM/python-sdk-core/blob/master/README.md
               about initializing the authenticator of your choice.
        """
        BaseService.__init__(self,
                             # service_url=self.DEFAULT_SERVICE_URL,
                             authenticator=authenticator)

class FactsheetServiceClientAutolog:

    def __init__(self, factsheet_auth_client=None) -> None:

        self.factsheet_service_client = factsheet_auth_client
        self.asset_id=None
    
    
    def add_payload(self, container_type: str, container_id: str, run_id: str, token: str, payload: Dict[str, Any], external:bool,is_cp4d:bool, **kwargs) -> DetailedResponse:
        
        headers = {}
        params={}
        
        self.run_id = run_id
        self.container_type = container_type
        self.container_id = container_id
        self.is_cp4d=is_cp4d
        self.asset_id = None 
        

        if not external:
            if self.container_type == ContainerType.SPACE:
                params_key=CONTAINER_SPACE                 
            elif self.container_type == ContainerType.PROJECT: 
                params_key=CONTAINER_PROJECT

            params[params_key]=self.container_id
        else:
            params.update(external_model=external)

        
        data = json.dumps(payload)
        headers["Authorization"] = "Bearer " + token
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        if self.is_cp4d:
            url = fact_trace.FactsClientAdapter._authenticator.token_manager.url + \
                '/v1/aigov/factsheet/notebook_experiments'
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'
       # try:
        # _logger.debug(
            # "Sending payload to factsheet......... {}".format(data))
        response = requests.post(url=url,
                                 headers=headers,
                                 params=params,
                                 data=data)
        
       
        if not response:
            if self.run_id:
                set_custom_tag_autolog(self.run_id)

        if response.status_code == 403:
            set_custom_tag_autolog(self.run_id)
            _logger.exception(response.json()['message'])
            raise

        elif response.status_code == 401:
            set_custom_tag_autolog(self.run_id)
            _logger.exception("Expired token found.")
            raise

        elif response.status_code == 201:
            if "metadata" in response.json():
                self.asset_id = response.json()["metadata"]["asset_id"]
                self.catalog_id = response.json().get("metadata", {}).get("catalog_id")

            else:
                self.asset_id = response.json()["asset_id"]
                self.catalog_id = response.json().get("metadata", {}).get("catalog_id")

            if self.run_id and self.asset_id:
                set_custom_tag_autolog(self.run_id, "True")

            # _logger.debug("Successfully logged results to Factsheet service for run_id {} under asset_id: {} and space_id : {} and result is {}".format(
            #     self.run_id, asset_id, self.container_id, response.json()))

            if not external and params_key is not None:
                _logger.info("Successfully logged results to Factsheet service for run_id {} under asset_id: {} and {} : {}".format(
                    self.run_id, self.asset_id, params_key, self.container_id))
            else:
                _logger.info("Successfully logged results to Factsheet service for run_id {} under asset_id: {} ".format(
                    self.run_id, self.asset_id))
            
            AssetContext.set_asset_id(self.asset_id)
            AssetContext.set_catalog_id(self.catalog_id)

        else:
            set_custom_tag_autolog(self.run_id)
            _logger.error(
                "Something went wrong when publishing to factsheet. ERROR: {}.{}".format(str(response.status_code),response.text))

class FactsheetServiceClientManual:

    def __init__(self, factsheet_auth_client=None) -> None:
        

        self.factsheet_service_client = factsheet_auth_client
        self.asset_id=None

    def add_payload(self,run_id: str, token: str, payload: Dict[str, Any],external:bool,is_cp4d:bool,container_type: str=None, container_id: str=None, **kwargs) -> DetailedResponse:
        headers = {}
        params={}
        
        self.run_id = run_id
        self.container_type = container_type
        self.container_id = container_id
        self.is_cp4d=is_cp4d
        self.asset_id = None 
        

        if not external:
            if self.container_type == ContainerType.SPACE:
                params_key=CONTAINER_SPACE                 
            elif self.container_type == ContainerType.PROJECT: 
                params_key=CONTAINER_PROJECT

            params[params_key]=self.container_id
        else:
            params.update(external_model=external)
        
        data = json.dumps(payload)

        headers["Authorization"] = "Bearer " + token
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        if self.is_cp4d:
            url = fact_trace.FactsClientAdapter._authenticator.token_manager.url + \
                '/v1/aigov/factsheet/notebook_experiments'
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v1/aigov/factsheet/notebook_experiments'


        response = requests.post(url=url,
                                 headers=headers,
                                 params=params,
                                 data=data)


        if not response:
            if self.run_id:
                set_custom_tag_autolog(self.run_id)

        if response.status_code == 403:
            set_custom_tag_autolog(self.run_id)
            _logger.exception(response.json()['message'])
            raise

        elif response.status_code == 401:
            set_custom_tag_autolog(self.run_id)
            _logger.exception("Expired token found.")
            raise

        elif response.status_code == 201:
            if "metadata" in response.json():
                self.asset_id = response.json()["metadata"]["asset_id"]
            else:
                self.asset_id = response.json()["asset_id"]
            
            if self.run_id and self.asset_id:
                set_custom_tag_autolog(self.run_id, "True")

            # _logger.debug("Successfully logged results to Factsheet service for run_id {} under asset_id: {}  and result is {}".format(
            #     self.run_id, asset_id, response.json()))

            _logger.info("Successfully logged results to Factsheet service for run_id {} under asset_id: {} ".format(
                    self.run_id, self.asset_id))
            
            AssetContext.set_asset_id(self.asset_id)

        else:
            set_custom_tag_autolog(self.run_id)
            _logger.error(
                "Something went wrong when exporting to factsheet. ERROR: {}.{}".format(str(response.status_code),response.text))
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
from typing import Dict
import jwt
import json
#import requests
import pandas as pd
import ibm_aigov_facts_client._wrappers.requests as requests
from ibm_aigov_facts_client.utils.constants import *

from ibm_cloud_sdk_core.authenticators.iam_authenticator import IAMAuthenticator
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.enums import FactsType
from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type
from ibm_aigov_facts_client.utils.cp4d_utils import CloudPakforDataConfig
from ibm_aigov_facts_client.supporting_classes.cp4d_authenticator import CP4DAuthenticator
from ibm_cloud_sdk_core.utils import  convert_model
from ibm_aigov_facts_client.supporting_classes.factsheet_utils import ModelEntryProps
from ibm_aigov_facts_client.utils.doc_annotations import deprecated

from ibm_aigov_facts_client.utils.utils import *
from ..utils.config import *


# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

_logger = logging.getLogger(__name__)

class FactSheetElements:
    """
    Factsheet elements 

    :param str api_key: (Optional) IBM Cloud API key.
    :param CloudPakforDataConfig cloud_pak_for_data_configs: (Optional) Cloud pak for data cluster details.

    """

    def __init__(self,api_key=None,cp4d_details:'CloudPakforDataConfig'=None):
        self.api_key = None
        self.type_name = None
        self.is_cpd=False
        self.cp4d_configs=None
        
        if api_key:
            self.api_key = api_key
        elif cp4d_details:
            self.is_cpd=True
            self.cp4d_configs=convert_model(cp4d_details)
        else:
            raise WrongParams("IBM Cloud API_KEY or CPD details needed")

    def _get_token(self, api_key):

        if api_key:
            try:
                if get_env() is None or get_env() == 'prod':
                    _authenticator = IAMAuthenticator(
                        apikey=api_key)

                elif get_env() == 'dev' or get_env() == 'test':
                    _authenticator = IAMAuthenticator(
                        apikey=api_key, url=dev_config['IAM_URL'])
                else:
                    _authenticator = IAMAuthenticator(
                        apikey=api_key)
            except:
                raise AuthorizationError(
                    "Something went wrong when initiating Authentication")

        if isinstance(_authenticator, IAMAuthenticator):
            token = _authenticator.token_manager.get_token()
        else:
            token = _authenticator.bearer_token
        return token

    def _get_token_cpd(self, cp4d_configs):

        if cp4d_configs:
            try:
                _auth_cpd=CP4DAuthenticator(url=cp4d_configs["url"],
                                            username=cp4d_configs["username"],
                                            password=cp4d_configs.get("password", None),
                                            apikey = cp4d_configs.get("api_key", None), 
                                            disable_ssl_verification=cp4d_configs["disable_ssl_verification"],
                                            bedrock_url = cp4d_configs.get("bedrock_url", None))
            except:
                raise AuthorizationError(
                    "Something went wrong when initiating Authentication")

        if isinstance(_auth_cpd, CP4DAuthenticator):
            token = _auth_cpd.get_cp4d_auth_token()
        else:
            raise AuthorizationError(
                    "Something went wrong when getting token")
        return token
    
    def _get_bss_id(self, api_key=None):
        try:
            token = self._get_token(api_key)
            decoded_bss_id = jwt.decode(token, options={"verify_signature": False})[
                "account"]["bss"]
        except jwt.ExpiredSignatureError:
            raise
        return decoded_bss_id

    def _get_bss_id_cpd(self):
        decoded_bss_id='999'
        return decoded_bss_id

    def _get_current_assets_prop(self, asset_type=FactsType.MODEL_FACTS_USER):
        headers = {}
        current_asset_prop=None
        
        if self.is_cpd:
            cur_bss_id = self._get_bss_id_cpd()
            headers["Authorization"] = "Bearer " + self._get_token_cpd(self.cp4d_configs)
        else:
            cur_bss_id = self._get_bss_id(self.api_key)
            headers["Authorization"] = "Bearer " + self._get_token(self.api_key)

        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        params = {"bss_account_id": cur_bss_id}

        if get_env() == 'dev' :
            url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                '/v2/asset_types/' + asset_type
        elif get_env() == 'test':
            url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                '/v2/asset_types/'+asset_type
        else:
            url = prod_config["DEFAULT_SERVICE_URL"] + \
                '/v2/asset_types/'+asset_type

        response = requests.get(url=url,
                                headers=headers,
                                params=params)

        if not response:
            _logger.exception("Current asset properties not found")

        elif response.status_code == 403:
            _logger.exception(response.json()['message'])
            
        elif response.status_code == 401:
            _logger.exception("Expired token found.")
            

        elif response.status_code == 200:
            current_asset_prop = response.json()
        return current_asset_prop

    def _file_data_validation(self, name, props):

        if not name or not props['type'] or not props['label']:
            raise MissingValue("Property name or type or label")

        if props["type"].lower() != "string" and props["type"].lower() != "integer" and props["type"].lower() != "date":
            raise UnexpectedValue(
                "Only string, integer and date type is supported ")

        if (props["type"].lower() == "string") and (props["minimum"] != '' or props["maximum"] != ''):
            raise UnexpectedValue(
                "For String type, ONLY min and max length should be defined if applicable")

        if (props["type"].lower() == "integer") and (props["min_length"] != '' or props["max_length"] != ''):
            raise UnexpectedValue(
                "For Integer type, ONLY minimum and maximum value should be defined if applicable")

    def _get_props_from_file(self, data):
        props = {}
        fields = []
        global_search = []

        for _, row in data.iterrows():
            tmp_props = {}

            name = row["name"]
            tmp_props["type"] = row["type"]
            tmp_props["description"] = row["description"]
            tmp_props["placeholder"] = row["placeholder"]

            tmp_props["is_array"] = row["is_array"] or False
            tmp_props["required"] = row["required"] or True
            tmp_props["hidden"] = row["hidden"] or False
            tmp_props["readonly"] = row["readonly"] or False

            tmp_props["default_value"] = row["default_value"]
            tmp_props["minimum"] = row["minimum"]
            tmp_props["maximum"] = row["maximum"]
            tmp_props["min_length"] = row["min_length"]
            tmp_props["max_length"] = row["max_length"]
            tmp_props["label"] = {"default": row["label"], "en": row["label"]}
            is_searchable = row["is_searchable"] or False

            props[row["name"]] = tmp_props
            self._file_data_validation(name, tmp_props)

            if is_searchable is True:
                fields_prop = {}
                fields_prop["key"] = row["name"]
                fields_prop["type"] = row["type"]
                fields_prop["facet"] = False
                fields_prop["is_array"] = row["is_array"]
                fields_prop["search_path"] = row["name"]
                fields_prop["is_searchable_across_types"] = False

                fields.append(fields_prop)

                global_search.append(name)
        return props, fields, global_search

    def _format_data(self, csvFilePath, overwrite, asset_type):
        props = {}
        fields = []
        global_search = []
        csv_data = pd.read_csv(csvFilePath, sep=",", na_filter=False)

        if csv_data.empty:
            raise ClientError("File can not be empty")

        props, fields, global_search = self._get_props_from_file(csv_data)

        if overwrite:
            final_dict = {}
            final_dict["description"] = "The model fact user asset type to capture user defined attributes."
            final_dict["fields"] = fields
            final_dict["relationships"] = []
            final_dict["global_search_searchable"] = global_search
            final_dict["properties"] = props

            if asset_type == FactsType.MODEL_USECASE_USER:
                final_dict["decorates"] = [{"asset_type_name": "model_entry"}]

            final_dict["localized_metadata_attributes"] = {
                "name": {"default": "Additional details", "en": "Additional details"}}

            return final_dict
        else:
            current_asset_props = self._get_current_assets_prop(asset_type)

            if current_asset_props and current_asset_props.get("properties"):

                if (current_asset_props["properties"] and props) or (not current_asset_props["properties"] and props):
                    current_asset_props["properties"].update(props)

                if (current_asset_props["fields"] and fields) or (not current_asset_props["fields"] and fields):
                    for field in fields:
                        current_asset_props["fields"].append(field)

                if (current_asset_props["global_search_searchable"] and global_search) or (not current_asset_props["global_search_searchable"] and global_search):
                    for global_search_item in global_search:
                        current_asset_props["global_search_searchable"].append(
                            global_search_item)
                entries_to_remove = ["name", "version", "scope"]
                list(map(current_asset_props.pop, entries_to_remove))

            elif current_asset_props and not current_asset_props.get("properties"):
                current_asset_props["properties"] = props
                if (current_asset_props["fields"] and fields) or (not current_asset_props["fields"] and fields):
                    for field in fields:
                        current_asset_props["fields"].append(field)

                if (current_asset_props["global_search_searchable"] and global_search) or (not current_asset_props["global_search_searchable"] and global_search):
                    for global_search_item in global_search:
                        current_asset_props["global_search_searchable"].append(
                            global_search_item)
                entries_to_remove = ["name", "version", "scope"]
                list(map(current_asset_props.pop, entries_to_remove))

            else:
                raise ClientError("Existing properties not found")

            return current_asset_props

    @deprecated(alternative="client.assets.create_custom_facts_definitions()")
    def replace_asset_properties(self, csvFilePath, type_name=None, overwrite=True):
        """
            Utility to add custom asset properties of model or model usecase.
            
            :param str csvFilePath: File path of csv having the asset properties.
            :param str type_name: Asset type user needs to update. Current options are `modelfacts_user` and `model_entry_user`. Default is set to `modelfacts_user`.
            :param bool overwrite: (Optional) Merge or replace current properties. Default is True.
            

            A way you might use me is:

            For IBM Cloud:

            >>> from ibm_aigov_facts_client import FactSheetElements
            >>> client = FactSheetElements(api_key=API_KEY)
            >>> client.replace_asset_properties("Asset_type_definition.csv")
            >>> client.replace_asset_properties("Asset_type_definition.csv",type_name="model_entry_user", overwrite=False)

            For Cloud Pak for Data:

            >>> from ibm_aigov_facts_client import FactSheetElements
            >>> client = FactSheetElements(cp4d_details=<CPD credentials>)
            >>> client.replace_asset_properties("Asset_type_definition.csv")
            >>> client.replace_asset_properties("Asset_type_definition.csv",type_name="model_entry_user", overwrite=False)
        
        """


        validate_enum(type_name,
                      "type_name", FactsType, False)

        if self.is_cpd:
            cur_bss_id = self._get_bss_id_cpd()
        else:
            cur_bss_id = self._get_bss_id(self.api_key)

        self.type_name = type_name or FactsType.MODEL_FACTS_USER

        asset_conf_data = self._format_data(
            csvFilePath, overwrite, self.type_name)


        if asset_conf_data:
            self._update_props(asset_conf_data, cur_bss_id, self.type_name)
        else:
            raise ClientError("Error formatting properties data from file")

    def _update_props(self, data, bss_id, type_name):
        
        headers = {}
        if self.is_cpd:
            headers["Authorization"] = "Bearer " + self._get_token_cpd(self.cp4d_configs)
            url = self.cp4d_configs["url"] + \
                 '/v2/asset_types/'+type_name
        else:
            headers["Authorization"] = "Bearer " + self._get_token(self.api_key)
            if get_env() ==  'dev' :  
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                '/v2/asset_types/'+type_name
            elif get_env() == 'test' :
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/asset_types/'+type_name
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/asset_types/'+type_name
           
        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        params = {"bss_account_id": bss_id}

        response = requests.put(url=url,
                                headers=headers,
                                params=params,
                                data=json.dumps(data))

        if response.status_code == 401:
            _logger.exception("Expired token found.")
            raise
        elif response.status_code == 200 or response.status_code == 202:
            _logger.info("Asset properties updated Successfully")
        else:
            _logger.exception(
                "Error updating properties..{}".format(response.json()))


    @deprecated(alternative="client.assets.get_model().add_tracking_model_usecase()")
    def register_model_entry(self,model_entry_props:'ModelEntryProps'):
        """
        Link Model to Model Usecase. Model asset should be stored in either Project or Space and corrsponding ID should be provided when registering to model usecase. 

        
        :param ModelEntryProps mdoel_entry_props: Properties about model asset and model usecase catalog.


        For IBM Cloud:

        >>> from ibm_aigov_facts_client import FactSheetElements
        >>> from ibm_aigov_facts_client.supporting_classes.factsheet_utils import ModelEntryProps
        >>> client = FactSheetElements(api_key=API_KEY)

        For new model usecase:

        >>> props=ModelEntryProps(
                    model_entry_catalog_id=<catalog_id>,
                    asset_id=<model_asset_id>,
                    model_entry_name=<name>,
                    model_entry_desc=<description>,
                    project_id=<project_id>
                    )

        >>> client.register_model_entry(model_entry_props=props)
        
        
        For linking to existing model usecase:

        >>> props=ModelEntryProps(
                    asset_id=<model_asset_id>,
                    model_entry_catalog_id=<catalog_id>,
                    model_entry_id=<model_entry_id to link>,
                    space_id_id=<space_id>
                    )

        >>> client.register_model_entry(model_entry_props=props)
        
        For CPD, initialization changes only:

        >>> from ibm_aigov_facts_client import FactSheetElements
        >>> from ibm_aigov_facts_client.supporting_classes.factsheet_utils import CloudPakforDataConfig
        >>> creds=CloudPakforDataConfig(service_url=<host url>,username=<user name>,password=<password>)
        >>> client = FactSheetElements(cp4d_details=creds)

        """

        meta_props=convert_model(model_entry_props)


        model_asset_id=meta_props['asset_id']
        model_entry_catalog_id=meta_props['model_entry_catalog_id']
        model_catalog_id= meta_props.get('model_catalog_id')
        model_entry_id= meta_props.get('model_entry_id')
        model_entry_name= meta_props.get('model_entry_name')
        model_entry_desc=meta_props.get('model_entry_desc') 
        project_id=meta_props.get('project_id') 
        space_id=meta_props.get('space_id')
        grc_model_id=meta_props.get('grc_model_id') 

        validate_type(model_asset_id,u'asset_id', STR_TYPE, True)
        validate_type(model_entry_catalog_id, u'model_entry_catalog_id', STR_TYPE, True)
        
        params={}
        headers={}
        payload={}

        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        if model_catalog_id is not None:
            params['catalog_id']=model_catalog_id
            if 'project_id' in params:
                del params['project_id']
            elif 'space_id' in params:
                del params['space_id']   
        elif project_id is not None:
            params['project_id']=project_id
            if 'catalog_id' in params:
                del params['catalog_id']
            elif 'space_id' in params:
                del params['space_id']
        elif space_id is not None:
            params['space_id']=space_id
            if 'catalog_id' in params:
                del params['catalog_id']
            elif 'project_id' in params:
                del params['project_id']
        else:
            raise MissingParams("Missing valid params")

        if grc_model_id and not self.is_cpd:
            raise WrongParams ("grc_model_id only applicable for CPD")

        payload['model_entry_catalog_id']=model_entry_catalog_id
        
        if model_entry_name or (model_entry_name and model_entry_desc):
            if model_entry_id:
                raise WrongParams("Please provide either NAME and DESCRIPTION or MODEL_ENTRY_ID")
            payload['model_entry_name']=model_entry_name
            if model_entry_desc:
                payload['model_entry_description']=model_entry_desc        
            
        elif model_entry_id:
            if model_entry_name and model_entry_desc:
                raise WrongParams("Please provide either NAME and DESCRIPTION or MODEL_ENTRY_ID")
            payload['model_entry_asset_id']=model_entry_id 
            
        else:
            raise WrongParams("Please provide either NAME and DESCRIPTION or MODEL_ENTRY_ID")

        wkc_register_url=WKC_MODEL_REGISTER.format(model_asset_id)

        if self.is_cpd:
            if grc_model_id:
                payload['grc_model_id']=grc_model_id
            headers["Authorization"] = "Bearer " + self._get_token_cpd(self.cp4d_configs)
            url = self.cp4d_configs["url"] + \
                 wkc_register_url
        else:
            headers["Authorization"] = "Bearer " + self._get_token(self.api_key)
            if get_env() ==  'dev' :  
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                wkc_register_url
            elif get_env() == 'test':    
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    wkc_register_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    wkc_register_url
        
        if model_entry_id:
            _logger.info("Initiate linking model to existing model usecase {}......".format(model_entry_id))
        else:
            _logger.info("Initiate linking model to new model usecase......")
        response = requests.post(url,
                                headers=headers,
                                params=params,
                                data=json.dumps(payload))

        
        if response.status_code == 200:
            _logger.info("Successfully finished linking model {} to model usecase".format(model_asset_id))

        else:
            error_msg = u'Model registration failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' + str(response.status_code) + '. ' + reason)

        return response.json()

    @deprecated(alternative="client.assets.get_model().remove_tracking_model_usecase()")
    def unregister_model_entry(self, asset_id, catalog_id=None ,project_id=None, space_id=None):
        """
            Unregister WKC Model Usecase

            :param str asset_id: WKC model usecase id
            :param str catalog_id: (Optional) Catalog ID where asset is stored 
            :param str project_id: (Optional) Project ID where the model exist
            :param str space_id: (Optional) Space ID where model exist


            Example for IBM Cloud or CPD:

            >>> client.unregister_model_entry(asset_id=<model id>,project_id=<cpd_project_id>)
            >>> client.unregister_model_entry(asset_id=<model id>,space_id=<cpd_space_id>)
            >>> client.unregister_model_entry(asset_id=<model id>,catalog_id=<catalog_id>)

        """

        validate_type(asset_id,u'asset_id', STR_TYPE, True)
        validate_type(catalog_id, u'catalog_id', STR_TYPE, False)
        validate_type(project_id, u'project_id', STR_TYPE, False)
        validate_type(space_id, u'space_id', STR_TYPE, False)

        if not project_id and not space_id and not catalog_id:
            raise MissingParams("Project or space or catalog id is required")

        wkc_unregister_url=WKC_MODEL_REGISTER.format(asset_id)

        params={}
        headers={}
        payload={}

        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"
        if catalog_id is not None:
            params['catalog_id']=catalog_id
            if 'project_id' in params:
                del params['project_id']
            elif 'space_id' in params:
                del params['space_id']   
        elif project_id is not None:
            params['project_id']=project_id
            if 'catalog_id' in params:
                del params['catalog_id']
            elif 'space_id' in params:
                del params['space_id']
        elif space_id is not None:
            params['space_id']=space_id
            if 'catalog_id' in params:
                del params['catalog_id']
            elif 'project_id' in params:
                del params['project_id']
        else:
            raise MissingParams("catalog_id, project_id or space_id")

        if self.is_cpd:
            headers["Authorization"] = "Bearer " + self._get_token_cpd(self.cp4d_configs)
            url = self.cp4d_configs["url"] + \
                 wkc_unregister_url
        else:
            headers["Authorization"] = "Bearer " + self._get_token(self.api_key)
            if get_env() ==  'dev' :  
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                wkc_unregister_url
            elif get_env() == 'test':    
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    wkc_unregister_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    wkc_unregister_url
        
        response = requests.delete(url,
                                headers=headers,
                                params=params,
                                )

        
        if response.status_code == 204:
            _logger.info("Successfully finished unregistering WKC Model {} from Model Usecase.".format(asset_id))
        else:
            error_msg = u'WKC Model Usecase unregistering failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' + str(response.status_code) + '. ' + reason)

    @deprecated(alternative="client.assets.list_model_usecases()")
    def list_model_entries(self, catalog_id=None)-> Dict:
        """
        Returns all WKC Model Usecase assets for a catalog

        :param str catalog_id: (Optional) Catalog ID where you want to register model, if None list from all catalogs
        
        :return: All WKC Model Usecase assets for a catalog
        :rtype: dict

        Example:
        
        >>> client = FactSheetElements(cp4d_details=creds) or client = FactSheetElements(api_key=API_KEY)
        >>> client.list_model_entries()
        >>> client.list_model_entries(catalog_id=<catalog_id>)

        """

        params={}
        headers={}

        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        
        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)
            list_url=WKC_MODEL_LIST_FROM_CATALOG.format(catalog_id)
        else:
            list_url=WKC_MODEL_LIST_ALL


        if self.is_cpd:
            headers["Authorization"] = "Bearer " + self._get_token_cpd(self.cp4d_configs)
            url = self.cp4d_configs["url"] + \
                 list_url
        else:
            headers["Authorization"] = "Bearer " + self._get_token(self.api_key)
            if get_env() ==  'dev' :   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                list_url
            elif get_env() =='test':   
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    list_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    list_url
        
        response = requests.get(url,
                                headers=headers,
                                #params=params,
                                )

        if response.status_code == 200:
            return response.json()

        else:
            error_msg = u'WKC Models listing failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' + str(response.status_code) + '. ' + reason)

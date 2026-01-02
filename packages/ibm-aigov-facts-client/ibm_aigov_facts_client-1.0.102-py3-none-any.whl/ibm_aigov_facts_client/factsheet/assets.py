
import logging
import json
import re
import collections
import concurrent.futures
import concurrent.futures
import warnings
import jwt
import time
import pandas as pd
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import boto3
import uuid

import ibm_aigov_facts_client._wrappers.requests as requests


from ..utils.client_errors import *
from typing import BinaryIO, Dict, List, Any, Sequence
from urllib.parse import urlencode

from ibm_aigov_facts_client.client import fact_trace
from ibm_aigov_facts_client.factsheet.asset_utils_model import ModelAssetUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_prompt import AIGovAssetUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_inventory import AIGovInventoryUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_me_prompt import AIUsecaseUtilities
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal, ContainerType, FactsType, ModelEntryContainerType, AllowedDefinitionType, FormatType, AttachmentFactDefinitionType, Status, Risk,Task,InputMode,ModelType,Role,S3Storage
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator, MCSPV2Authenticator

from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type, STR_TYPE
from ibm_aigov_facts_client.utils.me_containers_meta import AssetsContainersDefinitions
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.doc_annotations import deprecated
from ibm_aigov_facts_client.supporting_classes.factsheet_utils import PromptTemplate,DetachedPromptTemplate


_logger = logging.getLogger(__name__)




class Assets:

    def __init__(self, facts_client: 'fact_trace.FactsClientAdapter'):
        self._container_type = facts_client._container_type
        self._container_id = facts_client._container_id
        self._asset_id = None
        self._model_id = None
        self._model_usecase_id = None
        self._current_model = None
        self._current_model_usecase = None
        self._facts_type = None
        self._cpd_configs = None
        self._is_cp4d = facts_client._is_cp4d
        self._facts_client = facts_client
        self._external_model = self._facts_client._external
        if self._is_cp4d:
            self._cpd_configs = facts_client.cp4d_configs
            self._cp4d_version = facts_client._cp4d_version
        self._cpd_op_enabled = False
        self._facts_definitions = None
        self._facts_type = FactsType.MODEL_FACTS_USER
        self.DISABLE_LOGGING = False
        self._account_id=self._facts_client._account_id
       
    
    def create_custom_facts_definitions(self, csvFilePath, type_name: str = None, section_name: str = None, overwrite=True):
        """
            Utility to add custom facts attribute properties of model or model usecase.

            :param str csvFilePath: File path of csv having the asset properties.
            :param str type_name: Asset type user needs to add/update. Current options are `modelfacts_user`,`model_entry_user`. Default is set to `modelfacts_user`.
            :param str section_name: Custom name to show for custom attribute section. Applies only to `model_entry_user` type.
            :param bool overwrite: (Optional) Merge or replace current properties. Default is True.


            A way you might use me is:

            >>> client.assets.create_custom_facts_definitions("Asset_type_definition.csv") # uses default type `modelfacts_user` type
            >>> client.assets.create_custom_facts_definitions("Asset_type_definition.csv",type_name="model_entry_user", localized_name=<custom name for attributes section>,overwrite=False)

        """

        validate_enum(type_name,
                      "type_name", FactsType, False)

        if section_name and type_name != FactsType.MODEL_USECASE_USER:
            raise ClientError(
                "localized name change is only supported for `model_entry_user` type")

        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            cur_bss_id = self._account_id
        elif self._is_cp4d:
            cur_bss_id = self._get_bss_id_cpd()
        else:
            cur_bss_id = self._get_bss_id()

        self.type_name = type_name or FactsType.MODEL_FACTS_USER
        _logger.info("Creating definitions for type {}".format(self.type_name))

        asset_conf_data = self._format_data(
            csvFilePath, overwrite, self.type_name, section_name)
        
        if asset_conf_data:
            operation_type = "create"
            self._update_props(asset_conf_data, cur_bss_id, self.type_name,operation_type)
        else:
            raise ClientError("Error formatting properties data from file")
    

    def reset_custom_facts_definitions(self,type_name:str=None):
        """
            Utility to remove custom facts attribute properties of model or model usecase.
            
            :param str type_name: Asset type user needs to add/update. Current options are `modelfacts_user`,`model_entry_user`. Default is set to `modelfacts_user`.
            

            A way you might use me is,::

              client.assets.reset_custom_facts_definitions(type_name="model_entry_user")

        """

        validate_enum(type_name,
                      "type_name", FactsType, False)

        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST,AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            cur_bss_id = self._account_id
        elif self._is_cp4d:
            cur_bss_id = self._get_bss_id_cpd()
        else:
            cur_bss_id = self._get_bss_id()

        self.type_name = type_name or FactsType.MODEL_FACTS_USER
        _logger.info("Removing definitions for type {}".format(self.type_name))

        asset_conf_data=self._remove_asset_conf_data()

        if asset_conf_data:
            operation_type = "remove"
            self._update_props(asset_conf_data, cur_bss_id, self.type_name,operation_type)


        else:
            raise ClientError("Error formatting properties data from file")

    def get_facts_definitions(self, type_name: str, container_type: str = None, container_id: str = None) -> Dict:
        """
            Get all facts definitions

            :param str type_name: Asset fact type. Current options are `modelfacts_user` and `model_entry_user`.
            :param str container_type: (Optional) Asset container type. Options are `project`, `space` or `catalog`. Default to container type used when initiating client.
            :param str container_id: (Optional) Asset container id. Default to container id when initiating client

            :rtype: dict

            A way you might use me is:

            >>> client.assets.get_facts_definitions(type_name=<fact type>) # uses container type and id used initializing facts client
            >>> client.assets.get_facts_definitions(type_name=<fact type>,container_type=<container type>,container_id=<container id>)

        """

        validate_enum(type_name,
                      "type_name", FactsType, True)
        validate_enum(container_type,
                      "container_type", ContainerType, False)

        if self._external_model:
            container_type = container_type or MODEL_USECASE_CONTAINER_TYPE_TAG
            container_id = container_id or self._get_pac_catalog_id()
        else:
            container_type = container_type or self._container_type
            container_id = container_id or self._container_id

        if not container_type or not container_id:
            raise ClientError(
                "Please provide a valid container type and container id")

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                "/v2/asset_types/" + type_name + "?" + container_type + "_id=" + container_id
        else:
            if get_env() =='dev' :   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    "/v2/asset_types/" + type_name + "?" + container_type + "_id=" + container_id
            elif get_env() == 'test' :  
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    "/v2/asset_types/" + type_name + "?" + container_type + "_id=" + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    "/v2/asset_types/" + type_name + "?" + container_type + "_id=" + container_id

        response = requests.get(url, headers=self._get_headers())
        if not response.ok:
            raise ClientError("User facts definitions not found. ERROR {}. {}".format(
                response.status_code, response.text))
        else:
            return response.json()

    def _get_asset_type(self, model_id: str = None, container_id: str = None, container_type: str = None):
        """
            Returns asset type : "wx_prompt" or "wml_model" or "model_stub"

            :param str model_id: (Optional) Id of the model asset.
            :param str container_type: (Optional) Name of the container where model is saved. Currently supported container_type are `space` or `project`. For external models it is not needed and defaulted to `catalog`.
            :param str container_id: (Optional) Id of the container where model asset is saved. For external models, it refers to catalog id where model stub is saved. if not provided for external models,if available and user have access, default platform asset catalog is used 
            :rtype: str

            :return: "wx_prompt" or "wml_model" or "model_stub"

        """
        if not container_id:
            container_id = self._container_id
        if not container_type:
            container_type = self._container_type
        
        if not self._external_model and model_id and container_type and container_id:
            url = self._get_assets_url(model_id, container_type, container_id)
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                get_type = response.json()["metadata"][ASSET_TYPE_TAG]
                return get_type
            elif str(response.status_code).startswith("4"):
                raise ClientError(f"Failed to retrieve asset type for the asset due to error : {response.json()['errors'][0]['message']}")            
            else:                
                raise Exception(
                    "Failed to retrieve asset_type for the specified asset")
        
    # def _get_prompt(self, prompt_id: str = None, container_type: str = None, container_id: str = None):
    #     try:
    #         self.model_asset_util_model = self.get_prompt_assest(prompt_id,container_type,container_id)
    #         self.model_asset_util_model_dict = self.model_asset_util_model.to_dict()
    #         self.model_asset_util_model_dict_modified = {f'_{key}': value for key, value in self.model_asset_util_model_dict.items()}
    #         self.model_asset_util_model_dict_modified['_assets_client'] = self.model_asset_util_model
    #         self.ai_gov_util_model = AIGovAssetUtilities.from_dict(self.model_asset_util_model_dict_modified)
    #         return self.ai_gov_util_model
        
    #     except RuntimeError as e:
    #         _logger.error(f"Runtime error encountered. Check error stack for more details {e}")
    


    # def get_model(self, model_id: str=None, container_type: str=None, container_id: str=None, wml_stored_model_details:dict=None, is_prompt: bool=False)-> ModelAssetUtilities:
    # removed reference of prompt from get_model as part of 4.8.3 changes made by Lakshmi
    # get_model always relates to traditional models
    # def get_model(self, model_id: str=None, container_type: str=None, container_id: str=None, wml_stored_model_details:dict=None, is_prompt: bool=False):

    def get_model(self, model_id: str = None, container_type: str = None, container_id: str = None, wml_stored_model_details: dict = None):
        """
            Get model asset.

            :param str model_id: (Optional) Id of the traditional machine learning model asset.
            :param str container_type: (Optional) Name of the container where model is saved. Currently supported container_type are `space` or `project`. For external models it is not needed and defaulted to `catalog`.
            :param str container_id: (Optional) Id of the container where model asset is saved. For external models, it refers to catalog id where model stub is saved. if not provided for external models,if available and user have access, default platform asset catalog is used 
            :param dict wml_stored_model_details: (Optional) Watson machine learning model details. Applied to Watson Machine Learning models only.

            :rtype: ModelAssetUtilities

            The way to use me is:

            >>> client.assets.get_model(model_id=<model_id>) # uses container type and id used to initiate client
            >>> client.assets.get_model(model_id=<model id>,container_type=<space or project>,container_id=<space or project id>)
            >>> client.assets.get_model(wml_stored_model_details=<wml model details>) # uses model id, container type and id part of model details

            for external models,

            >>> client.assets.get_model(model_id=<model_id>) # uses available platform asset catalog id as container_id
            >>> client.assets.get_model(model_id=<model_id>,container_id=<catalog id>)

        """

        if wml_stored_model_details and (model_id or container_type or container_id):
            raise ClientError(
                "Model and container info is not needed when providing wml_stored_model_details")

        validate_enum(container_type, "container_type", ContainerType, False)

        # if is_prompt:
        #     replace_name = "prompt"
        # else:
        #     replace_name = "model"
        replace_name = "model"
        # add the current active container_id & type if container_id and container_type is not passed

        if not self._external_model and model_id and container_type and container_id:
            url = self._get_assets_url(model_id, container_type, container_id)
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                get_type = response.json()["metadata"][ASSET_TYPE_TAG]
                if get_type == EXT_MODEL:
                    self._external_model = True

            else:
                raise ClientError(
                    "Provide correct details for retrieving a {}".format(replace_name))

        if not self._external_model and container_type == ContainerType.CATALOG:
            raise ClientError(
                "Container type should be `space` or `project` for non-external models")

        if self._external_model:
            self._asset_id = model_id
            self._container_type = container_type or MODEL_USECASE_CONTAINER_TYPE_TAG
            self._container_id = container_id or self._get_pac_catalog_id()
            if not self._container_id:
                raise ClientError(
                    "Container id is not provided and no platform asset catalog found to use as default. Please provide a valid catalog id as container_id")
        else:
            if wml_stored_model_details:

                try:
                    model_meta = wml_stored_model_details["metadata"]
                    self._asset_id = model_meta.get("id")
                    if model_meta.get(CONTAINER_SPACE):
                        self._container_type = ContainerType.SPACE
                        self._container_id = model_meta.get(CONTAINER_SPACE)
                    elif model_meta.get(CONTAINER_PROJECT):
                        self._container_type = ContainerType.PROJECT
                        self._container_id = model_meta.get(CONTAINER_PROJECT)
                    else:
                        raise ClientError("Failed to get container type from {} details {}".format(
                            replace_name, model_meta))

                except:
                    raise ClientError(
                        "Failed to get model details from provided wml_stored_model_details")
            else:
                if not model_id or model_id == "":
                    raise ClientError(
                        "Model id is required and can not be empty value")
                self._asset_id = model_id
                self._container_type = container_type or self._facts_client._container_type
                self._container_id = container_id or self._facts_client._container_id

        self._facts_type = FactsType.MODEL_FACTS_USER

        if self._container_type and self._container_id and self._asset_id:
            url = self._get_assets_url(
                self._asset_id, self._container_type, self._container_id)
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 404:
                raise ClientError("Invalid asset id or container id. ERROR {}. {}".format(
                    response.status_code, response.text))
            elif response.status_code == 200:
                # if is_prompt:
                #     self._current_model=AIGovAssetUtilities(self,model_id=self._asset_id,container_type=self._container_type,container_id=self._container_id,facts_type=self._facts_type)
                # else:
                self._current_model = ModelAssetUtilities(
                    self, model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id, facts_type=self._facts_type)
                _logger.info("Current {} information: {}".format(
                    replace_name, self._current_model.to_dict()))
            else:
                raise ClientError("Asset information not found for {} id {}. ERROR {}. {}".format(
                    replace_name, self._asset_id, response.status_code, response.text))
        else:
            raise ClientError("Could not get current {} {}".format(
                replace_name, self._current_model.to_dict()))

        return self._current_model

    def get_ai_usecase(self, ai_usecase_id: str, catalog_id: str = None) -> AIUsecaseUtilities:
        """
            Get AI usecase asset.

            :param str ai_usecase_id: Id of the ai usecase.
            :param str catalog_id: Id of the catalog where ai usecase is saved.

            :rtype: AIUsecaseUtilities

            The way to use me is:

            >>> client.assets.get_ai_usecase(ai_usecase_id=<ai usecase id>, catalog_id=<catalog id>)

        """

        # condition self._cp4d_version < "4.8.3" added by Lakshmi as part of 4.8.3 changes
        # if self._is_cp4d:
        if self._is_cp4d and self._cp4d_version < "4.8.3":
            # raise ClientError("Mismatch: This functionality is only supported in SaaS IBM Cloud")
            raise ClientError(
                "Mismatch: This functionality is only supported in SaaS IBM Cloud and CPD versions >=4.8.3")

        if (ai_usecase_id is None or ai_usecase_id == ""):
            # raise MissingValue("id", "AI usecase asset ID is missing")
            raise MissingValue(
                "ai_usecase_id", "AI usecase asset ID is missing")
        if (catalog_id is None or catalog_id == ""):
            raise MissingValue("catalog_id", "Catalog ID is missing")
        self._facts_type = FactsType.MODEL_USECASE_USER
        catalog_id = catalog_id
        replace_name = "AI"
        if ai_usecase_id and catalog_id:
            model_usecase_id = ai_usecase_id
            url = self._get_assets_url(
                model_usecase_id, MODEL_USECASE_CONTAINER_TYPE_TAG, catalog_id)
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 404:
                raise ClientError("Invalid {} usecase id or catalog id. ERROR {}. {}".format(
                    replace_name, response.status_code, response.text))
            elif response.status_code == 200:
                data = response.json()
                ai_usecase_name = data.get('metadata', {}).get('name', None)
                self._current_model_usecase = AIUsecaseUtilities(
                    self,ai_usecase_name=ai_usecase_name, model_usecase_id=model_usecase_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=catalog_id, facts_type=self._facts_type)
                # if is_prompt:
                #     self._current_model_usecase= AIUsecaseUtilities(self,model_usecase_id=model_usecase_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=catalog_id,facts_type=self._facts_type)
                # else:
                #     self._current_model_usecase= ModelUsecaseUtilities(self,model_usecase_id=model_usecase_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=catalog_id,facts_type=self._facts_type)
                _logger.info("Current {} usecase information: {}".format(
                    replace_name, self._current_model_usecase.to_dict()))
                return self._current_model_usecase
            else:
                raise ClientError("{} usecase information is not found. ERROR {}. {}".format(
                    replace_name, response.status_code, response.text))

        # return self.get_model_usecase(ai_usecase_id, catalog_id, is_prompt=True)

    # added by Lakshmi
    @deprecated(alternative="client.assets.get_ai_usecase()", reason="new generalized method available to cover models and prompts")
    def get_model_usecase(self, model_usecase_id: str, catalog_id: str = None) -> ModelUsecaseUtilities:
        # def get_model_usecase(self, model_usecase_id: str,catalog_id:str=None, is_prompt: bool=False)->ModelUsecaseUtilities:
        """
            Get model usecase asset.

            :param str model_usecase_id: Id of the model usecase.
            :param str catalog_id: Id of the catalog where model usecase is saved.

            :rtype: ModelUsecaseUtilities

            The way to use me is:

            >>> client.assets.get_model_usecase(model_usecase_id=<model usecase id>, catalog_id=<catalog id>)

        """

        # if is_prompt:
        #     replace_name = "AI"
        # else:
        #     replace_name = "model"
        replace_name = "model"
        if (model_usecase_id is None or model_usecase_id == ""):
            raise MissingValue("model_usecase_id",
                               "model usecase asset ID is missing")
        if (catalog_id is None or catalog_id == ""):
            raise MissingValue("catalog_id", "Catalog ID is missing")

        self._facts_type = FactsType.MODEL_USECASE_USER
        # catalog_id=catalog_id or self._get_pac_catalog_id()
        catalog_id = catalog_id

        # if not catalog_id:
        #    raise ClientError("Catalog id is not provided and no platform asset catalog found to use as default. Please provide a valid catalog id for used model usecase")

        if model_usecase_id and catalog_id:
            url = self._get_assets_url(
                model_usecase_id, MODEL_USECASE_CONTAINER_TYPE_TAG, catalog_id)
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 404:
                raise ClientError("Invalid {} usecase id or catalog id. ERROR {}. {}".format(
                    replace_name, response.status_code, response.text))
            elif response.status_code == 200:
                self._current_model_usecase = ModelUsecaseUtilities(
                    self, model_usecase_id=model_usecase_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=catalog_id, facts_type=self._facts_type)
                # if is_prompt:
                #     self._current_model_usecase= AIUsecaseUtilities(self,model_usecase_id=model_usecase_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=catalog_id,facts_type=self._facts_type)
                # else:
                #     self._current_model_usecase= ModelUsecaseUtilities(self,model_usecase_id=model_usecase_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=catalog_id,facts_type=self._facts_type)
                _logger.info("Current {} usecase information: {}".format(
                    replace_name, self._current_model_usecase.to_dict()))
                return self._current_model_usecase
            else:
                raise ClientError("{} usecase information is not found. ERROR {}. {}".format(
                    replace_name, response.status_code, response.text))
            
    def _get_aws_temp_credentials(self):

        env=aws_env()
        if env==AWS_TEST:
            aws_region="test" 
        elif env==AWS_DEV:  
            aws_region="test" 
        else:
            aws_region="ap-south-1"   
        
        url = f"https://api.{aws_region}.aws.data.ibm.com/v2/catalogs/temporary_credentials"
        if env == AWS_GOVCLOUD_PREPROD:
            url = aws_govcloudpreprod["DEFAULT_TEST_SERVICE_URL"]+"/v2/catalogs/temporary_credentials"
        elif env == AWS_GOVCLOUD:
            url = aws_govcloud["DEFAULT_SERVICE_URL"]+"/v2/catalogs/temporary_credentials"

        data = {}   
        try:
            response = requests.post(url, headers=self._get_headers(), data=json.dumps(data), verify=False)   
        
            if response.status_code == 200:
                response_data = response.json()
                aws_temp_creds = {
                "access_key_id": response_data.get("access_key_id"),
                "secret_access_key": response_data.get("secret_access_key"),
                "session_token": response_data.get("session_token")
                }
                return  aws_temp_creds

            else:
                raise ClientError(f"Error in Authenticating:{response.status_code}, {response.text}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")
                  

    def create_inventory(self, name: str, description: str, container_type:str=None,cloud_object_storage_name:str=None,s3_storage:str=None)->AIGovInventoryUtilities:

        """
        **Create a new inventory item**.

        This method creates an inventory item with the specified name and description. 

        **Note:**
            - If using **IBM Cloud**, provide the `cloud_object_storage_name` to properly associate the inventory with a Cloud Object Storage (COS) instance.
        **Parameters:**
            - **name** (str): The name of the inventory item to be created.
            - **description** (str): A brief description of the inventory item.
            - **cloud_object_storage_name** (str, optional): The name of the cloud object storage instance to associate with the inventory. Required if using **IBM Cloud**.To retrieve the available COS instances, see the documentation for the :func:`~ibm_aigov_facts_client.factsheet.utils.Utils.get_cloud_object_storage_instances` function.
            - **s3_storage** (str): The bucket storage preference, shared or dedicated is mandatory for AWS region
            - **container_type** (str): The container type is mandatory for AWS region

        **Returns:**
            InventoryUtilities`: An instance of `AIGovInventoryUtilities` representing the created inventory item.

        **Example:**

        1. Creating an inventory in the Watsonx.Governance platform:

            >>> inventory = client.assets.create_inventory(name="My Inventory", description="This is a test inventory.")

        2. Creating an inventory with a COS name in IBM Cloud:

            >>> inventory = client.assets.create_inventory(name="Data Inventory", description="Inventory for data storage", cloud_object_storage_name="my-cos-instance")

        3. Creating an inventory with AWS:
             >>> inventory = client.assets.create_inventory(name="My Inventory", container_type"<container_type>", s3_storage="shared" or "dedicated",description="<description>")

        """

        print("-" * OUTPUT_WIDTH)
        print(" Inventory Creation Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)
        env=aws_env()
       

        # cpd code 
        if self._is_cp4d:
            if cloud_object_storage_name:
                raise ClientError("cloud object storage is not used for on-prem environment")
            if s3_storage:
                raise ClientError("s3 storage is used only for AWS environment")
            else:
                try:
                    inventory_cpd_body={
                        "name": name,
                        "description": description,
                        "generator": "factsheet_onprem_bucket",
                        "bss_account_id": "999",
                        "is_governed": "false",
                        "bucket": {
                            "bucket_type": "assetfiles"
                        },
                        "subtype": "ibm_watsonx_governance_catalog"
                        }
                    

                    inventory_cpd_url = self._cpd_configs['url'] + "/v1/aigov/inventories"
                    inventory_response = requests.post(inventory_cpd_url, json=inventory_cpd_body, headers=self._get_headers())
                    if inventory_response.status_code == 201:
                        response_json = inventory_response.json()
                        inventory_id = response_json.get('metadata', {}).get('guid', 'Unknown ID')
                        inventory_name = response_json.get('entity', {}).get('name', 'Unknown Name')
                        description = response_json.get('entity', {}).get('description', 'No Description')
                        inventory_creator_id=response_json.get('metadata', {}).get('creator_id', 'Unknown ID')

                        creator_name = self._fetch_user_name(inventory_creator_id)
                        _logger.info(f"Inventory '{inventory_name}' has been created successfully.")
                        _logger.info(f"Details:\n"
                                    f"  Inventory ID: {inventory_id}\n"
                                    f"  Inventory Name: {inventory_name}\n"
                                    f"  Description: {description}\n"
                                    f"  Creator ID: {inventory_creator_id}\n"
                                    f"  Creator Name: {creator_name}\n")
                        
                        
                        self._inventory=AIGovInventoryUtilities(self,inventory_id=inventory_id,inventory_name=inventory_name,
                                                                inventory_description=description,inventory_creator_name=creator_name,
                                                                inventory_creator_id=inventory_creator_id)
                        return self._inventory
                    else:
                        # Failed request - log detailed error message
                        error_message = inventory_response.json().get('message', 'Unknown error occurred')
                        raise ClientError(f"Failed to create inventory. Status code: {inventory_response.status_code}, Error: {error_message}")

                

                except Exception as e:
                    # Handle any other unexpected errors
                    _logger.error(f"An error occurred: {e}")
                    raise


        elif env in {AWS_DEV, AWS_MUM, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            if cloud_object_storage_name:
                raise ClientError("cloud object storage is not used for AWS environment")
            try:
                if env in [AWS_GOVCLOUD_PREPROD, AWS_GOVCLOUD]:
                    aws_region = "us-gov-east-1"
                elif env in (AWS_TEST, AWS_DEV):
                    aws_region = "us-east-1"
                else:
                    aws_region = "ap-south-1"
                container_code = "c" 
                validate_enum(s3_storage,"s3_storage",S3Storage,True)
                if s3_storage=="shared":
                    bucket_name=f"ibm-wx-s{container_code}-{self._account_id}-{aws_region}"
                    is_shared="true"
                elif s3_storage=="dedicated":
                    random_uuid = str(uuid.uuid4())
                    random_string = re.sub(r'[^a-zA-Z0-9]', '', random_uuid).lower()[:14]
                    truncatedCatalogName=re.sub(r'[^a-zA-Z0-9]', '', name).lower()[:35]
                    bucket_name=f"ibm-wx-{container_code}-{truncatedCatalogName}-{random_string}"
                    is_shared="false"
                is_bucket=False
                _logger.info(f"The s3 bucket name for {s3_storage} storage : {bucket_name}")
                _logger.info(f"Checking if the bucket {bucket_name} exists....")
                list_buckets=self._list_s3_buckets()
                s3_buckets_name = [bucket['Name'] for bucket in list_buckets]
                if list_buckets is None or (bucket_name not in  s3_buckets_name):
                    _logger.info(f"Creating bucket {bucket_name} as the S3 bucket list is empty / {bucket_name} does not exists")
                    is_bucket=self._create_s3_bucket(bucket_name=bucket_name)    
                else:
                    is_bucket=True
                    _logger.info(f"The S3 bucket {bucket_name} already exists, proceeding to create Inventory")
                if is_bucket:
                    role_arn,env_url=self._get_account_settings(env)  
                    inventory_aws_body={
                                "name": name,
                                "description": description,
                                "generator": "Catalog-UI-Service",              
                                "bucket": {
                                    "bucket_name":bucket_name,   
                                    "bucket_type": "aws_s3",
                                    "role_arn": role_arn,
                                    "shared": is_shared
                                },                                  
                                } 

                    inventory_aws_url = env_url+ "/v1/aigov/inventories"
                    inventory_response = requests.post(inventory_aws_url, json=inventory_aws_body, headers=self._get_headers())
                    if inventory_response.status_code == 201:
                            response_json = inventory_response.json()
                            inventory_id = response_json.get('metadata', {}).get('guid', 'Unknown ID')              
                            inventory_name = response_json.get('entity', {}).get('name', 'Unknown Name')
                            description = response_json.get('entity', {}).get('description', 'No Description')
                            inventory_creator_id=response_json.get('metadata', {}).get('creator_id', 'Unknown ID')

                            creator_name = self._fetch_user_name(inventory_creator_id)
                            _logger.info(f"Inventory '{inventory_name}' has been created successfully.")
                            _logger.info(f"Details:\n"
                                        f"  Inventory ID: {inventory_id}\n"
                                        f"  Inventory Name: {inventory_name}\n"
                                        f"  Description: {description}\n"
                                        f"  Creator ID: {inventory_creator_id}\n"
                                        f"  Creator Name: {creator_name}\n")        
                            
                            self._inventory=AIGovInventoryUtilities(self,inventory_id=inventory_id,inventory_name=inventory_name,
                                                                    inventory_description=description,inventory_creator_name=creator_name,
                                                                    inventory_creator_id=inventory_creator_id)
                            return self._inventory
                    else:
                        error_message = inventory_response.json().get('message', 'Unknown error occurred')
                        raise ClientError(f"Failed to create inventory. Status code: {inventory_response.status_code}, Error: {error_message}")
                else:
                    raise ClientError("Error in creating bucket")
            except:
                raise ClientError("Error occured while creating inventory")
        
        
        # saas code 
        else:   
            if s3_storage:
                raise ClientError("s3 storage is used only for AWS environment")   
            try:
                _ENV = get_env()
                cur_bss_id = self._get_bss_id_cpd() if self._is_cp4d else self._get_bss_id()
                resource_url = RESOURCES_URL_MAPPING_NEW.get(_ENV)
                resource_key_url = RESOURCE_KEY_URL_MAPPING.get(_ENV)
                bucket_base_url = BUCKET_BASE_URL_MAPPING.get(_ENV)
                inventory_url = INVENTORY_URL_MAPPING.get(_ENV)

                if not resource_url or not resource_key_url or not bucket_base_url or not inventory_url:
                    raise ValueError(f"One or more URLs are missing for environment: {_ENV}")

                # Fetch resource instances
                _logger.info("Checking for the existence of the specified Cloud Object Storage.")
                response = requests.get(resource_url, headers=self._get_headers())
                response.raise_for_status()
                resources = response.json()

                # Search for cloud object storage GUID
                cloud_object_storage_guid = next(
                    (resource["guid"] for resource in resources.get("resources", []) if resource["name"] == cloud_object_storage_name),
                    None
                )
                if cloud_object_storage_guid:
                    _logger.info(f"Cloud Object Storage '{cloud_object_storage_name}' is Found.")
                else:
                    raise ClientError(f"No Cloud Object Storage found with the name '{cloud_object_storage_name}'. Please check the name.")

                # Define roles and their corresponding CRNs
                _logger.info("Initiating the creation of service credentials.")
                role_crns = {
                    "Reader": "crn:v1:bluemix:public:iam::::serviceRole:Reader",
                    "Writer": "crn:v1:bluemix:public:iam::::serviceRole:Writer",
                    "Manager": "crn:v1:bluemix:public:iam::::serviceRole:Manager"
                }

                credentials_data = {}
                for role_name, role_crn in role_crns.items():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    credential_name = f"{role_name}_service_cred_{timestamp}"
                    body = {
                        "name": credential_name,
                        "source": cloud_object_storage_guid,
                        "role": role_crn,
                        "parameters": {"HMAC": True}
                    }
                    response = requests.post(resource_key_url, json=body, headers=self._get_headers())
                    # response.raise_for_status()
                    

                    if response.status_code == 201:
                        response_json = response.json()
                        credentials = response_json.get("credentials", {})
                        credentials_data[role_name] = {
                            "apikey": credentials.get("apikey"),
                            "access_key_id": credentials.get("cos_hmac_keys", {}).get("access_key_id"),
                            "secret_access_key": credentials.get("cos_hmac_keys", {}).get("secret_access_key"),
                            "serviceid": credentials.get("iam_serviceid_crn", "").split(":")[-1],
                            "resource_instance_id": credentials.get("resource_instance_id")
                        }
                    else:
                        _logger.error(f"Failed to create service credential for role '{role_name}'.")
                        raise ClientError("Response Error:", response.json())
                
                _logger.info("Service credentials created successfully.")
                # Create bucket
                _logger.info("Starting the bucket creation process.")
                old_headers = self._get_headers()
                old_headers.pop("Content-Type", None)
                resource_instance_id = credentials_data["Manager"]["resource_instance_id"]
                if resource_instance_id:
                    old_headers["ibm-service-instance-id"] = resource_instance_id
                else:
                    raise ValueError("Resource instance ID not found in Manager credentials.")

                timestamp = datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
                bucket_name = f"sample-catalog-bucket-test-{timestamp}"
                bucket_url = f"{bucket_base_url}/{bucket_name}"
                bucket_response = requests.put(bucket_url, headers=old_headers)
                # bucket_response.raise_for_status()
                if bucket_response.status_code == 200 or bucket_response.status_code == 201:
                    _logger.info(f"Bucket '{bucket_name}' created successfully.")
                else:
                    _logger.error(f"Failed to create bucket '{bucket_name}'. Status Code: {bucket_response.status_code}, Response: {bucket_response.text}")
                # _logger.info(f"Bucket '{bucket_name}' created successfully.")

                # Create inventory
                inventory_body = {
                    "name": name,
                    "description": description,
                    "generator": "Model governance demo",
                    "bss_account_id": cur_bss_id,
                    "capacity_limit": 5,
                    "bucket": {
                        "bucket_name": bucket_name,
                        "bucket_location": "us-geo",
                        "endpoint_url": bucket_base_url,
                        "resource_instance_id": resource_instance_id,
                        "credentials_rw": {
                            "access_key_id": credentials_data["Manager"]["access_key_id"],
                            "secret_access_key": credentials_data["Manager"]["secret_access_key"]
                        },
                        "bluemix_cos_credentials": {
                            "viewer": {
                                "api_key": credentials_data["Reader"]["apikey"],
                                "service_id": credentials_data["Reader"]["serviceid"],
                                "access_key_id": credentials_data["Reader"]["access_key_id"],
                                "secret_access_key": credentials_data["Reader"]["secret_access_key"]
                            },
                            "editor": {
                                "api_key": credentials_data["Writer"]["apikey"],
                                "service_id": credentials_data["Writer"]["serviceid"],
                                "access_key_id": credentials_data["Writer"]["access_key_id"],
                                "secret_access_key": credentials_data["Writer"]["secret_access_key"]
                            },
                            "admin": {
                                "api_key": credentials_data["Manager"]["apikey"],
                                "service_id": credentials_data["Manager"]["serviceid"],
                                "access_key_id": credentials_data["Manager"]["access_key_id"],
                                "secret_access_key": credentials_data["Manager"]["secret_access_key"]
                            }
                        }
                    },
                    "is_governed": False,
                    "subtype": "ibm_watsonx_governance_catalog"
                }

                inventory_response = requests.post(inventory_url, json=inventory_body, headers=old_headers)
                if inventory_response.status_code == 201:
                    response_json = inventory_response.json()
                    inventory_id = response_json.get('metadata', {}).get('guid', 'Unknown ID')
                    inventory_name = response_json.get('entity', {}).get('name', 'Unknown Name')
                    description = response_json.get('entity', {}).get('description', 'No Description')
                    inventory_creator_id=response_json.get('metadata', {}).get('creator_id', 'Unknown ID')

                    creator_name = self._fetch_user_name(inventory_creator_id)
                    _logger.info(f"Inventory '{inventory_name}' has been created successfully.")
                    _logger.info(f"Details:\n"
                                f"  Inventory ID: {inventory_id}\n"
                                f"  Inventory Name: {inventory_name}\n"
                                f"  Description: {description}\n"
                                f"  Creator ID: {inventory_creator_id}\n"
                                f"  Creator Name: {creator_name}\n")
                    
                    
                    self._inventory=AIGovInventoryUtilities(self,inventory_id=inventory_id,inventory_name=inventory_name,
                                                            inventory_description=description,inventory_creator_name=creator_name,
                                                            inventory_creator_id=inventory_creator_id)
                    return self._inventory
                else:
                    error_message = inventory_response.json().get('message', 'Unknown error occurred')
                    raise ClientError(f"Failed to create inventory. Status code: {inventory_response.status_code}, Error: {error_message}")

            except Exception as e:
                _logger.error(f"An error occurred: {e}")
                raise

    def list_inventories(self, name:str=None, exact_match:bool=False)->list[AIGovInventoryUtilities]:
        """
            **List All Inventories**

            This method retrieves and returns a list of all inventories associated with the account.
            Each inventory item is represented as an instance of `AIGovInventoryUtilities`.

            Args:
                - name (str, optional): The name of the inventory to filter the results. If provided, the method will search for inventories matching this name.
                - exact_match (bool, optional): If set to `True`, the method will perform an exact match on the inventory name. Default is `False`, which allows for partial matches.

            Returns:
                list[AIGovInventoryUtilities]: A list of `AIGovInventoryUtilities` instances, each representing an inventory item.

            Examples:
                >>> inventories = client.assets.list_inventories()  # Retrieve all inventories
                >>> inventories = client.assets.list_inventories(name="sample")  # Retrieve inventories matching "sample"
                >>> inventories = client.assets.list_inventories(name="sample", exact_match=True)  # Retrieve inventories with an exact match for "sample"
        """
        print("-" * OUTPUT_WIDTH)
        print(" Inventory Retrieval Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)

        if name is None and exact_match:
            raise TypeError("'name' should not be empty when 'exact_match' is set to True.")

        if name is not None and not isinstance(name, str):
            raise TypeError(f"Invalid type for 'name'. Expected str, got {type(name).__name__}")

        inventory_list = []
        total_count = 0
        base_url = self._retrieve_inventory_url()
        if name:
            encoded_name = quote(str(name)) 
            name_url = f"{base_url}&name={encoded_name}" 
        else:
            name_url = base_url

        user_name_cache = {}  # Cache for user names
        
        _logger.info("Initiating the inventory retrieval process. Please wait...")

        while name_url:
            try:
                response = requests.get(name_url, headers=self._get_headers())
                
                if response.status_code == 200:
                    data = response.json()
                    catalogs = data.get('catalogs', [])

                    total_count += len(catalogs)
                    
                    if catalogs:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            futures = []
                            
                            for catalog in catalogs:
                                inventory_details = {
                                    'Name': catalog['entity'].get('name'),
                                    'Description': catalog['entity'].get('description'),
                                    'Inventory ID': catalog['metadata'].get('guid'),
                                    'Creator ID': catalog['metadata'].get('creator_id')
                                }

                                creator_id = inventory_details['Creator ID']
                                
                                if creator_id in user_name_cache:
                                    creator_name = user_name_cache[creator_id]
                                else:
                                    creator_name = self._fetch_user_name(creator_id)
                                    user_name_cache[creator_id] = creator_name

                                futures.append(executor.submit(
                                    lambda details, name: AIGovInventoryUtilities(
                                        self,
                                        inventory_id=details['Inventory ID'],
                                        inventory_name=details['Name'],
                                        inventory_description=details['Description'],
                                        inventory_creator_name=name,
                                        inventory_creator_id=details['Creator ID'],
                                    ), inventory_details, creator_name
                                ))

                            for future in concurrent.futures.as_completed(futures):
                                inventory_list.append(future.result())
                        
                        next_bookmark = data.get('nextBookmark')
                        if next_bookmark:
                            if name:
                                name_url = f"{name_url}&bookmark={next_bookmark}" 
                            else:
                                name_url = f"{base_url}&bookmark={next_bookmark}"
                        else:
                            name_url = None  
                    else:
                        break 
                else:
                    _logger.error(f"Failed to fetch inventories. Status code: {response.status_code}")
                    break

            except Exception as e:
                _logger.error(f"An error occurred while retrieving inventories: {str(e)}")
                break

        # name and exact_match
        if exact_match and name:
            matching_inventories = [item for item in inventory_list if item.to_dict().get('inventory_name') == name]

            if not matching_inventories: 
                _logger.error("No exact matching inventories were found.")
                return []
            else:
                _logger.info(f"Found {len(matching_inventories)} exact matching inventories for the name: {name}.")
                inventory_list = matching_inventories 

        # only name 
        if name:
            if total_count > 0:
                if not exact_match:
                    _logger.info(f"Found {total_count} inventories.")
            else:
                _logger.error("No matching inventories were found for the specified name.")

        # no parameter
        if inventory_list:
            _logger.info("Inventory details fetched successfully.")
        else:
            _logger.error("No Inventories were found.")

        return inventory_list
    



    def get_inventory(self, inventory_id: str)->AIGovInventoryUtilities:
            """
            **Retrieve a specific inventory by its inventory_id**.

            This method fetches the details of a specific inventory item using its inventory_id. 
            The returned inventory is represented as an instance of `AIGovInventoryUtilities`.

            Parameters:
                inventory_id (str): The unique identifier of the inventory item to retrieve.

            Returns:
                AIGovInventoryUtilities: An instance of `AIGovInventoryUtilities` representing the requested inventory item.

            Example:
                >>> inventory = client.assets.get_inventory(inventory_id="993738-383****")
            """
            print("-" * OUTPUT_WIDTH)
            print(" Inventory Retrieval Started ".center(OUTPUT_WIDTH))
            print("-" * OUTPUT_WIDTH)

            if not inventory_id:
                raise ClientError("Inventory ID is required for Fetching inventory details.")

            try:
                url = self._retrieve_inventory_url(inventory_id)
                response = requests.get(url, headers=self._get_headers())

                if response.status_code == 200:
                    data = response.json()

                    inventory_details = {
                        'Name': data['entity'].get('name'),
                        'Description': data['entity'].get('description'),
                        'Inventory ID': data['metadata'].get('guid'),
                        'Creator ID': data['metadata'].get('creator_id')
                    }

                    # Fetch user profile details based on creator ID
                    creator_name = self._fetch_user_name(inventory_details['Creator ID'])

                    inventory_name = inventory_details['Name']
                    description = inventory_details['Description']
                    inventory_creator_id=inventory_details['Creator ID']


                    _logger.info("Inventory details fetched successfully")
                    _logger.info(
                        f"\nInventory Details:\n"
                        f"  Inventory ID: {inventory_details['Inventory ID']}\n"
                        f"  Name: {inventory_name}\n"
                        f"  Description: {description}\n"
                        f"  Creator ID: { inventory_creator_id}\n"
                        f"  Creator Name: {creator_name}\n"
                    )

                    self._inventory=AIGovInventoryUtilities(self,inventory_id=inventory_id,inventory_name=inventory_name,
                                                            inventory_description=description,inventory_creator_name=creator_name,
                                                            inventory_creator_id=inventory_creator_id)
                    return self._inventory

                else:
                    error_message = response.json().get('message', 'Unknown error occurred')
                    raise ClientError(f"Failed to fetch inventory details. Status code: {response.status_code}, Error: {error_message}")

            except Exception as e:
                _logger.error(f"An error occurred: {e}")
                raise
            

    def _retrieve_inventory_url(self, inventory_id=None):

        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            bss_id =self._account_id
        elif self._is_cp4d :    
            bss_id = self._get_bss_id_cpd()
        else:
            bss_id = self._get_bss_id()
        
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev' :
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test':
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']
        if inventory_id:
            url = f"{base_url}/v1/aigov/inventories/{inventory_id}"
        
        else:
            url = f"{base_url}/v1/aigov/inventories?bss_account_id={bss_id}&limit=100&skip=0"
        return url
    
    def _fetch_user_name(self, user_id: str) -> str:
        try:
            env= aws_env()
            if env in (AWS_MUM, AWS_DEV, AWS_TEST):
                if env in (AWS_DEV ,AWS_TEST):
                    url =f"{aws_test['API_URL']}/api/2.0/accounts"
                else:
                    url=f"{aws_mumbai['API_URL']}/api/2.0/accounts"
                user_id = user_id.split("::", 1)[0]
                user_profile_url = f"{url}/{self._account_id}/identity/users/{user_id}"
                response = requests.get(user_profile_url, headers=self._get_headers())
                if response.status_code == 200:
                    user_data =response.json()
                    if(user_data.get('uid',{})==user_id):
                        user_name =user_data.get('displayName','N/A')
                        return user_name
                else:
                    _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                                f"Status code: {response.status_code}")
            elif env in (AWS_GOVCLOUD,AWS_GOVCLOUD_PREPROD) and not user_id.startswith('iam-ServiceId-'):
                if env == AWS_GOVCLOUD:
                    url =aws_govcloud['DEFAULT_SERVICE_URL']
                else:
                    url=aws_govcloudpreprod['DEFAULT_TEST_SERVICE_URL']
                user_id = user_id.split("::", 1)[0]
                user_profile_url = f"{url}/v1/aigov/factsheet/account/users/{user_id}"
                response = requests.get(user_profile_url, headers=self._get_headers())
                if response.status_code == 200:
                    user_data =response.json()
                    if(user_data.get('uid',{})==user_id):
                        user_name =user_data.get('displayName','N/A')
                        return user_name
                else:
                    _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                                  f"Status code: {response.status_code}")
            else:
                user_profile_url = self._retrieve_user_profile_url(user_id)
                response = requests.get(user_profile_url, headers=self._get_headers())
                if response.status_code == 200:
                    user_data = response.json()
                    user_names = [
                        resource['entity'].get('name', 'N/A')
                        for resource in user_data.get('resources', [])
                        if resource.get('entity', {}).get('iam_id') == user_id
                    ] or ['N/A']
                    return user_names[0]
                else:
                    _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                                f"Status code: {response.status_code}")
                    return 'N/A'
        except Exception as e:
            _logger.error(f"An error occurred while fetching user profile: {e}")
            return 'N/A'
    
    def _get_inventory_name(self, inventory_id: str) -> str:
        url = self._retrieve_inventory_url(inventory_id)
        
        try:
            response = requests.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                # Directly access 'entity' for the inventory name
                return data['entity'].get('name', 'Unknown Inventory')
            else:
                raise ClientError(f"Failed to fetch inventory details. Status code: {response.status_code}, "
                            f"Error: {response.json().get('message', 'Unknown error occurred')}")
            
        except Exception as e:
            raise ClientError(f"An error occurred while fetching inventory details: {e}")
    
    def _list_external_model_url(self):
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev':
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test':
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

        url = f"{base_url}/v3/search?auth_cache=false&auth_scope=ibm_watsonx_governance_catalog%2Ccatalog"
         
        return url



    def get_default_inventory_details(self):
        """

         Retrieves details for the default inventory along with the username also.

        Usage:
          >>> client.assets.get_default_inventory_details()
        """

        if self._is_cp4d:
            raise ClientError(
                "Mismatch: This functionality is only supported in SaaS IBM Cloud")
        else:
            url = self._retrieve_default_inventory_status_url()
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                api_response = response.json()
                external_model_admin = api_response.get("external_model_admin")
                external_model_tracking = api_response.get(
                    "external_model_tracking")
                inventory_name = api_response.get("inventory_name")

                new_url = self._retrieve_user_profile_url(external_model_admin)
                new_response = requests.get(
                    new_url, headers=self._get_headers())

                if new_response.status_code == 200:
                    new_api_response = new_response.json()
                    user_names = [
                        resource['entity'].get('name', 'N/A')
                        for resource in new_api_response.get('resources', [])
                        if resource.get('entity', {}).get('iam_id') == external_model_admin
                    ] or ['N/A']

                    result_string = (
                        f"Default Inventory Details:\n"
                        f"ExternalModel Inventory Enabled: {external_model_tracking}\n"
                        f"Inventory Name: {inventory_name}\n"
                        f"ExternalModel AdminID: {external_model_admin}\n"
                        f"User Names: {', '.join(user_names)}\n"
                    )

                    _logger.info(result_string)
                else:
                    raise ClientError(
                        "Failed to fetch the user profile. Unable to proceed.")
            else:
                error_message = "External Model Inventory is not enabled"
                raise ClientError(

                    f"Failed to retrieve members for catalog. Reason: {error_message}")
    
    def _get_account_settings(self,region):
        try:          
                if aws_env()==AWS_DEV :
                    env_url=aws_dev["DEFAULT_DEV_SERVICE_URL"]
                elif aws_env()==AWS_TEST :
                    env_url=aws_test["DEFAULT_TEST_SERVICE_URL"]
                elif aws_env()==AWS_GOVCLOUD_PREPROD :
                    env_url=aws_govcloudpreprod["DEFAULT_TEST_SERVICE_URL"]
                elif aws_env() == AWS_GOVCLOUD :
                    env_url=aws_govcloud["DEFAULT_SERVICE_URL"]
                else:
                    env_url=aws_mumbai["DEFAULT_SERVICE_URL"]
                url=f'{env_url}/v2/account_settings/{self._account_id}'
                response = requests.get(url, headers=self._get_headers(), verify=False)
                role_arn=response.json()["entity"]["cloud_integrations"]["aws"]["role_arn"]             
                return role_arn,env_url
        except Exception as ex:
           raise ClientError(f"Error in retrieving the aws account settings :{ex}")
             
    def _create_s3_session_from_token( self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_session_token: str
    ) -> boto3.Session:
      
        if not all([aws_access_key_id, aws_secret_access_key, aws_session_token]):
            raise ValueError("All the tempropary crdentials aws_access_key_id, aws_secret_access_key, aws_session_token must be provided")
        if aws_env() in [AWS_GOVCLOUD_PREPROD, AWS_GOVCLOUD]:
            region_name = "us-gov-east-1"
        elif aws_env() in [AWS_TEST , AWS_DEV]:
            region_name= "us-east-1"
        else:
            region_name= "ap-south-1"
        try:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=region_name
            )
            return session
        except Exception as e:
            _logger.error(f"Error creating boto3 session: {e}")
            raise
        
    def _list_s3_buckets(self,s3_client: boto3.client =None):
   
        try: 
            if not s3_client:
                aws_temp_creds=self._get_aws_temp_credentials()
                aws_session= self._create_s3_session_from_token(aws_access_key_id=aws_temp_creds["access_key_id"],aws_secret_access_key=aws_temp_creds["secret_access_key"],aws_session_token=aws_temp_creds["session_token"])
                s3_client = aws_session.client('s3')
                response = s3_client.list_buckets()
                if response and 'Buckets' in response:
                    bucket_list =response['Buckets']
                    return bucket_list
                else:
                    _logger.warning("No 'Buckets' key found in list_buckets response, or response is empty.")
                    return []
        except Exception as e:
            _logger.error(f"An unexpected error occurred while listing S3 buckets: {e}")

    def _create_s3_bucket(self,bucket_name: str,s3_client: boto3.client =None,  region: str=None) -> bool:

        try:
            env=aws_env()
            if env in [AWS_GOVCLOUD_PREPROD, AWS_GOVCLOUD] :
                aws_region = "us-gov-east-1"
            elif env==AWS_TEST or env==AWS_DEV :
                aws_region="test"
            else:
                aws_region="ap-south-1" 
            if not s3_client:
                aws_temp_creds=self._get_aws_temp_credentials()
                aws_session= self._create_s3_session_from_token(aws_access_key_id=aws_temp_creds["access_key_id"],aws_secret_access_key=aws_temp_creds["secret_access_key"],aws_session_token=aws_temp_creds["session_token"])
                s3_client = aws_session.client('s3')
            if not bucket_name:
                raise ValueError("Bucket name should follow the format ibm-wx-s{<container_type: s for space, p for project, c for catalog>}-{<aws_account_id>}-{<aws_region :us-east-1 for test env>}")
                
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
           
            else:
                s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': aws_region}
                    )
            _logger.info(f"Bucket '{bucket_name}' created successfully.")
            return True
        except Exception as e:
            raise ClientError(f"Error occurred while creating inventory: {str(e)}")

    
    def _remove_asset(self,asset_id: str, container_type: str = None, container_id: str = None,use_prompt_url: bool = False):
        """Remove a model or model usecase or prompt asset.

        :param asset_id: Id of the asset
        :type asset_id: str
        :param container_type: container where asset is stored, defaults to container type use when initiating client
        :type container_type: str, optional
        :param container_id: container id where asset is stored, defaults to container id used when initiating client. For external models, if not provided, uses available platform asset catalog.
        :type container_id: str, optional
        :raises ClientError: Report exception details
        """ 
        if self._external_model:
            container_type = container_type or MODEL_USECASE_CONTAINER_TYPE_TAG
            container_id = container_id or self._get_pac_catalog_id()
        else:
            container_type = container_type or self._container_type
            container_id = container_id or self._container_id
        if use_prompt_url:
            url = self._get_prompts_url(asset_id, container_type, container_id)
        else:
            url = self._get_assets_url(asset_id, container_type, container_id)

        response = requests.delete(url, headers=self._get_headers())

        if response.status_code == 204:
            _logger.info("Successfully deleted asset id {} in {} {}".format(
                asset_id, container_type, container_id))
        else:
            raise ClientError("Failed to delete asset {}. ERROR {}. {}".format(
                asset_id, response.status_code, response.text))
            
    def remove_asset(self, asset_id: str, container_type: str = None, container_id: str = None):
        """Remove a model or model usecase asset."

        :param asset_id: Id of the asset
        :type asset_id: str
        :param container_type: container where asset is stored, defaults to container type use when initiating client
        :type container_type: str, optional
        :param container_id: container id where asset is stored, defaults to container id used when initiating client. For external models, if not provided, uses available platform asset catalog.
        :type container_id: str, optional
        :raises ClientError: Report exception details

        The way you can use me is :

        >>> client.assets.remove_asset(asset_id=<model or model usecase id>)
        >>> client.assets.remove_asset(asset_id=<model or model usecase id>,container_type=<space,project or catalog>, container_id=<container id>)

        """       
        
        if not container_id:
            container_id = self._container_id
        if not container_type:
            container_type = self._container_type
            
        asset_type = self._get_asset_type(
            asset_id, container_id, container_type)

        # if asset_type is prompt, raise error
        if asset_type == PROMPT_ASSET:
            raise ClientError(f"This method if for not for prompt assets. For deleting prompt asset of type {PROMPT_ASSET} use 'delete_prompt_asset()' method instead")
        else:
            self._remove_asset(asset_id=asset_id, container_type=container_type, container_id=container_id)
           


    def delete_prompt_asset(self, asset_id: str, container_type: str = None, container_id: str = None):
        """Deletes a prompt asset after checking the tracking status of the prompt against an AI usecase
        In case a prompt is tracked to an ai usecase, then user is warned. User may untrack the prompt and re-execute the delete prompt command for deleting the same.

        :param asset_id: Id of the asset
        :type asset_id: str
        :param container_type: container where asset is stored, defaults to container type use when initiating client
        :type container_type: str, optional
        :param container_id: container id where asset is stored, defaults to container id used when initiating client. For external models, if not provided, uses available platform asset catalog.
        :type container_id: str, optional

        The way you can use me is :

        >>> client.assets.delete_prompt_asset(asset_id=<model or model usecase id>)
        >>> client.assets.delete_prompt_asset(asset_id=<model or model usecase id>,container_type=<space,project or catalog>, container_id=<container id>)
        """

        _logger.info("------------------------------ Prompt Deletion Started ------------------------------")
        if not container_id:
            container_id = self._container_id
        if not container_type:
            container_type = self._container_type
        asset_type = self._get_asset_type(
            asset_id, container_id, container_type)

        # if asset_type is prompt, check for the tracking status
        if asset_type == PROMPT_ASSET:
            self.DISABLE_LOGGING=True
            prompt_to_delete = self._facts_client.assets.get_prompt(
                asset_id, container_type, container_id)
            flag = False
            try:
                linked_ai_usecase_info = prompt_to_delete.get_tracking_model_usecase().to_dict()
                if "model_usecase_id" in linked_ai_usecase_info:
                    flag = True
                    linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']

                    if linked_ai_usecase:
                        warnings.warn(
                            f"Prompt Asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}. Please untrack it before deleting the prompt asset", category=UserWarning)
            except ClientError as ce:
                if ce.error_msg.endswith("lmid is missing"):
                    # delete
                    _logger.info(
                        f"Deleting prompt asset {asset_id}. Prompt is not tracked with any AI usecase")
                    self._facts_client.assets._remove_asset(asset_id,container_type,container_id,use_prompt_url=True)
                elif flag == False and ce.error_msg.endswith("is not tracked by a model use case"):
                    # delete
                    _logger.info(
                        f"Deleting prompt asset {asset_id}. Prompt is not tracked with any AI usecase")
                    self._facts_client.assets._remove_asset(asset_id,container_type,container_id,use_prompt_url=True)
                    # self._facts_client.assets._remove_asset(asset_id)
                else:
                    _logger.info(
                        f"Failed to delete prompt asset due to {ce.error_msg}")
        else:
            raise ClientError(
                f"asset_id passed is not of the type :{PROMPT_ASSET}")

    @deprecated(alternative="client.assets.get_model_usecases()")
    def list_model_usecases(self, catalog_id: str = None) -> list:
        """
            Returns WKC Model usecase assets

            :param str catalog_id: Catalog ID where registered model usecase. if not provided, dafault shows all model usecases in all catalogs across all accounts to which the user has access.

            :return: All WKC Model usecase assets for a catalog
            :rtype: list

            Example:

            >>> client.assets.list_model_usecases(catalog_id=<catalog_id>)
            >>> client.assets.list_model_usecases()

        """

        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)
            list_url = WKC_MODEL_LIST_FROM_CATALOG.format(catalog_id)
        else:
            list_url = WKC_MODEL_LIST_ALL

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                list_url
        else:
            if get_env() == 'dev' :
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    list_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    list_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    list_url

        # request=self._facts_client.prepare_request(method='GET',url=url,headers=self._get_headers())

        response = requests.get(url,
                                headers=self._get_headers()
                                )
        # response=self._facts_client.send(request)

        if response.status_code == 200:
            return response.json()["results"]

        else:
            error_msg = u'WKC Model Entries listing failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)

    def _get_pac_catalog_id(self):
        
        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            bss_id = self._account_id
        elif self._is_cp4d :
            bss_id = self._get_bss_id_cpd()
        else:
            bss_id = self._get_bss_id()

        if self._is_cp4d :
            url = self._cpd_configs["url"] + \
                '/v2/catalogs/ibm-global-catalog?bss_account_id=' + bss_id

        else:
            if get_env()== 'dev' and aws_env()==AWS_DEV:
                url = dev_config["DEFAULT_DEV_SERVICE_URL"]+ \
                f'/v2/catalogs?bss_account_id={bss_id}'

            elif get_env()== 'test' and aws_env()==AWS_TEST or aws_env()==AWS_GOVCLOUD_PREPROD:
                url = test_config["DEFAULT_TEST_SERVICE_URL"]+ \
                f'/v2/catalogs?bss_account_id={bss_id}'

            elif get_env()== 'aws_mumbai' and aws_env()==AWS_MUM:
                url = prod_config["DEFAULT_SERVICE_URL"]+ \
                f'/v2/catalogs?bss_account_id={bss_id}'

            elif get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/catalogs/ibm-global-catalog?bss_account_id=' + bss_id
            elif get_env() == 'test' :
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/catalogs/ibm-global-catalog?bss_account_id=' + bss_id

            elif aws_env() == AWS_GOVCLOUD :
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      f'/v2/catalogs?bss_account_id={bss_id}'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/catalogs/ibm-global-catalog?bss_account_id=' + bss_id

        response = requests.get(url, headers=self._get_headers())
        catalog_id = response.json()["metadata"]["guid"]

        return catalog_id
    def _retrieve_default_inventory_status_url(self):
        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            bss_id=self._account_id
        elif self._is_cp4d:
            bss_id = self._get_bss_id_cpd()
        else:
            bss_id = self._get_bss_id()
        if self._is_cp4d:
            url = self._cpd_configs['url'] + \
                '/v1/aigov/model_inventory/externalmodel_config?bss_account_id' + bss_id
        else:
            if get_env() =='dev' :   
                url = dev_config['DEFAULT_DEV_SERVICE_URL'] + \
                    '/v1/aigov/model_inventory/externalmodel_config?bss_account_id='+bss_id
            elif get_env() =='test' :   
                url = test_config['DEFAULT_TEST_SERVICE_URL'] + \
                    '/v1/aigov/model_inventory/externalmodel_config?bss_account_id='+bss_id
            else:
                url = prod_config['DEFAULT_SERVICE_URL'] + \
                    '/v1/aigov/model_inventory/externalmodel_config?bss_account_id='+bss_id
        return url

    def _retrieve_user_profile_url(self, external_model_admin: str) -> str:
        if self._is_cp4d:
            url = self._cpd_configs['url'] + \
                '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
        else:
            if get_env() =='dev' :
                url = dev_config['DEFAULT_DEV_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
            elif get_env() =='test':  
                url = test_config['DEFAULT_TEST_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
            else:
                url = prod_config['DEFAULT_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
               

        return url

    def _get_bss_id(self):
        try:
            token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator))) else self._facts_client.authenticator.bearer_token
            decoded_bss_id = jwt.decode(token, options={"verify_signature": False})[
                "account"]["bss"]
        except jwt.ExpiredSignatureError:
            raise
        return decoded_bss_id
    
    # def _get_bss_id_aws(self):
    #     try:
    #         token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
    #             isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator))) else self._facts_client.authenticator.bearer_token
    #         decoded_bss_id = jwt.decode(token, options={"verify_signature": False})["accountId"]
            
    #     except jwt.ExpiredSignatureError:
    #         raise
    #     return decoded_bss_id
    
    def _get_bss_id_cpd(self):
        decoded_bss_id = "999"
        return decoded_bss_id
    

    def _remove_asset_conf_data(self):
        value1="true"
        value2="false"
        return {
            "description": "The modelfacts user AssetType to capture the user defined attributes of a model.",
            "fields": [],
            "relationships": [],
            "global_search_searchable": [],
            "localized_metadata_attributes": {
                "name": {
                    "default": "Additional details",
                    "en": "Additional details"
                }
            },
            "properties": {},
            "attribute_only":value1,
            "allow_decorators":value2
        }

    def _update_props(self, data, bss_id, type_name,operation_type):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/asset_types/'+type_name
        else:
            if get_env() =='dev':    
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/asset_types/'+type_name
            elif get_env() =='test':   
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/asset_types/'+type_name
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/asset_types/'+type_name

        params = {"bss_account_id": bss_id}

        response = requests.put(url=url,
                                headers=self._get_headers(),
                                params=params,
                                data=json.dumps(data))

        if response.status_code == 401:
            _logger.exception("Expired token found.")
            raise
        elif response.status_code == 200 or response.status_code == 202:
            if operation_type == "create":
               _logger.info("Custom facts definitions updated Successfully")
            elif operation_type=="remove":
                 _logger.info("Custom facts definitions Removed Successfully")
        else:
            _logger.exception(
                "Error updating properties. ERROR {}. {}".format(response.status_code,response.text))

    def _get_current_assets_prop(self, asset_type):
        current_asset_prop = None

        if self._is_cp4d:
            cur_bss_id = self._get_bss_id_cpd()
        else:
            cur_bss_id = self._get_bss_id()

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/asset_types/' + asset_type + "?" + "bss_account_id=" + cur_bss_id
        else:

            if get_env() == 'dev' :   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/asset_types/' + asset_type + "?" + "bss_account_id=" + cur_bss_id
            elif get_env() =='test':   
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/asset_types/'+ asset_type + "?" + "bss_account_id=" + cur_bss_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/asset_types/'+ asset_type + "?" + "bss_account_id=" + cur_bss_id
                

        response = requests.get(url=url,
                                headers=self._get_headers())

        if not response:
            _logger.exception(
                "Current asset properties not found for type {}".format(asset_type))

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
            description = row["description"]
            order = row.get("order") 
            
            if isinstance(order, int) or (isinstance(order, str) and order.isdigit()):
                description = f'@{order} {description}' 

            tmp_props["type"] = row["type"]
            tmp_props["description"] = description
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

    def _format_data(self, csvFilePath, overwrite, asset_type, section_name):
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

            if section_name:
                final_dict["localized_metadata_attributes"] = {
                    "name": {"default": section_name, "en": section_name}}
            else:
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

    def _check_if_op_enabled(self):
        url = self._cpd_configs["url"] + "/v1/aigov/model_inventory/grc/config"
        response = requests.get(url,
                                headers=self._get_headers()
                                )

        if response.status_code == 404:
            raise ClientError("Could not check if Openpages enabled in the platform or not. Make sure you have factsheet installed in same namespace as WKC/WSL. ERROR {}. {}".format(
                response.status_code, response.text))
        elif response.status_code == 200:
            return response.json().get("grc_integration")
        else:
            raise ClientError("Failed not find openpages integrations config details. ERROR {}. {}".format(
                response.status_code, response.text))

    def _get_assets_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        else:
            if get_env() =='dev':   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            elif get_env() =='test':   
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        return url

    def _get_prompts_url(self, prompt_id, container_type, container_id,create_prompt=False):
       
        base_url = ''
        if self._is_cp4d:
            base_url = self._cpd_configs["url"]
        else:
            env = get_env()
            if env == 'dev':   
                base_url = dev_config["DEFAULT_DEV_SERVICE_URL"]
            elif env == 'test' :
                base_url = test_config["DEFAULT_TEST_SERVICE_URL"]
            else:
                base_url = prod_config["DEFAULT_SERVICE_URL"]
        
        if container_type is None or container_id is None:
           raise ValueError("container_type and container_id must be specified and cannot be None")

        if create_prompt:
            url = base_url + '/wx/v1/prompts?' + container_type + '_id=' +  container_id
        else:
            url = base_url + '/wx/v1/prompts/' + prompt_id + '?' + container_type + '_id=' + container_id

        return url

    # utils============================

    def _get_headers(self):

        
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token

        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers

    def _get_fact_definition_properties(self, fact_id):

        if self._facts_definitions:
            props = self._facts_definitions.get(PROPERTIES)
            props_by_id = props.get(fact_id)
        else:
            data = self.get_user_fact_definitions()
            props = data.get(PROPERTIES)
            props_by_id = props.get(fact_id)

        if not props_by_id:
            raise ClientError(
                "Could not find properties for fact id {} ".format(fact_id))

        return props_by_id

    def _type_check_by_id(self, id, val):
        cur_type = self._get_fact_definition_properties(id).get("type")
        is_arr = self._get_fact_definition_properties(id).get("is_array")

        if cur_type == "integer" and not isinstance(val, int):
            raise ClientError("Invalid value used for type of Integer")
        elif cur_type == "string" and not isinstance(val, str) and not is_arr:
            raise ClientError("Invalid value used for type of String")
        elif (cur_type == "string" and is_arr) and (not isinstance(val, str) and not isinstance(val, list)):
            raise ClientError(
                "Invalid value used for type of String. Value should be either a string or list of strings")

    def _get_assets_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        asset_id = asset_id or self._asset_id
        container_type = container_type or self._container_type
        container_id = container_id or self._container_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        else:
            if get_env() =='dev' :
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            elif get_env() =='test' :
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        return url

    # added by Lakshmi
    @deprecated(alternative="client.assets.create_ai_usecase()", reason="new generalized method available to cover models and prompts")
    def create_model_usecase(self, catalog_id: str = None, name: str = None, description: str = None) -> ModelUsecaseUtilities:
        """
            Returns WKC Model usecase

            :param str catalog_id:  Catalog ID where this model usecase needs to create.
            :param str name: Name of model usecase
            :param str description: (Optional) Model usecase description

            :rtype: ModelUsecaseUtilities

            :return: WKC Model usecase asset

            Example:

            >>> client.assets.create_model_usecase(catalog_id=<catalog_id>,name=<model usecase name>,description=<model usecase description>)

        """

        if (catalog_id is None or catalog_id == ""):
            raise MissingValue("catalog_id", "catalog ID is missing")
        if (name is None or name == ""):
            raise MissingValue("name", "Model usecase name is missing")

        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)

        if name:
            body = {
                "name": name,
                "description": description
            }
        else:
            raise ClientError("Provide model usecase name")

        url = self._get_create_usecase_url(catalog_id)

        response = requests.post(url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 201:
            _logger.info("Model usecase created successfully")
            retResponse = response.json()
            retrieved_catalog_id = retResponse["metadata"]["catalog_id"]
            retrieved_asset_id = retResponse["metadata"]["asset_id"]
            # self._current_model_usecase = ModelUsecaseUtilities(self,model_usecase_id=retrieved_asset_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=retrieved_catalog_id)
            self._current_model_usecase = ModelUsecaseUtilities(
                self, model_usecase_id=retrieved_asset_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=retrieved_catalog_id, facts_type=FactsType.MODEL_USECASE_USER)
            return self._current_model_usecase
        else:
            raise ClientError("Failed while creating model usecase. ERROR {}. {}".format(
                response.status_code, response.text))

    def _get_create_usecase_url(self, catalog_id: str = None):

        usecase_url = '/v1/aigov/model_inventory/model_entries?catalog_id=' + catalog_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + usecase_url
        else:
            if get_env() =='dev' :   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + usecase_url
            elif get_env() =='test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + usecase_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + usecase_url
        return url

    def get_ai_usecases(self, catalog_id: str = None,limit_to_apikey_account:bool = True) -> list:
        """
        Returns AI usecase assets.

        :param str catalog_id: (Optional) Catalog ID where AI usecases are registered. If not provided, defaults to showing all AI usecases in all catalogs across all accounts to which the user has access.
        :param bool limit_to_apikey_account: (Optional) Value is set to True by default, limiting the returned results to the current BSS account ID linked to the API key used. Can be modified and set to False when required. This flag works only when no catalog ID is passed and in a cloud environment.

        :rtype: list of AIUsecaseUtilities

        :return: All AI usecase assets for a catalog.

        Example:

        >>> client.assets.get_ai_usecases(catalog_id=<catalog_id>)
        >>> client.assets.get_ai_usecases()
        """
        
        # condition self._cp4d_version < "4.8.3" added by Lakshmi as part of 4.8.3 changes
        # if self._is_cp4d:
        if self._is_cp4d and self._cp4d_version < "4.8.3":
            # raise ClientError("Mismatch: This functionality is only supported in SaaS IBM Cloud")
            raise ClientError(
                "Mismatch: This functionality is only supported in SaaS IBM Cloud and CPD versions >=4.8.3")
        
        #addings checks
         # Checking if more parameters are passed
        if len((catalog_id, limit_to_apikey_account)) > 2:
            raise TypeError("get_ai_usecases() accepts at most two positional arguments.")

        #checking type of catalog id passed
        if catalog_id:
            if not isinstance(catalog_id, str):
                raise TypeError("The 'catalog_id' must be a string.")
            if "," in catalog_id:
                raise TypeError("Only a single catalog id should be passed. Multiple values were provided.")

        # Checking type of limit_to_apikey_account 
        if not isinstance(limit_to_apikey_account, bool):
            raise TypeError("The 'limit_to_apikey_account' parameter must be a boolean.")

 
        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)
            list_url = WKC_MODEL_LIST_FROM_CATALOG.format(catalog_id)
        else:
            if not self._is_cp4d and limit_to_apikey_account:
                bss_id = self._get_bss_id()
                params = {
                    'bss_account_id' : bss_id
                }
                query_bss_account_id = urlencode(params)
                list_url = f"{WKC_MODEL_LIST_ALL}?{query_bss_account_id}"
            else:
                list_url = WKC_MODEL_LIST_ALL

        if self._is_cp4d and self._cp4d_version >= "4.8.3":
            url = self._cpd_configs["url"] + \
                list_url
        else:
            if get_env() == 'dev' :    
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    list_url
            elif get_env() == 'test' :   
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    list_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    list_url
        response = requests.get(url,
                                headers=self._get_headers()
                                )
        if response.status_code == 200:
            usecase_list = response.json()["results"]
            # usecase_list_values = [
            #     AIUsecaseUtilities(
            #         self,
            #         ai_usecase_name=usecaseVal["metadata"]["name"],
            #         model_usecase_id=usecaseVal["metadata"]["asset_id"],
            #         container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,
            #         container_id=usecaseVal["metadata"]["catalog_id"],
            #         facts_type=self._facts_type
            #     )
            #     for usecaseVal in usecase_list
            # ]
            # return usecase_list_values
            
            # Use ThreadPoolExecutor to create AIUsecaseUtilities concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                usecase_list_values = list(executor.map(
                    lambda usecaseVal: AIUsecaseUtilities(
                        self,
                        ai_usecase_name=usecaseVal["metadata"]["name"],
                        model_usecase_id=usecaseVal["metadata"]["asset_id"],
                        container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,
                        container_id=usecaseVal["metadata"]["catalog_id"],
                        facts_type=self._facts_type
                    ), usecase_list
                ))

            return usecase_list_values
        
        else:
            error_msg = u'WKC Model Entries listing failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)
       # return self.get_model_usecases(catalog_id, is_prompt=True)
    

    def get_ai_usecases_by_name(self, name: str, inventory_id: str = None,exact_match:bool=None) -> List[AIUsecaseUtilities]:
        """
        Retrieve AI use cases by name.

        Search for AI use cases based on the provided name. If `exact_match` is True, only exact matches are returned; otherwise, partial matches are included. An optional `inventory_id` can limit the search to a specific inventory.

        Parameters:
            - name (str): The name or partial name of the AI use case.
            - inventory_id (str, optional): The ID to filter by inventory. Defaults to None.
            - exact_match (bool, optional): If True, returns only exact matches. Defaults to False.

        Returns:
            List[AIUsecaseUtilities]: A list of matching AI use cases.

        Examples:
            ::
            
                # Search for AI use cases with names that contain 'sample'
                usecases = client.assets.get_ai_usecases_by_name(name='sample')

                # Search for AI use cases with an exact name match
                usecases = client.assets.get_ai_usecases_by_name(name='sample', exact_match=True)
        """
        print("-" * OUTPUT_WIDTH)
        print(" AI Usecase Retrieval by Name Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)

        
        if not name:
            raise ValueError("The 'name' parameter is required and cannot be None or empty.")

        query = {
            "query": {
                "bool": {
                    "filter": [{"term": {"metadata.artifact_type": "model_entry"}}], 
                    "must": [] 
                }
            },
            "sort": [{"metadata.modified_on": {"order": "desc", "unmapped_type": "date"}}]
        }

        if exact_match:
            query["query"]["bool"]["filter"].append({"term": {"metadata.name.keyword": name}})
        else:
            query["query"]["bool"]["must"].append({"match": {"metadata.name": name}})


        if inventory_id:
            query["query"]["bool"]["filter"].append({"term": {"entity.assets.catalog_id": inventory_id}})


        try:

            api_url = self._get_ai_usecase_url()
            response = requests.post(api_url, headers=self._get_headers(), data=json.dumps(query))
            response.raise_for_status()
            total_size = response.json().get("size", 0)
            rows = response.json().get("rows", [])

            _logger.info(f"Total number of AI use cases with matching names found: {total_size}")

            with ThreadPoolExecutor() as executor:
             futures = [
                executor.submit(
                    AIUsecaseUtilities,
                    self,
                    ai_usecase_name=row.get("metadata", {}).get("name", ""),
                    model_usecase_id=row.get("artifact_id", ""),
                    container_id=row.get("entity", {}).get("assets", {}).get("catalog_id", ""),
                    container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,
                    facts_type=self._facts_type
                )
                for row in rows
            ]

            # Collect the results from the futures
            usecase_utilities = [future.result() for future in futures]

            return usecase_utilities

        except Exception as e:
            print(f"An error occurred: {e}")
            return []
        

        
    def _get_ai_usecase_url(self):
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev' :   
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() =='test' :   
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

        url = f"{base_url}/v3/search?auth_cache=false&auth_scope=ibm_watsonx_governance_catalog%2Ccatalog"
         
        return url

    # added by Lakshmi, removed reference of is_prompt
    @deprecated(alternative="client.assets.get_ai_usecases()", reason="new generalized method available to cover models and prompts")
    def get_model_usecases(self, catalog_id: str = None) -> list:
        # def get_model_usecases(self, catalog_id:str=None, is_prompt: bool=False)-> list:
        """
            Returns WKC Model usecase assets

            :param str catalog_id:  (Optional) Catalog ID where model usecase are registered. if not provided, dafault shows all model usecases in all catalogs across all accounts to which the user has access.

            :rtype: list(ModelUsecaseUtilities)

            :return: All WKC Model usecase assets for a catalog

            Example:

            >>> client.assets.get_model_usecases(catalog_id=<catalog_id>)
            >>> client.assets.get_model_usecases()

        """

        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)
            list_url = WKC_MODEL_LIST_FROM_CATALOG.format(catalog_id)
        else:
            list_url = WKC_MODEL_LIST_ALL

        # if is_prompt:
        #     replace_name = "AI"
        # else:
        #     replace_name = "model"
        replace_name = "model"
        if self._is_cp4d:
            url = self._cpd_configs["url"] + list_url
        else:
            if get_env() == 'dev' :   
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + list_url
            elif get_env() == 'test' :
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + list_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + list_url

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:

            usecase_list = response.json()["results"]
            usecase_list_values = []
            for usecaseVal in usecase_list:
                retrieved_catalog_id = usecaseVal["metadata"]["catalog_id"]
                retrieved_asset_id = usecaseVal["metadata"]["asset_id"]
                usecase_list_values.append(ModelUsecaseUtilities(self, model_usecase_id=retrieved_asset_id,
                                           container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=retrieved_catalog_id, facts_type=FactsType.MODEL_USECASE_USER))
                # if is_prompt:
                #     usecase_list_values.append(AIUsecaseUtilities(self,model_usecase_id=retrieved_asset_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=retrieved_catalog_id))
                # else:
                #     usecase_list_values.append(ModelUsecaseUtilities(self,model_usecase_id=retrieved_asset_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=retrieved_catalog_id))
            _logger.info(
                "{} usecases retrieved successfully".format(replace_name))
            return usecase_list_values
        else:
            error_msg = u'Usecase listing failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)

    def get_PAC_id(self) -> str:
        """
            Get Platform Asset Catalog ( PAC ) ID.

            :rtype: PAC ID

            The way to use me is:

            >>> client.assets.get_PAC_id()

        """

        return self._get_pac_catalog_id()

    def _print_attachment_definitions_tree_structure(self, data: dict) -> None:
        if not isinstance(data, dict) or "attachment_fact_definitions" not in data:
            print("Invalid data format or missing required fields.")
            print(f"data: {data}")
            return

        for definition in data["attachment_fact_definitions"]:
            if not isinstance(definition, dict) or "type" not in definition:
                print("Invalid definition format or missing required 'type' field.")
                continue
            print(f"type: {definition['type']}")
            # Handling for type model_usecase and model
            # Check "phases"
            if "phases" in definition:
                print("<<<<< phases >>>>>:\n")
                for phase in definition["phases"]:
                    print("-" * 40)
                    print(f"    phase_name: {phase.get('phase_name', ' ')}")
                    print("-" * 40)
                    self._print_groups(phase.get("groups", []))

            elif "groups" in definition:
                self._print_groups(definition.get("groups", []))

    def _print_groups(self, groups: list) -> None:
        for group in groups:
            print(f"      **group**:\n")
            print(f"      -- name: {group.get('name', ' ')}")
            print(f"      -- id: {group.get('id', ' ')}")
            print(f"      -- description: {group.get('description', ' ')}")
            print()
            for fact in group.get("facts", []):
                print("            **facts**:\n")
                print(f"           -- name: {fact.get('name', ' ')}")
                print(f"           -- id: {fact.get('id', ' ')}")
                print(f"           -- description: {fact.get('description', ' ')}")
                print(f"           -- arrangement_order_id: {fact.get('arrangement_order_id', ' ')}")
                print("\n")

    def get_attachment_definitions(self, type_name: str = None) -> None:
            """
                Displays all attachment fact definitions for model or model_usecase. Supported for CPD version >=4.6.5
                :return: None
                :rtype: list()

                The way to use me is:

                >>> client.assets.get_attachment_definitions(type_name=<model or model_usecase>)

            """

            if self._is_cp4d and self._cp4d_version < "4.6.5":
                raise ClientError(
                    "Version mismatch: Retrieving attachment fact definitions functionality is only supported in CP4D version 4.6.4.0 or higher. Current version of CP4D is "+self._cp4d_version)

            validate_enum(type_name, "type_name",
                          AttachmentFactDefinitionType, True)

            url = self._get_attachment_definitions_url(type_name)

            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                _logger.info("Attachment fact definitions retrieved successfully")
                data = response.json()
                self._print_attachment_definitions_tree_structure(data)
                #return data
            else:
                raise ClientError("Failed in retrieving attachment fact definitions. ERROR {}. {}".format(
                    response.status_code, response.text))

    def _get_attachment_definitions_url(self, type_name: str = None):

        append_url = '/v1/aigov/factsheet/attachment_fact_definitions/' + type_name

        if self._is_cp4d:
            url = self._cpd_configs["url"] + append_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + append_url
            elif get_env() == 'test' :
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + append_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + append_url

        return url

    def create_ai_usecase(self, catalog_id: str = None, name: str = None, description: str = None, status: str = None, risk: str = None, tags: list = None) -> AIUsecaseUtilities:
        """
            Returns AI usecase

            :param str catalog_id:  Catalog ID where this model usecase needs to create.
            :param str name: Name of model usecase
            :param str description: (Optional) Model usecase description
            :param str status: (Optional) AI Usecase status.Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Status`
            :param str risk: (Optional) AI Usecase risk.Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Risk`
            :param list tags: (Optional) AI usecase tags. Provide list of tags, for example ["usecase for prod","model for prod"]

            :rtype: AIUsecaseUtilities

            :return: AI usecase asset

            Example:

            >>> client.assets.create_ai_usecase(catalog_id=<catalog_id>,name=<AI usecase name>,description=<AI usecase description>)

        """
        # condition self._cp4d_version < "4.8.3" added by Lakshmi as part of 4.8.3 changes
        if self._is_cp4d and self._cp4d_version < "4.8.3":
            raise ClientError(
                "Mismatch: This functionality is only supported in SaaS IBM Cloud and CPD versions >=4.8.3")

        if (catalog_id is None or catalog_id == ""):
            raise MissingValue("catalog_id", "catalog ID is missing")
        if (name is None or name == ""):
            raise MissingValue("name", "AI usecase name is missing")
        if not (tags is None or tags == "") and not isinstance(tags, list):
            raise MissingValue(
                "tags", "If AI usecase tags is provided then tags should be list of values")

        validate_enum(status, "Status", Status, False)
        validate_enum(risk, "Risk", Risk, False)

        if catalog_id:
            validate_type(catalog_id, u'catalog_id', STR_TYPE, True)

        if name:
            body = {
                "name": name
            }
        if description:
            body["description"] = description
        if status:
            body["status"] = status
        if risk:
            body["risk_level"] = risk
        if tags:
            body["tags"] = tags

        url = self._get_create_usecase_url(catalog_id)

        response = requests.post(url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 201:
            _logger.info("AI usecase created successfully")
            retResponse = response.json()
            retrieved_catalog_id = retResponse["metadata"]["catalog_id"]
            retrieved_asset_id = retResponse["metadata"]["asset_id"]
            # self._current_model_usecase = AIUsecaseUtilities(self,model_usecase_id=retrieved_asset_id,container_type=MODEL_USECASE_CONTAINER_TYPE_TAG,container_id=retrieved_catalog_id,facts_type="model_entry_user")
            self._current_model_usecase = AIUsecaseUtilities(
                self,ai_usecase_name=name, model_usecase_id=retrieved_asset_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=retrieved_catalog_id, facts_type=FactsType.MODEL_USECASE_USER)
            return self._current_model_usecase
        else:
            raise ClientError("Failed while creating AI usecase. ERROR {}. {}".format(
                response.status_code, response.text))
#=====================================  PROMPT ASSET  ======================================================================================
        
    def create_detached_prompt(self, name:str, model_id:str,task_id:str,detached_information:'DetachedPromptTemplate',description:str=None, prompt_details:'PromptTemplate'=None,container_type:str=None,container_id:str=None)->AIGovAssetUtilities:
        """
        Create a Detached/External Prompt Template Asset.


        :param str name: The name of the detached prompt being created.
        :param str model_id: The identifier of the model associated with the extrnal prompt
        :param str task_id: Describes possible Task for the prompt template creation
        :param DetachedPromptTemplate detached_information: Holds information about an external prompt, including its ID, associated model ID, provider, model name and URL, prompt URL, and additional information
        :param str description: (Optional) description of the external prompt to be created
        :param PromptTemplate prompt_details: (Optional) Holds information about  task IDs, model version details, prompt variables, instructions, input/output prefixes, and example data
        :param str container_id: (Optional) used to save the detached prompt 

        Returns:
         AIGovAssetUtilities
        
            
        Example-1 (**Creating a Detached prompt with minimal information**),::
            
                detached_info = DetachedPromptTemplate(prompt_id="n/a",
                                                       model_id="arn:aws:bedrock:us-east1:123456789012:provisioned-model/anthropic.claude-v2",
                                                       model_provider="AWS Bedrock",
                                                       model_name="Anthropic Claude 2.0",
                                                       model_url="https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html",
                                                       prompt_url="n/a",
                                                       prompt_additional_info={"AWS Region": "us-east1"}
                                                       )

                external_prompt = facts.client.asests.create_detached_prompt(name="External prompt sample (model AWS Bedrock Anthropic)",
                                                                         task_id="summarization",
                                                                         model_id="anthropic.claude-v2", 
                                                                         description="My First External Prompt",
                                                                         detached_information=ivar_detached_info)


        Example-2 (**Creating a Detached prompt with additional details**),::
              
            detached_info = DetachedPromptTemplate(prompt_id="n/a",
                                            model_id="arn:aws:bedrock:us-east1:123456789012:provisioned-model/anthropic.claude-v2",
                                            model_provider="AWS Bedrock",
                                            model_name="Anthropic Claude 2.0",
                                            model_url="https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html",
                                            prompt_url="n/a",
                                            prompt_additional_info={"AWS Region": "us-east1"}
                                            )
            
            prompt_template = PromptTemplate(
                                             prompt_variables= {"text": "value" }
                                             input="Input text to be given",
                                             
                                             model_parameters={"decoding_method":"greedy"
                                                              "max_new_tokens":2034,
                                                              "min_new_tokens":0,
                                                              "random_seed":0,
                                                              "top_k":0,
                                                              "top_p":0
                                                              }

    
            external_prompt = facts.client.asests.create_detached_prompt(name="External prompt sample (model AWS Bedrock Anthropic)", 
                                                 model_id="anthropic.claude-v2", 
                                                 task_id="summarization",
                                                 detached_information=ivar_detached_info, 
                                                 description="My First External Prompt", 
                                                 prompt_details=prompt_template, 
                                                )
        """
        if self._is_cp4d and self._cp4d_version < "5.0.0":
              raise ClientError("Version mismatch: Detached prompt functionality is only supported in CP4D version 5.0.0 or higher. Current version of CP4D is "+self._cp4d_version)
        

        validate_enum(task_id,"task_id",Task,False)

    
        if prompt_details is not None:
            data = {
                    "instruction": prompt_details.prompt_instruction or None,
                    "input_prefix": prompt_details.input_prefix or None,
                    "output_prefix": prompt_details.output_prefix or None,
                    "examples":None
                    }
            
            if prompt_details.structured_examples is not None:
                 formatted_examples = []
                 for input_text, output_text in prompt_details.structured_examples.items():
                      formatted_examples.append([input_text, output_text])
                 if formatted_examples:
                     data["examples"] = formatted_examples
    

            new_data = {k: v for k, v in data.items() if v is not None}
        else:
            new_data = {}


        body = {
                "task_ids":[task_id],
                "input_mode":'detached',
                "name": name,
                "description": description,
                "prompt": { 
                    "model_id":model_id ,
                    "data":new_data
                }
            }
             
        if prompt_details is not None:
            if prompt_details.model_version is not None:
                body["model_version"]=prompt_details.model_version 
                
            if prompt_details.prompt_variables is not  None:
                body["prompt_variables"] = {key: {"default_value": value} for key, value in prompt_details.prompt_variables.items()}
                
                # if prompt_details.chat_items is not None:
                #      body["prompt"]["chat_items"]=prompt_details.chat_items

            if prompt_details.input is not None:
                body["prompt"]["input"]=[[prompt_details.input, ""]]

            if prompt_details.model_parameters is not None:
                body["prompt"]["model_parameters"] =prompt_details.model_parameters
             
        # external info
        external_information = {
                        "external_prompt_id": detached_information.prompt_id,
                        "external_model_id": detached_information.model_id,
                        "external_model_provider": detached_information.model_provider,
                   }
        
        if not detached_information.prompt_url  and not detached_information.prompt_additional_info:
             pass
        elif detached_information.prompt_url and detached_information.prompt_additional_info:
           external_information["external_prompt"] = {
           "url": detached_information.prompt_url,
         "additional_information": [detached_information.prompt_additional_info]
         }
        else:
            raise ClientError("Both prompt_url and prompt_additional_info must be provided together.")

        
        if not detached_information.model_url and not detached_information.model_name:
             pass
        elif detached_information.model_name and detached_information.model_url:
             external_information["external_model"] = {
                "name": detached_information.model_name,
                "url": detached_information.model_url
              }   
        else:
          raise ClientError("External model_name and model_url information must be provided together.")


        external_information_data = {k: v for (k, v) in external_information.items() if v}



        body["prompt"]["external_information"] = external_information_data

        # if  prompt_details is not None:
        #         # model_parameters_data = {
        #         #             "decoding_method": prompt_details.decoding_method,
        #         #             "max_new_tokens": prompt_details.max_new_tokens,
        #         #             "min_new_tokens":prompt_details.min_new_tokens,
        #         #             "random_seed": prompt_details.random_seed,
        #         #             "stop_sequences": prompt_details.stop_sequences,
        #         #             "temperature": prompt_details.temperature,
        #         #             "top_k": prompt_details.top_k,
        #         #             "top_p": prompt_details.top_p,
        #         #             "repetition_penalty": prompt_details.repetition_penalty
        #         #         }
                
        #         # model_parameters_data = {k: v for k, v in model_parameters_data.items() if v is not None}
        #     body["prompt"]["model_parameters"] =prompt_details.model_parameters
        

        try:
            _logger.info("------------------------------ Detached Prompt Creation Started ------------------------------")
            container_id=self._container_id if container_id is None else container_id
            container_type=self._container_type if container_type is None else container_type
            url = self._get_prompts_url(None,container_type,container_id,create_prompt=True)
            responseVal = requests.post(url, headers=self._get_headers(), data=json.dumps(body), verify=False)
            responseVal.raise_for_status()
             # Process the successful response
            json_data = responseVal.json()
            _logger.info("The detached prompt with ID {} was created successfully in container_id {}.".format(responseVal.json().get('id'),container_id))
            self._asset_id=json_data.get("id")
            self._current_model=AIGovAssetUtilities(self,json_data=json_data,model_id=self._asset_id,container_type=container_type,container_id=container_id,facts_type=self._facts_type)
            
            return self._current_model

        except Exception as e:
            error_msg = f"An error occurred during the detached prompt creation process: {str(e)}"
            try:
                error_response = responseVal.json()
                for error in error_response.get('errors', []):
                    error_msg += f"\nErrors found in : {error.get('instancePath', '')}"
            except json.JSONDecodeError:
                error_msg += f" Unexpected Response Content: {responseVal.text}"
            _logger.error(error_msg)
            raise


    def create_prompt(self,input_mode:str,name:str,task_id:str,prompt_details:'PromptTemplate',model_id:str=None,model_type:str=None,deployment_id:str=None,description:str=None,container_type:str=None,container_id:str=None)->AIGovAssetUtilities:
        """
        Create a Regular Prompt Template Asset.


        :param str input_mode: The mode in which the prompt is being created. Currently supports "structured" and "freeflow" modes.
        :param str name: The name of prompt being created.
        :param str model_id: The identifier of the model associated with the prompt
        :param str task_id: Describes possible Task for the prompt template creation
        :param PromptTemplate prompt_details: Holds information about  model version details, prompt variables, instructions, input/output prefixes, and example data
        :param str description: (Optional) description of the extrnal prompt to be created
        :param str container_id: (Optional) used to save the detached prompt 

        Return Type:
         AIGovAssetUtilities
        
            
        Example-1 (**Creating a Structured prompt template assest**),::
                
                prompt_template = PromptTemplate(model_version={"number": "2.0.0-rc.7", "tag": "tag", "description": "Description of the model version"},
                                             input="Input text to be given",
                                             prompt_variables= {"text": "value"}
                                             prompt_instruction="Your prompt instruction",
                                             input_prefix="Your input prefix,
                                             output_prefix="Your output prefix",
                                             examples={"What is the capidddtal of France{text}?": "The capital of France is Paris{text}.",
                                                        "Who wrote '1984{text}'?": "George Orwell wrote '1984'{text}."},
                                             
                                            model_parameters={"decoding_method":"greedy"
                                                              "max_new_tokens":2034,
                                                              "min_new_tokens":0,
                                                              "random_seed":0,
                                                              "top_k":0,
                                                              "top_p":0
                                                              }

                structured_prompt = facts.client.asests.create_prompt(input_mode="structured",
                                                                      name=" structured prompt sample",
                                                                      task_id="summarization",
                                                                      model_id="ibm/granite-13b-chat-v2", 
                                                                      description="My First structured prompt",
                                                                      prompt_details=prompt_template,
                                                                      )


        Example-2 (**Creating a Freeflow prompt template assest**),::
                
                prompt_template = PromptTemplate(
                                             input="Input text to be given",
                                             prompt_variables= {"text": "value"}

                                            model_parameters={"decoding_method":"greedy"
                                                              "max_new_tokens":2034,
                                                              "min_new_tokens":0,
                                                              "random_seed":0,
                                                              "top_k":0,
                                                              "top_p":0
                                                              }
                                            )

                freeflow_prompt = facts.client.asests.create_prompt(input_mode="freeflow",
                                                                    name="Freeflow prompt sample",
                                                                    task_id="summarization",
                                                                    model_id="ibm/granite-13b-chat-v2", 
                                                                    description="My First Freeflow prompt",
                                                                    prompt_details=prompt_template,
                                                                    )

        """
        container_id = self._container_id if container_id is None else container_id
        container_type = self._container_type if container_type is None else container_type

        validate_enum(task_id,"task_id",Task,False)
        validate_enum(input_mode, "input_mode", InputMode,False)
        validate_enum(model_type,"model_type", ModelType,False)
        _logger.info("------------------------------ {} Prompt Creation Started ------------------------------".format(input_mode.capitalize()))

        if model_id and model_type and deployment_id:
                raise ValueError("You must either provide a model_id, or If you are using BYOM (Bring Your Own Model) or IBM tuned models, you must provide both model_type and deployment_id.")

        if model_id:
            pass

        elif model_type and deployment_id:
            asset_id, base_model_id, deployed_asset_type = self._get_deployment_asset(deployment_id, container_type, container_id)

            if deployed_asset_type == "prompt_tune" and model_type == ModelType.TUNED_MODEL:
                    pass
            elif deployed_asset_type == "custom_foundation_model" and model_type == ModelType.BYOM:
                    base_model_id = "custom-model"
                    pass
            else:
                raise ValueError(
                    f"Invalid combination: Deployed asset type is '{deployed_asset_type}' and model type is '{model_type}'. "
                    "For IBM tuned models, model_type must be tuned_model. For BYOM, model_type must be byom."
                )
                    
            tuned_byom_model_name, resource_key = self._get_resource_info(asset_id, container_type, container_id)
            _logger.info(f"Successfully found {model_type} model: {tuned_byom_model_name} for deployment ID: {deployment_id}.")

            model_id = self._create_mrm_id(base_model_id, resource_key, deployment_id, container_type, container_id)
            # _logger.info(f"A new model_id is been generated for  {tuned_byom_model_name} ")
        
        elif not model_id and (not model_type or not deployment_id):
            raise ValueError("You must either provide a model_id, or If you are using BYOM (Bring Your Own Model) or IBM tuned models, you must provide both model_type and deployment_id.")
                
            
        # Prepare base data 
        examples = [[inp, outp] for inp, outp in prompt_details.structured_examples.items()] if prompt_details.structured_examples else None
        prompt_data = {
                    "instruction": prompt_details.prompt_instruction or None,
                    "input_prefix": prompt_details.input_prefix or None,
                    "output_prefix": prompt_details.output_prefix or None,
                    "examples":examples
                    }
        new_data = {k: v for k, v in  prompt_data.items() if v is not None}
        if not new_data:
             new_data ={}

        body = {
                "task_ids":[task_id],
                "input_mode":input_mode,
                "name": name,
                "description": description,
                "prompt": { 
                    "model_id":model_id ,
                    "data":new_data
                }
            }
        
        if prompt_details.model_version:
            body["model_version"]=prompt_details.model_version 
                
        if prompt_details.prompt_variables:
            body["prompt_variables"] = {key: {"default_value": value} for key, value in prompt_details.prompt_variables.items()}
                
                # if prompt_details.chat_items is not None:
                #      body["prompt"]["chat_items"]=prompt_details.chat_items

        if prompt_details.input:
            body["prompt"]["input"]=[[prompt_details.input, ""]]

    
        # model_parameters_data = {
        #                     "decoding_method": prompt_details.decoding_method,
        #                     "max_new_tokens": prompt_details.max_new_tokens,
        #                     "min_new_tokens":prompt_details.min_new_tokens,
        #                     "random_seed": prompt_details.random_seed,
        #                     "stop_sequences": prompt_details.stop_sequences,
        #                     "temperature": prompt_details.temperature,
        #                     "top_k": prompt_details.top_k,
        #                     "top_p": prompt_details.top_p,
        #                     "repetition_penalty": prompt_details.repetition_penalty
        #                 }
                
        # model_parameters_data = {k: v for k, v in model_parameters_data.items() if v is not None}
        if prompt_details.model_parameters:
            body["prompt"]["model_parameters"] =prompt_details.model_parameters

        try:
            url = self._get_prompts_url(None,container_type,container_id,create_prompt=True)
            responseVal = requests.post(url, headers=self._get_headers(), data=json.dumps(body), verify=False)
            responseVal.raise_for_status()
            # Process the successful response
            json_data = responseVal.json()
            _logger.info("The {} prompt with ID {} was created successfully in container_id {}.".format(input_mode, json_data.get('id'), container_id))
            self._asset_id=json_data.get("id")
            self._current_model=AIGovAssetUtilities(self,json_data=json_data,model_id=self._asset_id,container_type=container_type,container_id=container_id,facts_type=self._facts_type)
            
            return self._current_model
        
        except Exception as e:
            error_msg = "An error occurred during the {} prompt creation process: {}".format(input_mode, str(e))
            try:
                error_response = responseVal.json()
                for error in error_response.get('errors', []):
                    error_msg += f"\nErrors found in : {error.get('instancePath', '')}"
            except json.JSONDecodeError:
                error_msg += f" Unexpected Response Content: {responseVal.text}"
            _logger.error(error_msg)
            raise

   
    def get_prompt(self, asset_id: str, container_type: str=None , container_id: str=None ) -> AIGovAssetUtilities:
        """
            Retrieve a prompt asset from the AI government asset utilities.

            This method allows retrieval of a prompt asset from the AI government asset utilities, either by providing the ID of the
            prompt, or by specifying the container type and container ID where the prompt is stored.

            Parameters:
                - prompt_id (str): The ID of the prompt asset to retrieve.
                - container_type (str optional): The type of container where the prompt is stored.
                - container_id (str optional): The ID of the container where the prompt is stored.

            Returns:
                AIGovAssetUtilities: An instance of AIGovAssetUtilities for managing the retrieved prompt asset.

            Note:
                - To retrieve a prompt asset, either the 'prompt_id' or both 'container_type' and 'container_id' must be provided.
                - If 'prompt_id' is provided, the method will directly fetch the prompt with that ID.
                - If 'container_type' and 'container_id' are provided, the method will search for the prompt within the specified container.
            
            Example usage,::

                #Retrieve a prompt asset using prompt ID
                retrieved_prompt= facts_client.asests.get_prompt(asset_id="********")
                retrieved_prompt= facts_client.asests.get_prompt(asset_id="********")
                # Retrieve a prompt asset using container type and container ID
                retrieved_prompt= facts_client.asests.get_prompt(asset_id="********",container_type="project", container_id"*****")
                retrieved_prompt= facts_client.asests.get_prompt(asset_id="********",container_type="project", container_id"*****")
         """
        # condition self._cp4d_version < "4.8.3" added by Lakshmi as part of 4.8.3 changes

        if not asset_id or asset_id == "":
            raise ClientError(
                "Prompt id is required and can not be empty value")
        
        container_id=self._container_id if container_id is None else container_id
        container_type=self._container_type if container_type is None else container_type

        validate_enum(container_type, "container_type", ContainerType, False)
        if not self.DISABLE_LOGGING:
            _logger.info("------------------------------ Prompt Retrieval Process Started ------------------------------")
            _logger.info("Fetching the requested prompt details...")
        else:
            _logger.info("Fetching the requested prompt details...")
            self.DISABLE_LOGGING=False
        return self._get_prompt_assest(asset_id, container_type, container_id)
    
    
    def _get_prompt_assest(self,prompt_id:str=None,container_type: str = None, container_id: str = None):

         self._facts_type = FactsType.MODEL_FACTS_USER
         replace_name="prompt"
         prompt_id=self._asset_id if prompt_id is None else prompt_id

         if container_type and container_id and prompt_id:
            url = self._get_prompts_url(
                prompt_id, container_type, container_id)
            response = requests.get(url, headers=self._get_headers())

        
            if response.status_code == 404:
                raise ClientError("Invalid asset id or container id. ERROR {}. {}".format(
                    response.status_code, response.text))
            elif response.status_code == 200:
                    json_data = response.json()
                    self._asset_id=json_data.get("id")
                    self._current_model=AIGovAssetUtilities(self,json_data=json_data,model_id=self._asset_id,container_type=container_type,container_id=container_id,facts_type=self._facts_type)
                    _logger.info("Current {} information: {}".format(
                    replace_name, self._current_model.to_dict()))
                    _logger.info("Prompt Retrieval Successful")
            else:
             _logger.error("Prompt Retrieval Failed")
             raise ClientError("Asset information not found for {} id {}. ERROR {}. {}".format(
                    replace_name, self._asset_id, response.status_code, response.text))
                    
         else:
            raise ClientError("Could not get current {} {}".format(
                 replace_name, self._current_model.to_dict()))

         return self._current_model


    # Workspaces Search / look up

    def _get_workspace_search_url(self):
       #/v1/aigov/factsheet/workspace/search
       if self._is_cp4d and self._cp4d_version >= "5.0.1":
           url = self._cpd_configs["url"] + \
                 '/v1/aigov/factsheet/workspaces/search'

       else:
           if get_env() =='dev':
               url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                     '/v1/aigov/factsheet/workspaces/search'
           elif get_env() == 'test' :   
               url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                     '/v1/aigov/factsheet/workspaces/search'
           else:
               url = prod_config["DEFAULT_SERVICE_URL"] + \
                     '/v1/aigov/factsheet/workspaces/search'

       return url


    def get_workspace_association_info(self: object, workspace_info:List[dict[str,str]]) -> None:
        """
        This method can be used to get and display usecase and phase details for a single workspace or a list of workspaces. The workspace can be either project or space.

        :param workspace_info is a dictionary with worspace_details: project id or space id and workspace_type: type of workspace , values can be either "project" or "space"
        eg :  workspace_info = [
                            {"id": project_id1, "type": "project"},
                            {"id": project_id2, "type": "project"},
                            {"id": space_id, "type": "space"},
                        ]
        :return: None
        """
        if self._is_cp4d and self._cp4d_version < "5.0.1":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D 5.0.1 and higher. Current version of CP4D is " + self._cp4d_version)
        url = self._get_workspace_search_url()

        try:

            body = {"workspaces": workspace_info}
            response = requests.post(url, data=json.dumps(body, indent=2), headers=self._get_headers())
            if response.status_code == 200:
                data = response.json()
                associated_workspaces = data.get('associated_workspaces', [])

                if associated_workspaces:
                    for workspace in associated_workspaces:
                        print("\n\t\t====Workspace Details:====")
                        print(f"* workspace id: {workspace.get('workspace_id', '')}")
                        print(f"* workspace name: {workspace.get('workspace_name', '')}")
                        print(f"* workspace type: {workspace.get('workspace_type', '')}")
                        print(f"* phase name: {workspace.get('phase_name', '')}")
                        print(f"* is valid: {workspace.get('is_valid', False)}")

                        print("\n\t\t====Associated Use Cases:====")
                        associated_usecases = workspace.get('associated_usecases', [])
                        if associated_usecases:
                            for usecase in associated_usecases:
                                print(f"  * ai usecase id : {usecase.get('ai_usecase_id', '')}")
                                print(f"  * ai usecase name: {usecase.get('ai_usecase_name', '')}")
                                print(f"  * inventory id: {usecase.get('inventory_id', '')}")
                                print(f"  * status: {usecase.get('status', '')}")
                                print(f"  * risk level: {usecase.get('risk_level', '')}")
                        else:
                            print("  No record found")

                        print("\n\t\t====Tracked AI Assets:====")
                        tracked_assets = workspace.get('tracked_assets', [])
                        if tracked_assets:
                            for asset in tracked_assets:
                                print(f"  * aI asset id: {asset.get('ai_asset_id', '')}")
                                print(f"  * aI asset name: {asset.get('ai_asset_name', '')}")
                                print(f"  * aI asset type: {asset.get('ai_asset_type', '')}")
                        else:
                            print("  No record found")
                else:
                    print("No associated workspaces found")

                    print("\n" + "-" * 50 + "\n")
                return data
            else:
                raise ClientError(
                    f"Failed to associate workspace(s),Error encountered : {response.status_code}=>{response.text} ")
        #
        except Exception as e:
            raise ClientError(f"Failed to retrieve usecase and phase information for the given workspace(s). Exception encountered : {e}")

    def _get_deployment_asset(self, deployment_id: str, container_type: str, container_id: str) -> str:
        # Determine the base URL based on environment and CP4D flag
        if self._is_cp4d:
            base_url = self._cpd_configs["url"]
        else:
            env = get_env()
            if env == 'dev':
                base_url = dev_config["DEFAULT_DEV_WML_SERVICE_URL"]
            elif env =='test' :   
                base_url = test_config["DEFAULT_TEST_WML_SERVICE_URL"]
            else:
                base_url = prod_config["DEFAULT_WML_SERVICE_URL"]

        # Construct the deployment URL
        url = f"{base_url}/ml/v4/deployments/{deployment_id}?{container_type}_id={container_id}&version=2024-05-01"

        response = requests.get(url,headers=self._get_headers())
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch deployment details. Status Code: {response.status_code}")

        deployment_data = response.json()

        asset_id = deployment_data.get("entity", {}).get("asset", {}).get("id")
        base_model_id = deployment_data.get("entity", {}).get("base_model_id")
        deployed_asset_type = deployment_data.get("entity", {}).get("deployed_asset_type")

        return asset_id, base_model_id, deployed_asset_type

    def _get_resource_info(self, asset_id: str, container_type: str, container_id: str) -> tuple:
        if self._is_cp4d:
            base_url = self._cpd_configs["url"]
        else:
            env = get_env()
            if env == 'dev':
                base_url = dev_config["DEFAULT_DEV_SERVICE_URL"]
            elif env ==   'test' : 
                base_url = test_config["DEFAULT_TEST_SERVICE_URL"]
            else:
                base_url = prod_config["DEFAULT_SERVICE_URL"]

        # Construct the resource URL
        url = f"{base_url}/v2/assets/{asset_id}?{container_type}_id={container_id}"

        response = requests.get(url,headers=self._get_headers())
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch resource details. Status Code: {response.status_code}")

        resource_details = response.json()
        entity = resource_details.get("entity", {})
        metadata = resource_details.get("metadata", {})

        # base_model_id = entity.get("wml_model", {}).get("training", {}).get("base_model", {}).get("model_id")
        tuned_model_name = metadata.get("name")
        resource_key = metadata.get("resource_key")

        if not tuned_model_name or not resource_key:
            raise ValueError("Base model ID, Tuned model name, or Resource key not found in resource details.")

        return tuned_model_name, resource_key

    def _create_mrm_id(self, base_model_id: str, resource_key: str, deployment_id: str, container_type: str, container_id: str) -> str:
        mrn_prefix = "mrn:v1-beta:"
        deployment_type = "custom-model" if base_model_id == "custom-model" else "prompt-tune"


        stage = "" if self._is_cp4d else (get_env() if get_env() in [ 'dev', 'test'] else "")
        ctype = "software" if self._is_cp4d else "saas"
        cname = ""
        location = ""

        scope = f"{container_type[0]}/{container_id}"
        resource = deployment_id

        return f"{mrn_prefix}{stage}:{ctype}:{cname}:{location}:{scope}:{deployment_type}:{resource}:{base_model_id}:{resource_key}"
    
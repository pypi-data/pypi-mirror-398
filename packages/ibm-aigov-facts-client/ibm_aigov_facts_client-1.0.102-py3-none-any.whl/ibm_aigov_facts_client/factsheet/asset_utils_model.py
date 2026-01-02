import logging
import os
import io
import json
import collections
import itertools
import uuid
import ibm_aigov_facts_client._wrappers.requests as requests
import hashlib
import base64
import urllib.parse
import re
import collections.abc

from packaging import version as pkg_version
from typing import Optional
from datetime import datetime, date

from typing import BinaryIO, Dict, List, TextIO, Union, Any
from ibm_aigov_facts_client.factsheet import assets,utils
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal, ContainerType, FactsType, ModelEntryContainerType, AllowedDefinitionType, FormatType, RenderingHints, Phases
from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type, STR_TYPE
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_experiments import NotebookExperimentUtilities
from ibm_cloud_sdk_core.utils import convert_model
from ibm_aigov_facts_client.utils.metrics_utils import convert_metric_value_to_float_if_possible
from ibm_aigov_facts_client.utils.cell_facts import CellFactsMagic

from ibm_aigov_facts_client.factsheet.approaches import ApproachUtilities
from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.constants import get_cloud_url

from ibm_aigov_facts_client.factsheet.external_deployments import Deployment
from ibm_aigov_facts_client.factsheet.html_parser import FactHTMLParser
from ibm_aigov_facts_client.utils.doc_annotations import deprecated

_logger = logging.getLogger(__name__)



class ModelAssetUtilities:

    """
        Model asset utilities. Running `client.assets.model()` makes all methods in ModelAssetUtilities object available to use.

    """

    def __init__(self, assets_client: 'assets.Assets', model_id: str = None, container_type: str = None, container_id: str = None, facts_type: str = None) -> None:

        self._asset_id = model_id
        self._container_type = container_type
        self._container_id = container_id
        self._facts_type = facts_type

        self._assets_client = assets_client
        self._facts_client = self._assets_client._facts_client
        self._is_cp4d = self._assets_client._is_cp4d
        self._external_model = self._assets_client._external_model

        if self._is_cp4d:
            self._cpd_configs = self._assets_client._cpd_configs
            self._cp4d_version = self._assets_client._cp4d_version

        
        self._facts_definitions = self._get_fact_definitions()
        self._facts_definitions_op = self._get_fact_definitions(
            type_name=FactsType.MODEL_FACTS_USER_OP)
        self.utils_client = utils.Utils(self._facts_client)
    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ModelAssetUtilities':
        """Initialize a ModelAssetUtilities object from a json dictionary."""
        args = {}
        if '_asset_id' in _dict:
            args['asset_id'] = _dict.get('_asset_id')

        if '_container_type' in _dict:
            # [convert_model(x) for x in metrics]
            args['container_type'] = _dict.get('_container_type')
        else:
            raise ValueError(
                'Required property \'container_type\' not present in AssetProps JSON')

        if '_container_id' in _dict:
            # [convert_model(x) for x in metrics]
            args['container_id'] = _dict.get('_container_id')
        else:
            raise ValueError(
                'Required property \'container_id\' not present in AssetProps JSON')

        if '_facts_type' in _dict:
            # [convert_model(x) for x in metrics]
            args['facts_type'] = _dict.get('_facts_type')
        else:
            raise ValueError(
                'Required property \'facts_type\' not present in AssetProps JSON')
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, '_asset_id') and self._asset_id is not None:
            _dict['asset_id'] = self._asset_id
        if hasattr(self, '_container_type') and self._container_type is not None:
            _dict['container_type'] = self._container_type
        if hasattr(self, '_container_id') and self._container_id is not None:
            _dict['container_id'] = self._container_id
        if hasattr(self, '_facts_type') and self._facts_type is not None:
            _dict['facts_type'] = self._facts_type

        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ModelAssetUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this ModelAssetUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def get_info(self, verbose=False) -> Dict:
        """Get model object details

            :param verbose: If True, returns additional model details. Defaults to False
            :type verbose: bool, optional
            :rtype: dict

            The way to use me is:

            >>> model.get_info()
            >>> model.get_info(verbose=True)

        """
        _ENV = get_env()
        if get_env() != 'dev' and get_env() != 'test':
            CLOUD_URL = get_cloud_url()
        if verbose:
            url = self._get_assets_url(
                self._asset_id, self._container_type, self._container_id)
            response = requests.get(url, headers=self._get_headers())
            

            if response.status_code == 200:
                cur_metadata = self._to_dict()
                additional_data = {}

                model_name = response.json()["metadata"].get("name")
                asset_type = response.json()["metadata"].get("asset_type")
                desc = response.json()["metadata"].get("description")
                base_url = (CLOUD_DEV_URL if _ENV == "dev" else CLOUD_TEST_URL if _ENV == "test" else (CLOUD_URL if not self._is_cp4d else self._cpd_configs["url"]))
                if self._is_cp4d:
                    if self._container_type == ContainerType.CATALOG:
                        # url = CATALOG_PATH.format(
                        #     self._cpd_configs["url"], self._container_id, self._asset_id)
                        url = CATALOG_PATH.format(
                             base_url, self._container_id, self._asset_id)
                    elif self._container_type == ContainerType.PROJECT:
                        url = PROJECT_PATH.format(
                            base_url, self._asset_id, self._container_id)
                    elif self._container_type == ContainerType.SPACE:
                        url = SPACE_PATH.format(
                            base_url, self._asset_id, self._container_id)
                else:
                    if self._container_type == ContainerType.CATALOG:
                        url = CATALOG_PATH.format(
                            base_url, self._container_id, self._asset_id)
                    elif self._container_type == ContainerType.PROJECT:
                        url = PROJECT_PATH.format(
                            base_url, self._asset_id, self._container_id)
                    elif self._container_type == ContainerType.SPACE:
                        url = SPACE_PATH.format(
                            base_url, self._asset_id, self._container_id)

                additional_data["name"] = model_name
                if desc:
                    additional_data["description"] = desc
                additional_data["asset_type"] = asset_type
                additional_data["url"] = url
                additional_data.update(cur_metadata)
                return additional_data
            else:
                raise ClientError("Failed to get additional asset information. ERROR {}. {}".format(
                    response.status_code, response.text))
        else:
            return self._to_dict()

    def _get_fact_definitions(self, type_name=None) -> Dict:
        """
            Get all facts definitions

            :rtype: dict

        """

        facts_type = type_name or self._facts_type

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                "/v2/asset_types/" + facts_type + "?" + \
                self._container_type + "_id=" + self._container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    "/v2/asset_types/" + facts_type + "?" + \
                    self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    "/v2/asset_types/" + facts_type + "?" + \
                    self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    "/v2/asset_types/" + facts_type + "?" + \
                    self._container_type + "_id=" + self._container_id

        response = requests.get(url, headers=self._get_headers())
        if not response.ok:
            return None
        else:
            return response.json()

    def _get_tracking_model_usecase_info(self):
        """
            Get model use case info associated to the model.

        """

        url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())

        # get model use case

        if response.status_code == 200:
            all_resources = response.json().get("entity")
            get_facts = all_resources.get(FactsType.MODEL_FACTS_SYSTEM)
            modelentry_information = get_facts.get(MODEL_USECASE_TAG)
            if not modelentry_information:
                raise ClientError(
                    "Model use case info is not available for asset id {}".format(self._asset_id))
            else:
                lmid = modelentry_information.get('lmid')
                if not lmid:
                    raise ClientError(
                        "Model {} is not tracked by a model use case".format(self._asset_id))
                lmdidParts = lmid.split(':')
                if len(lmdidParts) < 2:
                    return None
                container_id = lmdidParts[0]
                model_usecase_id = lmdidParts[1]

            self._current_model_usecase = ModelUsecaseUtilities(
                self, model_usecase_id=model_usecase_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=container_id, facts_type=FactsType.MODEL_USECASE_USER)

            return self._current_model_usecase.to_dict()

        else:
            raise ClientError("Asset model use case information is not available for model id {}. ERROR. {}. {}".format(
                self._asset_id, response.status_code, response.text))

    def get_tracking_model_usecase(self) -> ModelUsecaseUtilities:
        """
            Get model use case associated to the model.

            :rtype: ModelUsecaseUtilities

            A way you might use me is:

            >>> model.get_tracking_model_usecase()

        """

        url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())

        # get model use case
        modelentry_information = None
        if response.status_code == 200:
            all_resources = response.json().get("entity")
            get_facts = all_resources.get(FactsType.MODEL_FACTS_SYSTEM)
            #added for resolving None type error when there is no tracking which was impacting delete_prompt_asset and get_version for prompts
            if MODEL_USECASE_TAG in get_facts:
                modelentry_information = get_facts.get(MODEL_USECASE_TAG)
            if not modelentry_information:
                raise ClientError(
                    "Model {} is not tracked by a model use case".format(self._asset_id))
            else:
                lmid = modelentry_information.get('lmid')
                if not lmid:
                    raise ClientError(
                        "Model {} is not tracked by a model use case. lmid is missing".format(self._asset_id))
                lmdidParts = lmid.split(':')
                if len(lmdidParts) < 2:
                    return None
                container_id = lmdidParts[0]
                model_usecase_id = lmdidParts[1]

            self._current_model_usecase = ModelUsecaseUtilities(
                self, model_usecase_id=model_usecase_id, container_type=MODEL_USECASE_CONTAINER_TYPE_TAG, container_id=container_id, facts_type=FactsType.MODEL_USECASE_USER)

            return self._current_model_usecase

        else:
            raise ClientError("Asset model use case information is not available for model id {}. ERROR. {}. {}".format(
                self._asset_id, response.status_code, response.text))

    @deprecated(alternative="model.track()")
    def add_tracking_model_usecase(self, model_usecase_name: str = None, model_usecase_desc: str = None, model_usecase_id: str = None, model_usecase_catalog_id: str = None, grc_model_id: str = None):
        """
            Link Model to model use case. Model asset should be stored in either Project or Space and corrsponding ID should be provided when registering to model use case. 


            :param str model_usecase_name: (Optional) New model use case name. Used only when creating new model use case. 
            :param str model_usecase_desc: (Optional) New model use case description. Used only when creating new model use case.
            :param str model_usecase_id: (Optional) Existing model use case to link with.
            :param str model_usecase_catalog_id: (Optional) Catalog ID where model use case exist.
            :param str grc_model_id: (Optional) Openpages model id. Only applicable for CPD environments.  


            For new model use case:

            >>> model.add_tracking_model_usecase(model_usecase_name=<name>,model_usecase_desc=<description>)

            For linking to existing model use case:

            >>> model.add_tracking_model_usecase(model_usecase_id=<model use case id to link with>,model_usecase_catalog_id=<model use case catalog id>)


        """

        model_asset_id = self._asset_id
        container_type = self._container_type
        container_id = self._container_id

        params = {}
        payload = {}

        params[container_type + '_id'] = container_id

        if grc_model_id and not self._is_cp4d:
            raise WrongParams(
                "grc_model_id is only applicable for Openpages enabled CPD platform")

        payload['model_entry_catalog_id'] = model_usecase_catalog_id or self._assets_client._get_pac_catalog_id()

        if model_usecase_name or (model_usecase_name and model_usecase_desc):
            if model_usecase_id:
                raise WrongParams(
                    "Please provide either NAME and DESCRIPTION or MODEL_USECASE_ID")
            payload['model_entry_name'] = model_usecase_name
            if model_usecase_desc:
                payload['model_entry_description'] = model_usecase_desc

        elif model_usecase_id:
            if model_usecase_name and model_usecase_desc:
                raise WrongParams(
                    "Please provide either NAME and DESCRIPTION or MODEL_USECASE_ID")
            payload['model_entry_asset_id'] = model_usecase_id

        else:
            raise WrongParams(
                "Please provide either NAME and DESCRIPTION or MODEL_USECASE_ID")

        wkc_register_url = WKC_MODEL_REGISTER.format(model_asset_id)

        if self._is_cp4d:
            if grc_model_id:
                payload['grc_model_id'] = grc_model_id
            url = self._cpd_configs["url"] + \
                wkc_register_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    wkc_register_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    wkc_register_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    wkc_register_url

        if model_usecase_id:
            _logger.info("Initiate linking model to existing model use case {}".format(
                model_usecase_id))
        else:
            _logger.info("Initiate linking model to new model use case......")

        response = requests.post(url,
                                 headers=self._get_headers(),
                                 params=params,
                                 data=json.dumps(payload))

        if response.status_code == 200:
            _logger.info("Successfully finished linking Model {} to model use case".format(
                model_asset_id))
        else:
            error_msg = u'Model registration failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)

        return response.json()

    @deprecated(alternative="model.untrack()")
    def remove_tracking_model_usecase(self):
        """
            Unregister from model use case

            Example for IBM Cloud or CPD:

            >>> model.remove_tracking_model_usecase()

        """

        wkc_unregister_url = WKC_MODEL_REGISTER.format(self._asset_id)

        params = {}
        params[self._container_type + '_id'] = self._container_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                wkc_unregister_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    wkc_unregister_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    wkc_unregister_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    wkc_unregister_url

        response = requests.delete(url,
                                   headers=self._get_headers(),
                                   params=params,
                                   )

        if response.status_code == 204:
            _logger.info("Successfully finished unregistering WKC Model {} from model use case.".format(
                self._asset_id))
        else:
            error_msg = u'WKC model use case unregistering failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)
    def _is_model_tracked(self) -> bool:

        tracked = False
        url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())

        # get model use case

        if response.status_code == 200:
            all_resources = response.json().get("entity")
           
            get_facts = all_resources.get(FactsType.MODEL_FACTS_SYSTEM)
            if not get_facts:
                _logger.debug("Model facts system info is not available for asset id {}".format(self._asset_id))
                return tracked, None
            modelentry_information = get_facts.get(MODEL_USECASE_TAG)
            if not modelentry_information:
                _logger.debug(
                    "Model use case info is not available for asset id {}".format(self._asset_id))
                return tracked, None
            lmid = modelentry_information.get('lmid')
            if not lmid:
                _logger.debug("The model is not tracked with an use case")
                return tracked, None
            lmdidParts = lmid.split(':')
            if len(lmdidParts) < 2:
                return tracked,None
            tracked=True
            self._current_model_usecase={
            "catalog_id" : lmdidParts[0],
            "model_usecase_id" : lmdidParts[1],
            "container_type" :"catalog"
            }
            return tracked, self._current_model_usecase

    def _is_new_usecase(self):
        """
           Checks if the model usecase is new or old
           Returns True if the model is tracked and the use case is new
           Returns False if the model is tracked and the use case is old
           Returns False if the model is not tracked

           Example
           >>> model._is_new_case()

        """

        tracked_response, model_use_case_info = self._is_model_tracked()
        if tracked_response and model_use_case_info:
            model_usecase_id = model_use_case_info.get('model_usecase_id')
            catalog_id = model_use_case_info.get('catalog_id')
            container_type = model_use_case_info.get('container_type')
            url = self._get_assets_url(
                model_usecase_id, container_type, catalog_id)
            response = requests.get(url, headers=self._get_headers())
            use_case_response = response.json()
            if response.status_code == 200:
                if use_case_response.get('entity', {}).get('model_entry', {}).get('data_model') == 'mastercopy1.0':
                    return True
                return False
            _logger.debug(f"Error is receiving response for the model case id {model_usecase_id}: {response.text}")
        return False


    def set_custom_fact(self, fact_id: str, value: Any) -> None:
        """
            Set custom fact by given id.

            :param str fact_id: Custom fact id.
            :param any value: Value of custom fact. It can be string, integer, date. if custom fact definition attribute `is_array` is set to `True`, value can be a string or list of strings.

            A way you might use me is:

            >>> model.set_custom_fact(fact_id="custom_int",value=50)
            >>> model.set_custom_fact(fact_id="custom_string",value="test")
            >>> model.set_custom_fact(fact_id="custom_string",value=["test","test2"]) # allowed if attribute property `is_array` is true.

        """
        # When it is not an external model, we check for workspace associations.
        model_container_id = self._container_id
        model_container_type = self._container_type
        
        
        if (not self._external_model) and (self._is_cp4d and self._cp4d_version >= "5.0.3"):
            container_search_dict = [{"id": model_container_id, "type": model_container_type}]
            try:
                # Fetching workspace association info
                model_container_info = self._facts_client.assets.get_workspace_association_info(workspace_info=container_search_dict)
                associated_workspace = model_container_info.get('associated_workspaces', [])
                associated_usecase = associated_workspace[0].get('associated_usecases', [])

                if not associated_usecase:
                    raise ClientError(
                        "Workspace containing the model is not associated to any use case. "
                        "Please ensure the required association before adding custom facts."
                    )
            except Exception as e:
                raise ClientError(f"Failed to fetch workspace association status: {e}")
        
        attr_is_array = None
        #if not value or value == '':
        #    raise ClientError("Value can not be empty")

        # convert date to ISO format
        if isinstance(value, date):
            value = value.isoformat()

        # Ensure all elements in a list are handled if `value` is a list
        if isinstance(value, list):
            value = [v.isoformat() if isinstance(v, date) else v for v in value]

        val_mfacts, val_mfacts_op = self._get_fact_definition_properties(
            fact_id)
        cur_val = val_mfacts or val_mfacts_op
        is_tracked, _ = self._is_model_tracked()
        use_factsheet_url = (self._is_cp4d and self._cp4d_version >= "5.2.1") and is_tracked

        if val_mfacts_op:
            facts_type = FactsType.MODEL_FACTS_USER_OP
            # Updating the custom facts to master copy
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy(
            #         type_name=facts_type)
            # else:
            url = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_url_by_factstype_container(type_name=facts_type)


        elif val_mfacts:
            facts_type = self._facts_type
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy()
            # else:
            url = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_url_by_factstype_container()

        else:
            raise ClientError(
                "Fact id {} is not defined under custom asset definitions".format(fact_id))

        if cur_val:
            attr_is_array = cur_val.get("is_array")

        value_type_array = (type(value) is not str and isinstance(
            value, collections.abc.Sequence))

        if isinstance(value, list) and any(isinstance(x, dict) for x in value):
            raise ClientError(
                "Value should be a list of Strings but found Dict")

        self._type_check_by_id(fact_id, value)

        path = "/" + fact_id
        op = ADD

        if (attr_is_array and value_type_array) or value_type_array:
            body = [
                {
                    "op": op,
                    "path": path,
                    "value": "[]"
                }
            ]
            response = requests.post(url, data=json.dumps(body), headers=self._get_headers()) \
                if use_factsheet_url else \
                requests.patch(url, data=json.dumps(body), headers=self._get_headers())

            if not response.status_code == 200:
                raise ClientError("Patching array type values failed. ERROR {}. {}".format(
                    response.status_code, response.text))

            op = REPLACE

        body = [
            {
                "op": op,
                "path": path,
                "value": value
            }
        ]

        response = requests.post(url, data=json.dumps(body), headers=self._get_headers()) \
            if use_factsheet_url else \
            requests.patch(url, data=json.dumps(body), headers=self._get_headers())

        if response.status_code == 200:
            _logger.info(
                "Custom fact {} successfully set to new value {}".format(fact_id, value))

        elif response.status_code == 404:
            # to check and exclude modelfacts_user_op

            url = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_assets_attributes_url()


            body = {
                "name": facts_type,
                "entity": {fact_id: value}
            }

            response = requests.post(url, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 201:
                _logger.info(
                    "Custom fact {} successfully set to new value {}".format(fact_id, value))
            else:
                _logger.error("Something went wrong. ERROR {}.{}".format(
                    response.status_code, response.text))
        else:
            raise ClientError("Failed to add custom fact {}. ERROR: {}. {}".format(
                fact_id, response.status_code, response.text))

    def set_custom_facts(self, facts_dict: Dict[str, Any]) -> None:
        """
            Set multiple custom facts.

            :param dict facts_dict: Multiple custom facts. Example: {id: value, id1: value1, ...}

            A way you might use me is:

            >>> model.set_custom_facts({"fact_1": 2, "fact_2": "test", "fact_3":["data1","data2"]})

        """
        
         # When it is not an external model, we check for workspace associations.
        model_container_id = self._container_id
        model_container_type = self._container_type
        is_tracked, _ = self._is_model_tracked()
        use_factsheet_url = (self._is_cp4d and self._cp4d_version >= "5.2.1") and is_tracked
        
        if not self._external_model:
            container_search_dict = [{"id": model_container_id, "type": model_container_type}]
            try:
                if self._is_cp4d and self._cp4d_version >= "5.0.3":
                    # Fetching workspace association info
                    model_container_info = self._facts_client.assets.get_workspace_association_info(workspace_info=container_search_dict)
                    associated_workspace = model_container_info.get('associated_workspaces', [])
                    associated_usecase = associated_workspace[0].get('associated_usecases', [])

                    if not associated_usecase:
                        raise ClientError(
                            "Workspace containing the model is not associated to any use case. "
                            "Please ensure the required association before adding custom facts."
                        )
            except Exception as e:
                raise ClientError(f"Failed to fetch workspace association status: {e}")

        # Convert dates to ISO format
        for key, value in facts_dict.items():
            if isinstance(value, date):
                facts_dict[key] = value.isoformat()
            elif isinstance(value, list):
                facts_dict[key] = [
                    v.isoformat() if isinstance(v, date) else v for v in value
                ]
        body = []
        body_op = []
        op_facts = []
        non_op_facts = []
        url_op = None
        url_non_op = None
        #tracked=self._is_new_usecase()
        for key, val in list(facts_dict.items()):
            is_array = None

            attr_is_array, attr_is_array_op = self._get_fact_definition_properties(
                key)

            if attr_is_array_op:
                facts_type = FactsType.MODEL_FACTS_USER_OP
                # if tracked and not self._external_model:
                #     url_op = self._get_url_by_factstype_container_mastercopy(
                #         type_name=facts_type)
                # else:
                url_op = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_url_by_factstype_container(
                        type_name=facts_type)

            elif attr_is_array:
                facts_type = self._facts_type
                # if tracked and not self._external_model:
                #     url_non_op = self._get_url_by_factstype_container_mastercopy()
                # else:
                url_non_op = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_url_by_factstype_container()

            else:
                _logger.info(
                    "Escaping Fact id {} as it is not defined under custom asset definitions".format(key))

            cur_val = attr_is_array or attr_is_array_op

            if cur_val:
                is_array = cur_val.get("is_array")

                value_type_array = (type(val) is not str and isinstance(
                    val, collections.abc.Sequence))

                self._type_check_by_id(key, val)

                path = "/" + key
                op = ADD

                if (is_array and value_type_array) or value_type_array:

                    tmp_body = {
                        "op": op,
                        "path": path,
                        "value": "[]"
                    }

                    if facts_type == FactsType.MODEL_FACTS_USER_OP:
                        body_op.append(tmp_body)
                    else:
                        body.append(tmp_body)

                    op = REPLACE

                v = {
                    "op": op,  # "replace",
                    "path": path,
                    "value": val
                }

                if facts_type == FactsType.MODEL_FACTS_USER_OP:
                    op_facts.append({key: val})
                    body_op.append(v)
                else:
                    non_op_facts.append({key: val})
                    body.append(v)

        if body_op:
            response_op = requests.post(url_op, data=json.dumps(body), headers=self._get_headers()) \
                if use_factsheet_url else \
                requests.patch(url_op, data=json.dumps(
                body_op), headers=self._get_headers())
            if response_op.status_code == 200:
                _logger.info("Custom Openpages facts {} successfully set to values {}".format(list(set().union(
                    *(d.keys() for d in op_facts))), list(itertools.chain(*[list(row.values()) for row in op_facts]))))
            else:
                raise ClientError(
                    "Failed to set Openpages custom facts. ERROR: {}-{}".format(response.status_code, response.text))

        if body:
            response = requests.post(url_non_op, data=json.dumps(body), headers=self._get_headers()) \
                if use_factsheet_url else \
                requests.patch(url_non_op, data=json.dumps(
                body), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info("Custom facts {} successfully set to values {}".format(list(set().union(
                    *(d.keys() for d in non_op_facts))), list(itertools.chain(*[list(row.values()) for row in non_op_facts]))))

            elif response.status_code == 404:
                # to check and exclude modelfacts_user_op

                url = self._get_url_using_factsheet(type_name="user_facts") if use_factsheet_url else self._get_assets_attributes_url()

                body = {
                    "name": self._facts_type,
                    "entity": facts_dict
                }

                response = requests.post(url, data=json.dumps(
                    body), headers=self._get_headers())
                if response.status_code == 201:
                    _logger.info("Custom facts {} successfully set to values {}".format(list(set().union(
                        *(d.keys() for d in non_op_facts))), list(itertools.chain(*[list(row.values()) for row in non_op_facts]))))
                else:
                    _logger.error("Something went wrong. ERROR {}.{}".format(
                        response.status_code, response.text))

            else:
                raise ClientError(
                    "Failed to add custom facts. ERROR: {}-{}".format(response.status_code, response.text))

    def get_custom_fact_by_id(self, fact_id: str):
        """
            Get custom fact value/s by id

            :param str fact_id: Custom fact id to retrieve.

            A way you might use me is:

            >>> model.get_custom_fact_by_id(fact_id="fact_id")

        """

        val_mfacts, val_mfacts_op = self._get_fact_definition_properties(
            fact_id)

        if val_mfacts_op:
            facts_type = FactsType.MODEL_FACTS_USER_OP
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy(
            #         type_name=facts_type)
            # else:
            url = self._get_url_by_factstype_container(
                    type_name=facts_type)

        else:
            facts_type = self._facts_type
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy()
            # else:
            url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            fact_details = response.json().get(facts_type)
            id_val = fact_details.get(fact_id)
            if not id_val:
                raise ClientError(
                    "Could not find value of fact_id {}".format(fact_id))
            else:
                return id_val

    def get_custom_facts(self) -> Dict:
        """
            Get all defined custom facts for modelfacts_user fact type.

            :rtype: dict

            A way you might use me is:

            >>> model.get_custom_facts()

        """

        # if self._is_new_usecase() and not self._external_model:
        #     url = self._get_url_by_factstype_container_mastercopy()
        # else:
        use_factsheet_url = (self._is_cp4d and self._cp4d_version >= "5.2.1")

        url = self._get_url_using_factsheet(type_name="system_facts") if use_factsheet_url else self._get_url_by_factstype_container()
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            user_facts = response.json().get("additional_details") if use_factsheet_url else (
                response.json().get(self._facts_type))
            return user_facts
        else:
            raise ClientError("Failed to get facts. ERROR. {}. {}".format(
                response.status_code, response.text))

    def get_all_facts(self) -> Dict:
        """
            Get all facts related to asset.

            :rtype: dict

            A way you might use me is:

            >>> model.get_all_facts()

        """

        # if self._is_new_usecase() and not self._external_model:
        #     url = self._get_assets_url_mastercopy()
        # else:
        url = self._get_assets_url(
                self._asset_id, self._container_type, self._container_id)
        print(url)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            raise ClientError("Failed to get facts. ERROR. {}. {}".format(
                response.status_code, response.text))

    def get_facts_by_type(self, facts_type: str = None) -> Dict:
        """
            Get custom facts by asset type. 

            :param str facts_type: (Optional) Custom facts asset type. Default to modelfacts_user type. For Openpages facts, use `modelfacts_user_op`.
            :rtype: dict

            A way you might use me is:

            >>> model.get_facts_by_type(facts_type=<type name>)

        """
        if not facts_type:
            facts_type = self._facts_type

        get_all_first = self.get_all_facts()
        all_resources = get_all_first.get("entity")
        if all_resources and all_resources.get(facts_type) != None:
            return all_resources.get(facts_type)
        else:
            raise ClientError(
                "Could not find custom facts for type {}".format(facts_type))

    def remove_custom_fact(self, fact_id: str) -> None:
        """
            Remove custom fact by id

            :param str fact_id: Custom fact id value/s to remove.

            A way you might use me is:

            >>> model.remove_custom_fact(fact_id=<fact_id>)

        """

        val_mfacts, val_mfacts_op = self._get_fact_definition_properties(
            fact_id)

        if val_mfacts_op:
            facts_type = FactsType.MODEL_FACTS_USER_OP
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy(
            #         type_name=facts_type)
            # else:
            url = self._get_url_by_factstype_container(
                    type_name=facts_type)

        else:
            facts_type = self._facts_type
            # if self._is_new_usecase() and not self._external_model:
            #     url = self._get_url_by_factstype_container_mastercopy()
            # else:
            url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            fact_details = response.json().get(facts_type)
            check_val_exists_for_id = fact_details.get(fact_id)
        if not check_val_exists_for_id:
            raise ClientError(
                "Fact id {} is invalid or have no associated value to remove".format(fact_id))

        body = [
            {
                "op": "remove",  # "replace",
                "path": "/" + fact_id,
            }
        ]

        response = requests.patch(url, data=json.dumps(
            body), headers=self._get_headers())
        if response.status_code == 200:
            _logger.info(
                " Value of Fact id {} removed successfully".format(fact_id))
        else:
            raise ClientError("Could not delete the fact_id {}. ERROR. {}. {}".format(
                fact_id, response.status_code, response.text))

    def remove_custom_facts(self, fact_ids: List[str]) -> None:
        """
            Remove multiple custom facts 

            :param list fact_ids: Custom fact ids to remove.

            A way you might use me is:

            >>> model.remove_custom_facts(fact_ids=["id1","id2"])

        """
        body = []
        body_op = []
        op_facts = []
        non_op_facts = []
        url_op = None
        url_non_op = None
        # tracked=self._is_new_usecase()
        for fact_id in fact_ids:
            val_mfacts, val_mfacts_op = self._get_fact_definition_properties(
                fact_id)

            if val_mfacts_op:
                facts_type = FactsType.MODEL_FACTS_USER_OP
                # if tracked and not self._external_model:
                #     url_op = self._get_url_by_factstype_container_mastercopy(
                #      type_name=facts_type)
                # else:
                url_op = self._get_url_by_factstype_container(
                        type_name=facts_type)
                response = requests.get(url_op, headers=self._get_headers())

            else:
                facts_type = self._facts_type
                # if tracked and not self._external_model:
                #     url_non_op = self._get_url_by_factstype_container_mastercopy()
                # else:
                url_non_op = self._get_url_by_factstype_container()
                response = requests.get(
                    url_non_op, headers=self._get_headers())

            if response.status_code == 200:
                fact_details = response.json().get(facts_type)
            else:
                raise ClientError("Failed to find facts information for fact id {}. ERROR {}. {}".format(
                    fact_id, response.status_code, response.text))

            cur_val = fact_details.get(fact_id)

            if cur_val:
                val = {
                    "op": "remove",  # "replace",
                    "path": "/" + fact_id
                }

                if facts_type == FactsType.MODEL_FACTS_USER_OP:
                    op_facts.append(fact_id)
                    body_op.append(val)
                else:
                    non_op_facts.append(fact_id)
                    body.append(val)

            else:
                if facts_type == FactsType.MODEL_FACTS_USER_OP:
                    _logger.info(
                        "Escaping Openpages fact_id {} as either it is invalid or have no value to remove".format(fact_id))
                else:
                    _logger.info(
                        "Escaping fact_id {} as either it is invalid or have no value to remove".format(fact_id))

        if body_op:
            response_op = requests.patch(url_op, data=json.dumps(
                body_op), headers=self._get_headers())
            if response_op.status_code == 200:
                _logger.info(
                    "Values of Openpages Fact ids {} removed successfully".format(op_facts))
            else:
                raise ClientError("Could not delete the Openpages fact_ids. ERROR. {}. {}".format(
                    response.status_code, response.text))

        if body:
            response = requests.patch(url_non_op, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 200:
                _logger.info(
                    "Values of Fact ids {} removed successfully".format(non_op_facts))
            else:
                raise ClientError("Could not delete the fact_ids. ERROR. {}. {}".format(
                    response.status_code, response.text))

    def get_environment_type(self) -> Dict:
        """
            Get current environement details for related model asset. .

            :rtype: dict

            A way you might use me is:

            >>> model.get_environment_type()

        """

        container_info = {}
        msg = "The space {} {} which is considered as {} environment and asset shows under {} stage"

        container_asset_id = self._asset_id
        asset_container_type = self._container_type
        asset_container_id = self._container_id

        if container_asset_id and asset_container_type and asset_container_id:

            url = self._get_url_sysfacts_container(
                container_asset_id, asset_container_type, asset_container_id)
            response = requests.get(url, headers=self._get_headers())

            if self._external_model:

                space_info_exists = response.json().get(
                    FactsType.MODEL_FACTS_SYSTEM).get(SPACE_DETAILS)
                deployment_details_exists = response.json().get(
                    FactsType.MODEL_FACTS_SYSTEM).get(DEPLOYMENT_DETAILS)

                if space_info_exists:
                    space_type = space_info_exists.get(SPACE_TYPE)

                    if (space_type == AssetContainerSpaceMapExternal.DEVELOP.value or space_type == '') and not deployment_details_exists:
                        container_info["classification"] = AssetContainerSpaceMapExternal.DEVELOP.name
                        container_info["reason"] = "The space type is {} and deployment_details are not available which is considered as {} environment and asset shows under {} stage".format(
                            space_type, DEVELOP, AssetContainerSpaceMapExternal.DEVELOP.name)

                    elif space_type == AssetContainerSpaceMapExternal.TEST.value and deployment_details_exists:
                        container_info["classification"] = AssetContainerSpaceMap.TEST.name
                        container_info["reason"] = "The space type is {} and deployment_details are available which is considered as {} environment and asset shows under {} stage".format(
                            space_type, TEST, AssetContainerSpaceMap.TEST.name)

                    elif space_type == AssetContainerSpaceMapExternal.VALIDATE.value:
                        container_info["classification"] = AssetContainerSpaceMapExternal.VALIDATE.name
                        container_info["reason"] = "The space is marked as {} by Watson Open Scale which is considered as PRE-PRODUCTION environment and asset shows under {} stage".format(
                            space_type, AssetContainerSpaceMapExternal.VALIDATE.name)

                    elif space_type == AssetContainerSpaceMapExternal.OPERATE.value:
                        container_info["classification"] = AssetContainerSpaceMapExternal.OPERATE.name
                        container_info["reason"] = "The space is marked as {} by Watson Open Scale which is considered as PRODUCTION environment and asset shows under {} stage".format(
                            space_type, AssetContainerSpaceMapExternal.OPERATE.name)

                    else:
                        raise ClientError(
                            "Invalid space type {} found".format(space_type))
                else:
                    raise ClientError(
                        "Associated space details not found for asset {}".format(container_asset_id))

            else:

                try:
                    sys_facts = response.json().get(FactsType.MODEL_FACTS_SYSTEM)
                    space_info_exists = sys_facts.get(SPACE_DETAILS)
                except:
                    raise ClientError(
                        "Failed to get space information details")

                if space_info_exists:
                    space_type = space_info_exists.get(SPACE_TYPE)

                    if space_type == AssetContainerSpaceMap.TEST.value:
                        container_info["classification"] = AssetContainerSpaceMap.TEST.name
                        container_info["reason"] = msg.format(
                            "type is", space_type, TEST, AssetContainerSpaceMap.TEST.name)

                    elif space_type == AssetContainerSpaceMap.VALIDATE.value:
                        container_info["classification"] = AssetContainerSpaceMap.VALIDATE.name
                        container_info["reason"] = "The space is marked as {} by Watson Open Scale which is considered as PRE-PRODUCTION environment and asset shows under {} stage".format(
                            AssetContainerSpaceMap.VALIDATE.value, AssetContainerSpaceMap.VALIDATE.name)

                    elif space_type == AssetContainerSpaceMap.OPERATE.value:
                        container_info["classification"] = AssetContainerSpaceMap.OPERATE.name
                        container_info["reason"] = "The space is marked as {} by Watson Open Scale which is considered as PRODUCTION environment and asset shows under {} stage".format(
                            AssetContainerSpaceMap.OPERATE.value, AssetContainerSpaceMap.OPERATE.name)

                    elif space_type == '':
                        container_info["classification"] = AssetContainerSpaceMap.DEVELOP.name
                        container_info["reason"] = msg.format(
                            "type is", space_type, DEVELOP, AssetContainerSpaceMap.DEVELOP.name)

                    else:
                        raise ClientError(
                            "Invalid space type {} found".format(space_type))

                else:
                    container_info["classification"] = AssetContainerSpaceMap.DEVELOP.name
                    container_info["reason"] = "Asset is developed in project so it is considered in {} stage".format(
                        DEVELOP)

            return container_info
        else:
            raise ClientError(
                "Valid asset informations not used (asset_id, container_type and contaoner_id)")

    #26/6/24  : commenting as may not work with associate workspaces functionality
    #update : added 5.0.1 check as commenting may impact existing users
    #update aug02: removed cloud condition, only cpd 5.0.3 condition check, removed condition for external model
    def set_environment_type(self, from_container: str, to_container: str) -> None:
        """
            Set current container for model asset. For available options check :func:`~ibm_aigov_facts_client.utils.enums.ModelEntryContainerType`

            :param str from_container: Container name to move from
            :param str to_container: Container name to move to


            A way you might use me is:

            >>> model.set_environment_type(from_container="test",to_container="validate")

        """

        if self._external_model:

            if self._is_cp4d and self._cp4d_version < "4.7.0":
                self._set_environment_classification_external(
                    from_container, to_container)
            elif (self._is_cp4d and self._cp4d_version >= "4.7.0") or (not self._is_cp4d):
                validate_enum(from_container, "from_container",
                              ModelEntryContainerType, True)
                validate_enum(to_container, "to_container",
                              ModelEntryContainerType, True)

                container_asset_id = self._asset_id
                asset_container_type = self._container_type
                asset_container_id = self._container_id
                body = {
                    "target_environment": to_container.capitalize()
                }

                url = self._get_deployments_url(
                    container_asset_id, asset_container_id, operation="modelput")
                response = requests.put(url, data=json.dumps(
                    body), headers=self._get_headers())
              
                if response.status_code == 200:
                    _logger.info("Asset successfully moved from {} to {} environment".format(
                        from_container, to_container))
                else:
                    raise ClientError("Asset movement failed. ERROR {}. {}".format(
                        response.status_code, response.text))
        else:
            if self._is_cp4d and self._cp4d_version < "5.0.3":
                validate_enum(from_container, "from_container",
                              ModelEntryContainerType, True)
                validate_enum(to_container, "to_container",
                              ModelEntryContainerType, True)

                container_asset_id = self._asset_id
                asset_container_type = self._container_type
                asset_container_id = self._container_id

                if (from_container == to_container) or from_container == '' or to_container == '':
                    raise ClientError(
                        "From and To containers can not be same or empty string")

                try:
                    self._get_tracking_model_usecase_info()
                    cur_container_info = self.get_environment_type()
                except:
                    raise ClientError("Current container details not found")

                if cur_container_info.get("classification") == to_container.upper():
                    raise ClientError(
                        "Asset is already set to {} container".format(to_container))

                if cur_container_info.get("classification") == ModelEntryContainerType.DEVELOP.upper() and asset_container_type == ContainerType.PROJECT:
                    raise ClientError(
                        " Asset in project should be promoted to space before invoking this method")

                if container_asset_id and asset_container_type and asset_container_id:

                    url = self._get_url_sysfacts_container(
                        container_asset_id, asset_container_type, asset_container_id)

                    try:
                        sys_facts_response = requests.get(
                            url, headers=self._get_headers())
                        sys_facts = sys_facts_response.json().get(FactsType.MODEL_FACTS_SYSTEM)
                    except:
                        raise ClientError(
                            "System facts for asset id {} are not found".format(container_asset_id))

                    is_wml_model = (WML_MODEL == sys_facts.get(
                        MODEL_INFO_TAG).get(ASSET_TYPE_TAG))

                    space_details = sys_facts.get(SPACE_DETAILS)

                    if is_wml_model and space_details:

                        current_model_usecase = self._get_tracking_model_usecase_info()

                        if not current_model_usecase:
                            raise ClientError(
                                "Could not find related model use case information. Please make sure, the model is associated to a model use case")

                        current_space_id = space_details.get(SPACE_ID)
                        get_spaces_url = self._get_url_space(current_space_id)
                        space_info = requests.get(
                            get_spaces_url, headers=self._get_headers())
                        get_tags = space_info.json()["entity"].get("tags")

                        if ((from_container == ModelEntryContainerType.DEVELOP and (to_container == ModelEntryContainerType.TEST or to_container == ModelEntryContainerType.VALIDATE or to_container == ModelEntryContainerType.OPERATE))
                                or (to_container == ModelEntryContainerType.DEVELOP and (from_container == ModelEntryContainerType.TEST or from_container == ModelEntryContainerType.VALIDATE or from_container == ModelEntryContainerType.OPERATE))):

                            raise ClientError("Model asset can not be moved from {} to {} container".format(
                                from_container, to_container))

                        elif from_container == ModelEntryContainerType.TEST and to_container == ModelEntryContainerType.VALIDATE:

                            if get_tags:

                                body = [
                                    {
                                        "op": "add",
                                        "path": "/tags/-",
                                        "value": SPACE_PREPROD_TAG
                                    }
                                ]
                            else:
                                body = [
                                    {
                                        "op": "add",
                                        "path": "/tags",
                                        "value": [SPACE_PREPROD_TAG]
                                    }
                                ]

                            response = requests.patch(get_spaces_url, data=json.dumps(
                                body), headers=self._get_headers())

                            if response.status_code == 200:
                                trigger_status = self._trigger_container_move(
                                    container_asset_id, asset_container_type, asset_container_id)
                                if trigger_status == 200:
                                    _logger.info("Asset successfully moved from {} to {} environment".format(
                                        from_container, to_container))
                            else:
                                raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                    response.status_code, response.text))

                        elif from_container == ModelEntryContainerType.TEST and to_container == ModelEntryContainerType.OPERATE:

                            if get_tags:

                                body = [
                                    {
                                        "op": "add",
                                        "path": "/tags/-",
                                        "value": SPACES_PROD_TAG
                                    }
                                ]
                            else:
                                body = [
                                    {
                                        "op": "add",
                                        "path": "/tags",
                                        "value": [SPACES_PROD_TAG]
                                    }
                                ]

                            response = requests.patch(get_spaces_url, data=json.dumps(
                                body), headers=self._get_headers())

                            if response.status_code == 200:
                                trigger_status = self._trigger_container_move(
                                    container_asset_id, asset_container_type, asset_container_id)
                                if trigger_status == 200:
                                    _logger.info("Asset successfully moved from {} to {} environment".format(
                                        from_container, to_container))
                            else:
                                raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                    response.status_code, response.text))

                        elif (from_container == ModelEntryContainerType.VALIDATE or from_container == ModelEntryContainerType.OPERATE) and to_container == ModelEntryContainerType.TEST:

                            openscale_monitored = space_details.get(
                                SPACE_OS_MONITOR_TAG)

                            if openscale_monitored:
                                raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                                    ModelEntryContainerType.VALIDATE, ModelEntryContainerType.TEST))
                            else:
                                if get_tags:
                                    if from_container == ModelEntryContainerType.VALIDATE:
                                        get_tag_idx = get_tags.index(
                                            SPACE_PREPROD_TAG)
                                    else:
                                        get_tag_idx = get_tags.index(
                                            SPACES_PROD_TAG)
                                else:
                                    raise ClientError(
                                        "Could not resolve space tags")

                                body = [{
                                    "op": "remove",
                                    "path": "/tags/" + str(get_tag_idx)
                                }
                                ]

                                response = requests.patch(get_spaces_url, data=json.dumps(
                                    body), headers=self._get_headers())

                                if response.status_code == 200:
                                    trigger_status = self._trigger_container_move(
                                        container_asset_id, asset_container_type, asset_container_id)
                                    if trigger_status == 200:
                                        _logger.info("Asset successfully moved from {} to {} environment".format(
                                            from_container, to_container))
                                else:
                                    raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                        response.status_code, response.text))

                        elif from_container == ModelEntryContainerType.VALIDATE and to_container == ModelEntryContainerType.OPERATE:

                            openscale_monitored = space_details.get(
                                SPACE_OS_MONITOR_TAG)

                            if openscale_monitored:
                                raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                                    ModelEntryContainerType.VALIDATE, ModelEntryContainerType.TEST))
                            else:

                                if get_tags:
                                    get_tag_idx = get_tags.index(SPACE_PREPROD_TAG)
                                else:
                                    raise ClientError(
                                        "Could not resolve space tags")

                                updated_space_info = requests.get(
                                    get_spaces_url, headers=self._get_headers())
                                get_updated_tags = updated_space_info.json()[
                                    "entity"].get("tags")

                                # todo check entity.tags
                                if get_updated_tags:
                                    add_tag_body = {
                                        "op": "add",
                                        "path": "/tags/-",
                                        "value": SPACES_PROD_TAG
                                    }
                                else:
                                    add_tag_body = {
                                        "op": "add",
                                        "path": "/tags",
                                        "value": [SPACES_PROD_TAG]
                                    }

                                body = [{
                                    "op": "remove",
                                    "path": "/tags/" + str(get_tag_idx)
                                }, add_tag_body

                                ]

                                response = requests.patch(get_spaces_url, data=json.dumps(
                                    body), headers=self._get_headers())
                                if response.status_code == 200:
                                    trigger_status = self._trigger_container_move(
                                        container_asset_id, asset_container_type, asset_container_id)
                                    if trigger_status == 200:
                                        _logger.info("Asset successfully moved from {} to {} environment".format(
                                            from_container, to_container))
                                else:
                                    raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                        response.status_code, response.text))

                        elif from_container == ModelEntryContainerType.OPERATE and to_container == ModelEntryContainerType.VALIDATE:
                            openscale_monitored = space_details.get(
                                SPACE_OS_MONITOR_TAG)

                            if openscale_monitored:
                                raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                                    ModelEntryContainerType.VALIDATE, ModelEntryContainerType.TEST))
                            else:
                                if get_tags:
                                    get_tag_idx = get_tags.index(SPACES_PROD_TAG)
                                else:
                                    raise ClientError(
                                        "Could not resolve space tags")

                                updated_space_info = requests.get(
                                    get_spaces_url, headers=self._get_headers())
                                get_updated_tags = updated_space_info.json()[
                                    "entity"].get("tags")

                                # todo check entity.tags
                                if get_updated_tags:
                                    add_tag_body = {
                                        "op": "add",
                                        "path": "/tags/-",
                                        "value": SPACE_PREPROD_TAG
                                    }
                                else:
                                    add_tag_body = {
                                        "op": "add",
                                        "path": "/tags",
                                        "value": [SPACE_PREPROD_TAG]
                                    }

                                body = [{
                                    "op": "remove",
                                    "path": "/tags/" + str(get_tag_idx)
                                }, add_tag_body

                                ]

                                response = requests.patch(get_spaces_url, data=json.dumps(
                                    body), headers=self._get_headers())
                                if response.status_code == 200:
                                    trigger_status = self._trigger_container_move(
                                        container_asset_id, asset_container_type, asset_container_id)
                                    if trigger_status == 200:
                                        _logger.info("Asset successfully moved from {} to {} environment".format(
                                            from_container, to_container))
                                else:
                                    raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                        response.status_code, response.text))
                        else:
                            raise ClientError("Could not set asset from {} to {} container".format(
                                from_container, to_container))
                    else:
                        raise ClientError(
                            "Asset should be in TEST stage (Deploy to space) before using this feature")
                else:
                    raise ClientError(
                        " Valid asset informations not used. please check provided asset_id, container_type and container_id")

            else:
                raise ClientError(f"The method 'set_environment_type' is available only for cp4d versions < 5.0.3, current cpd version is {self._cp4d_version}")

    def _set_environment_classification_external(self, from_container: str, to_container: str) -> None:
        """
            Set current container for external model asset. For available options check :func:`ibm_aigov_facts_client.utils.enums.ModelEntryContainerType`

            :param str from_container: Container name to move from
            :param str to_container: Container name to move to

        """

        validate_enum(from_container, "from_container",
                      ModelEntryContainerType, True)
        validate_enum(to_container, "to_container",
                      ModelEntryContainerType, True)

        if (from_container == to_container) or from_container == '' or to_container == '':
            raise ClientError(
                "From and To containers can not be same or empty string")

        if from_container == ModelEntryContainerType.DEVELOP and to_container == ModelEntryContainerType.TEST:
            raise ClientError(
                "Model asset in develop stage can not be moved to test. You can add deployment_details when saving model asset that will move asset to test environment")

        container_asset_id = self._asset_id
        asset_container_type = self._container_type
        asset_container_id = self._container_id

        url = self._get_url_sysfacts_container(
            container_asset_id, asset_container_type, asset_container_id)

        try:
            sys_facts_response = requests.get(url, headers=self._get_headers())
            sys_facts = sys_facts_response.json().get(FactsType.MODEL_FACTS_SYSTEM)
            is_ext_model = (EXT_MODEL == sys_facts.get(
                MODEL_INFO_TAG).get(ASSET_TYPE_TAG))
        except:
            raise ClientError(
                "System facts for asset id {} are not found".format(container_asset_id))

        if is_ext_model:

            if asset_container_type != ContainerType.CATALOG:
                raise ClientError(
                    "For external model, container type should be catalog only")

            try:
                cur_container_info = self.get_environment_type()
            except:
                raise ClientError("Current container details not found")

            if cur_container_info.get("CONTAINER_CARD") == to_container.upper():
                raise ClientError(
                    "Asset is already set to {} container".format(to_container))

            current_model_usecase = self._get_tracking_model_usecase_info()

            if current_model_usecase:

                try:
                    space_details = sys_facts.get(SPACE_DETAILS)
                except:
                    raise ClientError("Space details information not found")

                deploy_details = sys_facts.get(DEPLOYMENT_DETAILS)

                if ((from_container == ModelEntryContainerType.DEVELOP and (to_container == ModelEntryContainerType.TEST or to_container == ModelEntryContainerType.VALIDATE or to_container == ModelEntryContainerType.OPERATE)) and not deploy_details) or (from_container == ModelEntryContainerType.TEST and to_container == ModelEntryContainerType.DEVELOP):
                    raise ClientError("Model asset can not be moved from {} to {} container".format(
                        from_container, to_container))

                elif from_container == ModelEntryContainerType.TEST and to_container == ModelEntryContainerType.VALIDATE:

                    body = [
                        {"op": "add", "path": "/space_details/space_type",
                            "value": SPACE_PREPROD_TAG_EXTERNAL}
                    ]

                    patch_sys_facts = requests.patch(
                        url, data=json.dumps(body), headers=self._get_headers())

                    if patch_sys_facts.status_code == 200:
                        global_facts_url = self._get_url_sysfacts_container(
                            current_model_usecase["model_usecase_id"], current_model_usecase["container_type"], current_model_usecase["catalog_id"], key=FactsType.MODEL_FACTS_GLOBAL)

                        response = requests.get(
                            global_facts_url, headers=self._get_headers())
                        if response.status_code == 200:
                            get_facts = response.json()
                        else:
                            raise ClientError("Facts global metadata not found. ERROR {}. {}".format(
                                response.status_code, response.text))

                        try:
                            physical_models = get_facts.get(
                                'modelfacts_global').get('physical_models')
                            get_idx = physical_models.index(
                                next(filter(lambda n: n.get('id') == self._asset_id, physical_models)))
                        except:
                            raise ClientError(
                                " No physical model details found in modelfacts_global")

                        body = [
                            {"op": "add", "path": "/physical_models/{}/deployment_space_type".format(
                                get_idx), "value": SPACE_PREPROD_TAG_EXTERNAL}
                        ]

                        patch_physical_model = requests.patch(
                            global_facts_url, data=json.dumps(body), headers=self._get_headers())

                        if patch_physical_model.status_code == 200:

                            _logger.info("Asset successfully moved from {} to {} environment".format(
                                from_container, to_container))
                        else:
                            raise ClientError("Could not update physical model definition. ERROR {}. {}".format(
                                patch_physical_model.status_code, patch_physical_model.text))
                    else:
                        raise ClientError("Asset space update failed. ERROR {}. {}".format(
                            patch_sys_facts.status_code, patch_sys_facts.text))

                elif (from_container == ModelEntryContainerType.TEST or from_container == ModelEntryContainerType.VALIDATE) and to_container == ModelEntryContainerType.OPERATE:

                    openscale_monitored = space_details.get(
                        SPACE_OS_MONITOR_TAG)

                    if openscale_monitored:
                        raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                            from_container, to_container))

                    else:
                        body = [
                            {"op": "add", "path": "/space_details/space_type", "value": SPACES_PROD_TAG_EXTERNAL
                             }
                        ]

                        patch_sys_facts = requests.patch(
                            url, data=json.dumps(body), headers=self._get_headers())

                        if patch_sys_facts.status_code == 200:

                            global_facts_url = self._get_url_sysfacts_container(
                                current_model_usecase["model_usecase_id"], current_model_usecase["container_type"], current_model_usecase["catalog_id"], key=FactsType.MODEL_FACTS_GLOBAL)
                            response = requests.get(
                                global_facts_url, headers=self._get_headers())
                            if response.status_code == 200:
                                get_facts = response.json()
                            else:
                                raise ClientError("Facts global metadata not found. ERROR {}. {}".format(
                                    response.status_code, response.text))

                            try:
                                physical_models = get_facts.get(
                                    'modelfacts_global').get('physical_models')
                                get_idx = physical_models.index(
                                    next(filter(lambda n: n.get('id') == self._asset_id, physical_models)))

                            except:
                                raise ClientError(
                                    " No physical model details found in modelfacts_global")

                            body = [
                                {"op": "add", "path": "/physical_models/{}/deployment_space_type".format(get_idx), "value": SPACES_PROD_TAG_EXTERNAL}]

                            patch_physical_model = requests.patch(
                                global_facts_url, data=json.dumps(body), headers=self._get_headers())

                            if patch_physical_model.status_code == 200:

                                _logger.info("Asset successfully moved from {} to {} environment".format(
                                    from_container, to_container))
                            else:
                                raise ClientError("Could not update physical model definition. ERROR {}. {}".format(
                                    patch_physical_model.status_code, patch_physical_model.text))

                        else:
                            raise ClientError("Asset space update failed. ERROR {}. {}".format(
                                patch_sys_facts.status_code, patch_sys_facts.text))

                elif (from_container == ModelEntryContainerType.VALIDATE or from_container == ModelEntryContainerType.OPERATE) and to_container == ModelEntryContainerType.TEST:

                    openscale_monitored = space_details.get(
                        SPACE_OS_MONITOR_TAG)

                    if openscale_monitored:
                        raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                            from_container, to_container))

                    else:

                        body = [
                            {"op": "add", "path": "/space_details/space_type", "value": SPACE_TEST_TAG
                             }
                        ]

                    patch_sys_facts = requests.patch(
                        url, data=json.dumps(body), headers=self._get_headers())

                    if patch_sys_facts.status_code == 200:
                        global_facts_url = self._get_url_sysfacts_container(
                            current_model_usecase["model_usecase_id"], current_model_usecase["container_type"], current_model_usecase["catalog_id"], key=FactsType.MODEL_FACTS_GLOBAL)

                        response = requests.get(
                            global_facts_url, headers=self._get_headers())
                        if response.status_code == 200:
                            get_facts = response.json()
                        else:
                            raise ClientError("Facts global metadata not found. ERROR {}. {}".format(
                                response.status_code, response.text))

                        try:
                            physical_models = get_facts.get(
                                'modelfacts_global').get('physical_models')
                            get_idx = physical_models.index(
                                next(filter(lambda n: n.get('id') == self._asset_id, physical_models)))
                        except:
                            raise ClientError(
                                " No physical model details found in modelfacts_global")

                        body = [
                            {"op": "add", "path": "/physical_models/{}/deployment_space_type".format(get_idx), "value": SPACE_TEST_TAG}]

                        patch_physical_model = requests.patch(
                            global_facts_url, data=json.dumps(body), headers=self._get_headers())

                        if patch_physical_model.status_code == 200:
                            _logger.info("Asset successfully moved from {} to {} environment".format(
                                from_container, to_container))

                        else:
                            raise ClientError("Could not update physical model definition. ERROR {}. {}".format(
                                patch_physical_model.status_code, patch_physical_model.text))
                elif from_container == ModelEntryContainerType.OPERATE and to_container == ModelEntryContainerType.VALIDATE:

                    openscale_monitored = space_details.get(
                        SPACE_OS_MONITOR_TAG)

                    if openscale_monitored:
                        raise ClientError("The model deployment is already evaluated in Watson OpenScale and can not be moved from {} to {}".format(
                            from_container, to_container))
                    else:
                        body = [
                            {"op": "add", "path": "/space_details/space_type", "value": SPACE_PREPROD_TAG_EXTERNAL
                             }
                        ]
                    patch_sys_facts = requests.patch(
                        url, data=json.dumps(body), headers=self._get_headers())

                    if patch_sys_facts.status_code == 200:
                        global_facts_url = self._get_url_sysfacts_container(
                            current_model_usecase["model_usecase_id"], current_model_usecase["container_type"], current_model_usecase["catalog_id"], key=FactsType.MODEL_FACTS_GLOBAL)

                        response = requests.get(
                            global_facts_url, headers=self._get_headers())
                        if response.status_code == 200:
                            get_facts = response.json()
                        else:
                            raise ClientError("Facts global metadata not found. ERROR {}. {}".format(
                                response.status_code, response.text))

                        try:
                            physical_models = get_facts.get(
                                'modelfacts_global').get('physical_models')
                            get_idx = physical_models.index(
                                next(filter(lambda n: n.get('id') == self._asset_id, physical_models)))
                        except:
                            raise ClientError(
                                " No physical model details found in modelfacts_global")

                        body = [
                            {"op": "add", "path": "/physical_models/{}/deployment_space_type".format(get_idx), "value": SPACE_PREPROD_TAG_EXTERNAL}]

                        patch_physical_model = requests.patch(
                            global_facts_url, data=json.dumps(body), headers=self._get_headers())

                        if patch_physical_model.status_code == 200:
                            _logger.info("Asset successfully moved from {} to {} environment".format(
                                from_container, to_container))

                        else:
                            raise ClientError("Could not update physical model definition. ERROR {}. {}".format(
                                patch_physical_model.status_code, patch_physical_model.text))

                else:
                    raise ClientError("Could not set external model asset from {} to {} container".format(
                        from_container, to_container))
            else:
                raise ClientError(
                    "Could not find related model use case information. Please make sure, the model is associated to a model use case")
        else:
            raise ClientError(
                "For Watson Machine Learning models, use `set_asset_container()` instead")


    def has_attachment(self, fact_id: str = None) -> bool:
        """ Check if attachment/s exist. Supported for CPD version >=4.6.5

        :param fact_id: Id of attachment fact 
        :type fact_id: str, optional

        :rtype: bool

        The way to use me is :

        >>> model.has_attachment()
        >>> model.has_attachment(fact_id=<fact id>)

        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        if self._is_new_usecase() and not self._external_model:
            url = self._get_assets_url_mastercopy()
        else:
            url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        all_attachments = response.json().get(ATTACHMENT_TAG)
        if all_attachments:
            attachments = [i for i in all_attachments if i.get('asset_type') == self._facts_type and (
                fact_id == None or fact_id == i.get("user_data").get("fact_id"))]
            if attachments:
                return True
            else:
                return False

    def list_attachments(self, filter_by_factid: str = None, format: str = FormatType.DICT):
        """
            List available attachments facts. Supported for CPD version >=4.6.5

            :param str filter_by_factid: (Optional) Fact id for the attachment to filter by
            :param str format: Result output format. Default to dict. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.FormatType`

            A way to use me is:


            >>> model.list_attachments(format="str") # use this format if using output for `set_custom_fact()`
            >>> model.list_attachments() # get all attachment facts
            >>> model.list_attachments(filter_by_factid=<"fact_id_1">) # filter by associated fact_id_1

        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if self._is_new_usecase() and not self._external_model:
            url = self._get_assets_url_mastercopy()
        else:
            url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        all_attachments = response.json().get(ATTACHMENT_TAG)
        results = []
        if all_attachments:
            attachments = [i for i in all_attachments if i.get('asset_type') == self._facts_type and (
                filter_by_factid == None or filter_by_factid == i.get("user_data").get("fact_id"))]

            for a in attachments:
                if format == FormatType.STR:
                    get_url = self._get_attachment_download_url(
                        model_asset_id, model_container_type, model_container_id, a.get("id"), a.get("mime"), a.get("name"))
                    if self._is_cp4d and get_url:
                        get_url = self._cpd_configs["url"] + get_url
                    output_fmt = "{} - {} {}".format(
                        a.get("name"), a.get("mime"), get_url)
                    results.append(output_fmt)

                else:
                    attachment_dict = {}
                    attachment_dict["attachment_id"] = a.get("id")
                    attachment_dict["description"] = a.get("description")
                    attachment_dict["name"] = a.get("name")
                    attachment_dict["mime"] = a.get("mime")
                    if a.get("user_data"):
                        if a.get("user_data").get("fact_id"):
                            attachment_dict["fact_id"] = a.get(
                                "user_data").get("fact_id")
                        # phase information
                        if a.get("user_data").get("phase_type"):
                            attachment_dict["phase_name"] = a.get(
                                "user_data").get("phase_type")
                        if a.get("user_data").get("html_rendering_hint"):
                            attachment_dict["html_rendering_hint"] = a.get(
                                "user_data").get("html_rendering_hint")
                            
                    #commenting due to new revised adobe changes

                    # get_url = self._get_attachment_download_url(
                    #     model_asset_id, model_container_type, model_container_id, a.get("id"), a.get("mime"), a.get("name"))
                    # if self._is_cp4d and get_url:
                    #     get_url = self._cpd_configs["url"] + get_url
                    # attachment_dict["url"] = get_url
                    results.append(attachment_dict)
            return results

        else:
            return results
        
    def get_download_URL(self, attachment_id: str) -> str:
        """
        Constructs and returns the download URL for a given attachment.

        Args:
            attachment_id (str): The unique identifier of the attachment.

        Returns:
            str: The URL that can be used to download the specified attachment.

        Raises:
            ValueError: If the attachment_id is invalid or if there is an issue generating the URL.
        
        Example:
            >>> url = model.get_download_URL(attachment_id="12345")
            >>> print(url) 
        """
        try:
            if not attachment_id:
                raise ValueError("Attachment ID cannot be empty.")
            
            attachments = self.list_attachments(format=FormatType.DICT)
            attachment = next((a for a in attachments if a.get('attachment_id') == attachment_id), None)
            
            if attachment:
                model_asset_id = self._asset_id
                model_container_type = self._container_type
                model_container_id = self._container_id
                
                # Edge case scenario
                if not all(key in attachment for key in ['attachment_id', 'mime', 'name']):
                    raise ValueError(f"Incomplete attachment information for ID '{attachment_id}'.")
                

                if self._is_new_usecase() and not self._external_model:
                        download_url = self._get_attachment_download_url_mastercopy(
                        attachment['attachment_id'], attachment['mime'], attachment['name']
                )
                else:
                        download_url = self._get_attachment_download_url(
                        model_asset_id, model_container_type, model_container_id,
                        attachment['attachment_id'], attachment['mime'], attachment['name']
                )
                _ENV = get_env()
                base_url = (CLOUD_DEV_URL if _ENV == "dev" else CLOUD_TEST_URL if _ENV == "test" else (CLOUD_URL if not self._is_cp4d else self._cpd_configs["url"]))
                download_url = base_url + download_url
                _logger.info(f"Successfully fetched download URL for attachment ID '{attachment_id}'")
                return download_url  
            else:
                _logger.error(f"Attachment with ID '{attachment_id}' not found or incomplete information.")
                return None

        except Exception as e:
            _logger.error(f"Failed to retrieve download URL: {str(e)}")
            return None

    def remove_attachment(self, fact_id: str):
        """
            Remove available attachments facts for given id.Supported for CPD version >=4.6.5

            :param str fact_id:  Fact id of the attachment

            A way to use me is:

            >>> model.remove_attachment(fact_id=<fact id of attachment>)


        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        get_attachment = self.list_attachments(filter_by_factid=fact_id)

        if get_attachment:
            get_id = get_attachment[0].get("attachment_id")
            if self._is_new_usecase() and not self._external_model:
                del_url = self._get_url_attachments_mastercopy(get_id, action="del")
            else:
                del_url = self._get_url_attachments(
                model_asset_id, model_container_type, model_container_id, get_id, action="del")
            response = requests.delete(del_url, headers=self._get_headers())
            if response.status_code == 204:
                _logger.info(
                    "Deleted attachment for fact id: {} successfully".format(fact_id))
            else:
                _logger.error("Failed to delete attachment for fact id: {}. ERROR {}. {}".format(
                    fact_id, response.status_code, response.text))
        else:
            raise ClientError(
                "No valid attachment found related to fact id {}".format(fact_id))

    def remove_all_attachments(self):
        """
            Remove all attachments facts for given asset. Supported for CPD version >=4.6.5


            A way to use me is:

            >>> model.remove_all_attachments()


        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if self._is_new_usecase() and not self._external_model:
            url = self._get_assets_url_mastercopy()
        else:
            url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)

        get_assets = requests.get(url, headers=self._get_headers())
        all_attachments = get_assets.json().get(ATTACHMENT_TAG)
        if all_attachments == None:
            raise ClientError("No attachments available to remove")
        filtered_attachment_ids = [i.get('id') for i in all_attachments if i.get(
            ASSET_TYPE_TAG) == self._facts_type]
        if not filtered_attachment_ids:
            raise ClientError("No attachments available to remove")
        else:
            for id in filtered_attachment_ids:
                if self._external_model:
                    del_url = self._get_url_attachments(
                    model_asset_id, model_container_type, model_container_id, id, action="del")
                else:
                    if self._is_new_usecase():
                        del_url = self._get_url_attachments_mastercopy(id, action="del")
                    else:
                        del_url = self._get_url_attachments(
                    model_asset_id, model_container_type, model_container_id, id, action="del")
                response = requests.delete(
                    del_url, headers=self._get_headers())
                if response.status_code == 204:
                    _logger.info(
                        "Deleted attachment id {} successfully".format(id))
                else:
                    _logger.error("Could not delete attachment id {}. ERROR {}. {}".format(
                        id, response.status_code, response.text))
            _logger.info("All attachments deleted successfully")

# ============= custom log training facts===========================================

    def get_experiment(self, experiment_name: str = None) -> NotebookExperimentUtilities:
        """
            Get notebook experiment. Supported for CPD version >=4.6.4


            A way to use me is:

            >>> exp=model.get_experiment() # returns  experiment
            >>> exp=model.get_experiment(experiment_name="test") # In case notebook experiment not available, you can initiate a new one and run to add details.


        """

        get_notebook_exp_url = self._get_url_by_factstype_container(
            type_name=NOTEBOOK_EXP_FACTS)
        cur_data = requests.get(get_notebook_exp_url,
                                headers=self._get_headers())

        if cur_data.status_code == 200:

            cur_notebook_experiment = cur_data.json()[NOTEBOOK_EXP_FACTS]
            exp_id = cur_notebook_experiment[EXP_ID]
            exp_name = cur_notebook_experiment[EXP_NAME]
            get_exp = NotebookExperimentUtilities(
                self, exp_id=exp_id, exp_name=exp_name)

        elif cur_data.status_code == 404:
            if not experiment_name:
                raise ClientError(
                    "Notebook experiment asset attribute is missing. Please provide a experiment name to create new experiment and run")
            # patch a new one
            url = self._get_assets_attributes_url()
            exp_id = uuid.uuid4().hex
            run_id = uuid.uuid4().hex
            created_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            exp_name = experiment_name

            body = {
                "name": NOTEBOOK_EXP_FACTS,
                "entity": {EXP_ID: exp_id, EXP_NAME: exp_name, RUNS_META_NAME: [{RUN_ID: run_id, RUN_DATE: created_date, METRICS_META_NAME: [], PARAMS_META_NAME: [], TAGS_META_NAME: []}]}
            }

            response = requests.post(url, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 201:
                get_exp = NotebookExperimentUtilities(
                    self, exp_id=exp_id, exp_name=exp_name)

            else:
                _logger.error("Something went wrong. ERROR {}.{}".format(
                    response.status_code, response.text))
        else:
            raise ClientError("Failed to get experiment info. ERROR {}. {}".format(
                response.status_code, response.text))

        return get_exp


# utils===============================================================

    def _get_latest_run_and_item(self, data, fact_type, run_id=None):
        if run_id:
            get_latest_runs = [
                item for item in data if item["run_id"] == run_id]
            get_run_idx = next(idx for idx, item in enumerate(data) if item["run_id"] == run_id and item["created_date"] == max(
                get_latest_runs, key=(lambda item: item["created_date"]))["created_date"])
            get_run = data[get_run_idx]
            get_type_info = data[get_run_idx].get(fact_type)

        else:
            get_run_idx = max(range(len(data)),
                              key=lambda index: data[index]['created_date'])
            get_run = data[get_run_idx]
            get_type_info = data[get_run_idx].get(fact_type)

        return get_run, get_type_info

    def _get_latest_run_idx_and_item_idx(self, data, key, fact_type, run_id=None):

        cur_item_idx = None
        get_run_idx = None
        key_exists = False

        if run_id:
            get_latest_runs = [
                item for item in data if item["run_id"] == run_id]
            if not get_latest_runs:
                raise ClientError(
                    "No run information available for run id {}".format(run_id))
            else:
                get_run_idx = next(idx for idx, item in enumerate(data) if item["run_id"] == run_id and item["created_date"] == max(
                    get_latest_runs, key=(lambda item: item["created_date"]))["created_date"])
                get_run_type_metadata = data[get_run_idx].get(fact_type)
                key_exists = any(
                    item for item in get_run_type_metadata if item["key"] == key)
        else:
            get_run_idx = max(range(len(data)),
                              key=lambda index: data[index]['created_date'])
            get_run_type_metadata = data[get_run_idx].get(fact_type)
            key_exists = any(
                item for item in get_run_type_metadata if item["key"] == key)

        is_step_required = any(STEP in item for item in get_run_type_metadata)

        if key_exists and is_step_required:
            raise ClientError(
                "Runs with iterative steps are not allowed to patch (set/remove)")
        elif key_exists and not is_step_required:
            cur_item_idx = next(idx for idx, item in enumerate(
                get_run_type_metadata) if item["key"] == key)
        # else:
        #     raise ClientError("Failed to get info for fact id {}".format(key))
        return get_run_idx, cur_item_idx

    def _get_headers(self):

        
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers

    def _check_if_op_enabled(self):
        url = self._cpd_configs["url"] + "/v1/aigov/model_inventory/grc/config"
        response = requests.get(url,
                                headers=self._get_headers()
                                )
        return response.json().get("grc_integration")

    def _get_assets_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        asset_id = asset_id or self._asset_id
        container_type = container_type or self._container_type
        container_id = container_id or self._container_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        return url

    def _get_assets_url_mastercopy(self):

        master_copy_info = self.utils_client.get_master_copy_info(
            model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id)
        master_copy_id = master_copy_info['master_copy_id']
        inventory_id = master_copy_info['inventory_id']
        container_type = "catalog"

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + master_copy_id + '?' + container_type + '_id=' + inventory_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + '?' + container_type + '_id=' + inventory_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + '?' + container_type + '_id=' + inventory_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + '?' + container_type + '_id=' + inventory_id
        return url

    def _get_fact_definition_properties(self, fact_id):
        props_by_id = None
        props_by_id_op = None

        self._facts_definitions = self._get_fact_definitions()
        self._facts_definitions_op = self._get_fact_definitions(type_name=FactsType.MODEL_FACTS_USER_OP)

        if self._facts_definitions and self._facts_definitions_op:
            props = self._facts_definitions.get(PROPERTIES)
            if props is not None:
                props_by_id = props.get(fact_id)
            props_op = self._facts_definitions_op.get(PROPERTIES)
            if props_op is not None:
                props_by_id_op = props_op.get(fact_id)

        elif self._facts_definitions and not self._facts_definitions_op:
            props = self._facts_definitions.get(PROPERTIES)
            if props is not None:
                props_by_id = props.get(fact_id)

        elif self._facts_definitions_op and not self._facts_definitions:
            props_op = self._facts_definitions_op.get(PROPERTIES)
            if props_op is not None:
                props_by_id_op = props_op.get(fact_id)
        else:
            data = self._get_fact_definitions()
            if data:
                props = data.get(PROPERTIES)
                if props is not None:
                    props_by_id = props.get(fact_id)

            data_op = self._get_fact_definitions(
                type_name=FactsType.MODEL_FACTS_USER_OP)
            if data_op:
                props_op = data_op.get(PROPERTIES)
                if props_op is not None:
                    props_by_id_op = props_op.get(fact_id)

        if props_by_id and props_by_id_op:
            raise ClientError(
                " Fact id {} exists in both modelfacts_user and modelfacts_user_op. Please remove duplicates and try again".format(fact_id))
        # elif not props_by_id and not props_by_id_op:
        #     raise ClientError("Could not find properties for fact id {} ".format(fact_id))
        else:
            return props_by_id, props_by_id_op

    def _type_check_by_id(self, id, val):
        cur_type = None
        is_arr = None

        val_main, val_op = self._get_fact_definition_properties(id)
        cur_val = val_main or val_op

        if cur_val:
            cur_type = cur_val.get("type")
            is_arr = cur_val.get("is_array")

        if cur_type == "integer" and not isinstance(val, int):
            raise ClientError("Invalid value used for type of Integer")
        elif cur_type == "string" and not isinstance(val, str) and not is_arr:
            raise ClientError("Invalid value used for type of String")
        elif (cur_type == "string" and is_arr) and (not isinstance(val, str) and not isinstance(val, list)):
            raise ClientError(
                "Invalid value used for type of String. Value should be either a string or list of strings")

    def _trigger_container_move(self, asset_id: str, container_type: str = None, container_id: str = None):

        asset_id = asset_id or self._asset_id
        container_type = container_type or self._container_type
        container_id = container_id or self._container_id

        try:
            get_assets_url = self._get_assets_url(
                asset_id, container_type, container_id)
            assets_data = requests.get(
                get_assets_url, headers=self._get_headers())
            get_desc = assets_data.json()["metadata"].get("description")
            get_name = assets_data.json()["metadata"].get("name")
        except:
            raise ClientError(
                "Asset details not found for asset id {}".format(asset_id))

        if get_desc:
            body = [
                {
                    "op": "add",
                    "path": "/metadata/description",
                    "value": get_desc + ' '
                }
            ]
        else:
            body = [
                {
                    "op": "add",
                    "path": "/metadata/description",
                    "value": get_name
                }
            ]
        response = requests.patch(get_assets_url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 200:
            return response.status_code
        else:
            raise ClientError("Could not update asset container. ERROR {}. {}".format(
                response.status_code, response.text))

    def _get_mime(self, file):
        # pip install python-magic
        # On a Mac you may also have to run a "brew install libmagic"
        import magic
        mime = magic.Magic(mime=True)
        magic_mimetype_result = mime.from_file(file)
        # sometimes we need to post-correct where the magic result is not right
        # for csv
        if file.endswith(".csv") and not magic_mimetype_result.endswith("/csv"):
            return "text/csv"
        
        if file.endswith(".txt") and not magic_mimetype_result.endswith("/txt"):
            if self._is_cp4d and "5.1.0" <= self._cp4d_version < "5.2.0":
                return "txt"
            return "text"
            
        # for excel (both .xls and .xlsx)
        if file.endswith(".xlsx") and not magic_mimetype_result == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        if file.endswith(".xls") and not magic_mimetype_result == "application/vnd.ms-excel":
            return "application/vnd.ms-excel"

        if file.lower().endswith((".jpg", ".jpeg")) and magic_mimetype_result.strip() != "image/jpeg":
            return "image/jpeg"

        if file.lower().endswith(".docx"):
            #return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            return "application/docx"

        # for HTML
        if file.endswith(".html") and not magic_mimetype_result.endswith("/html"):
            return "text/html"
        
        if file.endswith(".json") and not magic_mimetype_result.endswith("/json"):
            return "application/json"
        
        if file.endswith(".yaml") and not magic_mimetype_result.endswith("/yaml"):
            return "application/yaml"
        return magic_mimetype_result

    def _get_assets_attributes_url(self):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + self._asset_id + "/attributes?" + \
                self._container_type + "_id=" + self._container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes?" + \
                    self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes?" + \
                    self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes?" + \
                    self._container_type + "_id=" + self._container_id

        return url

    def _get_url_by_factstype_container(self, type_name=None):

        facts_type = type_name or self._facts_type

        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                '/v2/assets/' + self._asset_id + "/attributes/" + \
                facts_type + "?" + self._container_type + "_id=" + self._container_id

        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes/" + \
                    facts_type + "?" + self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes/" + \
                    facts_type + "?" + self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes/" + \
                    facts_type + "?" + self._container_type + "_id=" + self._container_id

        return url

    def _get_url_using_factsheet(self,type_name):

        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/v1/aigov/model_inventory/models/' + self._asset_id + \
                  "/"+ type_name +"?" + self._container_type + "_id=" + self._container_id
            if type_name == "user_facts":
                url = url +  "&asset_type="+self._facts_type

        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/model_inventory/models/' + self._asset_id + \
                      "/" + type_name + "?" + self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/model_inventory/models/' + self._asset_id + \
                      "/" + type_name + "?" + self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/model_inventory/models/' + self._asset_id + \
                      "/" + type_name + "?" + self._container_type + "_id=" + self._container_id
                if type_name == "user_facts":
                    url = url +  "&asset_type="+self._facts_type

        return url

    def _get_url_by_factstype_container_mastercopy(self, type_name=None):
        master_copy_info = self.utils_client.get_master_copy_info(
            model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id)
        master_copy_id = master_copy_info['master_copy_id']
        inventory_id = master_copy_info['inventory_id']
        container_type = "catalog"
        facts_type = type_name or self._facts_type
        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                '/v2/assets/' + master_copy_id + "/attributes/" + \
                facts_type + "?" + container_type + "_id=" + inventory_id
        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                    facts_type + "?" + container_type + "_id=" + inventory_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                    facts_type + "?" + container_type + "_id=" + inventory_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                    facts_type + "?" + container_type + "_id=" + inventory_id

        return url
    def _get_url_sysfacts_container(self, asset_id: str = None, container_type: str = None, container_id: str = None, key: str = FactsType.MODEL_FACTS_SYSTEM):

        asset_id = asset_id or self._asset_id
        container_type = container_type or self._container_type
        container_id = container_id or self._container_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + "/attributes/" + \
                key + "?" + container_type + "_id=" + container_id

        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + "/attributes/" + \
                    key + "?" + container_type + "_id=" + container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + "/attributes/" + \
                    key + "?" + container_type + "_id=" + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + "/attributes/" + \
                    key + "?" + container_type + "_id=" + container_id

        return url

    def _get_url_space(self, space_id: str):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/spaces/' + space_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/spaces/' + space_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/spaces/' + space_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/spaces/' + space_id
        return url

    def _get_url_attachments(self, asset_id: str, container_type: str, container_id: str, attachment_id: str = None, mimetype: str = None, action: str = None):

        if action == "del":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                    '?' + container_type + '_id=' + container_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + container_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + container_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + container_id

        elif attachment_id and mimetype and action == "get":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + asset_id + '/attachments/' + attachment_id + '?' + \
                    container_type + '_id=' + container_id + '&response-content-type=' + mimetype
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + container_id + '&response-content-type=' + mimetype
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + container_id + '&response-content-type=' + mimetype
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + container_id + '&response-content-type=' + mimetype

        elif attachment_id and action == "complete":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                    '/complete?' + container_type + '_id=' + container_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + container_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + container_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + container_id

        else:
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + asset_id + '/attachments?' + \
                    container_type + '_id=' + container_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments?' + \
                        container_type + '_id=' + container_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments?' + \
                        container_type + '_id=' + container_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + asset_id + '/attachments?' + \
                        container_type + '_id=' + container_id
        return url
    def _get_url_attachments_mastercopy(self, attachment_id: str = None, mimetype: str = None, action: str = None):
        master_copy_info = self.utils_client.get_master_copy_info(
            model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id)
        master_copy_id = master_copy_info['master_copy_id']
        inventory_id = master_copy_info['inventory_id']
        container_type = "catalog"
        if action == "del":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                    '?' + container_type + '_id=' + inventory_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + inventory_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + inventory_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '?' + container_type + '_id=' + inventory_id

        elif attachment_id and mimetype and action == "get":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + '?' + \
                    container_type + '_id=' + inventory_id + '&response-content-type=' + mimetype
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + inventory_id + '&response-content-type=' + mimetype
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + inventory_id + '&response-content-type=' + mimetype
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + '?' + \
                        container_type + '_id=' + inventory_id + '&response-content-type=' + mimetype

        elif attachment_id and action == "complete":
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                    '/complete?' + container_type + '_id=' + inventory_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + inventory_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + inventory_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments/' + attachment_id + \
                        '/complete?' + container_type + '_id=' + inventory_id

        else:

            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    '/v2/assets/' + master_copy_id + '/attachments?' + \
                    container_type + '_id=' + inventory_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments?' + \
                        container_type + '_id=' + inventory_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments?' + \
                        container_type + '_id=' + inventory_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        '/v2/assets/' + master_copy_id + '/attachments?' + \
                        container_type + '_id=' + inventory_id
        return url

    def _get_attachment_download_url(self, asset_id, container_type, container_id, attachment_id, mimetype, filename):

        url = self._get_url_attachments(
            asset_id, container_type, container_id, attachment_id, mimetype, action="get")
        if mimetype.startswith("image/") or mimetype.startswith("application/pdf") or mimetype.startswith("text/html"):
            url += "&response-content-disposition=inline;filename=" + filename

        else:
            url += "&response-content-disposition=attachment;filename=" + filename

        response = requests.get(url, headers=self._get_headers())
        download_url = response.json().get("url")
        return download_url

    def _get_attachment_download_url_mastercopy(self,  attachment_id, mimetype, filename):

        url = self._get_url_attachments_mastercopy(
            attachment_id, mimetype, action="get")
        if mimetype.startswith("image/") or mimetype.startswith("application/pdf") or mimetype.startswith("text/html"):
            url += "&response-content-disposition=inline;filename=" + filename

        else:
            url += "&response-content-disposition=attachment;filename=" + filename

        response = requests.get(url, headers=self._get_headers())
        download_url = response.json().get("url")
        return download_url

    def _finalVersion(self, versionList: list = None):
        splitVersion = []
        FinalVersionList = []
        convertFromString = []

        version_pattern = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

        for version in versionList:
            # Match version using the regex pattern
            version_parts = re.match(version_pattern, version)
            if not version_parts:
                raise ValueError(f"Invalid version format: {version}")

            major, minor, patch = int(version_parts[1]), int(version_parts[2]), int(version_parts[3])
            pre_release, build_metadata = version_parts[4], version_parts[5]
            
            splitVersion.append([major, minor, patch, pre_release, build_metadata])

            convertFromString.append([major, minor, patch])

        # Sort the versions by their numeric values (major, minor, patch)
        sortedVersion = sorted(convertFromString)

        # Reconstruct the sorted versions into the original format (including pre-release and build metadata)
        for sortedVal in sortedVersion:
            # Find the corresponding original version and reattach the pre-release and build metadata
            for idx, val in enumerate(splitVersion):
                if sortedVal == val[:3]:  # Match major, minor, patch (ignore pre-release/build for sorting)
                    major, minor, patch, pre_release, build_metadata = val
                    version_str = f"{major}.{minor}.{patch}"
                    if pre_release:
                        version_str += f"-{pre_release}"
                    if build_metadata:
                        version_str += f"+{build_metadata}"
                    FinalVersionList.append(version_str)
                    break

        return FinalVersionList

    def _increment_ver(self, version, releaseVal):

        version_pattern = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        version_parts = re.match(version_pattern, version)

        # if not version_parts:
        #     raise ValueError(f"Invalid version format: {version}")
        
        major = int(version_parts.group("major"))
        minor = int(version_parts.group("minor"))
        patch = int(version_parts.group("patch"))

        version_list = [major, minor, patch]
       
        # version = version.split('.')
        if releaseVal == "major":
            major += 1
            minor = 0
            patch = 0
        elif releaseVal == "minor":
            minor += 1
            patch = 0
        elif releaseVal == "patch":
            patch += 1
        else:
            raise ValueError(f"Unknown release value: {releaseVal}")
        
        return '.'.join(map(str, [major, minor, patch]))
    
    # def track(self,model_usecase:ModelUsecaseUtilities=None,approach:ApproachUtilities=None,grc_model:dict=None, version_number:str=None, version_comment:str=None):
    def track(self, usecase: ModelUsecaseUtilities = None, approach: ApproachUtilities = None, grc_model: dict = None, version_number: str = None, version_comment: str = None):
        """
            Link Model to model use case. Model asset should be stored in either Project or Space and corrsponding ID should be provided when registering to model use case. 

            Supported for CPD version >=4.7.0

            :param ModelUsecaseUtilities usecase: Instance of ModelUsecaseUtilities
            :param ApproachUtilities approach: Instance of ApproachUtilities
            :param str grc_model: (Optional) Openpages model id. Only applicable for CPD environments. This should be dictionary, output of get_grc_model()
            :param str version_number: Version number of model. supports either a semantic versioning string or one of the following keywords for auto-incrementing based on the latest version in the approach: "patch", "minor", "major"
            :param str version_comment: (Optional) An optional comment describing the changes made in this version

            :rtype: ModelAssetUtilities

            For tracking model with model usecase:

            >>> model.track(usecase=<instance of ModelUsecaseUtilities>,approach=<instance of ApproachUtilities>,version_number=<version>)

        """

        output_width=125
        print("-" * output_width)
        print("Tracking Process Started".center(output_width))
        print("-" * output_width)

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Track model with model usecase and approach functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        # if (model_usecase is None or model_usecase == ""):
        #     raise MissingValue("model_usecase", "ModelUsecaseUtilities object or instance is missing")

        if (usecase is None or usecase == ""):
            raise MissingValue(
                "ai usecase", "ModelUsecaseUtilities object or instance is missing")

        # if ( not isinstance(model_usecase, ModelUsecaseUtilities)):
        #     raise ClientError("Provide ModelUsecaseUtilities object for model_usecase")
        if (not isinstance(usecase, ModelUsecaseUtilities)):
            raise ClientError(
                "Provide ModelUsecaseUtilities object for usecase parameter")

        if (approach is None or approach == ""):
            raise MissingValue(
                "approach", "ApproachUtilities object or instance is missing")

        if (not isinstance(approach, ApproachUtilities)):
            raise ClientError("Provide ApproachUtilities object for approach")

        if (version_number is None or version_number == ""):
            raise MissingValue("version_number", "version number is missing")

        model_asset_id = self._asset_id
        container_type = self._container_type
        container_id = self._container_id

        params = {}
        payload = {}
        version_details = {}

        params[container_type + '_id'] = container_id

        # model_usecase_id = model_usecase.get_id()
        # model_usecase_catalog_id = model_usecase.get_container_id()
        model_usecase_id = usecase.get_id()
        model_usecase_catalog_id = usecase.get_container_id()
        model_usecase_name=usecase.get_name()

        approach_id = approach.get_id()
        approach_name=approach.get_name()
       
        if approach._versions is None:
            approach._versions = []
        else:
            approach._versions.clear()
        
        _logger.info("Assigned {} to {} for tracking.".format(approach_name, model_usecase_name))
        
        latest_version_data = self._get_latest_approach_version(model_usecase_id, model_usecase_catalog_id, approach_id)
        if latest_version_data:
             approach._versions.append({
                "number": latest_version_data['number'],
                "comment": latest_version_data['comment']
                })
        else:
            raise ClientError("Failed to fetch the latest version")

        approachVersionList = approach.get_versions()
        versionList = []
        for version in approachVersionList:
            # version["number"]
            versionList.append(version["number"])
        finalVersionValList = self._finalVersion(versionList)
        finalVersionVal = finalVersionValList[-1]

        # Since support for the cloud is now live, commenting this line 
        # if grc_model and not self._is_cp4d:
        #     raise WrongParams(
        #         "grc_model is only applicable for Openpages enabled CPD platform")

        payload['model_entry_catalog_id'] = model_usecase_catalog_id or self._assets_client._get_pac_catalog_id()
        payload['model_entry_asset_id'] = model_usecase_id

        version_details['approach_id'] = approach_id

        if version_comment:
            version_details['comment'] = version_comment
        
        # if approach._versions is None:
        #     approach._versions = []

        if version_number in ["major", "minor", "patch"]:
                finalVersionVal = self._increment_ver(finalVersionVal, version_number)
        else:
            finalVersionVal = version_number

        latest_version = latest_version_data['number'] if latest_version_data else None
        latest_version = pkg_version.parse(latest_version)
        requested_version = pkg_version.parse(finalVersionVal)

        if latest_version > requested_version:
            _logger.warning(f"The latest version in this approach is {latest_version}. Please confirm that you want to assign a lower version number to this model.")
    
        version_details['number'] = finalVersionVal

        payload['version_details'] = version_details

        wkc_register_url = WKC_MODEL_REGISTER.format(model_asset_id)

        if grc_model:
            payload['grc_model_id'] = grc_model.get('GrcModel').get('id')

        if self._is_cp4d:
            url = self._cpd_configs["url"] + wkc_register_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + wkc_register_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    wkc_register_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + wkc_register_url

        if model_usecase_id:
            _logger.info("Initiate linking model to existing AI usecase {}".format(
                model_usecase_id))
        else:
            _logger.info("Initiate linking model to new AI usecase......")

        response = requests.post(url,
                                 headers=self._get_headers(),
                                 params=params,
                                 data=json.dumps(payload))

        if response.status_code == 200:
            _logger.info("Successfully finished linking Model {} to AI usecase".format(
                model_asset_id))
            # approach._versions.clear()
            
        else:
            error_msg = u'Model registration failed'
            # version_logging_data['success'] = False
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)

        return response.json()
    

    def untrack(self):
        """
            Unlink model from it's usecase and approach

            Example for IBM Cloud or CPD:

            >>> model.untrack()

        """
        tracked ,model_usecase = self._is_model_tracked()
        if not tracked:
            _logger.info("Cannot untrack model for asset {} as it is not currently tracked.".format(self._asset_id))
        else:
            model_usecase_id=model_usecase['model_usecase_id']
            _logger.info("Starting to untrack the model asset {} from the AI use case {}".format(self._asset_id,model_usecase_id))
            wkc_unregister_url = WKC_MODEL_REGISTER.format(self._asset_id)

            params = {}
            params[self._container_type + '_id'] = self._container_id

            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                    wkc_unregister_url
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                        wkc_unregister_url
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                        wkc_unregister_url
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                        wkc_unregister_url

            response = requests.delete(url,
                                    headers=self._get_headers(),
                                    params=params,
                                    )

            if response.status_code == 204:
                _logger.info("Successfully completed untracking of Watsonx Governance model asset {} from the AI use case.".format(self._asset_id))


            else:
                error_msg = u'ai use case untracking'
                reason = response.text
                _logger.info(error_msg)
                raise ClientError(error_msg + '. Error: ' +
                                str(response.status_code) + '. ' + reason)

    def get_version(self) -> Dict:
        """
            Get model version details. Supported for CPD version >=4.7.0

            :rtype: dict

            The way to use me is:

            >>> model.get_version()

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model version functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            model_version_details = {}

            if "model_version" in (response.json()["entity"]["wml_model"]):
                model_version = response.json(
                )["entity"]["wml_model"]["model_version"].get("number")
                model_version_comment = response.json(
                )["entity"]["wml_model"]["custom"].get("version_comment")

                model_version_details["number"] = model_version
                model_version_details["comment"] = model_version_comment

                _logger.info("Model version details retrieved successfully")
                return model_version_details
        else:
            raise ClientError("Failed to retrieve model version details information. ERROR {}. {}".format(
                response.status_code, response.text))

    def get_name(self) -> str:
        """
            Returns model name

            :return: Model name
            :rtype: str

            Example,::
            
              model.get_name()

        """

        return self.get_info(True).get("name")

    def get_id(self) -> str:
        """
            Returns model ID

            :return: Model ID
            :rtype: str

            Example,::
            
               model.get_id()

        """

        return self.get_info(True).get("asset_id")

    def get_container_id(self) -> str:
        """
            Returns model container ID

            :return: Model container ID
            :rtype: str

            Example,::
            
              model.get_container_id()

        """

        return self.get_info(True).get("container_id")

    def get_container_type(self) -> str:
        """
            Returns model container type

            :return: Model container type
            :rtype: str

            Example,::
            
               model.get_container_type()

        """

        return self.get_info(True).get("container_type")

    def get_description(self) -> str:
        """
            Returns model description

            :return: Model description
            :rtype: str

            Example,::
            
              model.get_description()

        """

        return self.get_info(True).get("description")

    def _encode_id(self, id):
        encoded_id = hashlib.md5(id.encode("utf-8")).hexdigest()
        return encoded_id

    def get_deployments(self) -> List:
        """
            Get all deployment details for the external model. Supported for CPD version >=4.7.0

            :return: All deployment details for external model
            :rtype: list(Deployment)

            The way to use me is,::

               model.get_deployments()

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Retrieving external model deployments functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        container_type = self._container_type
        container_id = self._container_id

        url = self._get_deployments_url(
            model_asset_id, container_id, operation="get")

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("Deployments retrieved successfully")
            deployment_list = response.json()["deployment_details"]
            deployment_list_values = []
            for deployment in deployment_list:
                deployment_list_values.append(Deployment(self, deployment.get('id'), deployment.get('name'), deployment.get('type'), deployment.get('scoring_endpoint'), deployment.get(
                    'external_identifier'), deployment.get('is_deleted'), deployment.get('description'), model_asset_id, self.get_name(), container_type, container_id))
            return deployment_list_values
        else:
            raise ClientError("Failed in retrieving deployments. ERROR {}. {}".format(
                response.status_code, response.text))

    def delete_deployments(self, deployment_ids: list = None):
        """
            Delete the deployments in external model for documentation purposes only. Supported for CPD version >=4.7.0

            :param list deployment_ids: List of deployment ID's to be deleted. Provide deployment_ids in a list.

            :rtype: None

            :return: External model deployments are deleted.
            
            The way to use me is,::

                model.delete_deployments([deployment_ids])
        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Deleting external model deployments functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        container_type = self._container_type
        container_id = self._container_id

        if (isinstance(deployment_ids, list)) and (deployment_ids is not None and len(deployment_ids) > 0):
            for deployment_id in deployment_ids:
                url = self._get_deployments_url(
                    model_asset_id, container_id, deployment_id, operation="delete")
                response = requests.delete(url, headers=self._get_headers())
                if response.status_code == 204:
                    _logger.info("Deployment " + deployment_id +
                                 " deleted successfully")
                else:
                    raise ClientError("Failed in deleting deployment {}. ERROR {}. {}".format(
                        deployment_id, response.status_code, response.text))
        else:
            raise MissingValue(
                "deployment_ids", "Missing list of deployment_ids")

    def add_deployments(self, deployments: list = None) -> list:
        """
            Adds deployments for external models for documentation purposes only. Supported for CPD version 4.7.0 and above

            :param list deployments: List of deployments to be added. Provide deployments in a list.

            :rtype: list(Deployment)

            :return: External model deployments are added
            
            The way to use me is,::
            
                model.add_deployments([{"id":"<id>","name":"<name>","type":"<type>","scoring_endpoint":"<scoring_endpoint>","description":"<description>"}])

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Adding deployments for external model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        container_type = self._container_type
        container_id = self._container_id

        if (isinstance(deployments, list)) and (deployments is not None and len(deployments) > 0):
            failed_deployments = []
            deployments_response = []
            for deployment in deployments:
                deployment_identifier = deployment.get('id')
                name = deployment.get('name')
                type = deployment.get('type')
                scoring_endpoint = deployment.get('scoring_endpoint')
                description = deployment.get('description')

                if (deployment_identifier is None or deployment_identifier == ""):
                    raise MissingValue("id", "ID is missing")
                if (name is None or name == ""):
                    raise MissingValue("name", "name is missing")

                id = self._encode_id(deployment_identifier)

                body = {
                    "id": id,
                    "external_identifier": deployment_identifier,
                    "name": name,
                    "type": type,
                    "scoring_endpoint": scoring_endpoint,
                    "description": description
                }
                final_body = {k: v for (k, v) in body.items() if v is not None}

                url = self._get_deployments_url(
                    model_asset_id, container_id, operation="add")
                response = requests.put(url, data=json.dumps(
                    final_body), headers=self._get_headers())

                if response.status_code == 200:
                    _logger.info(
                        "Deployment added successfully to an external model")
                    deployments_response.append(Deployment(self, id, name, type, scoring_endpoint, deployment_identifier,
                                                "false", description, model_asset_id, self.get_name(), container_type, container_id))

                else:
                    failed_deployments.append(response.text)
            if len(deployments_response) > 0:
                return deployments_response

            if len(failed_deployments) > 0:
                raise ClientError(
                    "Failed while adding deployment to an external model. ERROR {}".format(failed_deployments))
        else:
            raise MissingValue(
                "deployments", "Missing deployments as a list of dictionary values.")

    def _get_deployments_url(self, model_asset_id: str = None, catalog_id: str = None, deployment_id: str = None, operation: str = None):

        if operation == 'add':
            append_url = '/v1/aigov/model_inventory/models/' + \
                model_asset_id + '/deployments?catalog_id=' + catalog_id
        elif operation == 'get':
            append_url = '/v1/aigov/model_inventory/models/' + \
                model_asset_id + '/deployments?catalog_id=' + catalog_id
        elif operation == 'delete':
            append_url = '/v1/aigov/model_inventory/models/' + model_asset_id + \
                '/deployments/' + deployment_id + '?catalog_id=' + catalog_id
        elif operation == 'modelput':
            append_url = '/v1/aigov/model_inventory/models/' + \
                model_asset_id + '/environment?catalog_id=' + catalog_id
        else:
            append_url = ""

        if self._is_cp4d:
            url = self._cpd_configs["url"] + append_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + append_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + append_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + append_url

        return url

    #attachment changes - May 2024

    # Attachment url for below 5.1 CPD version
    def _set_model_attachments_url(self, asset_id: str, container_id: str, container_type: str, name: str = None,
                                   description: str = None, mimetype: str = None, fact_id: str = None,
                                   phase_type: str = None,html_rendering_hint:str=None):
            if html_rendering_hint and phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type  +'&html_rendering_hint='+html_rendering_hint

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint


            elif phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
            else:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
            return url
    def _set_model_attachments_url_mastercopy(self, name: str = None,
                                   description: str = None, mimetype: str = None, fact_id: str = None,
                                   phase_type: str = None,html_rendering_hint:str=None):

        master_copy_info = self.utils_client.get_master_copy_info(
            model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id)
        master_copy_id = master_copy_info['master_copy_id']
        inventory_id = master_copy_info['inventory_id']
        container_type = "catalog"

        if html_rendering_hint and phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type  +'&html_rendering_hint='+html_rendering_hint

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint


        elif phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
        else:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                else:
                    if get_env() == 'dev':   
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
        return url


    # Large Attachment url for above 5.1 CPD version
    def _set_model_attachments_url_new(self, asset_id: str, container_id: str, container_type: str, name: str = None,
                                   description: str = None, mimetype: str = None, fact_id: str = None,
                                   phase_type: str = None,html_rendering_hint:str=None):
            if html_rendering_hint and phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type  +'&html_rendering_hint='+html_rendering_hint

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint


            elif phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
            else:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
            return url
    def _set_model_attachments_url_new_mastercopy(self, name: str = None,
                                   description: str = None, mimetype: str = None, fact_id: str = None,
                                   phase_type: str = None,html_rendering_hint:str=None):
           
            master_copy_info = self.utils_client.get_master_copy_info(
            model_id=self._asset_id, container_type=self._container_type, container_id=self._container_id)
            master_copy_id = master_copy_info['master_copy_id']
            inventory_id = master_copy_info['inventory_id']
            container_type = "catalog"
            if html_rendering_hint and phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type  +'&html_rendering_hint='+html_rendering_hint

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint

                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type +'&html_rendering_hint='+html_rendering_hint


            elif phase_type:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&phase_type=' + phase_type
            else:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id

                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/models/large_attachment/' + master_copy_id + f'/content?{container_type}_id=' + inventory_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
            return url

    def set_attachment_fact(self,
                                file_to_upload: str,
                                fact_id: str,
                                description: str = None,
                                phase_name: str = None,
                                html_rendering_hint: str = None,
                                allow_large_files: bool = False) -> None:


            """
            Set an attachment fact for a given asset. Supported for CPD version >= 4.6.5.

            :param str file_to_upload: The file path of the attachment to be uploaded.
                This is the path to the file that will be added as an attachment.
            :param str fact_id: The Fact ID against which the attachment will be uploaded.
                If no Fact ID is provided, the attachment will appear under 'Other Attachments' in the factsheet.
            :param str description: (Optional) A description of the file to be attached.
            :param str phase_name: (Optional) The phase name where the attachment should appear.
                Available options are specified in :func:`~ibm_aigov_facts_client.utils.enums.Phases`.
            :param str html_rendering_hint: (Optional) The HTML rendering hint for the attachment.
                Available options are specified in :func:`~ibm_aigov_facts_client.utils.enums.RenderingHints`.

            Example:
                >>> model.set_attachment_fact(
                ...     file_to_upload="./artifacts/image.png",
                ...     description="Sample image",
                ...     fact_id="custom_fact_id",
                ...     phase_name="Design",
                ...     html_rendering_hint="inline"
                ... )
            """
            if self._is_cp4d and self._cp4d_version < "4.6.5":
                raise ClientError(
                    "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

            # if self._is_cp4d and self._cp4d_version< "5.0.1":
            #     raise ClientError("Version mismatch: Phase specific attachment functionality is only supported in CP4D version 5.0.1 or higher. Current version of CP4D is " + self._cp4d_version)

            model_asset_id = self._asset_id
            model_container_type = self._container_type
            model_container_id = self._container_id

            if phase_name:
                _logger.warning("The 'phase_name' parameter no longer needs to be provided in the Python SDK. The lifecycle phase is now determined automatically by the backend. The parameter is ignored and should be removed from existing code. Support for the parameter will be removed in a future release.")
            
            #when it is not external model, we check for workspace associations
            if (not self._external_model) and (self._is_cp4d and self._cp4d_version >= "5.0.3"):
                container_search_dict = [
                    {"id": model_container_id, "type": model_container_type}
                    ]
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                try:
                    # Fetching workspace association info
                    try:
                        model_container_info = self._facts_client.assets.get_workspace_association_info(workspace_info=container_search_dict)
                        associated_workspace = model_container_info.get('associated_workspaces', [])
                        associated_usecase = associated_workspace[0].get('associated_usecases', [])

                        # When no association, should not be allowed to attach
                        if not associated_usecase:
                            raise ClientError("Workspace containing the model is not associated to any usecase. Please ensure the required association before adding any attachment")

                        # Get phase name from association if the model is not external
                        model_container_phase = associated_workspace[0].get('phase_name', '')
                        if model_container_phase.lower() in ["develop", "validate", "operate", "unspecified"]:
                            phase_name = None

                    except Exception as e:
                        raise ClientError(f"Failed to fetch workspace association status: {e}")

                    finally:
                        sys.stdout = old_stdout

                except Exception as e:
                    raise ClientError(f"Failed to set the attachment fact. Exception encountered: {e}")

            # For external model also we set phase_name to None
            else:
                phase_name = None 
            
            if os.path.exists(file_to_upload):
                file_size = os.stat(file_to_upload).st_size
                # <500MB
                if file_size > MAX_SIZE and not allow_large_files:
                    raise ClientError(f"Maximum file size allowed is {MAX_SIZE}. Current file size is {file_size} ")
            else:
                raise ClientError("Invalid file path provided")

            if html_rendering_hint:
                validate_enum(html_rendering_hint,"html_rendering_hint", RenderingHints, False)

            # Check if there is already an attachment for the given fact id (only one attachment allowed per fact_id).
            get_factid_attachment = self.list_attachments(filter_by_factid=fact_id)

            if get_factid_attachment:
                raise ClientError(
                    "Fact id {} already have an attachment set and only allowed to have one. You can remove and set new attachment if needed".format(fact_id))

            else:
                try:
                        mimetype = self._get_mime(file_to_upload)
                        base_filename_before = os.path.basename(file_to_upload)
                        base_filename = urllib.parse.quote(base_filename_before)
                        file_name, _ = os.path.splitext(base_filename)
               
                        # description = urllib.parse.quote(description)
                        if description:
                            description = urllib.parse.quote(description)
                        else:
                            description = ""

                        if (self._is_cp4d and self._cp4d_version < "5.1.0") or (aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}):
                           
                            if self._is_new_usecase() and not self._external_model:    
                                attachment_url = self._set_model_attachments_url_mastercopy(name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name,html_rendering_hint=html_rendering_hint)                              
                            else:
                                attachment_url = self._set_model_attachments_url(
                                        asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name,html_rendering_hint=html_rendering_hint)                      
                            with open(file_to_upload, "rb") as file:
                                base64_encoded_string = base64.b64encode(file.read())
                            body = base64_encoded_string
                        else:
                           
                            if self._is_new_usecase() and not self._external_model :               
                                attachment_url = self._set_model_attachments_url_new_mastercopy(name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name,html_rendering_hint=html_rendering_hint)              
                            else:
                                attachment_url = self._set_model_attachments_url_new(
                                    asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name,html_rendering_hint=html_rendering_hint)                      
                            with open(file_to_upload, "rb") as file:
                                body=file.read()

                        #print(f"attachment_url : {attachment_url}")

                        if html_rendering_hint == RenderingHints.INLINE_HTML:
                            htmlparser = FactHTMLParser()
                            html_file = open(file_to_upload, 'r')
                            html_content = html_file.read()
                            htmlparser.feed(html_content)
                            htmlparser.close()
                            restricted_tags = "style istyle css"
                            # checking if any of the above restricted_tags values in html tags
                            contains_restricted_tag = any(
                                item in restricted_tags for item in htmlparser.start_tags)
                            if contains_restricted_tag:
                                raise ClientError(
                                    "Invalid inline HTML content: Attachments content to be rendered as inline_html is NOT allowed to contain any of the following HTML tags:{}".format(
                                        list(restricted_tags.split(" "))))

                        # convert png to jpeg
                        if mimetype == "image/png":
                            from PIL import Image

                            ima = Image.open(file_to_upload)
                            rgb_im = ima.convert('RGB')
                            rgb_im.save(os.path.splitext(file_to_upload)
                                        [0] + ".jpg", format='JPEG')
                            mimetype = "image/jpeg"
                            base_filename = os.path.splitext(base_filename)[0] + ".jpg"
                            file_to_upload = os.path.splitext(file_to_upload)[0] + ".jpg"

                        attachment_data = {}

                        if fact_id:
                            attachment_data["fact_id"] = fact_id
                        if html_rendering_hint:
                            attachment_data["html_rendering_hint"] = html_rendering_hint

                        iam_headers = self._get_headers()
                        if "Content-Type" in iam_headers:
                            iam_headers['Content-Type'] = 'application/octet-stream'
                        iam_headers['accept'] = '*/*'


                        create_attachment_response = requests.put(
                            attachment_url, data=body, headers=iam_headers)
                       
                        if create_attachment_response.status_code == 200:
                            attachment_id = create_attachment_response.json().get("attachment_id")
                            if attachment_id:
                                _logger.info(f"Successfully uploaded file {file_to_upload} to the factsheet of asset_id {model_asset_id}")
                                response_data = create_attachment_response.json()
                                print(f" \n\t=== Attachment Details : ===")
                                print(f" * attachment id : {response_data.get('attachment_id','')}")
                                print(f" * asset type : {response_data.get('asset_type','')}")
                                print(f" * attachment name : {response_data.get('name','')} ")
                                print(f" * description : {response_data.get('description','')}")
                                print(f" * MIME type : {response_data.get('mime','')}")
                                
                                attachment_size_bytes = response_data.get('size', 0)
                                if attachment_size_bytes:
                                    attachment_size_mb = attachment_size_bytes / (1024 * 1024)
                                    attachment_size_gb = attachment_size_bytes / (1024 * 1024 * 1024)

                                    if attachment_size_gb >= 1:
                                        print(f" * attachment size : {attachment_size_gb:.2f} GB")
                                    elif attachment_size_mb >= 1:
                                        print(f" * attachment size : {attachment_size_mb:.2f} MB")
                                    else:
                                        print(f" * attachment size : {attachment_size_bytes} bytes")
                                else:
                                    print(" * attachment size : 0 bytes")

                        else:
                            raise ClientError("Failed to set the attachment fact. ERROR {}. {}".format(
                                create_attachment_response.status_code, create_attachment_response.text))
                except Exception as e:
                    raise ClientError(f" Failed to set the attachment fact. Exception encountered : {e}")


    def set_cell_attachment_fact(self,
                                 fact_id: str,
                                 description: str = None,
                                 phase_name: str = None,
                                 ) -> None:
        """
             Set the cell attachment fact using captured cell output. Supported for CPD version >=4.6.5.
            :param str fact_id: Fact id for the attachment
            :param str description: (Optional) Description about the cell facts attachment file
            :param str phase_name: (Optional) Phase name in which the attachment should appear. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Phases`
            A way to use me is:
            .. code-block:: python
                >>> model.set_cell_attachment_fact(description="<file description>", fact_id="<custom fact id>", phase_name="<phase_name>")
        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is "+self._cp4d_version)

        # if self._is_cp4d and self._cp4d_version< "5.0.1":
        #     raise ClientError("Version mismatch: Phase specific attachment functionality is only supported in CP4D version 5.0.1 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if phase_name:
            _logger.warning("The 'phase_name' parameter no longer needs to be provided in the Python SDK. The lifecycle phase is now determined automatically by the backend. The parameter is ignored and should be removed from existing code. Support for the parameter will be removed in a future release.")

        #when it is not external model, we check for workspace associations
        if (not self._external_model) and (self._is_cp4d and self._cp4d_version >= "5.0.3"):
            container_search_dict = [
                {"id": model_container_id, "type": model_container_type}
            ]
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()

            try:
                # Fetching workspace association info
                try:
                    model_container_info = self._facts_client.assets.get_workspace_association_info(workspace_info=container_search_dict)
                    associated_workspace = model_container_info.get('associated_workspaces', [])
                    associated_usecase = associated_workspace[0].get('associated_usecases', [])

                    # When no association, should not be allowed to attach
                    if not associated_usecase:
                        raise ClientError("Workspace containing the model is not associated to any usecase. Please ensure the required association before adding any attachment")

                    # Get phase name from association if the model is not external
                    model_container_phase = associated_workspace[0].get('phase_name', '')
                    if model_container_phase.lower() in ["develop", "validate", "operate", "unspecified"]:
                        phase_name = None  

                except Exception as e:
                    raise ClientError(f"Failed to fetch workspace association status: {e}")

                finally:
                    sys.stdout = old_stdout 

            except Exception as e:
                raise ClientError(f"Failed to set the attachment fact. Exception encountered: {e}")

        # For external model also we set phase_name to None
        else:
            phase_name = None  
            
        file_to_upload = "{}/{}/{}".format(os.getcwd(),
                                           CELL_FACTS_TMP_DIR, CellFactsMagic._fname)
        if not os.path.exists(file_to_upload):
            raise ClientError(
                "Invalid file path. Failed to find {}".format(CellFactsMagic._fname))

        # check if have attachment for given fact id. only one attachment allowed per fact_id.
        get_factid_attachment = self.list_attachments(filter_by_factid=fact_id)

        if get_factid_attachment:
            raise ClientError(
                "Fact id {} already have an attachment set and only allowed to have one. You can remove and set new attachment if needed".format(fact_id))

        else:

            try:
                # create attachment

                mimetype = self._get_mime(file_to_upload)
                if self._is_new_usecase() and not self._external_model:
                    attachment_url = self._get_url_attachments_mastercopy()
                else:
                    attachment_url = self._get_url_attachments(
                    model_asset_id, model_container_type, model_container_id)
                base_filename = os.path.basename(file_to_upload)
                base_filename_before = os.path.basename(file_to_upload)
                base_filename = urllib.parse.quote(base_filename_before)
                file_name, _ = os.path.splitext(base_filename)
                # description = urllib.parse.quote(description)
                if description:
                    description = urllib.parse.quote(description)
                else:
                    description = "" 


                if (self._is_cp4d and self._cp4d_version < "5.1.0") or (aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD, AWS_GOVCLOUD}):
                    if self._is_new_usecase() and not self._external_model:    
                        attachment_url = self._set_model_attachments_url_mastercopy(name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name)
                    else:
                        attachment_url = self._set_model_attachments_url(asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name)
                    with open(file_to_upload, "rb") as file:
                        base64_encoded_string = base64.b64encode(file.read())
                    body = base64_encoded_string
                else:
                    if self._is_new_usecase() and not self._external_model:
                        attachment_url = self._set_model_attachments_url_new_mastercopy(name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name)
                    else:
                        attachment_url = self._set_model_attachments_url_new(asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id, phase_type=phase_name)
                    with open(file_to_upload, "rb") as file:
                        body=file.read()

                #print(f"attachment_url : {attachment_url}")

                # convert png to jpeg
                if mimetype == "image/png":
                    from PIL import Image

                    ima = Image.open(file_to_upload)
                    rgb_im = ima.convert('RGB')
                    rgb_im.save(os.path.splitext(file_to_upload)
                                [0] + ".jpg", format='JPEG')
                    mimetype = "image/jpeg"
                    # base_filename=os.path.splitext(file_to_upload)[0]+".jpg"
                    # file_to_upload=base_filename
                    base_filename = os.path.splitext(base_filename)[0] + ".jpg"
                    file_to_upload = os.path.splitext(file_to_upload)[0] + ".jpg"

                attachment_data = {}

                if fact_id:
                    attachment_data["fact_id"] = fact_id
                # if html_rendering_hint:
                #     attachment_data["html_rendering_hint"] = html_rendering_hint

                iam_headers = self._get_headers()
                if "Content-Type" in iam_headers:
                    iam_headers['Content-Type'] = 'application/octet-stream'
                    iam_headers['accept'] = '*/*'

                create_cell_attachment_response = requests.put(
                    attachment_url, data=body, headers=iam_headers)
                if create_cell_attachment_response.status_code == 200:
                    attachment_id = create_cell_attachment_response.json().get("attachment_id")
                    if attachment_id:
                        _logger.info(
                            f"Successfully uploaded file {file_to_upload} to the factsheet of asset_id {model_asset_id}")
                        response_data = create_cell_attachment_response.json()
                        print(f" \n\t=== Attachment Details : ===")
                        print(f" * attachment id : {response_data.get('attachment_id', '')}")
                        print(f" * asset type : {response_data.get('asset_type', '')}")
                        print(f" * attachment name : {response_data.get('name', '')} ")
                        print(f" * description : {response_data.get('description', '')}")
                        print(f" * MIME type : {response_data.get('mime', '')}")
                        
                        attachment_size_bytes = response_data.get('size', 0)
                        if attachment_size_bytes:
                            attachment_size_mb = attachment_size_bytes / (1024 * 1024)
                            attachment_size_gb = attachment_size_bytes / (1024 * 1024 * 1024)
    
                            if attachment_size_gb >= 1:
                                print(f" * attachment size : {attachment_size_gb:.2f} GB")
                            elif attachment_size_mb >= 1:
                                print(f" * attachment size : {attachment_size_mb:.2f} MB")
                            else:
                                print(f" * attachment size : {attachment_size_bytes} bytes")
                        else:
                            print(" * attachment size : 0 bytes")

                        os.remove(file_to_upload)

                else:
                    raise ClientError("Failed to set the attachment fact. ERROR {}. {}".format(
                        create_cell_attachment_response.status_code, create_cell_attachment_response.text))
            except Exception as e:
                raise ClientError(f" Failed to set the attachment fact. Exception encountered : {e}")
            
######################################################## UTILS #############################################################################
   
   
    def _get_latest_approach_version(self, model_asset_id, model_usecase_catalog_id, approach_id):
        url = self._get_approach_url(model_asset_id, model_usecase_catalog_id)
        response = requests.get(url, headers=self._get_headers())

        if response.status_code != 200:
            raise ClientError(f"Failed to fetch approach versions. Error: {response.status_code}")

        approach_response = response.json()
        approaches_list = approach_response.get("approaches", [])

        for approach_data in approaches_list:
            if approach_data.get('id') == approach_id:
                versions = approach_data.get('versions', [])
                if versions:
                    return {
                                "number": versions[0].get('number'),
                                 "comment": versions[0].get('comment')
                            }
                return {"number": "0.0.0", "comment": ""}

        raise ClientError(f"Approach with ID {approach_id} not found")


    def _get_approach_url(self, model_usecase_asset_id: str = None, catalog_id: str = None):
        if not model_usecase_asset_id or not catalog_id:
            raise ValueError("Model usecase asset ID and catalog ID are required.")

        append_url = '/v1/aigov/model_inventory/model_usecases/' + \
            model_usecase_asset_id + '/tracked_model_versions?catalog_id=' + catalog_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + append_url
        else:
            if get_env() == 'dev': 
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + append_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + append_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + append_url

        return url


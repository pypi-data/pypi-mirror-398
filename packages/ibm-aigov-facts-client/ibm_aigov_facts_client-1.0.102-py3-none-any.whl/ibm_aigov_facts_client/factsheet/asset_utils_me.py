import logging
import os
import json
import collections
import pandas as pd
import ibm_aigov_facts_client._wrappers.requests as requests
import urllib.parse

from typing import BinaryIO, Dict, List, TextIO, Union, Any
from ibm_aigov_facts_client.factsheet import assets
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal, ContainerType, \
    FactsType, RenderingHints, ModelEntryContainerType, AllowedDefinitionType, FormatType, Icon, Color, Phases
from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type
from ibm_aigov_facts_client.utils.cell_facts import CellFactsMagic

from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.constants import get_cloud_url

from ibm_aigov_facts_client.factsheet.approaches import ApproachUtilities
from ibm_aigov_facts_client.factsheet.html_parser import FactHTMLParser

_logger = logging.getLogger(__name__)


class ModelUsecaseUtilities:
    """
        Model use case utilities. Running `client.assets.model_usecase()` makes all methods in ModelUsecaseUtilities object available to use.

    """

    def __init__(self, assets_client: 'assets.Assets', model_id: str = None, model_usecase_id: str = None,
                 container_type: str = None, container_id: str = None, facts_type: str = None) -> None:
        """
        Initialize a ModelUsecaseUtilities object.

        """

        self._asset_id = model_usecase_id
        self._container_type = container_type
        self._container_id = container_id
        self._facts_type = facts_type

        self._assets_client = assets_client

        self._facts_client = assets_client._facts_client
        self._is_cp4d = assets_client._is_cp4d
        self._external_model = assets_client._external_model

        self.associated_workspaces = []

        if self._is_cp4d:
            self._cpd_configs = assets_client._cpd_configs
            self._cp4d_version = assets_client._cp4d_version

   

        self._facts_definitions = self._get_fact_definitions()

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ModelUsecaseUtilities':
        """Initialize a ModelUsecaseUtilities object from a json dictionary."""
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
            _dict['model_usecase_id'] = self._asset_id
        if hasattr(self, '_container_type') and self._container_type is not None:
            _dict['container_type'] = self._container_type
        if hasattr(self, '_container_id') and self._container_id is not None:
            _dict['catalog_id'] = self._container_id
        if hasattr(self, '_facts_type') and self._facts_type is not None:
            _dict['facts_type'] = self._facts_type

        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ModelUsecaseUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this ModelUsecaseUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def _get_fact_definitions(self) -> Dict:
        """
            Get all facts definitions

            :rtype: dict

            A way you might use me is:

            >>> model_usecase.get_fact_definitions()

        """

        if (self._facts_type != None):
            if self._is_cp4d:
                url = self._cpd_configs["url"] + \
                      "/v2/asset_types/" + self._facts_type + "?" + \
                          self._container_type + "_id=" + self._container_id
            else:
                if get_env() == 'dev':
                    url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                          "/v2/asset_types/" + self._facts_type + "?" + \
                              self._container_type + "_id=" + self._container_id
                elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                          "/v2/asset_types/" + self._facts_type + "?" + \
                              self._container_type + "_id=" + self._container_id
                else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                          "/v2/asset_types/" + self._facts_type + "?" + \
                              self._container_type + "_id=" + self._container_id

            response = requests.get(url, headers=self._get_headers())   
            if not response.ok:
                raise ClientError(
                    "User facts definitions not found. ERROR {}. {}".format(response.status_code, response.text))
            else:
                return response.json()

    def get_info(self, verbose=False) -> Dict:
        """Get model use case details

        :param verbose: If True, returns additional model details. Defaults to False
        :type verbose: bool, optional
        :rtype: dict

        The way to use me is:

        # >>> get_model_usecase.get_info()
        # >>> get_model_usecase.get_info(verbose=True)

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
                    # url = MODEL_USECASE_PATH.format(
                    #     self._cpd_configs["url"], self._container_id, self._asset_id)
                    url = MODEL_USECASE_PATH.format(
                        base_url, self._container_id, self._asset_id)
                else:
                    url = MODEL_USECASE_PATH.format(
                        base_url, self._container_id, self._asset_id)

                additional_data["name"] = model_name
                if desc:
                    additional_data["description"] = desc
                additional_data["asset_type"] = asset_type
                additional_data["url"] = url
                additional_data.update(cur_metadata)
                return additional_data
            else:
                raise ClientError(
                    "Failed to get additional model use case information. ERROR {}. {}".format(response.status_code,
                                                                                               response.text))
        else:
            return self._to_dict()

    def get_tracked_models(self) -> list:
        """
        Get models tracked in model use case

        :return: physical model details for all models in model use case
        :rtype: list[dict]
        """
        get_assets_url = self._get_tracked_models_url(
            self._asset_id, self._container_type, self._container_id)
        assets_data = requests.get(get_assets_url, headers=self._get_headers())
        if assets_data.status_code==200:
            get_models = assets_data.json().get('physical_models')
            return get_models
        else:
            raise ClientError(
                "Failed to get tracked models. ERROR {}. {}".format(assets_data.status_code, assets_data.text))

    def set_custom_fact(self, fact_id: str, value: Any) -> None:
        """
            Set custom fact by given id.

            :param str fact_id: Custom fact id.
            :param any value: Value of custom fact. It can be string, integer, date. if custom fact definition attribute `is_array` is set to `True`, value can be a string or list of strings.

            A way you might use me is:

            >>> model_usecase.set_custom_fact(fact_id="custom_int",value=50)
            >>> model_usecase.set_custom_fact(fact_id="custom_string",value="test")
            # allowed if attribute property `is_array` is true.
            >>> model_usecase.set_custom_fact(fact_id="custom_string",value=["test","test2"])

        """

        # if not value or value=='':
        #    raise ClientError("Value can not be empty")

        url = self._get_url_by_factstype_container()

        attr_is_array = self._get_fact_definition_properties(
            fact_id).get("is_array")
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
            response = requests.patch(url, data=json.dumps(
                body), headers=self._get_headers())

            if not response.status_code == 200:
                raise ClientError(
                    "Patching array type values failed. ERROR {}. {}".format(response.status_code, response.text))

            op = REPLACE

        body = [
            {
                "op": op,
                "path": path,
                "value": value
            }
        ]

        response = requests.patch(url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 200:
            _logger.info(
                "Custom fact {} successfully set to new value {}".format(fact_id, value))

        elif response.status_code == 404:
            url = self._get_assets_attributes_url()

            body = {
                "name": self._facts_type,
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
            raise ClientError(
                "Failed to add custom fact {}. ERROR: {}. {}".format(fact_id, response.status_code, response.text))

    def set_custom_facts(self, facts_dict: Dict[str, Any]) -> None:
        """
            Set multiple custom facts.

            :param dict facts_dict: Multiple custom facts. Example: {id: value, id1: value1, ...}

            A way you might use me is:

            >>> model_usecase.set_custom_facts({"fact_1": 2, "fact_2": "test", "fact_3":["data1","data2"]})

        """

        url = self._get_url_by_factstype_container()

        body = []

        for key, val in facts_dict.items():

            attr_is_array = self._get_fact_definition_properties(
                key).get("is_array")
            value_type_array = (type(val) is not str and isinstance(
                val, collections.abc.Sequence))

            self._type_check_by_id(key, val)

            path = "/" + key
            op = ADD

            if (attr_is_array and value_type_array) or value_type_array:
                tmp_body = {
                    "op": op,
                    "path": path,
                    "value": "[]"
                }

                body.append(tmp_body)
                op = REPLACE

            v = {
                "op": op,  # "replace",
                "path": path,
                "value": val
            }

            body.append(v)

        response = requests.patch(url, data=json.dumps(
            body), headers=self._get_headers())
        if response.status_code == 200:
            _logger.info("Custom facts {} successfully set to values {}".format(list(facts_dict.keys()),
                                                                                list(facts_dict.values())))

        elif response.status_code == 404:

            url = self._get_assets_attributes_url()

            body = {
                "name": self._facts_type,
                "entity": facts_dict
            }

            response = requests.post(url, data=json.dumps(
                body), headers=self._get_headers())
            if response.status_code == 201:
                _logger.info("Custom facts {} successfully set to values {}".format(list(facts_dict.keys()),
                                                                                    list(facts_dict.values())))
            else:
                _logger.error("Something went wrong. ERROR {}.{}".format(
                    response.status_code, response.text))

        else:
            raise ClientError(
                "Failed to add custom facts. ERROR: {}-{}".format(response.status_code, response.text))
    


    def set_new_owner(self,owner_iam_id: str) -> str:
        """
        Assign a new owner to the AI use case model.

        Args:
            owner_iam_id (str): IAM ID of the new owner (e.g., IBMid0).

        Returns:
            str: Response JSON on successful owner assignment.

        Raises:
            Exception: If the owner assignment fails.
        """
        if not owner_iam_id:
            raise ClientError("Owner IAM ID cannot be empty")
       
        url = self._get_owner_update_url()
        payload = {"owner_id": str(owner_iam_id)}
        try:
            response = requests.put(url, data=json.dumps(payload), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info(f"Successfully assigned new owner: IAM ID={owner_iam_id}")
            else:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text
                _logger.error(
                    f"Failed to assign new owner: IAM ID={owner_iam_id}, "
                    f"Status code: {response.status_code}, Response: {error_detail}"
                )

        except Exception as e: 
            raise Exception(f"Failed to assign new owner: {e}")
        

    def set_asset_collaborator(self, user_iam_id: str) -> str:
        """
        Adds a collaborator to the asset using the given IAM ID.

        Parameters:
            user_iam_id (str): IAM ID of the user to be added.

        Raises:
            ClientError: If IAM ID is empty.
            Exception: If the request fails.
        """
        if not user_iam_id:
            raise ClientError("User IAM ID cannot be empty")

        url = self._get_asset_collaborator_url()
        payload = [{
            "op": "add",
            "path": f"/metadata/rov/collaborator_ids/{user_iam_id}",
            "value": {"user_iam_id": user_iam_id}
        }]

        try:
            headers = self._get_headers()
            headers["Content-Type"] = "application/json-patch+json"
            response = requests.patch(url, data=json.dumps(payload), headers=headers)
            if response.status_code == 200:
                _logger.info(f"Successfully added IAM ID={user_iam_id} as an asset collaborator")
            else:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text
                _logger.error(
                    f"Failed to add collaborator: IAM ID={user_iam_id}, "
                    f"Status code: {response.status_code}, Response: {error_detail}"
                )
        except Exception as e:
            raise Exception(f"Failed to add collaborator: {e}")

    

    def remove_asset_collaborator(self, user_iam_id: str) -> str:
        """
        Removes a collaborator from the asset using the given IAM ID.

        Parameters:
            user_iam_id (str): IAM ID of the user to be removed.

        Raises:
            ClientError: If IAM ID is empty.
            Exception: If the request fails.
        """
        
        if not user_iam_id:
            raise ClientError("User IAM ID cannot be empty")

        url = self._get_asset_collaborator_url()
        payload = [{
            "op": "remove",
            "path": f"/metadata/rov/collaborator_ids/{user_iam_id}",
            "value": {"user_iam_id": user_iam_id}
        }]

        try:
            headers = self._get_headers()
            headers["Content-Type"] = "application/json-patch+json"
            response = requests.patch(url, json=payload, headers=headers)
            if response.status_code == 200:
                _logger.info(f"Successfully removed IAM ID={user_iam_id} from asset collaborators")
            else:
                try:
                    error_detail = response.json()
                except ValueError:
                    error_detail = response.text
                _logger.error(
                    f"Failed to remove collaborator: IAM ID={user_iam_id}, "
                    f"Status code: {response.status_code}, Response: {error_detail}"
                )
        except Exception as e:
            raise Exception(f"Failed to remove collaborator: {e}")


        

    def _get_owner_update_url(self):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                "/v2/assets/" + self._asset_id + "/owner?" + \
                 "catalog_id=" + self._container_id 
        else:
            env = get_env()
            if env == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    "/v2/assets/" + self._asset_id + "/owner?" + \
                    "catalog_id=" + self._container_id
                
            elif env == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    "/v2/assets/" + self._asset_id + "/owner?" + \
                    "catalog_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    "/v2/assets/" + self._asset_id + "/owner?" + \
                    "catalog_id=" + self._container_id

        return url
    

    def _get_asset_collaborator_url(self):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                "/v1/aigov/inventories/" + self._container_id + "/assets/" + \
                 self._asset_id + "/collaborators"
        else:
            env = get_env()
            if env == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                "/v1/aigov/inventories/" + self._container_id + "/assets/" + \
                 self._asset_id + "/collaborators"
                
            elif env == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                "/v1/aigov/inventories/" + self._container_id + "/assets/" + \
                self._asset_id + "/collaborators"
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                "/v1/aigov/inventories/" + self._container_id + "/assets/" + \
                self._asset_id + "/collaborators"

        return url

            

    def get_custom_fact_by_id(self, fact_id: str):
        """
            Get custom fact value/s by id

            :param str fact_id: Custom fact id to retrieve.

            A way you might use me is:

            >>> model_usecase.get_custom_fact_by_id(fact_id="fact_id")

        """

        url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            fact_details = response.json().get(self._facts_type)
            id_val = fact_details.get(fact_id)
            if not id_val:
                raise ClientError(
                    "Could not find value of fact_id {}".format(fact_id))
            else:
                return id_val

    def get_custom_facts(self) -> Dict:
        """
            Get all defined custom facts for model_entry_user fact type.

            :rtype: dict

            A way you might use me is:

            >>> model_usecase.get_custom_facts()

        """

        url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            user_facts = response.json().get(self._facts_type)
            return user_facts
        else:
            raise ClientError("Failed to get facts. ERROR. {}. {}".format(
                response.status_code, response.text))

    def get_all_facts(self) -> Dict:
        """
            Get all facts related to asset.

            :rtype: dict

            A way you might use me is:

            >>> model_usecase.get_all_facts()

        """

        url = self._get_assets_url(
            self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            raise ClientError("Failed to get facts. ERROR. {}. {}".format(
                response.status_code, response.text))

    def get_facts_by_type(self, facts_type: str = None) -> Dict:
        """
            Get custom facts by asset type.

            :param str facts_type: (Optional) Custom facts asset type.
            :rtype: dict

            A way you might use me is:

            >>> model_usecase.get_facts_by_type(facts_type=<type name>)
            >>> model_usecase.get_facts_by_type() # default to model_entry_user type

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

            >>> model_usecase.remove_custom_fact(fact_id=<fact_id>)

        """

        url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            fact_details = response.json().get(self._facts_type)
            check_val_exists_for_id = fact_details.get(fact_id)
        if not check_val_exists_for_id:
            raise ClientError(
                "Fact id {} is invalid or have no associated value to remove".format(fact_id))

        url = self._get_url_by_factstype_container()

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
            raise ClientError(
                "Could not delete the fact_id {}. ERROR. {}. {}".format(fact_id, response.status_code, response.text))

    def remove_custom_facts(self, fact_ids: List[str]) -> None:
        """
            Remove multiple custom facts ids

            :param list fact_ids: Custom fact ids to remove.

            A way you might use me is:

            >>> model_usecase.remove_custom_facts(fact_ids=["id1","id2"])

        """

        url = self._get_url_by_factstype_container()

        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            fact_details = response.json().get(self._facts_type)

        final_list = []
        for fact_id in fact_ids:
            check_val_exists = fact_details.get(fact_id)
            if check_val_exists:
                final_list.append(fact_id)
            else:
                _logger.info(
                    "Escaping fact_id {} as either it is invalid or have no value to remove".format(fact_id))

        body = []

        if final_list:
            for val in final_list:
                val = {
                    "op": "remove",  # "replace",
                    "path": "/" + val
                }
                body.append(val)

            response = requests.patch(url, data=json.dumps(
                body), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info(
                    "Values of Fact ids {} removed successfully".format(final_list))
            else:
                raise ClientError(
                    "Could not delete the fact_ids. ERROR. {}. {}".format(response.status_code, response.text))
        else:
            raise ClientError("Please use valid id with values to remove")

    def set_attachment_fact(self,
                            file_to_upload,
                            fact_id: str,
                            description: str = None,
                            html_rendering_hint: str = None,
                            allow_large_files: bool = False
                            ) -> None:
        """
        Set attachment fact for given model use case.

        :param str file_to_upload: Attachment file path to upload.
        :param str fact_id: Fact id for the attachment.
        :param str description: (Optional) Description about the attachment file.
        :param str html_rendering_hint: (Optional) HTML rendering hint. Available options are in ibm_aigov_facts_client.utils.enums.RenderingHints.

        A way to use me is:

        >>> model_usecase.set_attachment_fact(file_to_upload="./artifacts/image.png", description="<file description>", fact_id="<custom fact id>")
        >>> model_usecase.set_attachment_fact(file_to_upload="./artifacts/image.png", description="<file description>", fact_id="<custom fact id>", html_rendering_hint="<render hint>")

        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if os.path.exists(file_to_upload):
            file_size = os.stat(file_to_upload).st_size
            # <500MB
            if file_size > MAX_SIZE and not allow_large_files:
                raise ClientError("Maximum file size allowed is 500 MB")
        else:
            raise ClientError("Invalid file path provided")

        if html_rendering_hint:
            validate_enum(html_rendering_hint,
                          "html_rendering_hint", RenderingHints, False)

        # check if have attachment for given fact id. only one attachment allowed per fact_id.
        get_factid_attachment = self.list_attachments(filter_by_factid=fact_id)

        if (self._is_cp4d and self._cp4d_version < "5.1.0") or (aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST, AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}):

            # Attachment for below 5.1.0

            if get_factid_attachment:
                raise ClientError(
                    "Fact id {} already have an attachment set and only allowed to have one. You can remove and set new attachment if needed".format(
                        fact_id))

            else:
                # create attachment

                mimetype = self._get_mime(file_to_upload)

                attachment_url = self._get_url_attachments(
                    model_asset_id, model_container_type, model_container_id)

                base_filename = os.path.basename(file_to_upload)

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
                            "Invalid inline HTML content: Attachments content to be rendered as inline_html is NOT allowed to contain any of the following HTML tags: {}".format(
                                list(restricted_tags.split(" "))))

                # convert png to jpeg
                flag = False
                if mimetype == "image/png":
                    from PIL import Image

                    ima = Image.open(file_to_upload)
                    rgb_im = ima.convert('RGB')
                    rgb_im.save(os.path.splitext(file_to_upload)
                                [0] + ".jpg", format='JPEG')
                    mimetype = "image/jpeg"
                    base_filename = os.path.splitext(file_to_upload)[0] + ".jpg"
                    file_to_upload = base_filename
                    flag = True

                attachment_data = {}

                if fact_id:
                    attachment_data["fact_id"] = fact_id
                if html_rendering_hint:
                    attachment_data["html_rendering_hint"] = html_rendering_hint
            
                # Ensure description is not None
                description = description if description else ""

                body = "{ \"asset_type\": \"" + self._facts_type + "\" \
                        , \"name\": \"" + base_filename + "\",\"mime\": \"" + mimetype \
                    + "\",\"data_partitions\" : 0,\"private_url\": \"false\",\"is_partitioned\": \"false\",\"description\": \"" \
                    + description + "\",\"user_data\": " + \
                        json.dumps(attachment_data) + "}"

                create_attachment_response = requests.post(
                    attachment_url, data=body, headers=self._get_headers())

                if create_attachment_response.status_code == 400:
                    url = self._get_assets_attributes_url()

                    body = {
                        "name": self._facts_type,
                        "entity": {}
                    }

                    response = requests.post(url, data=json.dumps(
                        body), headers=self._get_headers())

                    if response.status_code == 201:
                        create_attachment_response = requests.post(
                            attachment_url, data=body, headers=self._get_headers())
                    else:
                        raise ClientError(
                            "Failed to initiate {} attribute. ERROR {}. {}".format(self._facts_type, response.status_code,
                                                                                response.text))

                if create_attachment_response.status_code == 201:
                    get_upload_uri = create_attachment_response.json().get("url1")
                    if not get_upload_uri:
                        raise ClientError("Upload url not found")
                else:
                    raise ClientError(
                        "Failed to create attachment URL. ERROR {}. {}".format(create_attachment_response.status_code,
                                                                            create_attachment_response.text))

                if self._is_cp4d:
                    get_upload_uri = self._cpd_configs["url"] + get_upload_uri

                attachment_id = create_attachment_response.json()["attachment_id"]

                # upload file

                if self._is_cp4d:
                    files = {'file': (file_to_upload, open(
                        file_to_upload, 'rb').read(), mimetype)}
                    response_update = requests.put(get_upload_uri, files=files)

                else:
                    # headers=self._get_headers()
                    with open(file_to_upload, 'rb') as f:
                        data = f.read()
                        response_update = requests.put(get_upload_uri, data=data)

                if response_update.status_code == 201 or response_update.status_code == 200:
                    # complete attachment
                    completion_url = self._get_url_attachments(model_asset_id, model_container_type, model_container_id,
                                                            attachment_id, action="complete")
                    completion_response = requests.post(
                        completion_url, headers=self._get_headers())

                    if completion_response.status_code == 200:

                        # get attachment info
                        get_attachmentUrl = self._get_url_attachments(model_asset_id, model_container_type,
                                                                    model_container_id, attachment_id, mimetype,
                                                                    action="get")

                        if (mimetype.startswith("image/") or mimetype.startswith("application/pdf")
                                or mimetype.startswith("text/html")):
                            get_attachmentUrl += '&response-content-disposition=inline;filename=' + file_to_upload

                        else:
                            get_attachmentUrl += '&response-content-disposition=attachment;filename=' + file_to_upload

                        response_get = requests.get(
                            get_attachmentUrl, headers=self._get_headers())


                        if response_get.status_code == 200:
                            _logger.info("Attachment uploaded successfully")
                            #removing url due to new revised change

                            # if self._is_cp4d:
                            #     url = self._cpd_configs["url"] + \
                            #         response_get.json().get("url")
                            
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
                            
                            # else:
                            #     _logger.info("Attachment uploaded successfully")
                            if flag:
                                os.remove(file_to_upload)
                        else:
                            raise ClientError(
                                "Could not fetch attachment url. ERROR {}. {}".format(response_get.status_code,
                                                                                    response_get.text))

                    else:
                        raise ClientError(
                            "Failed to mark attachment as complete. ERROR {}. {} ".format(completion_response.status_code,
                                                                                        completion_response.text))

                else:
                    raise ClientError("Failed to upload file using URI {}. ERROR {}. {}".format(get_upload_uri,
                                                                                                response_update.status_code,
                                                                                                response_update.text))
        
        else:
                
            # Large Attachment for above 5.1.0

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

                        attachment_url = self._get_url_attachments_new(
                            asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id)
                        
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
                            mimetype = "image/jpg"
                            base_filename = os.path.splitext(base_filename)[0] + ".jpg"
                            file_to_upload = os.path.splitext(file_to_upload)[0] + ".jpg"

                        attachment_data = {}

                        if fact_id:
                            attachment_data["fact_id"] = fact_id
                        if html_rendering_hint:
                            attachment_data["html_rendering_hint"] = html_rendering_hint

                        with open(file_to_upload, "rb") as file:
                            body=file.read()

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

    def set_cell_attachment_fact(self, description: str, fact_id: str) -> None:
        """
        Set attachment fact using captured cell output. Supported for CPD version >=4.6.5.

        :param str fact_id: Fact id for the attachment
        :param str description: (Optional) Description about the cell facts attachment file

        A way to use me is:

        .. code-block:: python

            model_usecase.set_cell_attachment_fact(description='<file description>', fact_id='<custom fact id>')
        """


        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        file_to_upload = "{}/{}/{}".format(os.getcwd(),
                                           CELL_FACTS_TMP_DIR, CellFactsMagic._fname)

        if not os.path.exists(file_to_upload):
            raise ClientError(
                "Invalid file path. Failed to find {}".format(CellFactsMagic._fname))

        # check if have attachment for given fact id. only one attachment allowed per fact_id.
        get_factid_attachment = self.list_attachments(filter_by_factid=fact_id)

        if (self._is_cp4d and self._cp4d_version < "5.1.0") or (aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST,AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}):

            # Attachment for below 5.1.0

            if get_factid_attachment:
                raise ClientError(
                    "Fact id {} already have an attachment set and only allowed to have one. You can remove and set new attachment if needed".format(
                        fact_id))

            else:
                # create attachment

                mimetype = self._get_mime(file_to_upload)

                attachment_url = self._get_url_attachments(
                    model_asset_id, model_container_type, model_container_id)

                base_filename = os.path.basename(file_to_upload)

                attachment_data = {}

                if fact_id:
                    attachment_data["fact_id"] = fact_id
                attachment_data["html_rendering_hint"] = "inline_html"
                
                description = description if description else ""

                body = "{ \"asset_type\": \"" + self._facts_type + "\" \
                        , \"name\": \"" + base_filename + "\",\"mime\": \"" + mimetype \
                    + "\",\"data_partitions\" : 0,\"private_url\": \"false\",\"is_partitioned\": \"false\",\"description\": \"" \
                    + description + "\",\"user_data\": " + \
                        json.dumps(attachment_data) + "}"

                create_attachment_response = requests.post(
                    attachment_url, data=body, headers=self._get_headers())

                if create_attachment_response.status_code == 400:
                    url = self._get_assets_attributes_url()

                    body = {
                        "name": self._facts_type,
                        "entity": {}
                    }

                    response = requests.post(url, data=json.dumps(
                        body), headers=self._get_headers())

                    if response.status_code == 201:
                        create_attachment_response = requests.post(
                            attachment_url, data=body, headers=self._get_headers())
                    else:
                        raise ClientError(
                            "Failed to initiate {} attribute. ERROR {}. {}".format(self._facts_type, response.status_code,
                                                                                response.text))

                if create_attachment_response.status_code == 201:
                    get_upload_uri = create_attachment_response.json().get("url1")
                    if not get_upload_uri:
                        raise ClientError("Upload url not found")
                else:
                    raise ClientError(
                        "Failed to create attachment URL. ERROR {}. {}".format(create_attachment_response.status_code,
                                                                            create_attachment_response.text))

                if self._is_cp4d:
                    get_upload_uri = self._cpd_configs["url"] + get_upload_uri

                attachment_id = create_attachment_response.json()["attachment_id"]

                # upload file

                if self._is_cp4d:
                    files = {'file': (file_to_upload, open(
                        file_to_upload, 'rb').read(), mimetype)}
                    response_update = requests.put(get_upload_uri, files=files)

                else:
                    # headers=self._get_headers()
                    with open(file_to_upload, 'rb') as f:
                        data = f.read()
                        response_update = requests.put(get_upload_uri, data=data)

                if response_update.status_code == 201 or response_update.status_code == 200:

                    # complete attachment
                    completion_url = self._get_url_attachments(model_asset_id, model_container_type, model_container_id,
                                                            attachment_id, action="complete")
                    completion_response = requests.post(
                        completion_url, headers=self._get_headers())

                    if completion_response.status_code == 200:

                        # get attachment info
                        get_attachmentUrl = self._get_url_attachments(model_asset_id, model_container_type,
                                                                    model_container_id, attachment_id, mimetype,
                                                                    action="get")

                        get_attachmentUrl += '&response-content-disposition=inline;filename=' + file_to_upload

                        response_get = requests.get(
                            get_attachmentUrl, headers=self._get_headers())

                        if response_get.status_code == 200:
                            if self._is_cp4d:
                                url = self._cpd_configs["url"] + \
                                    response_get.json().get("url")
                                _logger.info(
                                    "Cell facts attachment uploaded successfully and access url (15min valid) is - {}".format(
                                        url))
                            else:
                                _logger.info(
                                    "Cell facts attachment uploaded successfully and access url (15min valid) is - {}".format(
                                        response_get.json().get("url")))

                            os.remove(file_to_upload)
                        else:
                            raise ClientError(
                                "Could not fetch attachment url. ERROR {}. {}".format(response_get.status_code,
                                                                                    response_get.text))

                    else:
                        raise ClientError(
                            "Failed to mark attachment as complete. ERROR {}. {} ".format(completion_response.status_code,
                                                                                        completion_response.text))

                else:
                    raise ClientError("Failed to upload file using URI {}. ERROR {}. {}".format(get_upload_uri,
                                                                                                response_update.status_code,
                                                                                                response_update.text))
        else:

            # Large Attachment for above 5.1.0

            if get_factid_attachment:
                raise ClientError(
                    "Fact id {} already have an attachment set and only allowed to have one. You can remove and set new attachment if needed".format(fact_id))
            
            else:

                try:
                    # create attachment

                    mimetype = self._get_mime(file_to_upload)

                    #base_filename = os.path.basename(file_to_upload)
                    base_filename_before = os.path.basename(file_to_upload)
                    base_filename = urllib.parse.quote(base_filename_before)
                    file_name, _ = os.path.splitext(base_filename)
                    # description = urllib.parse.quote(description)
                    if description:
                        description = urllib.parse.quote(description)
                    else:
                        description = "" 

                    attachment_url = self._get_url_attachments_new(
                        asset_id=model_asset_id,container_id=model_container_id, container_type=model_container_type, name=base_filename, description=description, mimetype=mimetype, fact_id=fact_id)

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

                    with open(file_to_upload, "rb") as file:
                        body=file.read()

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

    def has_attachment(self, fact_id: str = None) -> bool:
        """ Check if attachment/s exist. Supported for CPD version >=4.6.5

        :param fact_id: Id of attachment fact
        :type fact_id: str, optional

        :rtype: bool

        The way to use me is :

        >>> model_usecase.has_attachment()
        >>> model_usecase.has_attachment(fact_id=<fact id>)

        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

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
            List available attachment facts. Supported for CPD version >=4.6.5.

            :param str filter_by_factid: (Optional) Fact id for the attachment to filter by.
            :param str format: Result output format ('dict' or 'str'). Defaults to 'dict'.

            A way to use me is:

            Use this format if using output for `set_custom_fact()`:

            .. code-block:: python

                model_usecase.list_attachments(format="str")
                model_usecase.list_attachments()  # Get all attachment facts
                # Filter by associated fact_id_1.
                model_usecase.list_attachments(filter_by_factid="fact_id_1")
        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        url = self._get_assets_url(
            model_asset_id, model_container_type, model_container_id)

        response = requests.get(url, headers=self._get_headers())
        all_attachments = response.json().get(ATTACHMENT_TAG)
        results = []
        if all_attachments:
            attachments = [i for i in all_attachments if i.get('asset_type') == self._facts_type and (
                    filter_by_factid == None or filter_by_factid == i.get("user_data").get("fact_id"))]

            for a in attachments:
                if format == FormatType.STR:

                    get_url = self._get_attachment_download_url(model_asset_id, model_container_type,
                                                                model_container_id, a.get(
                                                                    "id"), a.get("mime"),
                                                                a.get("name"))
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

                        if a.get("user_data").get("html_rendering_hint"):
                            attachment_dict["html_rendering_hint"] = a.get(
                                "user_data").get("html_rendering_hint")
                   
                    #commenting due to new revised adobe changes

                    # get_url = self._get_attachment_download_url(model_asset_id, model_container_type,
                    #                                             model_container_id, a.get(
                    #                                                 "id"), a.get("mime"),
                    #                                             a.get("name"))
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
            >>> url = ai_usecase.get_download_URL(attachment_id="12345")
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
            Remove available attachments facts for given id. Supported for CPD version >=4.6.5

            :param str fact_id:  Fact id of the attachment

            A way to use me is:

            >>> model_usecase.remove_attachment(fact_id=<fact id of attachment>)


        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        get_attachment = self.list_attachments(filter_by_factid=fact_id)

        if get_attachment:
            get_id = get_attachment[0].get("attachment_id")
            del_url = self._get_url_attachments(model_asset_id, model_container_type, model_container_id, get_id,
                                                action="del")
            response = requests.delete(del_url, headers=self._get_headers())
            if response.status_code == 204:
                _logger.info(
                    "Deleted attachment for fact id: {} successfully".format(fact_id))
            else:
                _logger.error(
                    "Failed to delete attachment for fact id: {}. ERROR {}. {}".format(fact_id, response.status_code,
                                                                                       response.text))
        else:
            raise ClientError(
                "No valid attachment found related to fact id {}".format(fact_id))

    def remove_all_attachments(self):
        """
            Remove all attachments facts for given asset. Supported for CPD version >=4.6.5


            A way to use me is:

            >>> model_usecase.remove_all_attachments()


        """

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Attachment functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        url = self._get_assets_url(
            model_asset_id, model_container_type, model_container_id)

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
                del_url = self._get_url_attachments(model_asset_id, model_container_type, model_container_id, id,
                                                    action="del")
                response = requests.delete(
                    del_url, headers=self._get_headers())
                if response.status_code == 204:
                    _logger.info(
                        "Deleted attachment id {} successfully".format(id))
                else:
                    _logger.error("Could not delete attachment id {}. ERROR {}. {}".format(id, response.status_code,
                                                                                           response.text))
            _logger.info("All attachments deleted successfully")

    # ====================================utils==========================================
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
    
    def _get_tracked_models_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                  '/v1/aigov/model_inventory/model_entries/' + asset_id + '/models' +'?' + container_type + '_id=' + container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                  '/v1/aigov/model_inventory/model_entries/' + asset_id + '/models' +'?' + container_type + '_id=' + container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                  '/v1/aigov/model_inventory/model_entries/' + asset_id + '/models' +'?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                  '/v1/aigov/model_inventory/model_entries/' + asset_id + '/models' +'?' + container_type + '_id=' + container_id

        return url



    # def _get_factsheet_attachments_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):
    #
    #     # if self._is_cp4d:
    #     #     url = self._cpd_configs["url"] + \
    #     #           '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
    #     # else:
    #     #     if get_env() == 'dev':
    #     #         url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
    #     #               '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
    #     #     elif get_env() == 'test':
    #     #         url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
    #     #               '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
    #     #     else:
    #     #         url = prod_config["DEFAULT_SERVICE_URL"] + \
    #     #               '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
    #     if self._is_cp4d:
    #         url = self._cpd_configs["url"] + \
    #               '/v1/aigov/model_inventory/ai_usecases/' + model_usecase_id + \
    #               '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
    #
    #     else:
    #         if get_env() == 'dev':
    #             url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
    #                   '/v1/aigov/model_inventory/ai_usecases/' + model_usecase_id + \
    #                   '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
    #         elif get_env() == 'test':
    #             url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
    #                   '/v1/aigov/model_inventory/ai_usecases/' + model_usecase_id + \
    #                   '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
    #         else:
    #             url = prod_config["DEFAULT_SERVICE_URL"] + \
    #                   '/v1/aigov/model_inventory/ai_usecases/' + model_usecase_id + \
    #                   '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
    #     return url
    def _get_fact_definition_properties(self, fact_id):

        if self._facts_definitions:
            props = self._facts_definitions.get(PROPERTIES)
            props_by_id = props.get(fact_id)
        else:
            data = self._get_fact_definitions()
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
            _logger.info("Asset container updated successfully")
        else:
            raise ClientError(
                "Could not update asset container. ERROR {}. {}".format(response.status_code, response.text))

    def _get_mime(self, file):
        # pip install python-magic
        # On a Mac you may also have to run a "brew install libmagic"
        import magic
        mime = magic.Magic(mime=True)
        magic_mimetype_result = mime.from_file(file)
        # sometimes we need to post-correct where the magic result is just not
        # for csv
        if file.endswith(".csv") and not magic_mimetype_result.endswith("/csv"):
            return "text/csv"
        
        # for excel (both .xls and .xlsx)
        if file.endswith(".xlsx") and not magic_mimetype_result == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        if file.endswith(".xls") and not magic_mimetype_result == "application/vnd.ms-excel":
            return "application/vnd.ms-excel"
        
        if file.lower().endswith((".jpg", ".jpeg")) and magic_mimetype_result.strip() != "image/jpeg":
            return "image/jpeg"

        if file.lower().endswith(".docx"):
            #return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            #return "application/docx"
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # for HTML
        if file.endswith(".html") and not magic_mimetype_result.endswith("/html"):
            return "text/html"
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

    def _get_url_by_factstype_container(self):

        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/v2/assets/' + self._asset_id + "/attributes/" + \
                  self._facts_type + "?" + self._container_type + "_id=" + self._container_id

        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v2/assets/' + self._asset_id + "/attributes/" + \
                      self._facts_type + "?" + self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v2/assets/' + self._asset_id + "/attributes/" + \
                      self._facts_type + "?" + self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v2/assets/' + self._asset_id + "/attributes/" + \
                      self._facts_type + "?" + self._container_type + "_id=" + self._container_id

        return url

    def _get_url_sysfacts_container(self, asset_id: str = None, container_type: str = None, container_id: str = None,
                                    key: str = FactsType.MODEL_FACTS_SYSTEM):

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
    
    # Attachment url for below 5.1 CPD version
    def _get_url_attachments(self, asset_id: str, container_type: str, container_id: str, attachment_id: str = None,
                             mimetype: str = None, action: str = None):

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
    
    # Large Attachment url for above 5.1 CPD version
    def _get_url_attachments_new(self, asset_id: str, container_id: str, container_type: str, name: str = None,
                                   description: str = None, mimetype: str = None, fact_id: str = None,
                                   html_rendering_hint:str=None):
            if html_rendering_hint :
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id +'&html_rendering_hint='+html_rendering_hint
                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&html_rendering_hint='+html_rendering_hint
                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&html_rendering_hint='+html_rendering_hint
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id + '&html_rendering_hint='+html_rendering_hint
            else:
                if self._is_cp4d:
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                          '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/model_entries/large_attachment/' + asset_id + f'/content?{container_type}_id=' + container_id + \
                              '&name=' + name + '&description=' + description + '&mime=' + mimetype + '&fact_id=' + fact_id
            return url

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

    # Commenting below 2 methods based on this defect  https://github.ibm.com/wdp-gov/tracker/issues/126147

    # def modify_approach_or_version_of_model(self,approach_id:str=None,version_number:str=None,target_approach_id:str=None,target_version_number:str=None,target_version_comment:str=None):

    #     """
    #         Returns WKC Model usecase updated approach. Supported for CPD version >=4.7.0

    #         :param str approach_id: Name of approach
    #         :param str version_number: Version number of the model
    #         :param str target_approach_id: Target approach ID
    #         :param str target_version_number: Target version number
    #         :param str target_version_comment: Target version comment

    #         :rtype: None

    #         :return: WKC Model usecase approache is modified

    #         Example:
    #         >>> client.assets.model_usecase.modify_approach_or_version_of_model(approach_id=<approach_id>,version_number=<version_number>,target_approach_id=<target_approach_id>,target_version_number=<target_version_number>,target_version_comment=<target_version_comment>)
    #     """

    #     if self._is_cp4d and self._cp4d_version < "4.7.0":
    #         raise ClientError("Version mismatch: Model usecase, modify approach or version of model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

    #     if (approach_id is None or approach_id == ""):
    #         raise MissingValue("approach_id", "approach ID is missing")
    #     if (version_number is None or version_number == ""):
    #         raise MissingValue("version_number", "version number is missing")
    #     if (target_approach_id is None or target_approach_id == ""):
    #         raise MissingValue("target_approach_id", "target approach ID is missing")
    #     if (target_version_number is None or target_version_number == ""):
    #         raise MissingValue("target_version_number", "target version number is missing")

    #     model_asset_id=self._asset_id
    #     model_container_id= self._container_id

    #     if target_approach_id:
    #         body= {
    #                 "target_approach_id": target_approach_id,
    #                 "target_version_number": target_version_number,
    #                 "target_version_comment": target_version_comment
    #             }
    #     else:
    #         raise ClientError("Provide target approach ID")

    #     url=self._get_approach_url(model_asset_id,model_container_id,approach_id,version_number,operation="put")

    #     response = requests.put(url,data=json.dumps(body), headers=self._get_headers())

    #     if response.status_code ==200:
    #         _logger.info("Approach or version of model updated successfully")
    #         return response
    #     else:
    #         raise ClientError("Failed while updating an approach or version of model. ERROR {}. {}".format(response.status_code,response.text))

    # def update_approach(self,approach_id:str=None,new_approach_name:str=None,new_approach_description:str=None):

    #     """
    #         Returns WKC Model usecase updated approach. Supported for CPD version >=4.7.0

    #         :param str approach_id: Name of approach
    #         :param str new_approach_name: New name for approach
    #         :param str new_approach_description: New description for approach

    #         :rtype: None

    #         :return: WKC Model usecase approache is updated

    #         Example:
    #         >>> client.assets.model_usecase.remove_approach(approach_id=<approach_id>,new_approach_name=<new_approach_name>,new_approach_description=<new_approach_description>)
    #     """

    #     if self._is_cp4d and self._cp4d_version < "4.7.0":
    #         raise ClientError("Version mismatch: Model usecase, update approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

    #     if (approach_id is None or approach_id == ""):
    #         raise MissingValue("approach_id", "approach ID is missing")
    #     if (new_approach_name is None or new_approach_name == ""):
    #         raise MissingValue("new_approach_name", "New approach name is missing")
    #     if (new_approach_description is None or new_approach_description == ""):
    #         raise MissingValue("new_approach_description", "New approach description is missing")

    #     model_asset_id=self._asset_id
    #     model_container_id= self._container_id

    #     if new_approach_name:
    #         body= [
    #             {
    #                 "op": "add",
    #                 "path": "/name",
    #                 "value": new_approach_name
    #             },
    #             {
    #                 "op": "add",
    #                 "path": "/description",
    #                 "value": new_approach_description
    #             }
    #             ]
    #     else:
    #         raise ClientError("Provide approach name")

    #     url=self._get_approach_url(model_asset_id,model_container_id,approach_id,operation="patch")

    #     response = requests.patch(url,data=json.dumps(body), headers=self._get_headers())

    #     if response.status_code ==200:
    #         _logger.info("Approach updated successfully")
    #         return response.json()
    #     else:
    #         raise ClientError("Failed while updating an approach. ERROR {}. {}".format(response.status_code,response.text))

    def remove_approach(self, approach: ApproachUtilities = None):
        """
            Returns WKC Model usecase removed approach. Supported for CPD version >=4.7.0

            :param ApproachUtilities approach: Object or instance of ApproachUtilities

            :rtype: None

            :return: WKC Model usecase approach is removed

            Example,::

                ai_usecase.remove_approach(approach=ApproachUtilities)
        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model usecase, remove approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is " + self._cp4d_version)

        if (approach is None or approach == ""):
            raise MissingValue(
                "approach", "ApproachUtilities object or instance is missing")

        if (not isinstance(approach, ApproachUtilities)):
            raise ClientError("Provide ApproachUtilities object for approach")

        approach_id = approach.get_id()
        if (approach_id == "00000000-0000-0000-0000-000000000000"):
            _logger.info("Can't delete default approach ")
        else:
            model_asset_id = self._asset_id
            model_container_id = self._container_id

            url = self._get_approach_url(
                model_asset_id, model_container_id, approach_id, operation="delete")

            response = requests.delete(url, headers=self._get_headers())

            if response.status_code == 204:
                _logger.info("Approach removed successfully")
            else:
                raise ClientError(
                    "Failed in removing an approach. ERROR {}. {}".format(response.status_code, response.text))

    # def create_approach(self,name:str=None,description:str=None)->ApproachUtilities:
    def create_approach(self, name: str = None, description: str = None, icon: str = None,
                        color: str = None) -> ApproachUtilities:
        """
            Returns WKC Model usecase approach. Supported for CPD version >=4.7.0

            :param str name: Name of approach
            :param str description: (Optional) Description of approach
            :param str icon: (Optional) Approach's icon
            :param str color: (Optional) Approach's color
            :rtype: ApproachUtilities

            :return: WKC Model usecase approach

            Example:
            # >>> client.assets.model_usecase.create_approach(name=<approach name>,description=<approach description>)
            # >>> client.assets.model_usecase.create_approach(name=<approach name>)

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model usecase, create approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if (name is None or name == ""):
            raise MissingValue("name", "approach name is missing")
        # changes added by Lakshmi to accept icon and color from user else use defaults
        if not (icon is None or icon == ""):
            validate_enum(icon, "Icon", Icon, False)
        else:
            icon = "Packages"
        if not (color is None or color == ""):
            validate_enum(color, "Color", Color, False)
        else:
            color = "Gray"

        if name:
            body = {
                "name": name,
                "description": description,
                # "icon": "Packages",
                # "icon_color": "Gray"
                # Lakshmi commented the above 2 lines and added the below 2 lines
                "icon": icon,
                "icon_color": color
            }
        else:
            raise ClientError("Provide approach name")

        url = self._get_approach_url(
            model_asset_id, model_container_id, operation="post")
        response = requests.post(url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("Approach created successfully")
            ret_create_approach = response.json()
            return ApproachUtilities(self, approach_id=ret_create_approach.get('id'),
                                     approach_name=ret_create_approach.get(
                                         'name'),
                                     approach_desc=ret_create_approach.get(
                                         'description'),
                                     approach_icon=ret_create_approach.get(
                                         'icon'),
                                     approach_icon_color=ret_create_approach.get(
                                         'icon_color'),
                                     model_asset_id=model_asset_id, model_container_type=model_container_type,
                                     model_container_id=model_container_id)
            # return response.json()
        else:
            raise ClientError(
                "Failed while creating an approach. ERROR {}. {}".format(response.status_code, response.text))

    def get_approaches(self) -> list:
        """
            Returns list of WKC Model usecase approaches. Supported for CPD version >=4.7.0

            :return: All WKC Model usecase approaches
            :rtype: list(ApproachUtilities)

            Example::

               ai_usecase.get_approaches()

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model usecase, retrieve approaches functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is " + self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        url = self._get_approach_url(
            model_asset_id, model_container_id, operation="get")
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("Approaches retrieved successfully")
            approaches_list = response.json()["approaches"]
            approach_list_values = []
            for approach in approaches_list:
                op_id = approach.get('op_id', None)
                approach_list_values.append(
                    ApproachUtilities(self, approach_id=approach.get('id'), approach_name=approach.get('name'),
                                      approach_desc=approach.get('description'), approach_icon=approach.get('icon'),
                                      approach_icon_color=approach.get('icon_color'), versions=approach.get('versions'),
                                      model_asset_id=model_asset_id, model_container_type=model_container_type,
                                      model_container_id=model_container_id,
                                      op_id=op_id))
            return approach_list_values
        else:
            raise ClientError(
                "Failed in retrieving an approach. ERROR {}. {}".format(response.status_code, response.text))

    def get_approach(self, approach_id: str = None) -> ApproachUtilities:
        """
            Returns WKC Model usecase approaches. Supported for CPD version >=4.7.0

            :param str approach_id: Approach ID

            :rtype: ApproachUtilities

            :return:  Specific WKC Model usecase approach


            Example,::

                ai_usecase.get_approach(approach_id=<approach_id>)

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model usecase, retrieve approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is " + self._cp4d_version)

        if (approach_id is None or approach_id == ""):
            raise MissingValue("approach_id", "approach ID is missing")

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        url = self._get_approach_url(
            model_asset_id, model_container_id, operation="get")
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            approaches_list = response.json()["approaches"]
            
            _is_approach_exists = False
            for approach in approaches_list:
                if approach.get('id') == approach_id:
                    _is_approach_exists = True
                    _logger.info("Approach retrieved successfully")
                    op_id = approach.get('op_id', None)
                    return ApproachUtilities(self, approach_id=approach.get('id'), approach_name=approach.get('name'),
                                             approach_desc=approach.get(
                                                 'description'),
                                             approach_icon=approach.get(
                                                 'icon'),
                                             approach_icon_color=approach.get(
                                                 'icon_color'),
                                             versions=approach.get('versions'), model_asset_id=model_asset_id,
                                             model_container_type=model_container_type,
                                             model_container_id=model_container_id,
                                             op_id=op_id)
            if not _is_approach_exists:
                raise ClientError(
                    "Approach " + approach_id + " is not available.")
        else:
            raise ClientError(
                "Failed in retrieving an approach. ERROR {}. {}".format(response.status_code, response.text))

    def _get_approach_url(self, model_usecase_asset_id: str = None, catalog_id: str = None, approach_id: str = None,
                          version_number: str = None, operation: str = None):

        if operation == 'post':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + \
                model_usecase_asset_id + '/version_approach?catalog_id=' + catalog_id
        elif operation == 'get':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + \
                model_usecase_asset_id + '/tracked_model_versions?catalog_id=' + catalog_id
        elif operation == 'delete' or operation == 'patch':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + \
                '/version_approach/' + approach_id + '?catalog_id=' + catalog_id
        elif operation == 'put':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + \
                '/version_approach/' + approach_id + '/versions/' + \
                    version_number + '?catalog_id=' + catalog_id
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

    def get_grc_models(self) -> list:
        """
            Returns list of WKC Models associated with Openpages for a particular model usecase

            :return: All WKC Models associated with Openpages for a particular model usecase
            :rtype: list()

            Example,::

               client.assets.model_usecase.get_grc_models()

        """

        modelusecase_asset_id = self._asset_id
        model_container_type = self._container_type
        modelusecase_catalog_id = self._container_id

        # if self._is_cp4d and self._cp4d_version < "4.7.0":
        #    raise ClientError("Version mismatch: models associated for a particular Model usecase in Openpages functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if (modelusecase_asset_id is None or modelusecase_asset_id == ""):
            raise MissingValue("modelusecase_asset_id",
                               "model usecase asset ID is missing")
        if (modelusecase_catalog_id is None or modelusecase_catalog_id == ""):
            raise MissingValue("modelusecase_catalog_id",
                               "model usecase catalog ID is missing")

        url = self._get_grc_url(modelusecase_asset_id, modelusecase_catalog_id)
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("GRC models retrieved successfully")
            grc_model_list = response.json()["models"]
            grc_model_list_values = []
            for grc_model in grc_model_list:
                grc_model_list_values.append({'GrcModel': {'id': grc_model.get('model_id'),
                                                           'name': grc_model.get('model_name'),
                                                           'description': grc_model.get('model_description'),
                                                           'status': grc_model.get('model_status')}})
            return grc_model_list_values
        else:
            raise ClientError(
                "Failed in retrieving GRC models. ERROR {}. {}".format(response.status_code, response.text))

    def get_grc_model(self, id: str = None):
        """
            Returns list WKC Model associated with Openpages for a particular model usecase

            :return: WKC Model associated with Openpages for a particular model usecase
            :rtype: dictionary

            Example,::

               client.assets.model_usecase.get_grc_model(id=<grc_model_id>)

        """

        modelusecase_asset_id = self._asset_id
        model_container_type = self._container_type
        modelusecase_catalog_id = self._container_id

        # if self._is_cp4d and self._cp4d_version < "4.7.0":
        #    raise ClientError("Version mismatch: models associated for a particular Model usecase in Openpages functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if (modelusecase_asset_id is None or modelusecase_asset_id == ""):
            raise MissingValue("modelusecase_asset_id",
                               "model usecase asset ID is missing")
        if (modelusecase_catalog_id is None or modelusecase_catalog_id == ""):
            raise MissingValue("modelusecase_catalog_id",
                               "model usecase catalog ID is missing")

        url = self._get_grc_url(modelusecase_asset_id, modelusecase_catalog_id)
        response = requests.get(url, headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("GRC models retrieved successfully")
            grc_model_list = response.json()["models"]
            _is_grc_model_exists = False
            for grc_model in grc_model_list:
                if grc_model.get('model_id') == id:
                    _is_grc_model_exists = True
                    _logger.info("GRC model retrieved successfully")
                    return {'GrcModel': {'id': grc_model.get('model_id'), 'name': grc_model.get('model_name'),
                                         'description': grc_model.get('model_description'),
                                         'status': grc_model.get('model_status')}}
            if not _is_grc_model_exists:
                raise ClientError("GRC Model ID " + id + " is not available.")
        else:
            raise ClientError(
                "Failed in retrieving GRC models. ERROR {}. {}".format(response.status_code, response.text))

    def _get_grc_url(self, model_usecase_asset_id: str = None, catalog_id: str = None):

        append_url = '/v1/aigov/model_inventory/grc/model_entries/' + \
            model_usecase_asset_id + '/models?catalog_id=' + catalog_id

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

    def get_name(self) -> str:
        """
            Returns model usecase name

            :return: Model usecase name
            :rtype: str

            Example,::

               client.assets.model_usecase.get_name()

        """

        # return self.get_info(True).get("name")
        info = self.get_info(True)
        return info.get("ai_usecase_name") or info.get("name")
    
    def get_id(self) -> str:
        """
            Returns model usecase asset ID

            :return: Model usecase asset ID
            :rtype: str

            Example,::

               client.assets.model_usecase.get_id()

        """

        return self.get_info(True).get("model_usecase_id")

    def get_container_id(self) -> str:
        """
            Returns model usecase container ID

            :return: Model usecase container ID
            :rtype: str

            Example,::

              client.assets.model_usecase.get_container_id()

        """

        return self.get_info(True).get("catalog_id")

    def get_container_type(self) -> str:
        """
            Returns model usecase container type

            :return: Model usecase container type
            :rtype: str

            Example,::

              client.assets.model_usecase.get_container_type()

        """

        return self.get_info(True).get("container_type")

    def get_description(self) -> str:
        """
            Returns model usecase description

            :return: Model usecase description
            :rtype: str

            Example,::

              client.assets.model_usecase.get_description()

        """

        return self.get_info(True).get("description")

    def relate_models(self, reference_model_asset_id: str = None, model_asset_id: str = None):
        """
            Returns Update master_id for a model

            :return: Update master_id for a model, now both models will be in same row.
            :rtype: None

            Example,::

               client.assets.model_usecase.get_grc_model(id=<grc_model_id>)

        """

        if (reference_model_asset_id is None or reference_model_asset_id == ""):
            raise MissingValue("reference_model_asset_id",
                               "Reference model asset ID is missing")

        if (model_asset_id is None or model_asset_id == ""):
            raise MissingValue("model_asset_id", "Model asset ID is missing")

        modelusecase_asset_id = self._asset_id
        model_container_type = self._container_type
        modelusecase_catalog_id = self._container_id

        # if self._is_cp4d and self._cp4d_version < "4.7.0":
        #    raise ClientError("Version mismatch: relate models functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if (modelusecase_asset_id is None or modelusecase_asset_id == ""):
            raise MissingValue("modelusecase_asset_id",
                               "model usecase asset ID is missing")
        if (modelusecase_catalog_id is None or modelusecase_catalog_id == ""):
            raise MissingValue("modelusecase_catalog_id",
                               "model usecase catalog ID is missing")

        url = self._get_relatemodels_url(
            modelusecase_asset_id, modelusecase_catalog_id)

        body = {
            "reference_model_id": reference_model_asset_id,
            "model_id": model_asset_id
        }

        response = requests.patch(url, data=json.dumps(
            body), headers=self._get_headers())

        if response.status_code == 200:
            _logger.info("Models are related successfully")
        else:
            raise ClientError("Failed in relating models. ERROR {}. {}".format(
                response.status_code, response.text))

    def _get_relatemodels_url(self, model_usecase_asset_id: str = None, catalog_id: str = None):

        append_url = '/v1/aigov/model_inventory/model_entries/' + \
            model_usecase_asset_id + '/relatemodels?catalog_id=' + catalog_id

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

    # ASSOCIATED WORKSPACES



    def _get_associated_workspaces_url(self, model_usecase_id: str = None, catalog_id: str = None, phase_name: Phases = None, operation: str = None) -> str:

        # if operation == 'post':
        #     append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + '/version_approach?catalog_id='+ catalog_id
        # elif operation == 'get':
        #     append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + '/tracked_model_versions?catalog_id='+ catalog_id
        # elif operation == 'delete' or operation == 'patch':
        #     append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + '/version_approach/' + approach_id + '?catalog_id='+ catalog_id
        # elif operation == 'put':
        #     append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + '/version_approach/' + approach_id + '/versions/'+ version_number +'?catalog_id='+ catalog_id
        # else:
        #     append_url = ""
        if (operation == "get") or (operation == "post") or (operation == "delete"):
            if phase_name:
                if self._is_cp4d and self._cp4d_version >= "5.0.3":
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                              '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id + '&phase_name=' + str(phase_name)
            else:
                if self._is_cp4d and self._cp4d_version >= "5.0.3":
                    url = self._cpd_configs["url"] + \
                          '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                              '/workspaces?inventory_id=' + catalog_id

                else:
                    if get_env() == 'dev':
                        url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id
                    elif get_env() == 'test':
                        url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id
                    else:
                        url = prod_config["DEFAULT_SERVICE_URL"] + \
                              '/v1/aigov/factsheet/ai_usecases/' + model_usecase_id + \
                                  '/workspaces?inventory_id=' + catalog_id

        return url



    def _display_results(self, title: str, data_list: list, columns:list) -> None:
        """
        Display the results as a table to the user.
        """
        if data_list:
            #df = pd.DataFrame(data_list, columns=['Workspace ID','Workspace Name','Workspace Type','Phase Name','Is Deleted','Is Legal'])
            df = pd.DataFrame(data_list,
                              columns=columns)

            print(f"{title}")
            print(df.to_string(index=False))
        else:
            _logger.error(f"No data found for {title}!")

    def _fetch_associated_workspaces(self, model_usecase_id: str = None, catalog_id: str = None)->list:
        """
        Fetch the associated workspaces .
        """
        if self._is_cp4d and self._cp4d_version < "5.0.3":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.3 or higher. Current version of CP4D is " + self._cp4d_version)

        url = self._get_associated_workspaces_url(model_usecase_id=model_usecase_id, catalog_id=catalog_id,
                                                operation="get")
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()

            if response.status_code == 200:
                _logger.info(
                    f"Associated Workspaces retrieved successfully for the given AI usecase with id: {model_usecase_id}")
                data = response.json()
                return data.get('associated_workspaces', [])

                # if not associated_workspaces:
                #     print(f"No Associated Workspaces found for AI usecase with id: {model_usecase_id}")

            elif response.status_code == 400:
                _logger.error(
                    f"Invalid parameters passed. Client Side error encountered : {response.json().get('message')}")
            else:
                _logger.error(
                    f"Failed to fetch the list of Associated Workspaces for AI usecase with id: {model_usecase_id}. Error encountered: {response.status_code} => {response.text}")
        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise ClientError(
                f"Failed in retrieving the list of Associated Workspaces for AI usecase with id: {model_usecase_id}. Error encountered: {e}")

    def _extract_workspace_data(self, workspaces: list) -> list:
        """
        Extract workspace data into a list of dictionaries.
        """
        workspace_data_list = []
        for phase in workspaces:
            phase_name = phase.get('phase_name', 'NA')
            for workspace in phase.get('workspaces', []):
                workspace_data_list.append({
                    'Phase Name': phase_name,
                    'Workspace ID': workspace.get('id', 'NA'),
                    'Workspace Type': workspace.get('type', 'NA'),
                    'Workspace Name': workspace.get('name', 'NA'),
                    'Is Deleted': workspace.get('is_deleted', 'NA'),
                    'Is Legal': workspace.get('is_legal', 'NA')
                })
        return workspace_data_list

    def list_all_associated_workspaces(self) -> None:
        """
            Lists all associated workspaces for a given AI usecase in tabular format. The method will display the associated workspaces for all the phases.

            :returns: None

            Example::

                client.assets.ai_usecase.list_all_associated_workspaces()
        """
        if self._is_cp4d and self._cp4d_version < "5.0.3":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.3 or higher. Current version of CP4D is " + self._cp4d_version)

        model_usecase_id = self._asset_id
        catalog_id = self._container_id
        print(f"model_usecase_id :{model_usecase_id} ,catalog_id : {catalog_id} ")

        associated_workspaces = self._fetch_associated_workspaces(
            model_usecase_id, catalog_id)
        has_associated_workspaces = any(phase.get('workspaces') for phase in associated_workspaces)
        if not has_associated_workspaces:
            _logger.info(
                f"No associated workspaces found for the specified model_usecase_id: {model_usecase_id}")
            return

        if has_associated_workspaces:
            workspace_data_list = self._extract_workspace_data(
                associated_workspaces)
            if workspace_data_list:
                self._display_results(
                    "\n\t\t\t\t\t== Associated Workspaces list ==\n", workspace_data_list,columns=['Workspace ID','Workspace Name','Workspace Type','Phase Name','Is Deleted','Is Legal'])
        else:
            _logger.error(
                f"No associated workspaces found for the specified model_usecase_id: {model_usecase_id}")

    # def list_all_associated_workspaces(self, model_usecase_id:str=None,catalog_id:str=None):
    #     """
    #         Lists all Associated Workspaces for a given AI usecase in tabular format. The method will display the Associated Workspaces for all the phases.
    #
    #         :param str model_usecase_id: id of the AI usecase for which the associated workspaces should be listed
    #         :param str catalog_id:  model inventory id under which the AI usecase is present
    #         :param str phase_name: (Optional) : phase names can be one of the following  values : "develop", "validate", "operate"
    #
    #         :returns:None
    #
    #         Example,::
    #
    #           client.assets.model_usecase.get_associated_workspaces()
    #
    #     """
    #     if self._is_cp4d and self._cp4d_version < "5.0.1":
    #         raise ClientError("Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.1 or higher. Current version of CP4D is "+self._cp4d_version)
    #
    #     url = self._get_associated_workspaces_url(model_usecase_id=model_usecase_id, catalog_id=catalog_id, phase_name=phase_name, operation="get")
    #     try:
    #         response = requests.get(url, headers=self._get_headers())
    #         if response.status_code == 200:
    #             _logger.info(f"Associated Workspaces retrieved successfully for the given ai usecase with id : {model_usecase_id}")
    #             associated_workspaces = response.json().get('associated_workspaces', [])
    #             if not associated_workspaces:
    #                 print(f"No Associated Workspaces found for ai usecase with id :{model_usecase_id}")
    #             associated_workspaces_data_list = []
    #             for phase in data.get('associated_workspaces', []):
    #                 phase_name = phase.get('phase_name', 'NA')
    #                 for workspace in phase.get('workspaces', []):
    #                     associated_workspaces_data_list.append({
    #                         'Phase Name': phase_name,
    #                         'Workspace ID': workspace.get('id', 'NA'),
    #                         'Workspace Type': workspace.get('type', 'NA'),
    #                         'Workspace Name': workspace.get('name', 'NA'),
    #                         'Is Deleted': workspace.get('is_deleted', 'NA'),
    #                         'Is Legal': workspace.get('is_legal', 'NA')
    #                     })
    #
    #             associated_workspaces_df = pd.DataFrame(associated_workspaces_data_list)
    #             _logger.info(f"Associated Workspaces table for ai usecase with id :{model_usecase_id} :\n%s {associated_workspaces_df.to_string(index=False)}")
    #
    #         if response.status_code == 400:
    #             _logger.error(f"Invalid parameters passed. Client Side error encountered : {response.json().get('message')}")
    #         else:
    #             raise ClientError(f"Failed to fetch the list of Associated Workspaces for ai usecase with id :{model_usecase_id}. Error encountered : {response.status_code}=>{response.text}")
    #     except Exception as e:
    #         raise ClientError( f"Failed in retrieving the list of Associated Workspaces for ai usecase with id :{model_usecase_id}. Error encountered : {e}")

    def list_associated_workspaces_by_phase(self, phase_name: Phases = None) -> list:
        """
        Lists all associated workspaces for a given AI usecase in tabular format. The method will display the filtered associated workspaces,
        filtered by the phase name passed.

        :param str phase_name: Phase name. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Phases`


        :returns: list

        Example::

            client.assets.ai_usecase.list_associated_workspaces_by_phase(phase_name='<valid phase name>')
        """
        if self._is_cp4d and self._cp4d_version < "5.0.3":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.3 or higher. Current version of CP4D is " + self._cp4d_version)

        model_usecase_id = self._asset_id
        catalog_id = self._container_id
        print(f"model_usecase_id :{model_usecase_id} ,catalog_id : {catalog_id} ")

        associated_workspaces = self._fetch_associated_workspaces(
            model_usecase_id, catalog_id)
        if phase_name:
            validate_enum(phase_name, "phase_name", Phases, False)
            filtered_workspaces = [phase for phase in associated_workspaces if
                                   phase.get('phase_name').lower() == phase_name]
            filtered_workspace_data_list = self._extract_workspace_data(
                filtered_workspaces)

            if not filtered_workspace_data_list:
                _logger.info(
                    f"No associated workspaces found for the specified model_usecase_id: {model_usecase_id} for the specified phase :{phase_name}")
                return

            if filtered_workspace_data_list:
                self._display_results(
                    "\n\t\t\t\t\t== Phase-specific Associated Workspaces list ==\n", filtered_workspace_data_list,columns=['Workspace ID','Workspace Name','Workspace Type','Phase Name','Is Deleted','Is Legal'])
                return filtered_workspace_data_list
            else:
                _logger.error(
                    f"No associated workspace found for the selected phase : {phase_name}")
        else:
            _logger.error(f"Empty or invalid phase name. you passed {phase_name} for the phase_name. It must be one of 'develop', 'validate', 'operate'.")

    def add_workspaces_associations(self, workspace_id: str = None, workspace_type: str = None,phase_name: str = None,):
        """
            Associate a workspace to a particular AI usecase under a specified phase.

            :param str workspace_id: Project ID or space ID which needs to be associated with the selected usecase.
            :param str workspace_type: Should be "project" when passing a project ID as workspace_id. If a space ID is passed for workspace_id, the workspace_type will be "space".
            :param str phase_name: Phase name, should be one of 'develop', 'validate', or 'operate'. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Phases`.

            :return: None

            Example::

                client.assets.ai_usecase.add_workspaces_associations(workspace_id='<project or space id>', workspace_type='<"project" or "space">', phase_name='<valid phase name>')
        """
        if self._is_cp4d and self._cp4d_version < "5.0.3":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.3 or higher. Current version of CP4D is " + self._cp4d_version)


        model_usecase_id = self._asset_id
        catalog_id = self._container_id
        print(f"model_usecase_id :{model_usecase_id} ,catalog_id : {catalog_id} ")

        url = self._get_associated_workspaces_url(model_usecase_id=model_usecase_id, catalog_id=catalog_id,
                                                  phase_name=phase_name, operation="post")

        current_associations = self._fetch_associated_workspaces(model_usecase_id,catalog_id)
        #print(f"current_associations === > {current_associations}")
        existing_id = any(workspace['id'] == workspace_id for phase in current_associations for workspace in phase.get('workspaces', []))

        if existing_id:
            _logger.error(f"Workspace id : {workspace_id} already associated with usecase_id : {model_usecase_id}")
            return
        try:
            body = {
                "phase_name": phase_name,
                "workspaces": [
                    {
                        "id": workspace_id,
                        "type": workspace_type,
                    }
                ]
            }

            response = requests.post(url, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 201:
                _logger.info(
                    f"Workspace associations attempted for the given workspace IDs: {workspace_id}")
                phase_name = response.json().get('phase_name', '')
                associated_workspaces = response.json().get("associated_workspaces", [])
                error_add_associations = response.json().get("error_add_associations", [])
                if phase_name:
                    self.associated_workspaces.extend(associated_workspaces)
                if associated_workspaces:
                    _logger.info(
                        f"Workspace association for model use case with id {model_usecase_id} done successfully for the following workspace(s)==>\n")
                    for workspace in associated_workspaces:
                        print(workspace)
                if error_add_associations:
                    _logger.error(
                        f"Workspace association for model use case with id {model_usecase_id} failed for the following workspace(s)==>\n")
                    for err_workspace in error_add_associations:
                        print(err_workspace)
            else:
                raise ClientError(
                    f"Failed to associate workspace(s),Error encountered : {response.status_code}=>{response.text} ")

        except Exception as e:
            raise ClientError(f"Failed to associate workspace(s). Exception encountered : {e}")

    # def _display_removed_associations(self, workspace_id_list):
    #      return '\n'.join([f"• {workspace_id}" for workspace_id in workspace_id_list])

    def remove_workspace_associations(self, workspace_ids:list=None)->None:
        """
            Removes association of one or more workspaces at once from a particular AI usecase, irrespective of the phase they are in.
            The disassociation works only if there are no tracked assets in the workspace(s) to be removed. User should have edit access to the usecase.

            :param list workspace_ids: List of workspace IDs to be disassociated. For example: workspace_ids=[project_id_1, space_id_1].

            :return: None

            Example::

                client.assets.model_usecase.remove_workspace_associations(workspace_ids=[<project id>, <space id>])
        """

        if not isinstance(workspace_ids,list):
            raise ValueError(f"The parameter workspace_ids must be a list. The value passed is of type {type(workspace_ids)}")
        if self._is_cp4d and self._cp4d_version < "5.0.3":
            raise ClientError(
                "Version mismatch: Associated Workspaces functionality is only supported in CP4D version 5.0.3 or higher. Current version of CP4D is " + self._cp4d_version)

        model_usecase_id = self._asset_id
        catalog_id = self._container_id
        #print(f"model_usecase_id :{model_usecase_id} ,catalog_id : {catalog_id} ")
        url = self._get_associated_workspaces_url(model_usecase_id=model_usecase_id, catalog_id=catalog_id, operation="delete")

        associated_workspaces_list = self._fetch_associated_workspaces(model_usecase_id,catalog_id)
        
        associated_workspaces_list_ids = [workspace["id"] for phase in associated_workspaces_list for workspace in phase["workspaces"]]
        missing_ids = list(set(workspace_ids) - set(associated_workspaces_list_ids))
        if missing_ids:
            print(f" missing_ids : {missing_ids} ")
            _logger.error(f"Error: The following workspace id(s) :{missing_ids} is/are missing from associated_workspaces_list: {associated_workspaces_list_ids}")
            _logger.info(f"Current list of workspace id associated with the usecase {model_usecase_id} : {associated_workspaces_list_ids}")
        try:
            
            valid_workspace_ids = list(set(associated_workspaces_list_ids).intersection(set(workspace_ids)))
            if valid_workspace_ids:
                
                body = {
                        "workspace_ids": valid_workspace_ids
                        }
                
                response = requests.delete(url, data=json.dumps(body), headers=self._get_headers())  
                if response.status_code == 201:
                    _logger.info(
                f"Workspace disassociations attempted for the given workspace IDs: {valid_workspace_ids}")
                    data = response.json()
                    disassociated_workspaces = data.get("disassociated_workspaces",[])
                    error_disassociation = data.get("error_disassociation")
                    if disassociated_workspaces:
                        # Update the associated_workspaces by removing the disassociated ones
                        self.associated_workspaces = [workspace for workspace in self.associated_workspaces if workspace['id'] not in disassociated_workspaces]
                        _logger.info("Following workspaces are disassociated successfully - \n")
                        self._display_results("\n\t\t==Disassociated Workspaces==\n",disassociated_workspaces,columns=['Workspace ID'])

                    if error_disassociation:
                        _logger.info("Following are the workspaces which could not be disassociated - \n")
                        self._display_results("\n\t\t==Workspaces with Failed Disassociations==\n",error_disassociation,columns=['Workspace ID'])

                elif 400 <= response.status_code < 500:
                    error_messages = {
                        400: "Bad Request: Invalid parameters passed.",
                        401: "Unauthorized: Access is denied due to invalid credentials.",
                        404: "Not Found: The requested data is not available."
                    }
                    error_message = error_messages.get(response.status_code, f"Client Error {response.status_code}")
                    raise ClientError(f"{error_message} Detailed error: {response.json().get('message')}")
                else:
                    raise ClientError(f"Failed to remove workspace associations. Error encountered: {response.status_code} => {response.text}")
        except Exception as e:
            raise ClientError(f"Failed in removing the workspace associations. Error encountered: {e}")









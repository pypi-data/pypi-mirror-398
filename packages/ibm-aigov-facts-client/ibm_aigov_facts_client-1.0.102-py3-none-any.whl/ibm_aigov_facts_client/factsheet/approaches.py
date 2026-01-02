import logging
import os
import json
import collections
import ibm_aigov_facts_client._wrappers.requests as requests

from typing import BinaryIO, Dict, List, TextIO, Union,Any
from ibm_aigov_facts_client.factsheet import assets 
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator,CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal,ContainerType, FactsType, RenderingHints,ModelEntryContainerType, AllowedDefinitionType,FormatType
from ibm_aigov_facts_client.utils.utils import validate_enum,validate_type


from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *

from ibm_aigov_facts_client.factsheet import asset_utils_me

_logger = logging.getLogger(__name__) 


class ApproachUtilities:

    """
        Approach utilities. Running `client.assets.ai_usecase().get_approaches` makes all methods in ApproachUtilities object available to use.
    
    """
   
    def __init__(self,assets_me_client:'asset_utils_me.ModelUsecaseUtilities', approach_id: str=None, approach_name: str=None, approach_desc: str=None, approach_icon: str=None,approach_icon_color: str=None, versions: list=None, model_asset_id: str=None, model_container_type: str=None, model_container_id: str=None, op_id: str=None) -> None:

        """
        Initialize a ApproachUtilities object.
        
        """
        self._approach_id=approach_id
        self._approach_name=approach_name
        self._approach_desc=approach_desc
        self._approach_icon=approach_icon
        self._approach_icon_color=approach_icon_color
        self._versions=versions

        self._model_asset_id = model_asset_id
        self._model_container_type = model_container_type
        self._model_container_id = model_container_id

        self._assets_me_client=assets_me_client
        self._facts_client=self._assets_me_client._facts_client

        self._assets_client=assets_me_client._assets_client
        self._is_cp4d=self._facts_client._is_cp4d
        self._external_model=self._assets_client._external_model
        self._op_id = op_id 
        
        if self._is_cp4d:
            self._cpd_configs=self._assets_client._cpd_configs
            self._cp4d_version=self._assets_client._cp4d_version


    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ApproachUtilities':
        """Initialize a ApproachUtilities object from a json dictionary."""
        args = {}

        if '_approach_id' in _dict:
            args['approach_id'] = _dict.get('_approach_id') 
        else:
            raise ValueError('Required property \'approach_id\' not present in ApproachProps JSON')

        if '_approach_name' in _dict:
            args['approach_name'] = _dict.get('_approach_name') 
        else:
            raise ValueError('Required property \'approach_name\' not present in ApproachProps JSON')
        
        if '_approach_desc' in _dict:
            args['approach_desc'] = _dict.get('_approach_desc')
        
        # if '_approach_icon' in _dict:
        #     args['approach_icon'] = _dict.get('_approach_icon')
        # else:
        #     raise ValueError('Required property \'approach_icon\' not present in AssetProps JSON')

        # if '_approach_icon_color' in _dict:
        #     args['approach_icon_color'] = _dict.get('_approach_icon_color')
        # else:
        #     raise ValueError('Required property \'approach_icon_color\' not present in AssetProps JSON')

        if '_versions' in _dict:
            args['versions'] = _dict.get('_versions')

        if '_model_asset_id' in _dict:
            args['model_asset_id'] = _dict.get('_model_asset_id')
        else:
            raise ValueError('Required property \'model_asset_id\' not present in AssetProps JSON')

        if '_model_container_type' in _dict:
            args['model_container_type'] = _dict.get('_model_container_type')
        else:
            raise ValueError('Required property \'model_container_type\' not present in AssetProps JSON')

        if '_model_container_id' in _dict:
            args['model_container_id'] = _dict.get('_model_container_id')
        else:
            raise ValueError('Required property \'model_container_id\' not present in AssetProps JSON')

        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        return cls.from_dict(_dict)


    def to_dict(self) -> Dict:
        """Return a json dictionary representing this approach."""
        _dict = {}
        if hasattr(self, '_approach_id') and self._approach_id is not None:
            _dict['approach_id'] = self._approach_id
        if hasattr(self, '_approach_name') and self._approach_name is not None:
            _dict['approach_name'] = self._approach_name
        if hasattr(self, '_approach_desc') and self._approach_desc is not None:
            _dict['approach_desc'] = self._approach_desc
        
        # if hasattr(self, '_approach_icon') and self._approach_icon is not None:
        #     _dict['approach_icon'] = self._approach_icon
        # if hasattr(self, '_approach_icon_color') and self._approach_icon_color is not None:
        #     _dict['approach_icon_color'] = self._approach_icon_color
        if hasattr(self, '_versions') and self._versions is not None:
            _dict['versions'] = self._versions
        if hasattr(self, '_model_asset_id') and self._model_asset_id is not None:
            _dict['model_asset_id'] = self._model_asset_id
        if hasattr(self, '_model_container_type') and self._model_container_type is not None:
            _dict['model_container_type'] = self._model_container_type
        if hasattr(self, '_model_container_id') and self._model_container_id is not None:
            _dict['model_container_id'] = self._model_container_id
        if hasattr(self, '_op_id') and self._op_id is not None:
            _dict['op_id'] = self._op_id
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()
    
    def __str__(self) -> str:
        """Return a `str` version of this ApproachUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this ApproachUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def get_info(self)-> Dict:

        """
            Get approach object details. Supported for CPD version >=4.7.0

            :rtype: dict

            The way to use me is:

            >>> get_approach.get_info()

        """

        return self._to_dict()

    def get_versions(self)->list:

        """
            Returns list of WKC Model usecase approache versions. Supported for CPD version >=4.7.0
            
            :return: All WKC Model usecase approache versions
            :rtype: list

            Example.::
            
              ai_usecase.get_approach.get_versions()

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Model usecase approach versions functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        versions = self._versions
        
        approach_list_values = []
        if versions is not None:
            for version in versions:
                version_dictionary = {}
                version_dictionary["number"]=version["number"]
                #version_dictionary["model_identity_key"]=version["model_identity_key"]
                version_dictionary["comment"]=version["comment"]
                approach_list_values.append(version_dictionary)
        else :
            approach_list_values.append({"number":"0.0.0","comment":""})
        return approach_list_values


    #def get_version(self):
    #
    #    if self._is_cp4d and self._cp4d_version < "4.7.0":
    #        raise ClientError("Version mismatch: Model usecase approach version functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)
    #
    #    versions = self._versions
    #    version_dictionary = {}
    #    approach_list_values = []
    #    for version in versions:
    #        version_dictionary["number"]=version["number"]
    #        version_dictionary["comment"]=version["comment"]
    #        approach_list_values.append(version_dictionary)
    #    return approach_list_values


    def set_name(self,name:str=None):
        
        """
            Returns WKC Model usecase updated approach. Supported for CPD version >=4.7.0
            
            :param str name: New name for approach
            
            :rtype: ApproachUtilities

            :return: WKC Model usecase approache is updated
            
            Example,::
            
               ai_usecase.get_approach.set_name(name=<new approach name>)
        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Model usecase, setting new name for approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if (name is None or name == ""):
            raise MissingValue("name", "New approach name is missing")

        if name:
            body= [
                {
                    "op": "add",
                    "path": "/name",
                    "value": name
                }
                ]
        else:
            raise ClientError("Provide approach name")

        url=self._get_approach_url(self._model_asset_id,self._model_container_id,self._approach_id,operation="patch")

        response = requests.patch(url,data=json.dumps(body), headers=self._get_headers())
        
        if response.status_code ==200:
            _logger.info("Approach name changed successfully")
            approaches_list = response.json()["approaches"]
            current_approach_id = self._approach_id
            for approach in approaches_list:
                if approach.get('id') == current_approach_id:
                    return ApproachUtilities(self._assets_me_client,approach_id=approach.get('id'),approach_name=approach.get('name'),approach_desc=approach.get('description'),approach_icon=approach.get('icon'),approach_icon_color=approach.get('icon_color'),versions=approach.get('versions'),model_asset_id=self._model_asset_id,model_container_type=self._model_container_type,model_container_id=self._model_container_id)
        else:
            raise ClientError("Failed while updating an approach name. ERROR {}. {}".format(response.status_code,response.text))
    

    def set_description(self,description:str=None):

        """
            Returns WKC Model usecase updated approach. Supported for CPD version >=4.7.0
            
            :param str description: New description for approach
            
            :rtype: ApproachUtilities

            :return: WKC Model usecase approache is updated
            
            Example,::
            
                ai_usecase.get_approach.set_description(description=<new approach description>)
        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Model usecase, setting new description for approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if (description is None or description == ""):
            raise MissingValue("description", "New approach description is missing")

        if description:
            body= [
                {
                     "op": "add",
                     "path": "/description",
                     "value": description
                 }
                ]
        else:
            raise ClientError("Provide approach description")

        url=self._get_approach_url(self._model_asset_id,self._model_container_id,self._approach_id,operation="patch")

        response = requests.patch(url,data=json.dumps(body), headers=self._get_headers())
        
        if response.status_code ==200:
            _logger.info("Approach description changed successfully")
            approaches_list = response.json()["approaches"]
            current_approach_id = self._approach_id
            for approach in approaches_list:
                if approach.get('id') == current_approach_id:
                    return ApproachUtilities(self._assets_me_client,approach_id=approach.get('id'),approach_name=approach.get('name'),approach_desc=approach.get('description'),approach_icon=approach.get('icon'),approach_icon_color=approach.get('icon_color'),versions=approach.get('versions'),model_asset_id=self._model_asset_id,model_container_type=self._model_container_type,model_container_id=self._model_container_id)
        else:
            raise ClientError("Failed while updating an approach description. ERROR {}. {}".format(response.status_code,response.text))
        
    def set_op_id_for_model_group(self,op_id):
    
        """
            Returns  updated approach with model group OP ID. Supported for CPD version >=4.7.0
            
            :param str set_op_id_for_model_group: New model group op ID for approach
            
            :rtype: ApproachUtilities
   
            Example:
            
                approach.set_op_id_for_model_group(op_id=<new op ID>)
        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Setting model group op ID for approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)
        
        url=self._get_approach_url(self._model_asset_id,self._model_container_id,self._approach_id,operation="get")
        response = requests.get(url, headers=self._get_headers())
        if response.status_code != 200:
            raise ClientError("Error in retrieving the approaches.")
        response_json=response.json()
        approaches_list = response_json.get("approaches")
        if not approaches_list or not response_json["approaches"]:
            raise ValueError("No approaches found in the response")
        index = next(
            (len(approaches_list) - 1 - i for i, a in enumerate(approaches_list) if a.get("id") == self._approach_id),
            None
        )
        body= [
                {
                    "op": "add",
                    "path": f"/approaches/{index}/op_id",
                    "value": op_id
                }
            ]
        
        url=self._get_approach_url_opId(self._model_asset_id,self._model_container_id,self._approach_id,operation="patch")
        response = requests.patch(url,data=json.dumps(body), headers=self._get_headers()) 
        if response.status_code ==200:
          _logger.info("Model group op ID updated successfully")
        else:
            raise ClientError("Failed while updating an model op ID. ERROR {}. {}".format(response.status_code,response.text))
     
        


    def _get_headers(self):
          
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers 

    def get_name(self)->str:

        """
            Returns model approach name
            
            :return: Model approach name
            :rtype: str

            Example,::
            
               ai_usecase.get_approach.get_name()

        """

        return self.get_info().get("approach_name")
    
    def get_id(self)->str:

        """
            Returns approach ID
            
            :return:  Approach ID
            :rtype: str

            Example,::
              
               ai_usecase.get_approach.get_id()

        """

        return self.get_info().get("approach_id")

    def get_description(self)->str:

        """
            Returns approach description
            
            :return:  Approach description
            :rtype: str

            Example,::
            
               ai_usecase.get_approach.get_description()

        """

        return self.get_info().get("approach_desc")

    def get_model_useacse_id(self)->str:

        """
            Returns model usecase asset ID to which approach is defined
            
            :return: Model usecase asset ID to which approach is defined
            :rtype: str

            Example,::
            
               model_usecase.get_approach.get_model_useacse_id()

        """

        return self._model_asset_id

    def get_model_usecase_container_type(self)->str:

        """
            Returns model usecase container type to which approach is defined
            
            :return: Model usecase container type to which approach is defined
            :rtype: str

            Example,::
            
               model_usecase.get_approach.get_model_usecase_container_type()

        """

        return self._model_container_type
    
    def get_model_usecase_container_id(self)->str:

        """
            Returns model usecase container ID to which approach is defined
            
            :return: Model usecase container ID to which approach is defined
            :rtype: str

            Example,::
            
               model_usecase.get_approach.get_model_usecase_container_id()

        """

        return self._model_container_id


    def _get_approach_url(self,model_usecase_asset_id:str=None,catalog_id:str=None,approach_id:str=None,version_number:str=None,operation:str=None):
        
        if operation == 'patch':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + model_usecase_asset_id + '/version_approach/' + approach_id + '?catalog_id='+ catalog_id
        
        elif operation == 'get':
            append_url = '/v1/aigov/model_inventory/model_usecases/' + \
                model_usecase_asset_id + '/tracked_model_versions?catalog_id=' + catalog_id
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
    
    def _get_approach_url_opId(self,model_usecase_asset_id:str=None,catalog_id:str=None,approach_id:str=None,version_number:str=None,operation:str=None):
        
        if operation == 'patch':
            append_url = '/v2/assets/{}/attributes/model_entry?catalog_id={}'.format(model_usecase_asset_id,catalog_id)
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
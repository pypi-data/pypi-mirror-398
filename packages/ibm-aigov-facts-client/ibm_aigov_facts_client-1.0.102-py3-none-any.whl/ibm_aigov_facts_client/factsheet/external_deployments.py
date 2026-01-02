import logging
import os
import json
import collections
import ibm_aigov_facts_client._wrappers.requests as requests
import hashlib

from typing import BinaryIO, Dict, List, TextIO, Union,Any
from ibm_aigov_facts_client.factsheet import asset_utils_model 
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator,CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal,ContainerType, FactsType, RenderingHints,ModelEntryContainerType, AllowedDefinitionType,FormatType,ModelEntryContainerTypeExternal
from ibm_aigov_facts_client.utils.utils import validate_enum,validate_type


from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *


_logger = logging.getLogger(__name__) 


class Deployment:

    """
        External model deployment. Running `client.assets.get_deployments` makes all methods in Deployment object available to use.
    
    """
   
    def __init__(self,asset_model_client:'asset_utils_model.ModelAssetUtilities', id: str=None, name: str=None, type: str=None, scoring_endpoint: str=None, external_identifier: str=None, is_deleted: str=None, description: str=None, model_asset_id: str=None, model_name: str=None, model_container_type: str=None, model_container_id: str=None) -> None:

        """
        Initialize a Deployment object.
        
        """
        self._id=id
        self._name=name
        self._type=type
        self._scoring_endpoint=scoring_endpoint
        self._external_identifier=external_identifier
        self._is_deleted=is_deleted
        self._description=description

        self._model_name=model_name
        self._model_asset_id=model_asset_id
        self._model_container_type=model_container_type
        self._model_container_id=model_container_id

        self._external_client=asset_model_client
        self._facts_client=self._external_client._facts_client

        self._external_model=self._facts_client._external
        self._is_cp4d=self._facts_client._is_cp4d

        if self._is_cp4d:
            self._cpd_configs=self._facts_client.cp4d_configs
            self._cp4d_version=self._facts_client._cp4d_version


    @classmethod
    def from_dict(cls, _dict: Dict) -> 'Deployment':
        """Initialize a Deployment object from a json dictionary."""
        args = {}

        if '_id' in _dict:
            args['id'] = _dict.get('_id') 
        else:
            raise ValueError('Required property \'id\' not present in Deployment JSON')

        if '_name' in _dict:
            args['name'] = _dict.get('_name') 
        else:
            raise ValueError('Required property \'name\' not present in Deployment JSON')
        
        if '_type' in _dict:
            args['type'] = _dict.get('_type')
        else:
            raise ValueError('Required property \'type\' not present in Deployment JSON')

        if '_scoring_endpoint' in _dict:
            args['scoring_endpoint'] = _dict.get('_scoring_endpoint')
        else:
            raise ValueError('Required property \'scoring_endpoint\' not present in Deployment JSON')

        if '_is_deleted' in _dict:
            args['is_deleted'] = _dict.get('_is_deleted')
        else:
            raise ValueError('Required property \'is_deleted\' not present in Deployment JSON')

        if '_description' in _dict:
            args['description'] = _dict.get('_description')
        else:
            raise ValueError('Required property \'description\' not present in Deployment JSON')

        if '_model_name' in _dict:
            args['model_name'] = _dict.get('_model_name')
        else:
            raise ValueError('Required property \'model_name\' not present in Deployment JSON')

        if '_model_asset_id' in _dict:
            args['model_asset_id'] = _dict.get('_model_asset_id')
        else:
            raise ValueError('Required property \'model_asset_id\' not present in Deployment JSON')

        if '_model_container_type' in _dict:
            args['model_container_type'] = _dict.get('_model_container_type')
        else:
            raise ValueError('Required property \'model_container_type\' not present in Deployment JSON')

        if '_model_container_id' in _dict:
            args['model_container_id'] = _dict.get('_model_container_id')
        else:
            raise ValueError('Required property \'model_container_id\' not present in Deployment JSON')
        
        if '_external_identifier' in _dict:
            args['external_identifier'] = _dict.get('_external_identifier')
        else:
            raise ValueError('Required property \'external_identifier\' not present in Deployment JSON')

        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        return cls.from_dict(_dict)


    def to_dict(self) -> Dict:
        """Return a json dictionary representing this deployment."""
        _dict = {}
        if hasattr(self, '_id') and self._id is not None:
            _dict['id'] = self._id
        if hasattr(self, '_name') and self._name is not None:
            _dict['name'] = self._name
        if hasattr(self, '_type') and self._type is not None:
            _dict['type'] = self._type
        if hasattr(self, '_scoring_endpoint') and self._scoring_endpoint is not None:
            _dict['scoring_endpoint'] = self._scoring_endpoint
        if hasattr(self, '_is_deleted') and self._is_deleted is not None:
            _dict['is_deleted'] = self._is_deleted
        if hasattr(self, '_description') and self._description is not None:
            _dict['description'] = self._description
        if hasattr(self, '_model_name') and self._model_name is not None:
            _dict['model_name'] = self._model_name
        if hasattr(self, '_model_asset_id') and self._model_asset_id is not None:
            _dict['model_asset_id'] = self._model_asset_id
        if hasattr(self, '_model_container_type') and self._model_container_type is not None:
            _dict['model_container_type'] = self._model_container_type
        if hasattr(self, '_model_container_id') and self._model_container_id is not None:
            _dict['model_container_id'] = self._model_container_id
        if hasattr(self, '_external_identifier') and self._external_identifier is not None:
            _dict['external_identifier'] = self._external_identifier

        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()
    
    def __str__(self) -> str:
        """Return a `str` version of this Deployment object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this Deployment object."""
        return json.dumps(self.to_dict(), indent=2)

    def _encode_model_id(self,model_id):
        encoded_id=hashlib.md5(model_id.encode("utf-8")).hexdigest()
        return encoded_id

    def _encode_deployment_id(self,deployment_id):
        encoded_deployment_id=hashlib.md5(deployment_id.encode("utf-8")).hexdigest()
        return encoded_deployment_id

    def _validate_payload(self, payload):
        if not payload["model_id"] or not payload["name"]:
            raise ClientError("model_identifier or name is missing")
        else:
            payload["model_id"]= self._encode_model_id(payload["model_id"])
        if payload.get("deployment_details"):
            payload["deployment_details"]["id"]= self._encode_deployment_id(payload["deployment_details"]["id"])

        return payload

    def get_info(self,verbose=False)-> Dict:

        """
            Get deployment object details. Supported for CPD version >=4.7.0

            :rtype: dict

            The way to use me is:

            >>> get_deployment.get_info()

        """

        if verbose:
            url=self._get_assets_url(self._model_asset_id,self._model_container_type,self._model_container_id)
           
            response = requests.get(url, headers=self._get_headers())
            if response.status_code==200:
                deployment_details_list=response.json()["entity"]["model_stub"].get("deployment_details")
                for deployment_return in deployment_details_list:
                    deployment_id_return = deployment_return.get('id')
                    if self._id == deployment_id_return:
                        self._type=deployment_return.get('type')
                        self._scoring_endpoint=deployment_return.get('scoring_endpoint')
                        self._description=deployment_return.get('description')
                        return  
        else:
            return self._to_dict()

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
            Returns external model's deployment name
            
            :return:  external model's deployment name
            :rtype: str

            Example:
            >>>  deployment.get_name()

        """

        return self._name
    
    def get_id(self)->str:

        """
            Returns external model's deployment ID
            
            :return:  external model's deployment ID
            :rtype: str

            Example:
            >>>  deployment.get_id()

        """

        return self._id

    def get_scoring_endpoint(self)->str:

        """
            Returns external model's deployment scoring endpoint
            
            :return:  external model's deployment scoring endpoint
            :rtype: str

            Example:
            >>>  deployment.get_scoring_endpoint()

        """

        self.get_info(True)
        return self._scoring_endpoint

    def get_type(self)->str:

        """
            Returns external model's deployment type
            
            :return:  external model's deployment type
            :rtype: str

            Example:
            >>>  deployment.get_type()

        """

        self.get_info(True)
        return self._type

    def get_description(self)->str:

        """
            Returns external model's deployment description
            
            :return:  external model's deployment description
            :rtype: str

            Example:
            >>>  deployment.get_description()

        """

        self.get_info(True)
        return self._description

    def get_model_id(self)->str:

        """
            Returns external model asset ID
            
            :return:  external model asset ID
            :rtype: str

            Example:
            >>>  deployment.get_model_id()

        """

        return self._model_asset_id
    
    def get_model_name(self)->str:

        """
            Returns external model asset ID
            
            :return:  external model asset ID
            :rtype: str

            Example:
            >>>  deployment.get_model_name()

        """

        return self._model_name

    def get_model_container_type(self)->str:

        """
            Returns external model container type
            
            :return:  external model container type
            :rtype: str

            Example:
            >>>  deployment.get_model_container_type()

        """

        return self._model_container_type
    
    def get_model_container_id(self)->str:

        """
            Returns external model container type
            
            :return:  external model container type
            :rtype: str

            Example:
            >>>  deployment.get_model_container_id()

        """
        
        return self._model_container_id

    def set_environment_type(self, to_container: str)->None:
        
        """
            Set current container for deployment inside model asset. For available options check :func:`~ibm_aigov_facts_client.utils.enums.ModelEntryContainerType`

            :param str to_container: Container name to move to
            
            A way you might use me is:

            >>> deployment.set_environment_type(to_container="validate")

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Setting environment type for deployment under external model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        if self._is_cp4d and self._cp4d_version >= "5.0.1":
            validate_enum(to_container, "to_container", ModelEntryContainerTypeExternal, True)
        else:
            validate_enum(to_container,"to_container", ModelEntryContainerType, True)



        body={
            "target_environment": to_container.capitalize()
        }
        
        url=self._get_deployment_environment_url(self._model_asset_id,self._model_container_id, self._id,operation="put")
        response = requests.put(url,data=json.dumps(body), headers=self._get_headers())
        if response.status_code == 200:
            _logger.info("Deployment successfully moved to {} environment".format(to_container))
        else:
            raise ClientError("Deployment movement failed. ERROR {}. {}".format(response.status_code,response.text))

    def _deployment_index(self,deployment_id: str)-> int:

        url=self._get_assets_url(self._model_asset_id,self._model_container_type,self._model_container_id)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code==200:
            deployment_index = 0
            deployment_details_list=response.json()["entity"]["model_stub"].get("deployment_details")
            for deployment_return in deployment_details_list:
                deployment_id_return = deployment_return.get('id')
                if deployment_id == deployment_id_return:
                    return deployment_index
                else:
                    deployment_index = deployment_index + 1
            return -1
        else:
            raise ClientError("Failed while fetching deployment index information. ERROR {}. {}".format(response.status_code,response.text))


    def set_description(self, value: str)->None:
        
        """
            Set description for a particular deployment

            :param str value: New description value for deployment
            
            A way you might use me is:

            >>> deployment.set_description(value="new description")

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Setting description for deployment under external model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        deployment_index_val = self._deployment_index(self._id)
        path= "/deployment_details/"+str(deployment_index_val)+"/description"
        op = ADD

        body = [
            {
                "op": op, 
                "path": path,
                "value": value
            }
        ]
        
        url=self._get_assets_attributes_url(self._model_asset_id,"model_stub",self._model_container_type,self._model_container_id)
        response = requests.patch(url, data=json.dumps(body), headers=self._get_headers())
  
        if response.status_code == 200:
            _logger.info("Description is updated for deployment successfully")
        else:
            raise ClientError("Patching description value failed. ERROR {}. {}".format(response.status_code,response.text))
            

    def set_scoring_endpoint(self, value: str)->None:
        
        """
            Set scoring endpoint for a particular deployment

            :param str value: New scoring endpoint value for deployment
            
            A way you might use me is:

            >>> deployment.set_scoring_endpoint(value="new scoring endpoint")

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Setting scoring endpoint for deployment under external model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        deployment_index_val = self._deployment_index(self._id)
        path= "/deployment_details/"+str(deployment_index_val)+"/scoring_endpoint"
        op = ADD

        body = [
            {
                "op": op, 
                "path": path,
                "value": value
            }
        ]
        
        url=self._get_assets_attributes_url(self._model_asset_id,"model_stub",self._model_container_type,self._model_container_id)
        response = requests.patch(url, data=json.dumps(body), headers=self._get_headers())
  
        if response.status_code == 200:
            _logger.info("Scoring endpoint is updated for deployment successfully")
        else:
            raise ClientError("Patching scoring endpoint value failed. ERROR {}. {}".format(response.status_code,response.text))
            

    def set_type(self, value: str)->None:
        
        """
            Set type for a particular deployment

            :param str value: New type value for deployment
            
            A way you might use me is:

            >>> deployment.set_type(value="new type")

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError("Version mismatch: Setting type for deployment under external model functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        deployment_index_val = self._deployment_index(self._id)
        path= "/deployment_details/"+str(deployment_index_val)+"/type"
        op = ADD

        body = [
            {
                "op": op, 
                "path": path,
                "value": value
            }
        ]
        
        url=self._get_assets_attributes_url(self._model_asset_id,"model_stub",self._model_container_type,self._model_container_id)
        response = requests.patch(url, data=json.dumps(body), headers=self._get_headers())
  
        if response.status_code == 200:
            _logger.info("Type is updated for deployment under model_stub successfully")
        else:
            raise ClientError("Patching type value failed at model_stub with ERROR {}. {}".format(response.status_code,response.text))

        path = "/deployment_details/"+str(deployment_index_val)+"/deployment_type"
        url=self._get_assets_attributes_url(self._model_asset_id,"modelfacts_system",self._model_container_type,self._model_container_id)
        response = requests.patch(url, data=json.dumps(body), headers=self._get_headers())
  
        if response.status_code == 200:
            _logger.info("Type is updated for deployment under modelfacts_system successfully")
        else:
            raise ClientError("Patching type value failed at modelfacts_system with ERROR {}. {}".format(response.status_code,response.text))


    def _get_deployment_environment_url(self,model_asset_id:str=None,catalog_id:str=None,deployment_id:str=None,operation:str=None):
        
        if operation == 'put':
            append_url = '/v1/aigov/model_inventory/models/' + model_asset_id + '/deployments/'+ deployment_id + '/environment?catalog_id='+ catalog_id
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

    def _get_assets_attributes_url(self,model_asset_id:str=None, attribute_key:str=None, container_type:str=None, container_id:str=None):

        append_url = '/v2/assets/' + model_asset_id + "/attributes/"+ attribute_key +"?" + container_type + "_id=" + container_id

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

    def _get_assets_url(self,asset_id:str=None,container_type:str=None,container_id:str=None):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + '?'+ container_type + '_id=' + container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?'+ container_type + '_id=' + container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?'+ container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?'+ container_type + '_id=' + container_id
        return url

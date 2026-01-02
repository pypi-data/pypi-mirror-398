import logging
import os
import json
import collections
import itertools
import uuid
import ibm_aigov_facts_client._wrappers.requests as requests
import hashlib
from typing import Any

from typing import Optional
from datetime import datetime

from typing import BinaryIO, Dict, List, TextIO, Union, Any
from ibm_aigov_facts_client.factsheet import assets
from ibm_aigov_facts_client.factsheet.asset_utils_model import ModelAssetUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_me_prompt import AIUsecaseUtilities
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal, ContainerType, FactsType, ModelEntryContainerType, AllowedDefinitionType, FormatType, RenderingHints
from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type, STR_TYPE
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_aigov_facts_client.factsheet.asset_utils_experiments import NotebookExperimentUtilities
from ibm_cloud_sdk_core.utils import convert_model
from ibm_aigov_facts_client.utils.metrics_utils import convert_metric_value_to_float_if_possible
from ibm_aigov_facts_client.utils.cell_facts import CellFactsMagic
from ibm_aigov_facts_client.factsheet.assets import *
from ibm_aigov_facts_client.utils.enums import  FactsType,Task

from ibm_aigov_facts_client.factsheet.approaches import ApproachUtilities
from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.constants import get_cloud_url

from ibm_aigov_facts_client.factsheet.external_deployments import Deployment
from ibm_aigov_facts_client.factsheet.html_parser import FactHTMLParser
from ibm_aigov_facts_client.utils.doc_annotations import deprecated

_logger = logging.getLogger(__name__)


class AIGovAssetUtilities(ModelAssetUtilities):

    """
        AI asset utilities. Running `client.assets.get_prompt()` makes all methods in AIGovAssetUtilities object available to use.

    """

    def __init__(self, assets_client: 'assets.Assets', json_data: dict,model_id: str = None, container_type: str = None, container_id: str = None, facts_type: str = None) -> None:

        self._asset_id = model_id
        self._container_type = container_type
        self._container_id = container_id
        self._facts_type = facts_type
        self.json_data = json_data

    

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

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'AIGovAssetUtilities':
        """Initialize a AIGovAssetUtilities object from a json dictionary."""
        args = {}
        # if '_assets_client' in _dict:
        #     #added by Lakshmi as in __init__() , as assets_client is expected
        #     args['assets_client'] = _dict.get('_assets_client')

        if '_asset_id' in _dict:
            # args['asset_id'] = _dict.get('_asset_id') #commented by Lakshmi as in __init__() , asset_id is not expected
            args['model_id'] = _dict.get('_asset_id')

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
        # return cls(**args)
        return cls(_dict.get('_assets_client'), **args)

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
        """Return a `str` version of this AIGovAssetUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this AIGovAssetUtilities object."""
        return json.dumps(self.to_dict(), indent=2)


    def set_environment_type(self, from_container: str, to_container: str) -> None:
        """
            This method is not available for prompt.
        """

        _logger.info("This method is not available for prompt")


    def get_experiment(self, experiment_name: str = None) -> NotebookExperimentUtilities:
        """
            This method is not available for prompt.
        """
        _logger.info("This method is not available for prompt")

    # def track(self,ai_usecase:AIUsecaseUtilities=None,approach:ApproachUtilities=None,grc_model:dict=None, version_number:str=None, version_comment:str=None):

    #     """
    #         Link Model to model use case. Model asset should be stored in either Project or Space and corrsponding ID should be provided when registering to model use case.

    #         Supported for CPD version >=4.7.0

    #         :param AIUsecaseUtilities ai_usecase: Instance of AIUsecaseUtilities
    #         :param ApproachUtilities approach: Instance of ApproachUtilities
    #         :param str grc_model: (Optional) Openpages model id. Only applicable for CPD environments. This should be dictionary, output of get_grc_model()
    #         :param str version_number: Version number of model. supports either a semantic versioning string or one of the following keywords for auto-incrementing based on the latest version in the approach: "patch", "minor", "major"
    #         :param str version_comment: (Optional) An optional comment describing the changes made in this version

    #         :rtype: AIGovAssetUtilities

    #         For tracking model with ai usecase:

    #         >>> prompt.track(ai_usecase=<instance of AIUsecaseUtilities>,approach=<instance of ApproachUtilities>,version_number=<version>)

    #     """

    #     if (ai_usecase is None or ai_usecase == ""):
    #         raise MissingValue("ai_usecase", "AIUsecaseUtilities object or instance is missing")

    #     if ( not isinstance(ai_usecase, AIUsecaseUtilities)):
    #         raise ClientError("Provide AIUsecaseUtilities object for ai_usecase")

    #

    def is_detached(self) -> bool:
        """
            Check if the fetched prompt is in offline mode.
            
            Returns:
                bool: True if the fetched prompt is offline and headless, False otherwise.
            
            Raises:
                ClientError: If the fetched prompt mode is not 'detached'.
            
            Example::

                prompt.is_offline()
        """
        input_mode = self.json_data.get('input_mode')
        return input_mode == 'detached'
    

    def get_asset_id(self):
        """
        Extracts the asset_id from the Prompt created.
        
        Returns:
        str: The asset_id if found, otherwise None.
        """
        asset_id = self.json_data.get('id')
        if asset_id is not None:
                return asset_id
        else:
            raise KeyError("asset_id not found ")
       
    # commenting this as it just returning string which is not usefull for automation
    # def get_info(self,verbose=False):
    #     """
    #         Get info of the fetched prompt.

    #         This method retrieves all available details of the fetched prompt and returns them as a formatted string.

    #         Args:
    #             verbose (bool): If True, print all details. Default is False

    #         Returns:
    #             None

    #         Raises:
    #             ValueError: If no prompt data is available.

    #         Example::

    #             # Call the method with verbose=True to print all details
    #             prompt.get_prompt_info(verbose=True)
    #     """
    #     _ENV = get_env()
    #     url = self._prompts_url(self._asset_id, self._container_type, self._container_id)
    #     response = requests.get(url, headers=self._get_headers())
    #     if response.status_code==200:
    #         json_data = response.json()
    #         base_url = (CLOUD_DEV_URL if _ENV == "dev" else CLOUD_TEST_URL if _ENV == "test" else (CLOUD_URL if not self._is_cp4d else self._cpd_configs["url"]))
    #         if self._container_type == "space":
    #             access_url = PROMPT_PATH_SPACE.format(base_url, self._asset_id, self._container_id)
    #         else:
    #             access_url = PROMPT_PATH_PROJECT.format(base_url, self._asset_id, self._container_id)
            
    #         _logger.info(f"The link to access the prompt created is: {access_url}")
             

    #         formatted_output = (
    #             f"\n"
    #             f"\033[1m\033[4mPrompt Details:\033[0m\n"
    #             f"  id: {json_data.get('id', '')}\n"
    #             f"  name: {json_data.get('name', '')}\n"
    #             f"  input mode: {json_data.get('input_mode', '')}\n"
    #             f"  model_id: {json_data.get('prompt', {}).get('model_id', '')}\n"
    #             f"  container ID: {self._container_id}\n"  
    #         )

    #         if json_data.get('input_mode', '') == "detached" and not verbose:
    #             external_information = json_data.get('prompt', {}).get('external_information', {})
    #             if external_information:
    #                 formatted_output += (
    #                     f"\ndetached information:\n"
    #                     f"  prompt_id: {external_information.get('external_prompt_id', '')}\n"
    #                     f"  model_id: {external_information.get('external_model_id', '')}\n"
    #                     f"  model_provider: {external_information.get('external_model_provider', '')}\n")

    #         if verbose:
    #             formatted_output += (
    #                 f"  description: {json_data.get('description', '')}\n"
    #                 f"  created By: {json_data.get('created_by', '')}\n"
    #                 f"  model_version: {json_data.get('model_version', {})}\n"
    #                 f"  prompt_variables: {json_data.get('prompt_variables', '')}\n"
    #                 f"  task_id: {json_data.get('task_ids', [])}\n"
    #                 f"  instruction: {json_data.get('prompt', {}).get('data', {}).get('instruction', '')}\n"
    #                 f"  input_prefix: {json_data.get('prompt', {}).get('data', {}).get('input_prefix', '')}\n"
    #                 f"  output_prefix: {json_data.get('prompt', {}).get('data', {}).get('output_prefix', '')}\n"    
    #             )

            
    #             # Add data examples
    #             formatted_output += ( f"  structured_examples:\n")
    #             examples = json_data.get('prompt', {}).get('data', {}).get('examples', [])
    #             for example in examples:
    #                 formatted_output += f"    input: {example[0]}\n"
    #                 formatted_output += f"    output: {example[1]}\n"

    #             formatted_output += ( f"  input:\n")
    #             # Add prompt input 
    #             inputs= json_data.get('prompt', {}).get('input', [])
    #             if inputs:
    #                 formatted_output += f"    {inputs[0]}\n"

    #             # Add external prompt details   
    #             model_parameters = json_data.get('prompt', {}).get('model_parameters', {})
    #             if model_parameters:
    #                 formatted_output += (
    #                     f"\n"
    #                     f"  model_parameters:\n"
    #                     f"     decoding_method: {model_parameters.get('decoding_method', '')}\n"
    #                     f"     max_new_tokens: {model_parameters.get('max_new_tokens', '')}\n"
    #                     f"     min_new_tokens: {model_parameters.get('min_new_tokens', '')}\n"
    #                     f"     random_seed: {model_parameters.get('random_seed', '')}\n"
    #                     f"     stop_sequences: {model_parameters.get('stop_sequences', [])}\n"
    #                     f"     temperature: {model_parameters.get('temperature', '')}\n"
    #                     f"     top_k: {model_parameters.get('top_k', '')}\n"
    #                     f"     top_p: {model_parameters.get('top_p', '')}\n"
    #                     f"     repetition_penalty: {model_parameters.get('repetition_penalty', '')}\n"
    #         )    
    #             # Add external info details    
    #             external_information = json_data.get('prompt', {}).get('external_information', {})
    #             if external_information:
    #                 formatted_output += (
    #                     f"\n"
    #                     f"  detached information:\n"
    #                     f"     prompt_id: {external_information.get('external_prompt_id', '')}\n"
    #                     f"     model_id: {external_information.get('external_model_id', '')}\n"
    #                     f"     model_provider: {external_information.get('external_model_provider', '')}\n"
    #                 )

    #                 # Add external model details
    #                 external_model = external_information.get('external_model', {})
    #                 if external_model:
    #                     formatted_output += (
    #                         f"     model_name: {external_model.get('name', '')}\n"
    #                         f"     model_url: {external_model.get('url', '')}\n"
    #                     )

    #                 # Add external prompt details
    #                 external_prompt = external_information.get('external_prompt', {})
    #                 if external_prompt:
    #                     formatted_output += (
    #                         f"     prompt_url: {external_prompt.get('url', '')}\n"
    #                         f"     Additional Information:\n"
    #                     )
    #                     additional_info = external_prompt.get('additional_information', [])
    #                     for info in additional_info:
    #                         for key, value in info.items():
    #                             formatted_output += f"        {key}: {value}\n"

                    

    #         _logger.info(formatted_output)
        
    #     else:
    #         raise ClientError("Error in fetching the prompt details. Error {}: {}".format(response.status_code, response.text))
    
    
    def get_info(self, verbose=False):
        """
        Get info of the fetched prompt.

        This method retrieves all available details of the fetched prompt and returns them as a dictionary.

        Args:
            verbose (bool): If True, include all details. Default is False.

        Returns:
            dict: A dictionary containing the prompt details.

        Raises:
            ValueError: If no prompt data is available.
        """
        
        _ENV = get_env()
        if get_env() != 'dev' and get_env() != 'test':
            CLOUD_URL = get_cloud_url()
        url = self._prompts_url(self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            json_data = response.json()
            base_url = (CLOUD_DEV_URL if _ENV == "dev" else CLOUD_TEST_URL if _ENV == "test" else (CLOUD_URL if not self._is_cp4d else self._cpd_configs["url"]))
            
            if self._container_type == "space":
                access_url = PROMPT_PATH_SPACE.format(base_url, self._asset_id, self._container_id)
            else:
                access_url = PROMPT_PATH_PROJECT.format(base_url, self._asset_id, self._container_id)

            prompt_details = {
                "asset_id": json_data.get('id', ''),
                "name": json_data.get('name', ''),
                "input_mode": json_data.get('input_mode', ''),
                "model_id": json_data.get('prompt', {}).get('model_id', ''),
                "container_id": self._container_id,
                "container_type":self._container_type,
                "access_url": access_url,
            }

            if json_data.get('input_mode', '') == "detached" and not verbose:
                external_information = json_data.get('prompt', {}).get('external_information', {})
                if external_information:
                    prompt_details["detached_information"] = {
                        "prompt_id": external_information.get('external_prompt_id', ''),
                        "model_id": external_information.get('external_model_id', ''),
                        "model_provider": external_information.get('external_model_provider', ''),
                    }

            if verbose:
                prompt_details.update({
                    "description": json_data.get('description', ''),
                    "created_by": json_data.get('created_by', ''),
                    "model_version": json_data.get('model_version', {}),
                    "prompt_variables": json_data.get('prompt_variables', ''),
                    "task_ids": json_data.get('task_ids', []),
                    "instruction": json_data.get('prompt', {}).get('data', {}).get('instruction', ''),
                    "input_prefix": json_data.get('prompt', {}).get('data', {}).get('input_prefix', ''),
                    "output_prefix": json_data.get('prompt', {}).get('data', {}).get('output_prefix', ''),
                })

                # Add structured examples
                examples = json_data.get('prompt', {}).get('data', {}).get('examples', [])
                prompt_details["structured_examples"] = [
                    {"input": example[0], "output": example[1]} for example in examples
                ]

                inputs = json_data.get('prompt', {}).get('input', [])
                if inputs:
                    prompt_details["input"] = inputs[0]

                # Add model parameters
                model_parameters = json_data.get('prompt', {}).get('model_parameters', {})
                if model_parameters:
                    prompt_details["model_parameters"] = {
                        "decoding_method": model_parameters.get('decoding_method', ''),
                        "max_new_tokens": model_parameters.get('max_new_tokens', ''),
                        "min_new_tokens": model_parameters.get('min_new_tokens', ''),
                        "random_seed": model_parameters.get('random_seed', ''),
                        "stop_sequences": model_parameters.get('stop_sequences', []),
                        "temperature": model_parameters.get('temperature', ''),
                        "top_k": model_parameters.get('top_k', ''),
                        "top_p": model_parameters.get('top_p', ''),
                        "repetition_penalty": model_parameters.get('repetition_penalty', ''),
                    }

                # Add external information
                external_information = json_data.get('prompt', {}).get('external_information', {})
                if external_information:
                    prompt_details["external_information"] = {
                        "prompt_id": external_information.get('external_prompt_id', ''),
                        "model_id": external_information.get('external_model_id', ''),
                        "model_provider": external_information.get('external_model_provider', ''),
                    }

                    # Add external model details
                    external_model = external_information.get('external_model', {})
                    if external_model:
                        prompt_details["external_information"]["external_model"] = {
                            "model_name": external_model.get('name', ''),
                            "model_url": external_model.get('url', ''),
                        }

                    # Add external prompt details
                    external_prompt = external_information.get('external_prompt', {})
                    if external_prompt:
                        prompt_details["external_information"]["external_prompt"] = {
                            "prompt_url": external_prompt.get('url', ''),
                            "additional_information": [
                                {key: value} for info in external_prompt.get('additional_information', [])
                                for key, value in info.items()
                            ]
                        }

            return prompt_details

        else:
            raise ClientError(f"Error in fetching the prompt details. Error {response.status_code}: {response.text}")


    def get_prompt_variables(self)-> str:
        """
        Get the prompt variables of the fetched prompt.

        This method retrieves the prompt variables from the fetched prompt. 

        Returns:
            str: A string representation of the prompt variables.

        Raises:
            ValueError: If no prompt data is available.

        Example::

            prompt.get_prompt_variables()
        """
        # Fetching latest details
        url = self._prompts_url(self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code==200:
            prompt_variables_data = response.json()  
            if not prompt_variables_data:
                raise ValueError("No prompt data is available")
            
            prompt_variables=prompt_variables_data.get('prompt_variables')
            if prompt_variables is not None:
                _logger.info("Successfully retrieved prompt variables: {}".format(prompt_variables))
            else:
                _logger.error("Unable to retrieve prompt variables. The prompt variables are not available.")
        else:
            raise ClientError("There is some error in the fetching the prompt variables.ERROR{}".format(response.status_code))

    ######################## UPDATE PROMPTS#######################################################################################
    

    def update_prompt_attribute(self, key_name:str, value:Any):
        """
            Update a specific attribute of the fetched prompt.

            This method updates a any attribute of the fetched prompt with the provided key name and value.

            Parameters:
                key_name (str): The name of the attribute to be updated.
                value (Any): The new value for the attribute. It can be of any type.

            Raises:
                ClientError: If the update operation fails.

            Example::

                prompt.update_prompt_attribute(key_name="task_id", value="Next steps")
        """
        if self.is_detached():
            raise ClientError("detached prompts updation is not yet supported")
        
        url = self._prompts_url(self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code==200:
            json_data = response.json()
        else:
            response.raise_for_status()

        update_body = {
            "prompt": {
                "model_id": json_data["prompt"].get("model_id"),
                "data": json_data["prompt"].get("data")
            }
        }
        
        if key_name == "model_id":
            update_body["prompt"]["model_id"] = value
        elif key_name in ["instruction", "input_prefix", "output_prefix"]:
            update_body["prompt"]["data"][key_name] = value
        elif key_name == "structured_examples":
            formatted_examples = [[input_text, output_text] for input_text, output_text in value.items()]
            if formatted_examples:
                update_body["prompt"]["data"]["examples"] = formatted_examples
        elif key_name == "model_parameters":
                existing_params = json_data["prompt"].get("model_parameters", {})
                merged_params = self._merge_dicts(existing_params, value)
                update_body["prompt"]["model_parameters"] = merged_params
        elif key_name == "input":
                update_body["prompt"]["input"] = [[value, ""]]
        elif key_name =="task_id":
                validate_enum(value,"task_id",Task,False)
                update_body["task_ids"] = [value]
        elif key_name=="prompt_variables":
                self.update_prompt_variables(prompt_variables=value)
                return
        elif key_name =="model_version":
                #fecthing the exisiting and updating 
                existing_params = json_data.get("model_version", {})
                merged_params = self._merge_dicts(existing_params, value)
                update_body[key_name]= merged_params
        else:  
            update_body[key_name] = value  
        
        url=self._prompts_url(self._asset_id,self._container_type,self._container_id)
        responseVal = requests.patch(url, headers=self._get_headers(), data=json.dumps(update_body, ensure_ascii=False), verify=False)

        if responseVal.status_code == 200:
            _logger.info("Prompt attribute '{}' updated successfully.".format(key_name))
        else:
            if responseVal.status_code == 409:
                 _logger.error("Failed to update prompt attribute '{}'. Modifying the attribute is restricted while the prompt is being tracked.".format(key_name))
            else:
                 _logger.error("Failed to update prompt attribute '{}'. Status code: {}. Error message: {}".format(key_name, responseVal.status_code, responseVal.text))
        
    

    def update_prompt_variables(self,prompt_variables:dict):
        """
            Update the prompt variables for the prompt.

            This method takes a dictionary of prompt variables and updates the prompt variables of the prompt.

            Parameters:
                prompt_variables (dict): A dictionary containing the new prompt variables.

            Example::

                prompt.update_prompt_variables(prompt_variables={"text": {}})
        """
        if prompt_variables=={}:
            raise ValueError("Prompt variables cannot be an empty dictionary.")
        
        url = self._prompts_url(self._asset_id, self._container_type, self._container_id)
        response = requests.get(url, headers=self._get_headers())
        if response.status_code==200:
            existing_params = response.json().get("prompt_variables", {})
        else:
                response.raise_for_status()

        merged_vars = self._merge_dicts(existing_params, prompt_variables)
        update_body = {"prompt_variables": {}}
        for key, value in merged_vars.items():
            if isinstance(value, dict) and 'default_value' in value:
              update_body["prompt_variables"][key] = value
            else:
              update_body["prompt_variables"][key] = {"default_value": value}
        url= self._prompts_url(self._asset_id,self._container_type,self._container_id)
        responseVal = requests.patch(url, headers=self._get_headers(), data=json.dumps(update_body, ensure_ascii=False), verify=False)
        if responseVal.status_code == 200:
             _logger.info("Prompt variables updated successfully.")
        else:
            _logger.error("Failed to update prompt variables. Status code: {}. Reason: {}".format(
             responseVal.status_code, responseVal.text))

    
    def update_prompt_name(self,name:str):
        """
            Update or set the name of the Prompt.

            This method allows the setting or updating of the prompt 'name' to a new value.

            Parameters:
                name (str): The new name to assign to the instance. This should be a non-empty string.

            Example::

                prompt.update_prompt_name(name="NewName")
       """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string.")
        
        update_body={'name': name}
        url=self._prompts_url(self._asset_id,self._container_type,self._container_id)
        responseVal = requests.patch(url, headers=self._get_headers(), data=json.dumps(update_body, ensure_ascii=False), verify=False)
        if responseVal.status_code == 200:
                 _logger.info("Successfully updated prompt name: '{}'.".format(name))
        else:
                _logger.error("Failed to update prompt name: '{}'. Status code: {}. Reason: {}".format(
                name, responseVal.status_code, responseVal.text))

    

    def update_prompt_description(self,prompt_description:str):
        """
            Update or set the description of the prompt.

            This method allows for the setting or updating of prompt description to a new value.

            Parameters:
                prompt_description (str): The new description to assign to the external prompt.

            Example::

                prompt.update_prompt_description(prompt_description="description")
         """
        if not isinstance(prompt_description, str) or not prompt_description.strip():
            raise ValueError("prompt_description must be a non-empty string.")
        
        update_body={'description': prompt_description}
        url=self._prompts_url(self._asset_id,self._container_type,self._container_id)
        responseVal = requests.patch(url, headers=self._get_headers(), data=json.dumps(update_body, ensure_ascii=False), verify=False)
        if responseVal.status_code == 200:
             _logger.info("Successfully updated prompt description: '{}'.".format(prompt_description))
        else:
             _logger.error("Failed to update prompt description: '{}'. Error: {} Reason: {}".format(
              prompt_description, responseVal.status_code, responseVal.text))

    
   

    
    def untrack(self):
        """
            Unlink prompt from it's usecase and approach

            Example for IBM Cloud or CPD:

            >>> prompt.untrack()

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
            _logger.info("Successfully finished unregistering prompt {} from AI use case.".format(
                self._asset_id))
        else:
            error_msg = u'AI use case unregistering failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)

    def get_deployments(self) -> List:
        """
            This method is not available for prompt.
        """
        _logger.info("This method is not available for prompt")

    def delete_deployments(self, deployment_ids: list = None):
        """
            This method is not available for prompt.
        """
        _logger.info("This method is not available for prompt")

    def add_deployments(self, deployments: list = None) -> list:
        """
            This method is not available for prompt.
        """
        _logger.info("This method is not available for prompt")

    # override get_version from parent class for prompt
    def get_version(self) -> Dict:
        """
            Get prompt template version details. Supported for CPD version >=4.7.0

            :rtype: dict

            The way to use me is:

            >>> get_prompt.get_version()

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model version functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)
        linked_ai_usecase_info = {}
        try:
            linked_ai_usecase_info = self._assets_client.get_tracking_model_usecase().to_dict()
            if "model_usecase_id" in linked_ai_usecase_info:
                linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']

            else:
                raise ClientError(
                    f"Version information will be unavailable for untracked Prompt template asset. Please track the Prompt Asset {self._asset_id} to a ai usecase to view the version of the prompt template.", category=UserWarning)

            if linked_ai_usecase:
                _logger.info(
                    f"Prompt Asset {self._asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")

                url = self._get_assets_url(
                    self._asset_id, self._container_type, self._container_id)
                response = requests.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    model_version_details = {}
                    if "model_version" in (response.json()["entity"]["wx_prompt"]):
                        model_version = response.json(
                        )["entity"]["wx_prompt"]["model_version"].get("number")
                        model_version_description = response.json(
                        )["entity"]["wx_prompt"]["model_version"].get("description")

                        model_version_details["number"] = model_version
                        model_version_details["description"] = model_version_description

                        _logger.info(
                            "Model version details retrieved successfully")
                        return model_version_details
                else:
                    raise ClientError("Failed to retrieve model version details information. ERROR {}. {}".format(
                        response.status_code, response.text))

        except ClientError as ce:
            if ce.error_msg.endswith("lmid is missing") or ce.error_msg.endswith("is not tracked by a model use case"):
                warnings.warn(
                    f"Version information unavailable for untracked Prompt template asset. Please track the Prompt Asset {self._asset_id} to ai usecase to view the version of the prompt template.", category=UserWarning)

            else:
                _logger.info(
                    f"Error getting version details for prompt asset {self._asset_id} due to following issue : {ce.error_msg}")
                
  # utils====================================================================================================================================================================================================================================================

    def _prompts_url(self, prompt_id, container_type, container_id):
        base_url = ''
        if self._is_cp4d:
            base_url = self._cpd_configs["url"]
        else:
            env = get_env()
            if env == 'dev':
                base_url = dev_config["DEFAULT_DEV_SERVICE_URL"]
            elif env == 'test':
                base_url = test_config["DEFAULT_TEST_SERVICE_URL"]
            else:
                base_url = prod_config["DEFAULT_SERVICE_URL"]

        url = base_url + '/wx/v1/prompts/' + prompt_id + '?' + container_type + '_id=' + container_id
        return url
    
    def _merge_dicts(self, dict1, dict2):
    #This function mixes dict2 into dict1, updating shared items and combines them.
        if not isinstance(dict2, dict):
            raise TypeError("Input value must be a dictionary.")
        for key in dict2:
                if key in dict1 and isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                    dict1[key] = self._merge_dicts(dict1[key], dict2[key])
                else:
                    dict1[key] = dict2[key]
        return dict1

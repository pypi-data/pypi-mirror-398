import logging
import os
import json
import collections
import ibm_aigov_facts_client._wrappers.requests as requests

from typing import BinaryIO, Dict, List, TextIO, Union, Any
from ibm_aigov_facts_client.factsheet import assets
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal, ContainerType, FactsType, RenderingHints, ModelEntryContainerType, AllowedDefinitionType, FormatType, Icon, Color,Phases
from ibm_aigov_facts_client.utils.utils import validate_enum, validate_type
from ibm_aigov_facts_client.utils.cell_facts import CellFactsMagic

from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.constants import get_cloud_url

from ibm_aigov_facts_client.factsheet.approaches import ApproachUtilities
from ibm_aigov_facts_client.factsheet.html_parser import FactHTMLParser

_logger = logging.getLogger(__name__)


class AIUsecaseUtilities(ModelUsecaseUtilities):

    """
        AI use case utilities. Running `client.assets.get_ai_usecase()` makes all methods in AIUsecaseUtilities object available to use.

    """

    def __init__(self, assets_client: 'assets.Assets', model_id: str = None, ai_usecase_name:str=None,model_usecase_id: str = None, container_type: str = None, container_id: str = None, facts_type: str = None) -> None:
        """
        Initialize a AIUsecaseUtilities object.

        """

        # Calling parent class constructor
        # super().__init__(assets_client,model_id,model_usecase_id,container_type,container_id,facts_type)

        self._asset_id = model_usecase_id
        self._ai_usecase_name=ai_usecase_name
        self._container_type = container_type
        self._container_id = container_id
        self._facts_type = facts_type

        self._assets_client = assets_client

        self._facts_client = assets_client._facts_client
        self._is_cp4d = assets_client._is_cp4d
        self._external_model = assets_client._external_model

        if self._is_cp4d:
            self._cpd_configs = assets_client._cpd_configs
            self._cp4d_version = assets_client._cp4d_version

        self._facts_definitions = self._get_fact_definitions()
        self.associated_workspaces = []

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'AIUsecaseUtilities':
        """Initialize a AIUsecaseUtilities object from a json dictionary."""
        args = {}
        if '_asset_id' in _dict:
            args['asset_id'] = _dict.get('_asset_id')
        
        if '_ai_usecase_name' in _dict:
            args['ai_usecase_name'] = _dict.get('_ai_usecase_name')

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
        if hasattr(self, '_ai_usecase_name') and self._ai_usecase_name is not None:
            _dict['ai_usecase_name'] = self._ai_usecase_name
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
        """Return a `str` version of this AIUsecaseUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def __repr__(self):
        """Return a `repr` version of this AIUsecaseUtilities object."""
        return json.dumps(self.to_dict(), indent=2)

    def get_info(self, verbose=False) -> Dict:
        """Get AI usecase details

        :param verbose: If True, returns additional model details. Defaults to False
        :type verbose: bool, optional
        :rtype: dict

        The way to use me is:

        >>> get_ai_usecase.get_info()
        >>> get_ai_usecase.get_info(verbose=True)

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

                additional_data["ai_usecase_name"] = model_name
                if desc:
                    additional_data["description"] = desc
                additional_data["asset_type"] = asset_type
                additional_data["url"] = url
                cur_metadata.pop('ai_usecase_name', None)  # Remove 'name' from cur_metadata if it exists
                additional_data.update(cur_metadata)
                # additional_data.update(cur_metadata)
                return additional_data
            else:
                raise ClientError("Failed to get additional AI usecase information. ERROR {}. {}".format(
                    response.status_code, response.text))
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

    def create_approach(self, name: str = None, description: str = None, icon: str = None, color: str = None) -> ApproachUtilities:
        """
            Returns WKC Model usecase approach. Supported for CPD version >=4.7.0

            :param str name: Name of approach
            :param str description: (Optional) Description of approach
            :param str icon: (Optional) Approach's icon Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Icon`
            :param str color: (Optional) Approach's color,Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Color`
            :rtype: ApproachUtilities

            :return: WKC Model usecase approach

            Example,::

               ai_usecase.create_approach(name=<approach name>,description=<approach description>,icon=<approach icon>,color=<approach color>)
               ai_usecase.create_approach(name=<approach name>)

        """

        if self._is_cp4d and self._cp4d_version < "4.7.0":
            raise ClientError(
                "Version mismatch: Model usecase, create approach functionality is only supported in CP4D version 4.7.0 or higher. Current version of CP4D is "+self._cp4d_version)

        model_asset_id = self._asset_id
        model_container_type = self._container_type
        model_container_id = self._container_id

        if (name is None or name == ""):
            raise MissingValue("name", "approach name is missing")
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
            return ApproachUtilities(self, approach_id=ret_create_approach.get('id'), approach_name=ret_create_approach.get('name'), approach_desc=ret_create_approach.get('description'), approach_icon=ret_create_approach.get('icon'), approach_icon_color=ret_create_approach.get('icon_color'), model_asset_id=model_asset_id, model_container_type=model_container_type, model_container_id=model_container_id)
            # return response.json()
        else:
            raise ClientError("Failed while creating an approach. ERROR {}. {}".format(
                response.status_code, response.text))


    # Workspace related changes

    def list_all_associated_workspaces(self) -> None:
        """
        Lists all Associated Workspaces for a given AI usecase in tabular format. The method will display the Associated Workspaces for all the phases.

        :returns: None

        Example,::
              client.assets.model_usecase.get_associated_workspaces(model_usecase_id=<model usecase id>,catalog_id=<model inventory id>))

        """
        super().list_all_associated_workspaces()


    def list_associated_workspaces_by_phase(self,phase_name: Phases = None) -> list:
        """
        Lists all Associated Workspaces for a given AI usecase in tabular format. The method will display the filtered Associated Workspaces ,
        filtered by the phase name passed

        :param phase_name : phase name. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Phases`

        :returns: list

        Example,::
              client.assets.model_usecase.get_associated_workspaces(model_usecase_id=<model usecase id>,catalog_id=<model inventory id>, phase_name=<valid phase name>))
        """
        workspace_list=super().list_associated_workspaces_by_phase(phase_name=phase_name)
        return workspace_list

    def add_workspaces_associations(self, ai_usecase_id: str = None, catalog_id: str = None,
                                    workspace_id: str = None, workspace_type: str = None, phase_name: str = None):
        '''
            Associate a workspace to a particular AI usecase under a specified phase

            :param workspace_id:project id or space id which needs to associated to the selected usecase
            :param workspace_type: should be "project" when passing "project id" as workspace_id , if space id is passed for workspace_id,the workspace_type will be "space"
            :param phase_name:phase name, should be one of 'develop','validate' and 'operate'. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Phases`

            :return:None

            Example,::

                # client.assets.model_usecase.add_workspaces_associations(model_usecase_id=<model usecase id>,catalog_id=<model inventory id>, phase_name=<valid phase name>, workspace_id=<project or space id>, workspace_type=<"project" or "space">)
        '''
        super().add_workspaces_associations(workspace_id = workspace_id, workspace_type= workspace_type,phase_name=phase_name)


    def remove_workspace_associations(self, workspace_ids: list = None) -> None:
        '''
        Removes association of one or more workspaces at once from a particular AI usecase, irrespective of the phase they are in.
        The disassocation works only if there are no tracked assets in the workspace(s) to be removed. User should have edit access to the usecase.

        :param workspace_ids: list of workspace ids to be disassociated. eg: workspace_ids=[project_id_1, space_id_1]
        :return:None

            Example,::

            client.assets.model_usecase.remove_workspace_associations(model_usecase_id=<model usecase id>,catalog_id=<model inventory id>, workspace_ids=<list of project or space id>)
        '''

        super().remove_workspace_associations(workspace_ids=workspace_ids)

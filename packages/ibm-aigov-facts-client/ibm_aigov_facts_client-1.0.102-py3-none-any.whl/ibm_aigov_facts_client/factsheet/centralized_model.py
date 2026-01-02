import logging
import ibm_aigov_facts_client._wrappers.requests as requests


from ibm_watsonx_ai import APIClient
from ibm_aigov_facts_client.client import fact_trace
from ibm_aigov_facts_client.utils.config import *
from ibm_cloud_sdk_core.utils import convert_model
from ibm_aigov_facts_client.utils.enums import  FactsType
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.client_errors import *
from typing import BinaryIO, Dict, List, TextIO, Union, Any
import json
import uuid
import re
from ibm_aigov_facts_client.utils.enums import ModelContainerType
from ibm_aigov_facts_client.utils.utils import validate_enum
from packaging import version as pkg_version
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_aigov_facts_client.factsheet.approaches import ApproachUtilities


_logger = logging.getLogger(__name__)





class CentralizedModel:

    def __init__(self, facts_client: 'fact_trace.FactsClientAdapter'):
        """
        Initialize the CentralizedModel class.

        :param facts_client: Instance of FactsClientAdapter
        """
        self._facts_client = facts_client
        self._container_type = facts_client._container_type
        self._container_id = facts_client._container_id
        self._is_cp4d = facts_client._is_cp4d
        self._asset_id = None
        self._model_id = None
        self._model_usecase_id = None
        self._current_model = None
        self._current_model_usecase = None
        self._facts_type = FactsType.MODEL_FACTS_USER
        self._external_model = self._facts_client._external
        self._cpd_op_enabled = False
        self._facts_definitions = None
        self.DISABLE_LOGGING = False
        self._account_id = self._facts_client._account_id

        if self._is_cp4d:
            self._cpd_configs=convert_model(facts_client.cp4d_configs)
            self._cp4d_version=facts_client._cp4d_version


    def _get_headers(self):

        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
            isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
            isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers

    def store_model(self,model_meta: dict ,model:str, inventory_id:str ):
        """
          Publishes a model to IBM watsonx.ai repository.
          :param model: Local path to the model file (e.g., .pmml or .zip)
          :param model_meta: Metadata properties for the model (e.g., name, software spec, type)
          :param inventory_id: inventory id we the model will be published to
          :return: The published model metadata (dict) or None if failed

          The way to use me is,::

          centralized_model.store_model(model=model, model_meta=meta_props, inventory_id= inventory_id)
          """
        try:
            Credentials = {
                "url": self._cpd_configs['url'],
                "username": self._cpd_configs['username'],
                "password" : self._cpd_configs['password'],
                "instance_id": "openshift"
            }

            client = APIClient(Credentials)

            #project creation
            project_id = self._create_project()
            client.set.default_project(project_id)

            _logger.info("Storing model ...")
            #store model to the created project
            published_model = client.repository.store_model(model=model, meta_props=model_meta)

            _logger.info("Model published successfully.")
            model_id = published_model.get("metadata", {}).get("id")
            #Publish model from Project to Inventory
            model_in_inventory = self._publish_asset_to_inventory(model_id, project_id, inventory_id)
            #delete the created project
            self._delete_project(project_id)
            published_model['metadata'].pop('project_id', None)
            return model_in_inventory
        except Exception as e:
            self._delete_project(project_id)
            _logger.error("Failed to publish model: {}".format( str(e)))
            _logger.info("Supported file types: PMML model file (.xml) or a ZIP containing one of the following: (.h5), (.hdf5), (.onnx), (.pickle), (.pkl), (.pt), or (.pb).")
            return None

    def _publish_asset_to_inventory(self, asset_id: str, project_id: str, catalog_id: str):
        """
        Publishes a project asset to a catalog in CP4D.

        :param asset_id: ID of the asset in the project
        :param project_id: ID of the project
        :param catalog_id: ID of the catalog to publish to
        :return: Response JSON or error details
        """

        try:
            url = self._get_publish_asset_url(asset_id,project_id)

            # You can modify these as needed
            payload = {
                "catalog_id": catalog_id,
                "mode": 0,
                "metadata": {
                    "name": "GermanCreditRiskModelChallengerICP",
                    "description": "",
                    "tags": []
                }
            }


            response = requests.post(url, headers=self._get_headers(), json=payload)
            publish_asset_response = response.json()

            if response.status_code == 200:
                _logger.info("Asset {} published successfully to inventory ID {}." .format(publish_asset_response["asset_id"],catalog_id))
                return publish_asset_response
            else :
                _logger.error("Failed to publish asset to an inventory. Status code: {}, Response: {}".format(
                    response.status_code, response.text))

        except Exception as err:
            _logger.error("Failed to publish model to an inventory: {}".format( str(err)))

    def _create_project(self):
        url = self._get_project_url()
        aid = str(uuid.uuid4())

        payload = {
            "name": f"Import Assets Project-{aid[:8]}",
            "description": "A project for staging asset imports to an inventory",
            "generator": "model-governance-project",
            "public": False,
            "enforce_members": True,
            "tags": ["Model-governance-project"],
            "storage": {
                "type": "assetfiles"
            }
        }
        project_id = None

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            if response.status_code == 201:
                response_data = response.json()
                project_id = response_data['location'].split('/')[-1]
                _logger.info("Project created successfully. ID: {}".format( project_id))
            else :
                _logger.error("Failed to create project. Status code: {}, Response: {}".format(
                              response.status_code, response.text))

        except Exception as e:
            _logger.error("Exception while creating project: {}".format (str(e)))

        return project_id

    def _delete_project(self, project_id: str) -> bool:
        """
        Deletes a project by project ID.

        :param project_id: The ID of the project to delete
        :return: True if deleted successfully, False otherwise
        """
        url = self._get_project_url() +'/'+ project_id

        try:
            response = requests.delete(url, headers=self._get_headers())

            if response.status_code == 204:
                _logger.info("Project deleted successfully: {}".format( project_id))
                return True
            else:
                _logger.error("Failed to delete project {}. Status: {}. Response: {}".format(
                              project_id, response.status_code, response.text))
                return False

        except Exception as e:
            _logger.error("Exception occurred while deleting project {}: {}".format( project_id, str(e)))
            return False

    def copy_assets_to_container(self, inventory_id: str, asset_id: str, container_type: str, container_id: str, metadata_overrides: dict[str, Any] = None):
        """
            copy asset from Inventory to Project or Space

            :param inventory_id: inventory id.
            :param list asset_id: List of assets ID's to be deleted.
            :param container_type: container type.
            :param container_id: container id.
            :param metadata_overrides: (optional) metadata_overrides.

            :rtype: None

            :return: assets copied successfully to a container.

            The way to use me is,::

                centralized_model.copy_assets_to_container(inventory_id,asset_id,container_type,container_id)
        """
        try:
            if (asset_id is not None ):
                params = {}
                params["asset_ids"] = asset_id
                payload  = {}
                payload["container"] = container_type
                payload["container_id"] = container_id
                payload["metadata_overrides"] = metadata_overrides
                url = self._get_externally_managed_asset_in_inventory_url(inventory_id)+ "copy_assets"
                response = requests.post(url, headers=self._get_headers(), params=params,data=json.dumps(payload))
                if response.status_code == 200:
                    _logger.info("Asset " + asset_id +
                                 " copied successfully")
                else:
                    raise ClientError("Failed in copy Assets. ERROR {}. {}".format(
                        response.status_code, response.text))
            else:
                raise MissingValue(
                    "asset_id", "Missing asset_id")
        except Exception as e:
            _logger.error("Exception occurred while copying asset to container {}: {}".format( container_id, str(e)))

    def delete_externally_managed_assets(self, inventory_id: str, asset_id: str ):
        """
            Delete externally managed assets in Inventory

            :param inventory_id: inventory id.
            :param asset_id: List of assets ID's to be deleted.

            :rtype: None

            :return: assets are deleted.

            The way to use me is,::

                centralized_model.delete_deployments(inventory_id,asset_id)
        """
        try:
            if (asset_id is not None ):
                params = {}
                params["asset_ids"] = asset_id
                url = self._get_externally_managed_asset_in_inventory_url(inventory_id)+ "assets"
                response = requests.delete(url, headers=self._get_headers(), params=params)
                if response.status_code == 200:
                    _logger.info("Asset " + asset_id +
                                 " deleted successfully")
                else:
                    raise ClientError("Failed in deleting Assets. ERROR {}. {}".format(
                        response.status_code, response.text))
            else:
                raise MissingValue(
                    "asset_id", "Missing asset_id")
        except Exception as e:
            _logger.error("Exception occurred while deleting asset {}: {}".format( asset_id, str(e)))

    def get_externally_managed_assets(self, inventory_id: str):
        """
            Get  externally managed assets in an inventory

            :param inventory_id: inventory id.

            :return: externally managed asset

            The way to use me is,::

               centralized_model.get_externally_managed_asset(inventory_id)

        """

        try:
            url = self._get_externally_managed_asset_in_inventory_url( inventory_id) + "assets"

            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                _logger.info("Assets retrieved successfully")
                assets_list = response.json()
                return assets_list
            else:
                raise ClientError("Failed in retrieving deployments. ERROR {}. {}".format(
                    response.status_code, response.text))
        except Exception as e:
            _logger.error("Exception occurred while retrieving assets from inventory {}: {}".format( inventory_id, str(e)))

    def get_all_externally_managed_assets(self):
        """
            Get all externally managed assets in an account

            :return: externally managed asset

            The way to use me is,::

               centralized_model.get_externally_managed_asset()

        """

        try:
            url = self._get_all_externally_managed_asset_url()

            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                _logger.info("Assets retrieved successfully")
                assets_list = response.json()
                return assets_list
            else:
                raise ClientError("Failed in retrieving deployments. ERROR {}. {}".format(
                    response.status_code, response.text))
        except Exception as e:
            _logger.error("Exception occurred while retrieving assets: {}".format( str(e)))

    def track_externally_managed_asset(self, asset_id: str , inventory_id: str , usecase: ModelUsecaseUtilities = None, approach: ApproachUtilities = None, grc_model: dict = None, version_number: str = None, version_comment: str = None):
        """
            Link Model to model use case. Model asset should be stored in either Project or Space and corrsponding ID should be provided when registering to model use case.

            Supported for CPD version >=4.7.0

            :param ModelUsecaseUtilities usecase: Instance of ModelUsecaseUtilities
            :param ApproachUtilities approach: Instance of ApproachUtilities
            :param asset_id : The asset id
            :param inventory_id : The inventory id
            :param str grc_model: (Optional) Openpages model id. Only applicable for CPD environments. This should be dictionary, output of get_grc_model()
            :param str version_number: Version number of model. supports either a semantic versioning string or one of the following keywords for auto-incrementing based on the latest version in the approach: "patch", "minor", "major"
            :param str version_comment: (Optional) An optional comment describing the changes made in this version

            :rtype: ModelAssetUtilities

            For tracking model with model usecase:

            >>> centralized_model.track(usecase=<instance of ModelUsecaseUtilities>,approach=<instance of ApproachUtilities>,version_number=<version>)
        """

        output_width = 125
        print("-" * output_width)
        print("Tracking Process Started".center(output_width))
        print("-" * output_width)

        if self._is_cp4d and self._cp4d_version < "4.6.5":
            raise ClientError(
                "Version mismatch: Track model with model usecase and approach functionality is only supported in CP4D version 4.6.5 or higher. Current version of CP4D is " + self._cp4d_version)

        if (usecase is None or usecase == ""):
            raise MissingValue(
                "ai usecase", "ModelUsecaseUtilities object or instance is missing")

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

        payload = {}
        version_details = {}

        model_usecase_id = usecase.get_id()
        model_usecase_catalog_id = usecase.get_container_id()
        model_usecase_name = usecase.get_name()

        approach_id = approach.get_id()
        approach_name = approach.get_name()
        model_asset_id = asset_id

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
            versionList.append(version["number"])
        finalVersionValList = self._finalVersion(versionList)
        finalVersionVal = finalVersionValList[-1]

        payload['usecase_inventory_id'] = model_usecase_catalog_id or self._assets_client._get_pac_catalog_id()
        payload['usecase_id'] = model_usecase_id

        version_details['approach_id'] = approach_id

        if version_comment:
            version_details['comment'] = version_comment

        if version_number in ["major", "minor", "patch"]:
            finalVersionVal = self._increment_ver(finalVersionVal, version_number)
        else:
            finalVersionVal = version_number

        latest_version = latest_version_data['number'] if latest_version_data else None
        latest_version = pkg_version.parse(latest_version)
        requested_version = pkg_version.parse(finalVersionVal)

        if latest_version > requested_version:
            _logger.warning(
                f"The latest version in this approach is {latest_version}. Please confirm that you want to assign a lower version number to this model.")

        version_details['number'] = finalVersionVal

        payload['version_details'] = version_details

        if grc_model:
            payload['grc_model_id'] = grc_model.get('GrcModel').get('id')

        url = self._get_externally_managed_asset_url(asset_id, inventory_id) + "track"

        if model_usecase_id:
            _logger.info("Initiate linking model to existing AI usecase {}".format(
                model_usecase_id))
        else:
            _logger.info("Initiate linking model to new AI usecase......")


        response = requests.post(url,
                                 headers=self._get_headers(),
                                 data=json.dumps(payload) )

        if response.status_code == 200:
            _logger.info("Successfully finished linking Model {} to AI usecase".format(
                model_asset_id))

        else:
            error_msg = u'Model registration failed'
            reason = response.text
            _logger.info(error_msg)
            raise ClientError(error_msg + '. Error: ' +
                              str(response.status_code) + '. ' + reason)
        return response.json()



    def untrack_externally_managed_asset(self, asset_id: str, inventory_id: str):

        """
            untrack model from it's usecase and approach

            :param asset_id: asset id.
            :param inventory_id: inventory id.

             The way to use me is,::

            >>> centralized_model.untrack()

        """
        try:
            _logger.info(
                "Starting to untrack the model asset {} ".format(asset_id))

            url = self._get_externally_managed_asset_url(asset_id, inventory_id) + "untrack"
            response = requests.delete(url, headers=self._get_headers())
            if response.status_code == 204:
                _logger.info(
                    "Successfully completed untracking of Watsonx Governance model asset {} .".format(
                        asset_id))
            else:
                error_msg = u'untracking model asset'
                reason = response.text
                _logger.info(error_msg)
                raise ClientError(error_msg + '. Error: ' +
                                  str(response.status_code) + '. ' + reason)
        except Exception as e:
            _logger.error("Exception occurred while untracking asset {} : {}".format( asset_id, str(e)))

    def set_phase_for_externally_managed_asset(self, to_container: str, asset_id: str, inventory_id: str) -> None:
        """
            Set  externally managed assets to a phase

            :param to_container: container phase .
            :param asset_id: asset id
            :param inventory_id: inventory id

            :return: externally managed asset

            The way to use me is,::

               centralized_model.get_externally_managed_asset(inventory_id)

        """
        try:

            if  to_container == '':
                raise ClientError(
                    "To containers can not be empty string")
            validate_enum(to_container, "to_container",
                          ModelContainerType, True)
            url = self._get_externally_managed_asset_url(asset_id, inventory_id) + "lifecycle_phase"
            params = {}
            params['to'] = to_container
            response = requests.post(url,
                                     headers=self._get_headers(),
                                     params=params)
            if response.status_code == 200:
                _logger.info("Asset successfully moved to {} environment".format( to_container))
            else:
                raise ClientError("Asset space update failed. ERROR {}. {}".format(
                    response.status_code, response.text))
        except Exception as e:
            _logger.error("Exception occurred while setting phase for asset {} : {}".format( asset_id, str(e)))

    def _get_externally_managed_asset_in_inventory_url(self, inventory_id: str):
        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/v1/aigov/inventories/' + inventory_id  + "/"
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id  + "/"
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id  + "/"
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id  + "/"
        return url

    def _get_project_url(self):
        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/transactional/v2/projects'
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/transactional/v2/projects'
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/transactional/v2/projects'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/transactional/v2/projects'
        return url

    def _get_all_externally_managed_asset_url(self):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                  '/v1/aigov/inventories/assets'
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/inventories/assets/'
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/inventories/assets/'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/inventories/assets/'
        return url

    def _get_externally_managed_asset_url(self, asset_id: str, inventory_id: str):
        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/v1/aigov/inventories/' + inventory_id + '/assets/' + asset_id + "/"
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/assets/' + asset_id + "/"
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/assets/' + asset_id + "/"
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/assets/' + asset_id + "/"
        return url

    def _get_publish_asset_url(self, asset_id, project_id):
        if self._is_cp4d:

            url = self._cpd_configs["url"] + \
                  '/v2/assets/'+ asset_id +'/publish?project_id='+project_id+'&duplicate_action=IGNORE'
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v2/assets/'+ asset_id +'/publish?project_id='+project_id+'&duplicate_action=IGNORE'
            elif get_env() == 'test':
                    url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                          '/v2/assets/'+ asset_id +'/publish?project_id='+project_id+'&duplicate_action=IGNORE'
            else:
                    url = prod_config["DEFAULT_SERVICE_URL"] + \
                          '/v2/assets/'+ asset_id +'/publish?project_id='+project_id+'&duplicate_action=IGNORE'
        return url

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


import logging
import ibm_aigov_facts_client._wrappers.requests as requests


from ..utils.client_errors import *
from typing import BinaryIO, Dict, List, Any, Sequence

from ibm_aigov_facts_client.client import fact_trace
from ibm_aigov_facts_client.factsheet import assets

from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.factsheet import assets


_logger = logging.getLogger(__name__)


class Utils:

    def __init__(self, facts_client: 'fact_trace.FactsClientAdapter'):
        self._is_cp4d = facts_client._is_cp4d
        self._facts_client = facts_client
        if self._is_cp4d:
            self._cpd_configs = facts_client.cp4d_configs
            self._cp4d_version = facts_client._cp4d_version
        self.assets_client = assets.Assets(self._facts_client)
        self._account_id=self._facts_client._account_id

    def get_cloud_object_storage_instances(self) -> List[Dict]:
        """
        Retrieves a list of cloud object storage instances.

        This method queries and returns information about all cloud object storage instances available in IBM Cloud.

        .. warning::
            **Note:**
            This method is applicable only in IBM Cloud and is not available in the Watsonx Governance platform.

        Returns:
            List[Dict]: A list of dictionaries, where each dictionary represents a cloud object storage instance
                        with the following keys:
                        
                        - Name: The name of the cloud object storage instance.
                        - GUID: The globally unique identifier (GUID) of the instance.
                        - Created ID: The identifier of the creation event.
                        - Creator Name: The name of the creator of the instance.


        Example:
            >>> storage_instances = obj.get_cloud_object_storage_instances()
            >>> for instance in storage_instances:
            >>>     print(instance['Name'], instance['GUID'])
        
        """
        
        if self._is_cp4d:
            raise ClientError("This method is not allowed in the on-prem environment")
        try:
            # Send the GET request
            _ENV = get_env()
            resource_url = RESOURCES_URL_MAPPING_NEW.get(_ENV)
            if not resource_url:
                raise ValueError("Resource URL for environment is not defined")
            
            response = requests.get(resource_url, headers=self._get_headers())
            
            # Check the status code
            if response.status_code == 200:
                data = response.json() 
                instances = []
                for resource in data.get('resources', []):
                    resource_id = resource.get('id', '')
                    if ':cloud-object-storage' in resource_id:
                        name = resource.get('name', 'Not Available')
                        guid = resource.get('guid', 'Not Available')
                        created_id = resource.get('created_by', 'Not Available')
                        creator_name = self._fetch_user_name(created_id)
                        
                        instances.append({
                            'Name': name,
                            'GUID': guid,
                            'Created ID': created_id,
                            'Creator Name': creator_name
                        })
                
                return instances
            else:
                _logger.error(f"Failed to fetch data. Status code: {response.status_code}")
                return []

        except Exception as e:
            _logger.error(f"An error occurred while fetching cloud object storage instances: {e}")
            return []
    

        # utils============================


    def get_current_phase_master_copy(self, asset_id:str, catalog_id:str) -> Dict:
        """
            **Get the Current Phase of the Master Copy**

            This method retrieves the current phase information for a specific master copy based on the provided `asset_id` and `catalog_id`.

            Args:
                - asset_id (str): The unique identifier of the asset. This parameter is required for retrieving asset information.
                - catalog_id (str): The identifier for the container that holds the asset. This parameter is required for fetching the data.

            Returns:
                dict: A dictionary containing the current phase information of the master copy.

            Example:
                >>> current_phase = client.utilities.get_current_phase_master_copy(asset_id="asset_id", catalog_id="catalog_id")
                # Retrieve current phase for the specified asset and container

            Raises:
                - ClientError: If any required parameter is missing, or if the asset data or current phase data cannot be retrieved.
        """
        try:
            if not asset_id:
                raise ClientError("Missing required parameter: asset id")
            if not catalog_id:
                raise ClientError("Missing required parameter: catalog id")
            # Fetch the initial asset data
            master_copy_info = self._fetch_master_copy_information(asset_id,catalog_id)
            if not master_copy_info:
                raise ClientError("Missing master copy information in response.")
            inventory_id = master_copy_info.get('inventory_id')
            master_copy_id = master_copy_info.get('master_copy_id')

            if not inventory_id or not master_copy_id:
                raise ClientError("Missing inventory id or master copy id in master copy information.")

            # Retrieve the current phase data
            current_phase_url = self._retrieve_current_phase_url(inventory_id, master_copy_id)
            response = requests.get(current_phase_url, headers=self._get_headers())

            if response.status_code != 200:
                raise ClientError(f"Failed to fetch current phase data. Status code: {response.status_code}")

            _logger.info(f"Successfully fetched current phase for inventory ID: {inventory_id} and master copy ID: {master_copy_id}")
            return response.json()

        except Exception as e:
            # Handle exception
            raise ClientError(f"An error occurred while retrieving the current phase of the master copy: {str(e)}")


    def set_current_phase_master_copy(self, asset_id:str, catalog_id:str, active_phase: str) -> Dict:
        """
            **Set the Current Phase of the Master Copy**

              This method sets the phase for a specific master copy asset, given an `asset_id`, `catalog_id`, and the desired `active_phase`.

            Args:
                - asset_id (str): The unique identifier of the asset.
                - catalog_id (str): The identifier for the container that holds the asset.
                - active_phase (str): The phase to set for the asset (e.g., "Develop", "Validate", "Operate", "Decommissioned").

            Returns:
                A dictionary containing the response data.

            Example:
                >>> response = client.utilities.set_inventory_phase(asset_id="asset_id", catalog_id="catalog_id", active_phase="Develop")
                 # Sets the phase for the specified asset and catalog


            Raises:
                - ClientError: If any required parameter is missing, or if the request fails.
        """
        try:
            if not asset_id:
                raise ClientError("Missing required parameter: asset id")
            if not catalog_id:
                raise ClientError("Missing required parameter: catalog id")
            if not active_phase:
                raise ClientError("Missing required parameter: active phase")

            # Fetch the initial asset data
            master_copy_info = self._fetch_master_copy_information(asset_id,catalog_id)
            if not master_copy_info:
                raise ClientError("Missing master copy information in response.")
            inventory_id = master_copy_info.get('inventory_id')
            master_copy_id = master_copy_info.get('master_copy_id')

            if not inventory_id or not master_copy_id:
                raise ClientError("Missing inventory id or master copy id in master copy information.")

            # Construct the body for the POST request
            request_body = {
                "active_phase": active_phase
            }
            # Retrieve the current phase data
            current_phase_url = self._retrieve_current_phase_url(inventory_id, master_copy_id)
            response = requests.post(current_phase_url, json=request_body, headers=self._get_headers())

            if response.status_code != 200:
                error_message = response.text
                raise ClientError(f"Failed to set inventory phase. Status code: {response.status_code}, Error: {error_message}")

            # Return the response data if successful
            _logger.info(f"Successfully set phase for inventory ID: {inventory_id} and master copy ID: {master_copy_id}")
            return response.json()

        except Exception as e:
            # Handle exception
            raise ClientError(f"An error occurred while setting the current phase of the master copy: {str(e)}")


    def get_all_master_copies(self, inventory_id:str) -> Dict:
        """
         **Get All Master Copies**

        Retrieves all master copies associated with the provided inventory ID.

        Args:
            inventory_id (str): The unique identifier for the inventory.

        Returns:
            Dict: A dictionary containing the master copies information.

        Example:
            >>> master_copies = client.utilities.get_all_master_copies(inventory_id="inventory_id")
            # all master copies for the specified inventory

        Raises:
            ClientError: If the parameter is missing, or if the request fails.
        """
        try:
            if not inventory_id:
                raise ClientError("Missing required parameter: inventory_id")

            url = self._retrieve_all_master_copies_url(
                inventory_id)
            _logger.info(f"Fetching master copies information")
            # Fetch master copies details
            response = requests.get(url, headers=self._get_headers())

            if response.status_code != 200:
                raise ClientError(f"Failed to fetch master copies information. Status code: {response.status_code}")

            # Return the master copies information if successful
            _logger.info(f"Successfully fetched master copies information for the given inventory ID")
            return response.json()

        except Exception as e:
            # Handle exception
            raise ClientError(f"An error occurred while retrieving the master copies information for an inventory: {str(e)}")

    def _retrieve_all_master_copies_url(self, inventory_id ):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                  '/v1/aigov/inventories/' + inventory_id + '/master_copies/'
        else:
            if get_env() == 'dev' or get_env()==AWS_DEV :
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/'
            elif get_env() == 'test' or get_env()==AWS_TEST:
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/'
        return url

    def _get_headers(self):
  
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers
    

    def get_external_model_governance_config_url(self) -> str:
         
        if aws_env() in {AWS_MUM, AWS_DEV, AWS_TEST,AWS_GOVCLOUD_PREPROD,AWS_GOVCLOUD}:
            bss_id = self._account_id
        elif self._is_cp4d:
            bss_id = self._get_bss_id_cpd()
        else:
            bss_id = self._get_bss_id()
        
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev':
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test':
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

    
        url = f"{base_url}/v1/aigov/model_inventory/externalmodel_config?bss_account_id={bss_id}"
        return url
    
    def _get_openpages_instance_url(self,instances=False):
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev' or get_env()==AWS_DEV:
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test' or get_env()==AWS_TEST:
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

    
        url = f"{base_url}/v1/aigov/model_inventory/grc/config"
        if instances:
          url = f"{base_url}/v1/aigov/model_inventory/grc/instances"

        return url
    
    def _fetch_user_name(self, user_id: str) -> str:
        try:
            env= get_env()
            if env in (AWS_MUM, AWS_DEV, AWS_TEST):
                if env in (AWS_DEV ,AWS_TEST):
                    url =f"{aws_test['API_URL']}/api/2.o/accounts"
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
                    url= aws_govcloud['DEFAULT_SERVICE_URL']
                else:
                    url= aws_govcloudpreprod['DEFAULT_TEST_SERVICE_URL']
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

    def _fetch_master_copy_information(self, asset_id, catalog_id):
        url = self._get_assets_url(
            asset_id, "catalog", catalog_id
        )
        response = requests.get(url, headers=self._get_headers())

        if response.status_code != 200:
            _logger.error(f"Failed to fetch asset data. Status code: {response.status_code}")

        # Extract master copy details from the response
        _logger.info("Successfully fetched asset data.")
        data = response.json()

        master_copy_info = data.get('entity', {}).get('modelfacts_system', {}).get('mastercopy_information',None)
        return master_copy_info

    def _retrieve_current_phase_url(self, inventory_id, master_copy_id):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                  '/v1/aigov/inventories/' + inventory_id + '/master_copies/' + master_copy_id + '/active_phase'
        else:
            if get_env() == 'dev' or get_env()==AWS_DEV:
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/' + master_copy_id + '/active_phase'
            elif get_env() == 'test' or get_env()==AWS_TEST:
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/' + master_copy_id + '/active_phase'
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v1/aigov/inventories/' + inventory_id + '/master_copies/' + master_copy_id + '/active_phase'
        return url

    def _get_assets_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                  '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        else:
            if get_env() == 'dev' or get_env()==AWS_DEV:
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                      '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            elif get_env() == 'test'  or get_env()==AWS_TEST:
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                      '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                      '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        return url

    def _retrieve_user_profile_url(self, external_model_admin: str) -> str:
        if self._is_cp4d:
            url = self._cpd_configs['url'] + \
                '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
        else:
            if get_env() == 'dev' or get_env()==AWS_DEV:
                url = dev_config['DEFAULT_DEV_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
            elif get_env() == 'test'  or get_env()==AWS_TEST:
                url = test_config['DEFAULT_TEST_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
            else:
                url = prod_config['DEFAULT_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin

        return url
    
    def get_master_copy_info(self, model_id: str , container_type: str= None, container_id: str= None):
        """  
        Retrieves the master copy Id and Inventory Id from mastercopy information
        
        Returns:
            master copy id , inventory id
        Example:
           >>> client.utilities.get_master_copy_id  
        Raises:
            ClientError: If the master copy information is missing, or if the request fails.
        """
        try:
            asset_url = self.assets_client._get_assets_url(
                model_id, container_type, container_id)
            response = requests.get(asset_url, headers=self._get_headers())
            if response.status_code == 200:
                asset_response = response.json()
                master_copy_info = asset_response.get('entity', {}).get(
                    'modelfacts_system', {}).get('mastercopy_information', None)
                if not master_copy_info or not master_copy_info['master_copy_id'] or not master_copy_info['inventory_id']:
                    raise ClientError(
                        "Master Copy ID or Inventory ID is missing in the response.")
                return master_copy_info
            else:
                raise ClientError("Failed to get asset info. ERROR. {}. {}".format(
                    response.status_code, response.text))
        except Exception as ex:
            raise ClientError(str(ex))

    def _construct_master_copy_url(self, master_copy_id: str, inventory_id: str):

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v1/aigov/' + 'inventories/' + inventory_id + '/master_copies/' + master_copy_id
        else:
            if get_env() == 'dev' or get_env()==AWS_DEV:
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v1/aigov/' + 'inventories/' + inventory_id + '/master_copies' + master_copy_id
            elif get_env() == 'test'  or get_env()==AWS_TEST:
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v1/aigov/' + 'inventories/' + inventory_id + '/master_copies' + master_copy_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v1/aigov/' + 'inventories/' + inventory_id + '/master_copies' + master_copy_id
        return url

    def get_mastercopy_evaluations(self, mastercopy_id: str, inventory_id: str ):
        """
        Retrieves all  the evaluation results for all lifecycle phases from a master copy

        Returns:
            dictionary containing the evaluation results for all phases
        Example:
             >>> client.utilities.retrieve_mastercopy_evaluations
        Raises:
            ClientError: If the master copy imformation is missing, or if the request fails.
        """
        try:        
            url = self._construct_master_copy_url(mastercopy_id, inventory_id)
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                master_response = response.json()
                evaluation_results = master_response['entity']['modelfacts_system_mc']
                _logger.info(
                    f"Evaluation results for the master copy {mastercopy_id} is retrieved successfully")
                return evaluation_results
            else:
                raise ClientError("Failed to get asset info. ERROR. {}. {}".format(
                    response.status_code, response.text))
        except Exception as ex:
            raise ClientError(str(ex))

    def _retrieve_inventory_url(self):
        if self._is_cp4d:
            bss_id = self._get_bss_id_cpd()
        else:
            bss_id = self._get_bss_id()
        
        if self._is_cp4d:
            base_url = self._cpd_configs['url']

        else:    
            if get_env() == 'dev' or get_env()==AWS_DEV:
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test' or get_env()==AWS_TEST:
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

    
        url = f"{base_url}/v1/aigov/inventories?bss_account_id={bss_id}&limit=100&skip=0"
         
        return url
    

    def _retrieve_admin_url(self, inventory_id):
        if self._is_cp4d:
            base_url = self._cpd_configs['url']
        else:    
            if get_env() == 'dev' or get_env()==AWS_DEV:
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test' or get_env()==AWS_TEST:
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']

        # Proper string interpolation
        url = f"{base_url}/v1/aigov/inventories/{inventory_id}/admins"
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
    
    def _get_bss_id_cpd(self):
        decoded_bss_id = "999"
        return decoded_bss_id

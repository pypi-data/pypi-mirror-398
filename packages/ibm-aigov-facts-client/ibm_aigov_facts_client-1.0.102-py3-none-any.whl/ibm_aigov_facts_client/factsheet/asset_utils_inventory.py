import logging
import json
import ibm_aigov_facts_client._wrappers.requests as requests
from typing import Any,List, Dict,Optional
from typing import Union



from typing import Dict
from ibm_aigov_facts_client.factsheet import assets
from ibm_aigov_facts_client.utils.utils import validate_enum
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import Role


from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *


_logger = logging.getLogger(__name__)


class AIGovInventoryUtilities():

    """
        AI asset utilities. Running `client.assets.get_inventory` and `client.assets.list_inventories` makes all methods in AIGovAssetUtilities object available to use.

    """

    def __init__(self, assets_client:'assets.Assets',inventory_id: str, inventory_name: str = None, inventory_description: str = None,
                 inventory_creator_name:str=None,inventory_creator_id:str=None) -> None:

        self._assets_client = assets_client
        self._facts_client = self._assets_client._facts_client
        ##
        self._inventory_id = inventory_id
        self._inventory_name =inventory_name
        self._inventory_description = inventory_description
        self._inventory_creator_name=inventory_creator_name
        self._inventory_creator_id=inventory_creator_id
        self._cpd_configs = None
        self._is_cp4d = self._assets_client._is_cp4d
        self._account_id=self._facts_client._account_id
        if self._is_cp4d:
            self._cpd_configs = self._assets_client._cpd_configs
            self._cp4d_version = self._assets_client._cp4d_version
    
    
    @classmethod
    def from_dict(cls, _dict: Dict[str, Any]) -> 'AIGovInventoryUtilities':
        """Initialize an AIGovInventoryUtilities object from a dictionary."""
        args = {}

        # Extract values from dictionary
        if 'inventory_id' in _dict:
            args['inventory_id'] = _dict.get('inventory_id')
        else:
            raise ValueError('Required property "inventory_id" not present in dictionary')

        if 'inventory_name' in _dict:
            args['inventory_name'] = _dict.get('inventory_name')
        else:
            raise ValueError('Required property "inventory_name" not present in dictionary')

        if 'inventory_description' in _dict:
            args['inventory_description'] = _dict.get('inventory_description')
        else:
            raise ValueError('Required property "inventory_description" not present in dictionary')

        if 'inventory_creator_name' in _dict:
            args['inventory_creator_name'] = _dict.get('inventory_creator_name')
        else:
            raise ValueError('Required property "inventory_creator_name" not present in dictionary')

        if 'inventory_creator_id' in _dict:
            args['inventory_creator_id'] = _dict.get('inventory_creator_id')
        else:
            raise ValueError('Required property "inventory_creator_id" not present in dictionary')

        # Assuming '_assets_client' is needed but not included in the dictionary
        # You'll need to set _assets_client appropriately here
        assets_client = None  # Replace with appropriate value for assets_client

        return cls(
            assets_client=assets_client,
            inventory_id=args['inventory_id'],
            inventory_name=args['inventory_name'],
            inventory_description=args['inventory_description'],
            inventory_creator_name=args['inventory_creator_name'],
            inventory_creator_id=args['inventory_creator_id']
        )

    @classmethod
    def _from_dict(cls, _dict: Dict[str, Any]) -> 'AIGovInventoryUtilities':
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary representing this model."""
        _dict = {}
        if hasattr(self, '_inventory_id') and self._inventory_id is not None:
            _dict['inventory_id'] = self._inventory_id
        if hasattr(self, '_inventory_name') and self._inventory_name is not None:
            _dict['inventory_name'] = self._inventory_name
        if hasattr(self, '_inventory_description') and self._inventory_description is not None:
            _dict['inventory_description'] = self._inventory_description
        if hasattr(self, '_inventory_creator_name') and self._inventory_creator_name is not None:
            _dict['inventory_creator_name'] = self._inventory_creator_name
        if hasattr(self, '_inventory_creator_id') and self._inventory_creator_id is not None:
            _dict['inventory_creator_id'] = self._inventory_creator_id

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
    
    # commenting this as it just returning string which is not usefull for automation
    
    # def get_info(self) -> None:
    #     """
    #     **Retrieve and display information related to the Inventory**.

    #     This method does not take any parameters

    #     Example:
    #         >>> inventory.get_info()
    #     """
    #     try:
    #         self._refresh_inventory()  # Refresh inventory details
    #         _logger.info(
    #             f"\n"
    #             f"Inventory ID: {self._inventory_id}\n"
    #             f"Name: {self._inventory_name or 'N/A'}\n"
    #             f"Description: {self._inventory_description or 'N/A'}\n"
    #             f"Creator: {self._inventory_creator_name or 'N/A'}\n"
    #             f"Creator ID: {self._inventory_creator_id or 'N/A'}"
    #         )
    #     except Exception as e:
    #         _logger.error(f"An unexpected error occurred: {e}")
    #         raise



    def get_info(self) -> dict:
        """
        **Retrieve and return information related to the Inventory**.

        This method does not take any parameters.

        Returns:
            dict: A dictionary containing inventory details.

        Example:
            >>> inventory_info = inventory.get_info()
        """
        try:
            self._refresh_inventory()
            inventory_details = {
                "inventory_id": self._inventory_id,
                "name": self._inventory_name or 'N/A',
                "description": self._inventory_description or 'N/A',
                "creator": self._inventory_creator_name or 'N/A',
                "creator_id": self._inventory_creator_id or 'N/A'
            }

            return inventory_details

        except Exception as e:
            raise ValueError(f"An unexpected error occurred: {e}")

    


    def get_id(self) -> str:
        """
        **Retrieve the Inventory ID**.

        This method does not take any parameters and returns the Inventory ID.

        Returns:
            str: The ID of the inventory.

        Example:
            >>> inventory_id = inventory.get_id()
        """
        try:
            return self._inventory_id
        except Exception as e:
            _logger.error(f"An unexpected error occurred: {e}")
            raise

        

    def set_detail(self,name: str = None,description: str = None):
        """
        **set details of an inventory item**.

        It allows updating the `name` and/or `description` of the inventory. 

        Parameters:
            - name (str, optional): The new name to set for the inventory. If not provided, the name will not be changed.
            - description (str, optional): The new description to set for the inventory. If not provided, the description will not be changed.

        Example:
            >>> innventory.set_detail(name="New Name", description="Updated description")
        """
        print("-" * OUTPUT_WIDTH)
        print(" Inventory Updation Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)


        if not self._inventory_id:
             raise ClientError("Inventory ID is required for updating inventory details.")
        
        patch_operations = []
        if name is not None: 
            patch_operations.append({
                "op": "replace",
                "path": "/entity/name",
                "value": name
            })
        if description is not None:  
            patch_operations.append({
                "op": "replace",
                "path": "/entity/description",
                "value": description
            })

        if not patch_operations:
            raise ClientError("At least one of 'name' or 'description' must be provided to update the inventory.")

        try:
            url = self._retrieve_inventory_url(self._inventory_id)
            
            # Override headers cp4d request
            headers = self._get_headers()
            headers["Content-Type"] = "application/json-patch+json"
            response = requests.patch(url, headers=headers, json=patch_operations)
            
            if response.status_code == 200:
                update_message = "Inventory details updated successfully."
                if name is not None:
                    update_message += f" Name: '{name}'"
                if description is not None:
                    update_message += f" Description: '{description}'"
                _logger.info(update_message)
                
                # update the inventory
                self._refresh_inventory()
            else:
                error_message = response.json().get('message', 'Unknown error occurred')
                raise ClientError(f"Failed to update inventory details. Status code: {response.status_code}, Error: {error_message}")
        
        except Exception as e:
            _logger.error(f"An error occurred while updating inventory details: {e}")
            raise 
        

    def delete_inventory(self, force_delete: bool = False):
        """
        **Delete the inventory**.

        This method also deletes the associated bucket created in IBM Cloud. 
        Use this function with caution, as deletion is irreversible.

        Args:
            force_delete (bool): If True, forces the deletion without checking for assets. Default is False.

        Example:
            >>> inventory.delete_inventory(force_delete=True)
        """
        print("-" * OUTPUT_WIDTH)
        print(" Inventory Deletion Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)

        if not self._inventory_id:
            raise ClientError("Inventory ID is required for deletion.")

        try:
            if not force_delete:
                if not self._check_assets_before_deletion():
                    return None 

            url = self._retrieve_inventory_url(self._inventory_id, delete_bucket=True)
            response = requests.delete(url, headers=self._get_headers())

            if response.status_code == 204:
                _logger.info(f"Inventory with ID '{self._inventory_id}' has been successfully deleted.")
            else:
                raise ClientError(f"Failed to delete inventory. Status code: {response.status_code}, Error: {response.json().get('message', 'Unknown error occurred')}")

        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise


    def list_collaborators(self) -> List[Dict[str, Optional[str]]]:
        """
        **Retrieve a list of collaborators for the inventory**.

        If no collaborators are found or if the collaborator information is unavailable, an empty list is returned.

        Returns:
            List[Dict[str, Optional[str]]]: A list of dictionaries with details about each collaborator, or an empty list if no collaborators are found.

        Example:
            >>> collaborators = inventory.list_collaborators()
        """
        print("-" * OUTPUT_WIDTH)
        print(" Collaborator Retrieval Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)
        
        if not self._inventory_id:
            raise ClientError("Inventory ID is required for fetching collaborators.")
        
        collaborators_list: List[Dict[str, Optional[str]]] = []
        env=aws_env()
        try:
            url = self._retrieve_inventory_url(self._inventory_id, collaborators=True)
            response = requests.get(url, headers=self._get_headers())
            if response.status_code == 200:
                data = response.json()
                if 'members' in data:
                    if data['members']:
                        _logger.info("Collaborators fetched successfully")
                        for member in data['members']:
                            user_iam_id = member.get('user_iam_id', 'N/A')
                            role = member.get('role', 'N/A')
                            create_time = member.get('create_time', 'N/A')
                            member_unique_id = member.get('memberUniqueId', 'N/A')
                            access_group_id=member.get("access_group_id")
                            
                            if access_group_id:
                                user_name, group_user_iam_id = self._fetch_group_user_name(user_id=access_group_id)
                                if not (user_name == 'N/A' and user_iam_id.startswith('iam-ServiceId-')):
                                    collaborators_list.append({
                                        "name": user_name,
                                        "access_group_id": access_group_id,
                                        "role": role,
                                        "creator_id": group_user_iam_id,
                                        "created_time": create_time
                                    })
                            elif  env in (AWS_MUM,AWS_DEV,AWS_TEST) and user_iam_id.startswith('iam-ServiceId-'):
                                user_name= self._fetch_serviceId_user_name(user_id=member_unique_id)
                                if not (user_name == 'N/A' and user_iam_id.startswith('iam-ServiceId-')):
                                    print(user_name,user_iam_id)
                                    collaborators_list.append({
                                        "name": user_name,
                                        "user_id": user_iam_id,
                                        "role": role,
                                        "created_time": create_time
                                    })
                            else:
                                user_name = self._fetch_user_name(user_id=member_unique_id)
                                if not (user_name == 'N/A' and user_iam_id.startswith('iam-ServiceId-')):
                                    collaborators_list.append({
                                        "name": user_name,
                                        "user_id": user_iam_id,
                                        "role": role,
                                        "created_time": create_time
                                    })
                        
                    else:
                        _logger.info("No collaborators found.")

                else:
                   _logger.info("No collaborators information available.")
            else:
                error_message = response.json().get('message', 'Unknown error occurred')
                raise ClientError(f"Failed to fetch collaborators for inventory ID '{self._inventory_id}'. "
                                f"Status code: {response.status_code}, Error: {error_message}")

        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise

        return collaborators_list


    def add_collaborator(self, role: str, user_id: Union[str, int] = None, access_group_id: Union[str, int] = None):
        """
        **Add a collaborator to the inventory**.

        This method assigns a user or an access group to the inventory with a specified role.

        Parameters:
            - role (str): The role to assign to the collaborator. Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Role`.
            - user_id (str, optional): The ID of the user to be added as a collaborator. 
            - access_group_id (str, optional): The ID of the access group to be added as a collaborator. 

        Note:
            - Ensure that you have the correct user ID or access group ID format based on the platform you are using.
            - Both `user_id` and `access_group_id` cannot be provided simultaneously.

        Example:
            >>> inventory.add_collaborator(role="Editor", user_id="IBMid-11000***")
            >>> inventory.add_collaborator(role="Viewer", access_group_id="access-group-12345")
        """

        if not self._inventory_id:
            raise ClientError("Inventory ID is required for adding collaborators.")
        
        if not user_id and not access_group_id:
            raise ClientError("At least one of 'user_id' or 'access_group_id' must be provided.")

        if user_id and access_group_id:
            raise ClientError("Cannot pass both 'user_id' and 'access_group_id' at the same time.")
        
        if user_id is not None:
            user_id = str(user_id)

        if access_group_id is not None:
            access_group_id = str(access_group_id)
        

        try:
            validate_enum(role, "role", Role, False)
            if access_group_id:
                creator_name,user_iam_id=self._fetch_group_user_name(user_id=access_group_id)
            else:
                creator_name,user_iam_id= self._fetch_user_name(user_id=user_id)
            
            inventory_name = self._get_inventory_name(self._inventory_id)

            log_msg = (
                f"\nAdding '{creator_name}' (ID: {user_id if user_id else access_group_id})\n"
                f"To inventory '{inventory_name}'\n"
                f"Inventory ID: {self._inventory_id}\n"
                f"Role: '{role}'\n"
            )
            _logger.info(log_msg)

            base_url = self._retrieve_inventory_url(catalog=True)
            env=aws_env()
            if env in (AWS_TEST,AWS_DEV,AWS_MUM):
                if user_id:
                     user_id= f"{user_id}::www.ibm.com-{user_iam_id}"  
                if access_group_id:
                    access_group_id=f"AccessGroupId-{access_group_id}"
            final_id=user_id or access_group_id               
            collaborator_url = f"{base_url}/{final_id}"
           
            body = {
                "members": [
                    {
                        "user_iam_id": user_id if user_id else None,
                        "access_group_id": access_group_id if access_group_id else None,
                        "role": role,
                        "href": collaborator_url
                    }
                ]
            }
            url = self._retrieve_inventory_url(self._inventory_id, add_collaborators=True)
            response = requests.post(url, headers=self._get_headers(), json=body)
            
            if response.status_code == 200:
                 _logger.info(f"Collaborator added successfully to {inventory_name}.")
            else:
                 error_message = f"Failed to add collaborator. Status code: {response.status_code}, " f"Response: {response.text}. Please verify if the user or group already exists."
                 _logger.error(error_message)
        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise


    def remove_collaborator(self,user_id: str = None, access_group_id: str = None):
        """
        **Remove a collaborator from the inventory**.

        This method removes a user from the inventory.

        Parameters:
            - user_id (str,optional): The ID of the user to be removed from the collaborators.
            - access_group_id (str, optional): The ID of the access group to be added as a collaborator. 
        
        Note:
            - Ensure that you have the correct user ID or access group ID format based on the platform you are using.
            - Both `user_id` and `access_group_id` cannot be provided simultaneously.

        Example:
            >>> inventory.remove_collaborator(user_id="IBMid-11000***")
            >>> inventory.remove_collaborator(access_group_id="access-group-12345")
        """

        print("-" * OUTPUT_WIDTH)
        print(" Deleting Collaborator Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)
       
        if not self._inventory_id:
            raise ClientError("Inventory ID is required for deleting collaborator.")
        
        if not user_id and not access_group_id:
            raise ClientError("At least one of 'user_id' or 'access_group_id' must be provided.")

        if user_id and access_group_id:
            raise ClientError("Cannot pass both 'user_id' and 'access_group_id' at the same time.")
        
        env=aws_env()
        try:
            if access_group_id:
                creator_name,user_iam_id=self._fetch_group_user_name(user_id=access_group_id)
            else:
                creator_name,user_iam_id = self._fetch_user_name(user_id=user_id)
           

            inventory_name = self._get_inventory_name(self._inventory_id)
           # Normal info message
            log_msg=(f" \n"
                     f" Removing '{creator_name}' (ID: {user_id or access_group_id})\n"
                     f" Inventory name: '{inventory_name}'\n"
                     f" Inventory ID: {self._inventory_id}\n")
            
            _logger.info(log_msg)
            if env in (AWS_TEST,AWS_DEV,AWS_MUM):
                if user_id:
                     user_id= f"{user_id}::www.ibm.com-{user_iam_id}"  
                if access_group_id:
                    access_group_id=f"AccessGroupId-{access_group_id}"

            final_id=user_id or access_group_id
            url = self._retrieve_inventory_url(self._inventory_id, add_collaborators=True) +"/" + final_id
            response = requests.delete(url, headers=self._get_headers())

            if response.status_code == 204:
                _logger.info("Collaborator {} (ID: {}) removed from {} successfully.".format(creator_name, final_id, inventory_name))
            else:
                error_message = f"Failed to remove collaborator. Status code: {response.status_code}, Response: {response.text}"
                raise ClientError(error_message)

        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise
    
    def set_collaborator_role(self,role:str,user_id: str = None, access_group_id: str = None):
        """
        **set the role of an existing collaborator in the inventory**.

        This method changes the role assigned to a user in the inventor.

        Parameters:
            - role (str): The role to assign to the user.Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Role`
            - user_id (str,optional): The ID of the user whose role is to be updated.
            - access_group_id (str, optional): The ID of the access group to be added as a collaborator. 
        
        Note:
            - Ensure that you have the correct user ID or access group ID format based on the platform you are using.
            - Both `user_id` and `access_group_id` cannot be provided simultaneously.
        Example:
            >>> inventory.set_collaborator_role(role="Viewer", user_id="IBMid-11000***")
            >>> inventory.set_collaborator(role="Viewer", access_group_id="access-group-12345")
        """

        print("-" * OUTPUT_WIDTH)
        print(" Updating Collaborator Role Started ".center(OUTPUT_WIDTH))
        print("-" * OUTPUT_WIDTH)

        if not self._inventory_id:
            raise ClientError("Inventory ID required for updating collaborators.")
        
        if not user_id and not access_group_id:
            raise ClientError("At least one of 'user_id' or 'access_group_id' must be provided.")

        if user_id and access_group_id:
            raise ClientError("Cannot pass both 'user_id' and 'access_group_id' at the same time.")
        
        env=aws_env()
        try:
            validate_enum(role, "role", Role, False)
            
            # Fetching creator_name and inventory_name
            if access_group_id:
                creator_name,user_iam_id=self._fetch_group_user_name(user_id=access_group_id)
            else:
                creator_name,user_iam_id= self._fetch_user_name(user_id=user_id)

            inventory_name = self._get_inventory_name(self._inventory_id)

            # Normal info message
            log_msg=(f" \n"
                     f" Updating '{creator_name}' (ID: {user_id or access_group_id})\n"
                     f" Inventory name : '{inventory_name}'\n"
                     f" Inventory ID: {self._inventory_id}\n"
                     f" with new Role: '{role}'\n")
            
            _logger.info(log_msg)

            if env in (AWS_TEST,AWS_DEV,AWS_MUM):
                if user_id:
                     user_id= f"{user_id}::www.ibm.com-{user_iam_id}"  
                if access_group_id:
                    access_group_id=f"AccessGroupId-{access_group_id}"
                    
            final_id=user_id or access_group_id
            url = self._retrieve_inventory_url(self._inventory_id, add_collaborators=True) +"/" + final_id
            body = {"role": role,}
            
            # Override headers cp4d request
            headers = self._get_headers()
            headers["Content-Type"] = "application/json-patch+json"

            response = requests.patch(url, headers=headers, json=body)
            
            if response.status_code == 200:
                _logger.info("Successfully updated '{}' (ID: '{}') with new role '{}' in inventory '{}'".format(creator_name, final_id,role,inventory_name))
            else:
                error_message = f"Failed to update the role of collaborator. Status code: {response.status_code}, Response: {response.text}"
                raise ClientError(error_message)
        except Exception as e:
            _logger.error(f"An error occurred: {e}")
            raise

        

    def _retrieve_inventory_url(self, inventory_id=None, delete_bucket=False,collaborators=False,add_collaborators=False,catalog=False):
        if self._is_cp4d:
            base_url = self._cpd_configs['url']
        else:
            if get_env() == 'dev':
                base_url = dev_config['DEFAULT_DEV_SERVICE_URL']
            elif get_env() == 'test' :
                base_url = test_config['DEFAULT_TEST_SERVICE_URL']
            else:
                base_url = prod_config['DEFAULT_SERVICE_URL']
            
        if catalog:
            url=f"{base_url}/v2/aigov/catalogs/{inventory_id}/members"

        if inventory_id:
            url = f"{base_url}/v1/aigov/inventories/{inventory_id}"
        
        if delete_bucket:
            url += f"?delete_bucket={str(delete_bucket).lower()}"
        
        if collaborators:
            url += f"/collaborators?collaborator_type=all"
        
        if add_collaborators:
            url += f"/collaborators"

         
        return url
    
    def _retrieve_user_profile_url(self, external_model_admin: str) -> str:
        if self._is_cp4d:
            url = self._cpd_configs['url'] + \
                '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
        else:
            if get_env() == 'dev' :
                url = dev_config['DEFAULT_DEV_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin
            elif get_env() == 'test':
                url = test_config['DEFAULT_TEST_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin       
            else:
                url = prod_config['DEFAULT_SERVICE_URL'] + \
                    '/v2/user_profiles?q=iam_id%20IN%20'+external_model_admin

        return url
    

    def _retrieve_user_group_profile_url(self, user_id: str) -> str:
        if self._is_cp4d:
            url = self._cpd_configs['url'] + \
                '/usermgmt/v2/groups'
        else:
            if get_env() == 'dev':
                url = dev_config['IAM_API_URL'].split('/identity')[0] + \
                    '/v2/groups/' + user_id
            elif get_env() == 'test':
                url = test_config['IAM_API_URL'].split('/identity')[0] + \
                    '/v2/groups/' + user_id
            else:
                url = prod_config['IAM_API_URL'].split('/identity')[0] + \
                    '/v2/groups/' + user_id
        return url
    
    
    def _fetch_user_name(self, user_id: str) -> str:
        try:
            env= aws_env()
            if env in (AWS_MUM,AWS_DEV,AWS_TEST):           
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
                        user_iam_id=user_data.get('idpUniqueId')
                        return user_name ,user_iam_id
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
                        user_iam_id=user_data.get('idpUniqueId')
                        return user_name,user_iam_id
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
                    return user_names[0],None
                else:
                    _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                                f"Status code: {response.status_code}")
                    return 'N/A', None
        except Exception as e:
            _logger.error(f"An error occurred while fetching user profile: {e}")
            return 'N/A'
        
    
    def _fetch_group_user_name(self, user_id: str) -> str:
        env= aws_env()
        try:
            if env in (AWS_MUM,AWS_DEV,AWS_TEST):  
                if env in (AWS_DEV ,AWS_TEST):
                    url =f"{aws_test['API_URL']}/api/2.0/accounts"
                else:
                    url=f"{aws_mumbai['API_URL']}/api/2.0/accounts"
                if user_id.startswith("AccessGroupId-"):
                    user_id = user_id.split("AccessGroupId-")[-1]
                user_profile_url = f"{url}/{self._account_id}/groups/{user_id}"
            else:
                user_profile_url = self._retrieve_user_group_profile_url(user_id)
            response = requests.get(user_profile_url, headers=self._get_headers())
            if response.status_code == 200:
                user_data = response.json()
                if self._is_cp4d:
                    groups = user_data.get('results', [])
                    for group in groups:
                        if str(group.get('group_id')) == user_id:
                            name = group.get('name', 'N/A')
                            created_by = group.get('created_by', 'N/A')
                            return name, created_by
                    _logger.info(f"Group ID '{user_id}' not found in the response.")
                    return 'N/A', 'N/A'
                else:
                    name = user_data.get('name', 'N/A')
                    created_by_id = user_data.get('created_by_id', 'N/A')
                    return name, created_by_id

            else:
                _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                            f"Status code: {response.status_code}")
                return 'N/A', 'N/A'
        except Exception as e:
            _logger.error(f"An error occurred while fetching user profile: {e}")
            return 'N/A', 'N/A'
        
    def _fetch_serviceId_user_name(self, user_id: str) -> str:
        try:
            url=f"{aws_mumbai['API_URL']}/api/2.0/accounts"        
            if user_id.startswith("iam-ServiceId-"):
                user_id = user_id.split("iam-ServiceId-")[1].split("_")[0]   
            user_profile_url = f"{url}/{self._account_id}/serviceids/{user_id}"
            response = requests.get(user_profile_url, headers=self._get_headers())
            if response.status_code == 200:
                user_data = response.json()
                name = user_data.get('name', 'N/A')
                created_by_id = user_data.get('created_by_id', 'N/A')
                return name, created_by_id
            else:
                _logger.error(f"Failed to fetch user profile for user ID '{user_id}'. "
                            f"Status code: {response.status_code}")
                return 'N/A', 'N/A'
        except Exception as e:
            _logger.error(f"An error occurred while fetching user profile: {e}")
            return 'N/A', 'N/A'
    
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
    
    def _refresh_inventory(self) -> None:
        try:
            response = requests.get(self._retrieve_inventory_url(self._inventory_id), headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            entity, metadata = data.get('entity', {}), data.get('metadata', {})
            
            self._inventory_name = entity.get('name', 'N/A')
            self._inventory_description = entity.get('description', 'N/A')
            creator_id = metadata.get('creator_id', 'N/A')
            self._inventory_creator_id = creator_id
            self._inventory_creator_name = self._fetch_user_name(creator_id)
        except Exception as e:
            _logger.error(f"An unexpected error occurred: {e}")
            raise
    

    def _get_inventory_assest_url(self):
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
     
    def _check_assets_before_deletion(self) -> bool:
        """
        **Check if the inventory contains assets before deletion**.

        This method queries the assets of the inventory and checks if there are any assets.
        
        Returns:
            bool: True if no assets are found (i.e., safe to delete), False if assets exist.
        """
        inventory_assets_url = self._get_inventory_assest_url()
        query = {
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"entity.assets.catalog_id": self._inventory_id}}
                    ]
                }
            },
            "sort": [{"metadata.modified_on": {"order": "desc", "unmapped_type": "date"}}]
        }
        
        response = requests.post(inventory_assets_url, headers=self._get_headers(), json=query)

        if response.status_code == 200:
            total_size = response.json().get('size', 0)

            if total_size > 0:
                _logger.warning(f"Inventory with ID '{self._inventory_id}' contains {total_size} asset(s). Cannot delete.")
                return False  
            else:
                _logger.info(f"No assets found in inventory '{self._inventory_id}'.")
                return True  
        else:
            raise ClientError(f"Failed to retrieve assets. Status code: {response.status_code}, Error: {response.json().get('message', 'Unknown error occurred')}")
    

        


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
    
    # def _get_bss_id(self):
    #     try:
    #         token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
    #             isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator))) else self._facts_client.authenticator.bearer_token
    #         decoded_bss_id = jwt.decode(token, options={"verify_signature": False})[
    #             "account"]["bss"]
    #     except jwt.ExpiredSignatureError:
    #         raise
    #     return decoded_bss_id
    
    
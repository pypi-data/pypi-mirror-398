# coding: utf-8

# Copyright 2020,2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, Optional

from requests import Request

from ibm_cloud_sdk_core.authenticators.cp4d_authenticator import CloudPakForDataAuthenticator
from ibm_aigov_facts_client.supporting_classes.cp4d_token_manager import CPDTokenManager

class CP4DAuthenticator(CloudPakForDataAuthenticator):
    """The CloudPakForDataAuthenticator utilizes a username and password pair to
    obtain a suitable bearer token, and adds it requests.
    The bearer token will be sent as an Authorization header in the form:
        Authorization: Bearer <bearer-token>
    Args:
        username: The username used to obtain a bearer token.
        url: The URL representing the Cloud Pak for Data token service endpoint.
    Keyword Args:
        password: The password used to obtain a bearer token.
        apikey: Platform api key
        disable_ssl_verification:  A flag that indicates whether verification of the server's SSL
            certificate should be disabled or not. Defaults to False.
        headers: Default headers to be sent with every CP4D token request. Defaults to None.
        proxies: Dictionary for mapping request protocol to proxy URL.
        proxies.http (optional): The proxy endpoint to use for HTTP requests.
        proxies.https (optional): The proxy endpoint to use for HTTPS requests.
    Attributes:
        token_manager (CP4DTokenManager): Retrives and manages CP4D tokens from the endpoint specified by the url.
    Raises:
        ValueError: The username, password, and/or url are not valid for CP4D token requests.
    """

    def __init__(self,
                 username: str,
                 url: str,
                 *,
                 password: str = None,
                 apikey: str = None,
                 disable_ssl_verification: bool = False,
                 headers: Optional[Dict[str, str]] = None,
                 proxies: Optional[Dict[str, str]] = None,
                 bedrock_url: str = None) -> None:
        self.token_manager = CPDTokenManager(
            username=username, password=password, url=url, apikey = apikey, disable_ssl_verification=disable_ssl_verification,
            headers=headers, proxies=proxies,bedrock_url = bedrock_url)
        self.validate()
        self.bedrock_url = bedrock_url

    def get_cp4d_auth_token(self) -> None:
        """Adds CP4D authentication information to the request.
        The CP4D bearer token will be added to the request's headers in the form:
            Authorization: Bearer <bearer-token>
        Args:
            req:  The request to add CP4D authentication information too. Must contain a key to a dictionary
            called headers.
        """
        #headers = req.get('headers')
        bearer_token = self.token_manager.request_token()
        #headers['Authorization'] = 'Bearer {0}'.format(bearer_token)
        return bearer_token
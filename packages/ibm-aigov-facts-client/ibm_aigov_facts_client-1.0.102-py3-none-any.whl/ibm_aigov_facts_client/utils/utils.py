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

import json
import time
import os
import errno
import urllib
import posixpath
import pkg_resources
import ibm_aigov_facts_client._wrappers.requests as requests


from ibm_cloud_sdk_core.api_exception import *

from urllib.request import pathname2url
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_aigov_facts_client.custom import DEFAULT_LOCAL_FILE_AND_ARTIFACT_PATH, CUSTOM_TAG_GUID
from typing import TYPE_CHECKING, Callable, List, Union


from .client_errors import *
from . import constants
from .enums import ContainerType,StatusStateType
from .config import *


STR_TYPE = type(u'string or unicode')


def version():
    try:
        version = pkg_resources.get_distribution(
            "ibm-aigov-facts-client").version
    except pkg_resources.DistributionNotFound:
        version = u'0.0.1-local'

    return version


def validate_type(el, el_name, expected_type, mandatory=True, subclass=False):
    if el_name is None:
        raise MissingValue(u'el_name')

    if type(el_name) is not str:
        raise UnexpectedType(u'el_name', str, type(el_name))

    if expected_type is None:
        raise MissingValue(u'expected_type')

    if type(expected_type) is not type and type(expected_type) is not list:
        raise UnexpectedType(
            'expected_type', 'type or list', type(expected_type))

    if type(mandatory) is not bool:
        raise UnexpectedType(u'mandatory', bool, type(mandatory))

    if type(subclass) is not bool:
        raise UnexpectedType(u'subclass', bool, type(subclass))

    if mandatory and el is None:
        raise MissingValue(el_name)
    elif el is None:
        return

    validation_func = isinstance

    if subclass is True:
        def validation_func(x, y): return issubclass(x.__class__, y)

    if type(expected_type) is list:
        try:
            next((x for x in expected_type if validation_func(el, x)))
            return True
        except StopIteration:
            return False
    else:
        if not validation_func(el, expected_type):
            raise UnexpectedType(el_name, expected_type, type(el))

def _is_active(api_key,env=None):
    import requests
    params={"apikey":api_key}

    if env == 'dev':
        url = dev_config["IAM_API_URL"]
    elif env == 'test':
        url = test_config["IAM_API_URL"]
    else:
        url = prod_config["IAM_API_URL"]

    response = requests.post(url, params= params)
    is_active=response.json().get('active') 
    
    return is_active


def get_instance_guid(authenticator, env, container_type:str=None, is_cp4d: bool = False, service_url: str = None,bearer_token_flag = False):

    import json
    import ibm_aigov_facts_client._wrappers.requests as requests

    valid_instance_guid = False 

    if is_cp4d:
        valid_instance_guid = True
        cp4d_wkcinstance_guid = "" #TBD
    else:
        token = authenticator.token_manager.get_token() if isinstance(
            authenticator, IAMAuthenticator) else authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }

        if env == 'dev':
            resources_url = constants.RESOURCES_URL_MAPPING[dev_config["DEFAULT_DEV_SERVICE_URL"]]
        elif env == 'test':
            resources_url = constants.RESOURCES_URL_MAPPING[test_config["DEFAULT_TEST_SERVICE_URL"]]
        elif env == 'sydney':
            resources_url = constants.RESOURCES_URL_MAPPING[sydney_region["DEFAULT_SERVICE_URL"]]
        elif env == 'frankfurt':
            resources_url = constants.RESOURCES_URL_MAPPING[frankfurt_region["DEFAULT_SERVICE_URL"]]
        elif env == 'toronto':
            resources_url = constants.RESOURCES_URL_MAPPING[toronto_region["DEFAULT_SERVICE_URL"]]
        elif env == 'tokyo':
            resources_url = constants.RESOURCES_URL_MAPPING[tokyo_region["DEFAULT_SERVICE_URL"]]
        elif env == 'london':
            resources_url = constants.RESOURCES_URL_MAPPING[london_region["DEFAULT_SERVICE_URL"]]
        else:
            resources_url = constants.RESOURCES_URL_MAPPING[prod_config["DEFAULT_SERVICE_URL"]]

        resources_response = requests.get(resources_url, headers=iam_headers)

        # if resources_response.status_code == 401:
        #     raise AuthorizationError("Expired token provided.")
        # elif resources_response.status_code == 404:
        #     raise ClientError("Resources for current key not found")
        if resources_response.status_code != 200:
            if bearer_token_flag:
                raise ClientError("Failed to get resource details. This may be due to an expired or invalid token.")
            else:
                raise ClientError("Failed to get resource details.")
        else:
            # Go through all the pages until next_url is null
            resources = json.loads(resources_response.text)["resources"]
            next_url = json.loads(resources_response.text)['next_url']
            reached_end = False
            while not reached_end:
                if next_url == None:
                    reached_end = True
                    break
                resources_response = requests.get(
                    "https://resource-controller.cloud.ibm.com" + next_url, headers=iam_headers)
                resources.extend(json.loads(
                    resources_response.text)['resources'])
                next_url = json.loads(resources_response.text).get("next_url")

            
            wkc_unique_resource_id= "ed3a5a53-eb60-4f3c-8fd1-17f88585b6ed" #wkc 
            wml_unique_resource_id="51c53b72-918f-4869-b834-2d99eb28422a" #wml
            ws_unique_resource_id="39ba9d4c-b1c5-4cc3-a163-38b580121e01" #ws
            wx_gov_unique_resource_id="2ad019f3-0fd6-4c25-966d-f3952481a870" #wx gov


            # if container_type == ContainerType.SPACE:
            #     resource_id = "51c53b72-918f-4869-b834-2d99eb28422a"  # wml
            # elif container_type==ContainerType.PROJECT:
            #     resource_id = "39ba9d4c-b1c5-4cc3-a163-38b580121e01"  # ws
            # else:
            #     resource_id=wkc_unique_resource_id
                
            if container_type == ContainerType.SPACE:
                for resource in resources:
                    if resource["resource_id"] in [wml_unique_resource_id,wkc_unique_resource_id,wx_gov_unique_resource_id]:
                        valid_instance_guid=True
                        break
                    
            elif container_type==ContainerType.PROJECT:
                for resource in resources:    
                    if resource["resource_id"] in [ws_unique_resource_id,wkc_unique_resource_id,wx_gov_unique_resource_id]:
                        valid_instance_guid=True
                        break
            else:
                for resource in resources:    
                    # if resource["resource_id"] == wkc_unique_resource_id: # facts-client without wkc
                        valid_instance_guid=True
                        break

    return valid_instance_guid


# def check_if_cp4d(service_url: str):
#     """
#     Returns True if the URL provided belongs to a CP4D environment.
#     :service_url: The service URL for Factsheet service.
#     """
#     is_cp4d = None

#     # Calling the fairness heartbeat API to check for environment details
#     url = "{}/v1/aigov/factsheet/heartbeat".format(service_url)

#     payload = {}
#     headers = {
#         "Accept": "application/json"
#     }

#     response = requests.request(
#         "GET", url, headers=headers, data=payload, verify=False)

#     if response.status_code == 404:
#         # This means that the V2 changes are not yet available and this can happen only in CP4D environments
#         # Hence, marking is_cp4d as True
#         is_cp4d = True
#     else:
#         if response.ok is False:
#             # Heartbeat call failed
#             raise ClientError("Heartbeat call to check for environment details failed with status code {}. Error: {}".format(
#                 response.status_code, response.text))
#         else:
#             response_json = json.loads(response.text)
#             is_cp4d = not response_json["is_cloud"] if "is_cloud" in response_json else False

#     return is_cp4d

def validate_external_connection_props(props:dict):
    ml_engine=None
    if "model_name" in props and "endpoint_name" in props:
        ml_engine="aws_sagemaker"
    elif "web_service_name" in props and "scoring_url" in props:
        ml_engine="azureml_studio"
    elif "service_id" in props and "service_url" in props:
        ml_engine="azureml_service"
       
    return ml_engine


def validate_enum(el, el_name, enum_class, mandatory=True):
    if mandatory and el is None:
        raise MissingValue(el_name)
    elif el is None:
        return

    validate_type(el, el_name, str, mandatory)

    acceptable_values = list(map(lambda y: enum_class.__dict__[y], list(
        filter(lambda x: not x.startswith('_'), enum_class.__dict__))))

    if el is not None and el not in acceptable_values:
        raise UnexpectedValue('Unexpected value of \'{}\', expected one of: {}, actual: {}'.format(
            el_name, acceptable_values, el))


def default_root_dir():
    return os.path.abspath(DEFAULT_LOCAL_FILE_AND_ARTIFACT_PATH)


def exists(name):
    return os.path.exists(name)


def local_file_uri_to_path(uri):
    """
    Convert URI to local filesystem path.
    """
    path = urllib.parse.urlparse(uri).path if uri.startswith("file:") else uri
    return urllib.request.url2pathname(path)


def path_to_local_file_uri(path):
    """
    Convert local filesystem path to local file uri.
    """
    path = pathname2url(path)
    if path == posixpath.abspath(path):
        return "file://{path}".format(path=path)
    else:
        return "file:{path}".format(path=path)


def mkdir(root, name=None):  # noqa
    """
    Make directory with name "root/name", or just "root" if name is None.
    :param root: Name of parent directory
    :param name: Optional name of leaf directory
    :return: Path to created directory
    """
    target = os.path.join(root, name) if name is not None else root
    try:
        os.makedirs(target)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(target):
            raise e
    return target

# def is_ipython():
#     # checks if the code is run in the notebook
#     try:
#         get_ipython
#         return True
#     except Exception:
#         return False
def is_python_2():
    return sys.version_info[0] == 2

# def str_type_conv(string):
#     # if is_python_2() and type(string) is str:
#     #     return unicode(string)
#     # else:
#     return string

# def meta_props_str_conv(meta_props):
#     for key in meta_props:
#         if type(meta_props[key]) is not str:
#             meta_props[key] = str(meta_props[key])

def validate_type(el, el_name, expected_type, mandatory=True):
        if el_name is None:
            raise MissingValue(u'el_name')

        #el_name = str_type_conv(el_name)
        if type(el_name) is not STR_TYPE:
            raise UnexpectedType(u'el_name', STR_TYPE, type(el_name))

        if expected_type is None:
            raise MissingValue(u'expected_type')

        if type(expected_type) is not type and type(expected_type) is not list:
            raise UnexpectedType('expected_type', 'type or list', type(expected_type))

        if type(mandatory) is not bool:
            raise UnexpectedType(u'mandatory', bool, type(mandatory))

        if mandatory and el is None:
            raise MissingValue(el_name)
        elif el is None:
            return

        if type(expected_type) is list:
            try:
                next((x for x in expected_type if isinstance(el, x)))
                return True
            except StopIteration:
                return False
        else:
            if not isinstance(el, expected_type):
                raise UnexpectedType(el_name, expected_type, type(el))

def _validate_meta_prop(meta_props, name, expected_type, mandatory=True):
        if name in meta_props:
           validate_type(meta_props[name], u'meta_props.' + name, expected_type, mandatory)
        else:
            if mandatory:
                raise MissingMetaProp(name)

def print_text_header_h1(title: str) -> None:
    print(u'\n\n' + (u'=' * (len(title) + 2)) + u'\n')
    print(' ' + title + ' ')
    print(u'\n' + (u'=' * (len(title) + 2)) + u'\n\n')


def print_text_header_h2(title: str) -> None:
    print(u'\n\n' + (u'-' * (len(title) + 2)))
    print(' ' + title + ' ')
    print((u'-' * (len(title) + 2)) + u'\n\n')


def print_synchronous_run(title: str, check_state: Callable, run_states: List[str] = None,
                          success_states: List[str] = None,
                          failure_states: List[str] = None, delay: int = 5,
                          get_result: Callable = None) -> Union[None, dict]:
    if success_states is None:
        success_states = [StatusStateType.SUCCESS, StatusStateType.FINISHED, StatusStateType.COMPLETED,
                          StatusStateType.ACTIVE]
    if failure_states is None:
        failure_states = [StatusStateType.FAILURE, StatusStateType.FAILED, StatusStateType.ERROR,
                          StatusStateType.CANCELLED, StatusStateType.CANCELED]

    if get_result is None:
        def tmp_get_result():
            if state in success_states:
                return 'Successfully finished.', None, None
            else:
                return 'Error occurred.', None, None

        get_result = tmp_get_result

    print_text_header_h1(title)

    state = None
    start_time = time.time()
    elapsed_time = 0
    timeout = 300

    while (run_states is not None and state in run_states) or (
            state not in success_states and state not in failure_states):
        time.sleep(delay)

        last_state = state
        state = check_state()

        if state is not None and state != last_state:
            print('\n' + state, end='')
        elif last_state is not None:
            print('.', end='')

        elapsed_time = time.time() - start_time

        if elapsed_time > timeout:
            break

    if elapsed_time > timeout:
        result_title, msg, result = 'Run timed out', 'The run didn\'t finish within {}s.'.format(timeout), None
    else:
        result_title, msg, result = get_result()

    print_text_header_h2(result_title)

    if msg is not None:
        print(msg)

    return result


def install_package(package, version=None):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import subprocess

        if version is None:
            package_name = package
        else:
            package_name = "{}=={}".format(package, version)

        subprocess.call([sys.executable, '-m', 'pip', 'install', package_name])


def install_package_from_pypi(name, version=None, test_pypi=False):
    from setuptools.command import easy_install

    if version is None:
        package_name = name
    else:
        package_name = "{}=={}".format(name, version)

    if test_pypi:
        index_part = ["--index-url", "https://test.pypi.org/simple/"]
    else:
        index_part = ["--index-url", "https://pypi.python.org/simple/"]

    easy_install.main(index_part + [package_name])

    import importlib
    globals()[name] = importlib.import_module(name)

def validate_pandas_dataframe(el, el_name, mandatory):
    import pandas as pd
    if el_name is None:
        raise MissingValue(u'el_name')

    if mandatory:
        if el is None:
            raise MissingValue(el_name)
        else:
            if not isinstance(el, pd.DataFrame):
                raise UnexpectedType(el_name, pd.DataFrame, type(el))

    elif el is None:
        return


def handle_response(expected_status_code, operationName, response, json_response=True):
    if response.status_code == expected_status_code:
        #print(u'Successfully finished {} for url: \'{}\''.format(operationName, response.url))
        #print(u'Response({} {}): {}'.format(response.request.method, response.url, response.text))
        if json_response:
            try:
                return response.json()
            except Exception as e:
                raise ClientError(u'Failure during parsing json response: \'{}\''.format(response.text), e)
        else:
            return response.text
    # elif response.status_code == 409:
    #     raise ApiRequestWarning(u'Warning during {}.'.format(operationName), response)
    else:
        raise ApiRequestFailure(u'Failure during {}.'.format(operationName), response) 

def get(obj: dict, path, default=None):
    """Gets the deep nested value from a dictionary
    Arguments:
        obj {dict} -- Dictionary to retrieve the value from
        path {list|str} -- List or . delimited string of path describing path.
    Keyword Arguments:
        default {mixed} -- default value to return if path does not exist (default: {None})
    Returns:
        mixed -- Value of obj at path
    """
    if isinstance(path, str):
        path = path.split(".")

    new_obj = {
        **obj
    }
    for key in path:
        if not new_obj:
            # for cases where key has null/none value
            return default

        if key in new_obj.keys():
            new_obj = new_obj.get(key)
        else:
            return default
    return new_obj 


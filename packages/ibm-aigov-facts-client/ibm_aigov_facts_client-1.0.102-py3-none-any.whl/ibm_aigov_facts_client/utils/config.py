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

import os 


dev_config = {
    'DEFAULT_DEV_SERVICE_URL': 'https://api.dataplatform.dev.cloud.ibm.com',
    'IAM_URL': 'https://iam.stage1.ng.bluemix.net/identity/token',
    'IAM_API_URL':'https://iam.test.cloud.ibm.com/identity/introspect',
    'DEFAULT_DEV_WML_SERVICE_URL':'https://wml-fvt.ml.test.cloud.ibm.com'
}

test_config = {
    'DEFAULT_TEST_SERVICE_URL': 'https://api.dataplatform.test.cloud.ibm.com',
    'IAM_URL': 'https://iam.cloud.ibm.com/identity/token', 
    'IAM_API_URL': 'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_TEST_WML_SERVICE_URL':'https://yp-qa.ml.cloud.ibm.com'
}

sydney_region = {
    "DEFAULT_SERVICE_URL": "https://api.au-syd.dai.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL':'https://us-south.ml.cloud.ibm.com',
    'UI_SERVICE_URL': 'https://au-syd.dai.cloud.ibm.com'
    
    }

frankfurt_region = {
    "DEFAULT_SERVICE_URL": "https://api.eu-de.dataplatform.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL':'https://us-south.ml.cloud.ibm.com',
    'UI_SERVICE_URL': 'https://eu-de.dataplatform.cloud.ibm.com',
    
    }

toronto_region = {
    "DEFAULT_SERVICE_URL": "https://api.ca-tor.dai.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL': "https://ca-tor.ml.cloud.ibm.com",
    'UI_SERVICE_URL': 'https://ca-tor.dai.cloud.ibm.com'

    }

tokyo_region = {
    "DEFAULT_SERVICE_URL": "https://api.jp-tok.dataplatform.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL': "https://jp-tok.ml.cloud.ibm.com",
    'UI_SERVICE_URL': "https://jp-tok.dataplatform.cloud.ibm.com"

    }

london_region = {
    "DEFAULT_SERVICE_URL": "https://api.eu-gb.dataplatform.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL': "https://eu-gb.ml.cloud.ibm.com",
    'UI_SERVICE_URL': 'https://eu-gb.dataplatform.cloud.ibm.com'

    }

prod_config = {
    "DEFAULT_SERVICE_URL": "https://api.dataplatform.cloud.ibm.com",
    'IAM_API_URL':'https://iam.cloud.ibm.com/identity/introspect',
    'DEFAULT_WML_SERVICE_URL':'https://us-south.ml.cloud.ibm.com'
}

aws_dev = {
    "DEFAULT_DEV_SERVICE_URL": "https://api.dev.aws.data.ibm.com",
    'API_URL':'https://account-iam.platform.test.saas.ibm.com',
    'DEFAULT_TEST_WML_SERVICE_URL': "https://dev.aws.wxai.ibm.com",
    'UI_SERVICE_URL': 'https://dev.aws.data.ibm.com'
    }

aws_mumbai = {
    "DEFAULT_SERVICE_URL": "http://api.ap-south-1.aws.data.ibm.com",
    'API_URL':'https://account-iam.platform.saas.ibm.com',
    'DEFAULT_WML_SERVICE_URL': "http://ap-south-1.aws.wxai.ibm.com",
    'UI_SERVICE_URL': 'http://ap-south-1.aws.data.ibm.com',
    
    }

aws_test = {
    "DEFAULT_TEST_SERVICE_URL": "https://api.test.aws.data.ibm.com",
    'API_URL':'https://account-iam.platform.test.saas.ibm.com',
    'DEFAULT_TEST_WML_SERVICE_URL': "https://test.aws.wxai.ibm.com",
    'UI_SERVICE_URL': 'https://test.aws.data.ibm.com'
    }

aws_govcloud={
    "DEFAULT_SERVICE_URL": "https://api.dai.ibmforusgov.com",
    "API_URL":"https://account-iam.awsg.usge1.private.platform.ibmforusgov.com",
    "IAM_URL" : "https://dai.ibmforusgov.com/api/rest/mcsp/apikeys/token",
    "DEFAULT_WML_SERVICE_URL": "https://wxai.ibmforusgov.com",
    "UI_SERVICE_URL": "https://dai.ibmforusgov.com"
}
aws_govcloudpreprod={
    "DEFAULT_TEST_SERVICE_URL": "https://api.dai.prep.ibmforusgov.com",
    "API_URL":"https://account-iam.awsg.usge1.private.platform.prep.ibmforusgov.com",
    'IAM_URL': 'https://dai.prep.ibmforusgov.com/api/rest/mcsp/apikeys/token',
    "DEFAULT_WML_SERVICE_URL": "https://wxai.prep.ibmforusgov.com",
    'UI_SERVICE_URL': 'https://dai.prep.ibmforusgov.com'
}

# def ensure_sydney_override():
#     current_env = os.environ.get("FACTS_CLIENT_ENV")
#     if current_env == "sydney":
#         prod_config.update(sydney_region)  
#     else:
#         os.environ["FACTS_CLIENT_ENV"] = os.environ.get("FACTS_CLIENT_ENV", "prod")

# def get_env():
#     ensure_sydney_override()
#     env_value = os.environ.get("FACTS_CLIENT_ENV", "prod")
#     return env_value



def ensure_sydney_override():
    if os.environ.get('FACTS_CLIENT_ENV') == "sydney":
        prod_config.update(sydney_region)  

    elif  os.environ.get('FACTS_CLIENT_ENV') == "frankfurt":
        prod_config.update(frankfurt_region) 

    elif  os.environ.get('FACTS_CLIENT_ENV') == "toronto":
        prod_config.update(toronto_region) 

    elif  os.environ.get('FACTS_CLIENT_ENV') == "tokyo":
        prod_config.update(tokyo_region)

    elif  os.environ.get('FACTS_CLIENT_ENV') == "london":
        prod_config.update(london_region) 

    elif  os.environ.get('FACTS_CLIENT_ENV') == "aws_dev":
        dev_config.update(aws_dev)

    elif  os.environ.get('FACTS_CLIENT_ENV') == "aws_test":
        test_config.update(aws_test)  

    elif  os.environ.get('FACTS_CLIENT_ENV') == "aws_mumbai":
        prod_config.update(aws_mumbai)

    elif  os.environ.get('FACTS_CLIENT_ENV') == "aws_govcloudpreprod":
        test_config.update(aws_govcloudpreprod)

    elif  os.environ.get('FACTS_CLIENT_ENV') == "aws_govcloud":
        prod_config.update(aws_govcloud)

    else:
        os.environ["FACTS_CLIENT_ENV"] = os.environ.get("FACTS_CLIENT_ENV", "prod")

def get_env():
    ensure_sydney_override()
    run_env = os.environ.get('FACTS_CLIENT_ENV', 'prod')
    if run_env in ['aws_test' , 'aws_govcloudpreprod']:
        return 'test'
    elif run_env == 'aws_dev':
        return 'dev'
    elif run_env in ['aws_mumbai' , 'aws_govcloud']:
        return 'prod'
    else:
        return run_env
def aws_env():
    return os.environ.get('FACTS_CLIENT_ENV', ' ')




WKC_MODEL_REGISTER = u"/v1/aigov/model_inventory/models/{}/model_entry"
WKC_MODEL_LIST_FROM_CATALOG = u"/v1/aigov/model_inventory/{}/model_entries"
WKC_MODEL_LIST_ALL = u"/v1/aigov/model_inventory/model_entries"

WKC_MODEL_UPDATE_RUNTIME = u"/v1/aigov/model_inventory/model_stub/{}/system_facts"
WKC_MODEL_DELETE_MONITOR_FROM_EVAL = u"/v1/aigov/model_inventory/models/{}/monitor/"

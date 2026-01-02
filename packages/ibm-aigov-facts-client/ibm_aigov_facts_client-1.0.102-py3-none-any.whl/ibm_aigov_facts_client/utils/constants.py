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


from .config import *


RESOURCES_URL_MAPPING = {
    dev_config["DEFAULT_DEV_SERVICE_URL"]: "https://resource-controller.test.cloud.ibm.com/v2/resource_instances",
    test_config["DEFAULT_TEST_SERVICE_URL"]: "https://resource-controller.cloud.ibm.com/v2/resource_instances",
    prod_config["DEFAULT_SERVICE_URL"]: "https://resource-controller.cloud.ibm.com/v2/resource_instances",
    sydney_region["DEFAULT_SERVICE_URL"]:"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    frankfurt_region["DEFAULT_SERVICE_URL"]:"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    toronto_region["DEFAULT_SERVICE_URL"]:"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    tokyo_region["DEFAULT_SERVICE_URL"]:"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    london_region["DEFAULT_SERVICE_URL"]:"https://resource-controller.cloud.ibm.com/v2/resource_instances",
   
}

RESOURCES_URL_MAPPING_NEW = {
    "dev" :"https://resource-controller.test.cloud.ibm.com/v2/resource_instances",
    "test": "https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "prod": "https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "sydney":"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "frankfurt":"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "toronto":"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "tokyo":"https://resource-controller.cloud.ibm.com/v2/resource_instances",
    "london":"https://resource-controller.cloud.ibm.com/v2/resource_instances"
}

RESOURCE_KEY_URL_MAPPING = {
    "dev": "https://resource-controller.test.cloud.ibm.com/v2/resource_keys",
    "test": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "prod": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "sydney": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "frankfurt": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "toronto": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "tokyo": "https://resource-controller.cloud.ibm.com/v2/resource_keys",
    "london": "https://resource-controller.cloud.ibm.com/v2/resource_keys"
}

BUCKET_BASE_URL_MAPPING = {
    "dev": "https://s3.us-west.cloud-object-storage.test.appdomain.cloud",
    "test": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "prod": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "sydney": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "frankfurt": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "toronto": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "tokyo": "https://s3.us.cloud-object-storage.appdomain.cloud",
    "london": "https://s3.us.cloud-object-storage.appdomain.cloud"

}

INVENTORY_URL_MAPPING = {
    "dev": "https://api.dataplatform.dev.cloud.ibm.com/v1/aigov/inventories",
    "test": "https://api.dataplatform.test.cloud.ibm.com/v1/aigov/inventories",
    "prod": "https://api.dataplatform.cloud.ibm.com/v1/aigov/inventories",
    "sydney": "https://api.au-syd.dai.cloud.ibm.com/v1/aigov/inventories",
    "frankfurt": "https://api.eu-de.dataplatform.cloud.ibm.com/v1/aigov/inventories",
    "toronto": "https://api.ca-tor.dai.cloud.ibm.com/v1/aigov/inventories",
    "tokyo": "https://api.jp-tok.dataplatform.cloud.ibm.com/v1/aigov/inventories",
    "london": "https://api.eu-gb.dataplatform.cloud.ibm.com/v1/aigov/inventories"

}

SPARK_FRAMEWORKS = ['pyspark', 'spark']
SPARK_ESTIMATOR_CLS = ['estimator_class']
DL_FRAMEWORKS = ['tensorflow', 'keras', 'pytorch']
BST_FRAMEWORKS = ['xgboost', 'lightgbm']


SPARK_JAR_PKG = "org.mlflow:mlflow-spark:1.11.0"
DL_EPOCHS_TAG = "epochs"
TF_EPOCHS_TAG = "steps"
BST_EPOCHS_TAG = "num_boost_round"
SPARK_HYP_TAG = "numFolds"


PRE_AUTOLOG_KEY = 'mlflow.autologging'
POST_AUTOLOG_KEY = 'facts.autologging'

SUPPORTED_FRAMEWORKS = ["sklearn", "pyspark",
                        "tensorflow", "keras", "xgboost", "lightgbm", "pytorch"]

IS_SPECIAL_FRAMEWORKS=["pycaret"] 

MANUAL_SUPPORTED_FRAMEWORKS = ['sklearn']
MANUAL_FRAMEWORK_KEY = 'facts.manual'

AUTO_FRAMEWORK_KEYS = ['mlflow.autologging',
                       'facts.autologging', 'facts_manual']

TRASH_FOLDER = ".trash"
SUBFOLDER_DEFAULT = "metrics"

CONTAINER_PROJECT = "project_id"
CONTAINER_SPACE = "space_id"


METRICS_FOLDER_NAME = "metrics"
PARAMS_FOLDER_NAME = "params"
TAGS_FOLDER_NAME = "tags"
PUBLISH_TAG = "facts.publish"

METRICS_META_NAME = "metrics"
PARAMS_META_NAME = "params"
TAGS_META_NAME = "tags"
RUNS_META_NAME = "runs"


EST_TAG = "estimator_name"

EARLY_STOP_TAG = "monitor"
EARLY_STOP_EPOCH_TAG = "stopped_epoch"
EARLY_STOP_ROUND_TAG = "early_stopping_rounds"
EARLY_STOP_ROUND_METRIC_TAG = "stopped_iteration"

LGBM_TAG = "lightgbm"
XGB_TAG = "xgboost"

KERAS_TAG = "keras"
TF_TAG = "tensorflow"

DEFAULT_DB_FILE_PATH = "file:///mlruns"
DEFAULT_LOCAL_FILE_PATH = "file://{}/mlruns"

# user facts
FACTS_USER_TYPE_TAG = "user"

# system facts
SYSTEM_FACTS_TAG = "modelfacts_system"

# dev facts tag
NOTEBOOK_EXP_FACTS = "notebook_experiment"
EXP_ID = "experiment_id"
EXP_NAME = "name"
RUN_ID = "run_id"
RUN_DATE = "created_date"

# model usecase
MODEL_USECASE_TAG = "modelentry_information"
MODEL_USECASE_CONTAINER_TYPE_TAG = "catalog"


# container model entry tags
TEST = "TEST"
DEVELOP = "DEVELOPMENT"
VALIDATE = "PRE-PRODUCTION"
OPERATE = "PRODUCTION"

# model tags

MODEL_INFO_TAG = "model_information"
ASSET_TYPE_TAG = "asset_type"
WML_MODEL = "wml_model"
EXT_MODEL = "model_stub"
PROMPT_ASSET = "wx_prompt"

# space

SPACE_DETAILS = "space_details"
SPACE_ID = "space_id"
SPACE_TYPE = "space_type"

SPACE_PREPROD_TAG = "AIGovernance: Pre-Production"
SPACES_PROD_TAG = "AIGovernance: Production"

SPACE_PREPROD_TAG_EXTERNAL = "pre-production"
SPACES_PROD_TAG_EXTERNAL = "production"

SPACE_TEST_TAG = "development"
SPACE_OS_MONITOR_TAG = "is_spacetype_openscale_value"

# deployment
DEPLOYMENT_DETAILS = "deployment_details"

# attachments
ATTACHMENT_TAG = "attachments"

# facts definnitions
PROPERTIES = "properties"

# operations
ADD = "add"
REPLACE = "replace"
REMOVE = "remove"

# steps tag
STEP = "step"

# file
MAX_SIZE = 524288000  # 500MB

# output width
OUTPUT_WIDTH=125
 
# cell facts path
CELL_FACTS_TMP_DIR = "captured_cell_facts"

#path
OPERATION_PATH = "/api/rest/mcsp/apikeys/token"

#AWS
AWS_TEST= "aws_test"
AWS_MUM= "aws_mumbai"
AWS_DEV="aws_dev"

#GOVCLOUD
AWS_GOVCLOUD= "aws_govcloud"
AWS_GOVCLOUD_PREPROD= "aws_govcloudpreprod"





# UI url
CLOUD_URL = "https://dataplatform.cloud.ibm.com"
CLOUD_DEV_URL = "https://dataplatform.dev.cloud.ibm.com"
CLOUD_TEST_URL = "https://dataplatform.test.cloud.ibm.com"
CATALOG_PATH = "{}/data/catalogs/{}/asset/{}/asset-preview?context=cpdaas"
PROJECT_PATH = "{}/ml/models/{}?projectid={}&context=cpdaas"
SPACE_PATH = "{}/ml-runtime/models/{}?space_id={}&context=cpdaas"
MODEL_USECASE_PATH = "{}/data/catalogs/{}/asset/{}?context=cpdaas"
PROMPT_PATH_PROJECT = "{}/wx/prompt-details/{}/factsheet?project_id={}&context=wx"
PROMPT_PATH_SPACE = "{}/ml-runtime/prompt-templates/{}/schema?space_id={}&context=wx"

urls = {
    "prod": "https://dataplatform.cloud.ibm.com",
    "dallas": "https://dataplatform.cloud.ibm.com",
    "sydney": "https://au-syd.dai.cloud.ibm.com",
    "frankfurt": "https://eu-de.dataplatform.cloud.ibm.com",
    "toronto": "https://ca-tor.dai.cloud.ibm.com",
    "tokyo": "https://jp-tok.dataplatform.cloud.ibm.com",
    "london": "https://eu-gb.dataplatform.cloud.ibm.com",
    "aws_dev":"https://dev.aws.data.ibm.com",
    "aws_test":"https://test.aws.data.ibm.com",
    "aws_mumbai":"https://ap-south-1.aws.data.ibm.com",
    "aws_govcloudpreprod":"https://dai.prep.ibmforusgov.com",
    "aws_govcloud":"https://dai.ibmforusgov.com"
}

def get_cloud_url():
    region = os.getenv("FACTS_CLIENT_ENV", "dallas").lower() 
    # print(f"region:{region}")
    cloud_url = urls.get(region)
    
    if not cloud_url:
        raise ValueError(f"No URL configured for region: {region}")
    
    return cloud_url
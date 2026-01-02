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

from enum import Enum


class ContainerType:
    """
        Describes possible container types. Client initialization works for SPACE or PROJECT only.
        Contains: [PROJECT,SPACE,CATALOG]
    """
    PROJECT = 'project'
    SPACE = 'space'
    CATALOG= "catalog"

class FormatType:
    """
        Describes output formats options
        Contains: [DICT,STR]
    """
    DICT = 'dict'
    STR = 'str'

class ModelEntryContainerType:
    """
        Describes possible model usecase container types.
        Contains: [DEVELOP,TEST,VALIDATE,OPERATE]
    """
    DEVELOP = 'develop'
    TEST = 'test'
    VALIDATE= 'validate'
    OPERATE= 'operate'

class ModelContainerType:
    """
        Describes possible model usecase container types.
        Contains: [DEVELOP,VALIDATE,OPERATE]
    """
    DEVELOP = 'Develop'
    VALIDATE= 'Validate'
    OPERATE= 'Operate'

class AllowedDefinitionType:
    """
        Describes possible CAMS data types for definitions.
        Contains: [INTEGER,STRING,DATE]
    """
    INTEGER = 'int'
    STRING = 'str'
    DATE= 'date'


class FactsType:
    """
        Describes possible Factsheet custom asset types. Only MODEL_FACTS_USER and MODEL_USECASE_USER supported when creating definitions.
        Contains: [MODEL_FACTS_USER,MODEL_USECASE_USER,MODEL_FACTS_USER_OP,MODEL_FACTS_SYSTEM,MODEL_FACTS_GLOBAL]

        - The modelfacts user AssetType to capture the user defined attributes of a model
        - The model usecase user asset type to capture user defined attributes of a model usecase
        - The modelfacts user AssetType to capture the user defined attributes of a model to be synced to OpenPages
        - The modelfacts system AssetType to capture the system defined attributes of a model
        - The modelfacts global AssetType to capture the global attributes of physical model (external model)

    """
    MODEL_FACTS_USER = 'modelfacts_user'
    MODEL_USECASE_USER = 'model_entry_user'
    MODEL_FACTS_USER_OP= 'modelfacts_user_op'
    MODEL_FACTS_SYSTEM= 'modelfacts_system'
    MODEL_FACTS_GLOBAL= 'modelfacts_global'


class AssetContainerSpaceMap(Enum):
    """
    Describes possible environment and space types.
    Contains: [DEVELOP,TEST,VALIDATE,OPERATE]

    """
    DEVELOP= ''
    TEST = 'development'
    VALIDATE= 'pre-production'
    OPERATE= 'production'


class AssetContainerSpaceMapExternal(Enum):
    """
    Describes possible environment and space types for external models.
    Contains: [DEVELOP,TEST,VALIDATE,OPERATE]

    """
    DEVELOP = 'development'
    TEST= 'development'
    VALIDATE= 'pre-production'
    OPERATE= 'production'

class RenderingHints:

    """Describes rendering hints for attachment facts.
    Contains: [INLINE_HTML,INLINE_IMAGE,LINK_DOWNLOAD,LINK_NEW_TAB]
    """
    
    INLINE_HTML='inline_html'
    INLINE_IMAGE='inline_image'
    LINK_DOWNLOAD='link_download'
    LINK_NEW_TAB='link_new_tab'


class OnErrorTypes:
    """
    expected behaviour on error.
    """
    STOP = 'stop'
    CONTINUE = 'continue'


class ContentTypes:
    """
    The type of the input. A character encoding can be specified by including a
    `charset` parameter. For example, 'text/csv;charset=utf-8'.
    """
    APPLICATION_JSON = 'application/json'
    TEXT_CSV = 'text/csv'

class StatusStateType:
    ACTIVE = "active"
    RUNNING = "running"
    FINISHED = "finished"
    PREPARING = "preparing"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILURE = "failure"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"
    CANCELED = "canceled"


class AttachmentFactDefinitionType:
    """
        Describes possible Factsheet attachment definition types. Only MODEL_TYPE and MODEL_USECASE_TYPE are supported.
        Contains: [MODEL_TYPE,MODEL_USECASE_TYPE]

        - The model to list attachment fact definitions for all models defined.
        - The model_usecase to list attachment fact definitions for all model usecases defined.
    """
    MODEL_TYPE = 'model'
    MODEL_USECASE_TYPE = 'model_usecase'


class Status:
    """
        Describes possible status types.
        Contains: [DRAFT,AWAITING_DEVELOPMENT,DEVELOPED,PROMPTED_TO_PRE_PRODUCTION,DEPLOYED_FOR_VALIDATION,VALIDATED,APPROVED,PROMPTED_TO_PRODUCTION,DEPLOYED_FOR_OPERATION,IN_OPERATION,UNDER_REVISION,DECOMMISSIONED]
    """
    DRAFT = 'draft'
    AWAITING_DEVELOPMENT = 'Awaiting development'
    DEVELOPED = 'Developed'
    PROMPTED_TO_PRE_PRODUCTION = 'Promoted to pre-production'
    DEPLOYED_FOR_VALIDATION = 'Deployed for validation'
    VALIDATED = 'Validated'
    APPROVED = 'Approved'
    PROMPTED_TO_PRODUCTION = 'Promoted to production'
    DEPLOYED_FOR_OPERATION = 'Deployed for operation'
    IN_OPERATION = 'In operation'
    UNDER_REVISION = 'Under revision'
    DECOMMISSIONED = 'Decommissioned'

class Risk:
    """
        Describes possible risk types.
        Contains: [HIGH,MEDIUM,LOW,CUSTOM,NONE]
    """
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    CUSTOM = 'custom'
    NONE = 'none'

class Provider:
    """
        Describes possible provider types.
        Contains: [WATSON_MACHINE_LEARNING,AMAZON_SAGEMAKER,AZURE_MACHINE_LEARNING,CUSTOM_MACHINE_LEARNING,SPSS_COLLABORATION_AND_DEPLOYMENT_SERVICES,AZURE_MACHINE_LEARNING_SERVICE]
    """
    WATSON_MACHINE_LEARNING = 'Watson Machine Learning'
    AMAZON_SAGEMAKER = 'Amazon SageMaker'
    AZURE_MACHINE_LEARNING = 'Microsoft Azure ML Studio'
    CUSTOM_MACHINE_LEARNING = 'Custom Environment'
    SPSS_COLLABORATION_AND_DEPLOYMENT_SERVICES = 'IBM SPSS Collaboration and Deployment Services'
    AZURE_MACHINE_LEARNING_SERVICE = 'Microsoft Azure ML Service'

class Icon:
    """
            Describes possible icon types.
            Contains: [PACKAGES, SPROUT, TREE, NEURAL_NETWORK, ROCKET, CODE, LINEAR, LOGISTIC, DECISION_TREE, SUPPORT_VECTOR_MACHINES, NETWORK, UNRELATED,DIMENSIONS, BOT, CHAT_BOT, IMAGE, SCALE, FINANCE, PIGGY_BANK, DELIVERY, FACTORY, ELECTRONICS, IDEA, RECYCLE, GLOBE, LANGUAGE, GIFT, ZOMBIE]
    """
    PACKAGES = 'Packages'
    SPROUT = 'Sprout'
    TREE = 'Tree'
    NEURAL_NETWORK = 'Neural_network'
    ROCKET = 'Rocket'
    CODE = 'Code'
    LINEAR = 'Linear'
    LOGISTIC = 'Logistic'
    DECISION_TREE = 'Decision-tree'
    SUPPORT_VECTOR_MACHINES = 'Support-vector-machines'
    NETWORK = 'Network'
    UNRELATED = 'Nnrelated'
    DIMENSIONS = 'Dimensions'
    BOT = 'Bot'
    CHAT_BOT = 'Chat-bot'
    IMAGE = 'Image'
    SCALE = 'Scale'
    FINANCE = 'Finance'
    PIGGY_BANK = 'Piggy-bank'
    DELIVERY = 'Delivery'
    FACTORY = 'Factory'
    ELECTRONICS = 'Electronics'
    IDEA = 'Idea'
    RECYCLE = 'Recycle'
    GLOBE = 'Globe'
    LANGUAGE = 'Language'
    GIFT = 'Gift'
    ZOMBIE = 'Zombie'

class Color:
    """
        Describes possible color types.
        Contains: [GRAY,GREEN,TEAL,CYAN,BLUE,PURPLE,MAGENTA,RED,ORANGE,YELLOW]
    """
    GRAY = 'Gray'
    GREEN = 'Green'
    TEAL = 'Teal'
    CYAN = 'Cyan'
    BLUE = 'Blue'
    PURPLE = 'Purple'
    MAGENTA = 'Magenta'
    RED = 'Red'
    ORANGE = 'Orange'
    YELLOW = 'Yellow'

class Task:
    """
        Describes possible Task for the prompt template creations
    """
    QUESTION_ANSWERING ="question_answering"
    SUMMARIZATION ="summarization"
    RETRIEVAL_AUGMENTED_GENERATION ="retrieval_augmented_generation"
    CLASSIFICATION ="classification"
    GENERATION = "generation"
    CODE_GENERATION_AND_CONVERSION ="code_generation_and_conversion"
    EXTRACTION ="extraction"
    TRANSLATION ="translation"

class InputMode:
    """
    Describes possible tasks for the prompt template creations.
    """
    STRUCTURED = "structured"
    FREEFORM = "freeform"


class ModelType:
    """
    Describes possible ModelType for the prompt  creations.
    """
    TUNED_MODEL = "tuned_model"
    BYOM = "byom"


class Phases:
    '''
    Descibes the possible values for Phases
    Contains : [DEVELOP, VALIDATE, OPERATE]
    '''
    DEVELOP = "develop"
    VALIDATE = "validate"
    OPERATE = "operate"

class ModelEntryContainerTypeExternal:
    """
        Describes possible model usecase container types for external model for cpd version >=5.0.1
        Contains: [DEVELOP,VALIDATE,OPERATE]
    """
    DEVELOP = 'develop'
    VALIDATE= 'validate'
    OPERATE=  'operate'

class Role:
    """
        Describes possible Role for collaborator creations
    """
    ADMIN ="admin"
    EDITOR ="editor"
    VIEWER ="viewer"

class Region:
    """
        Describes Region
    """
    SYDNEY = "sydney"
    FRANKFURT = "frankfurt"
    TORONTO = "toronto"
    TOKYO ="tokyo"
    LONDON ="london"
    AWS_MUMBAI= "aws_mumbai"
    AWS_GOVCLOUD= "aws_govcloud"


class DeploymentNode:
    """
        Describes Region
    """

    PLATFORM_INTEGRATED = "platform-integrated"
    STANDALONE = "standalone"

class S3Storage:
    """
        Describes S3 Storage
    """
    SHARED = "shared"
    DEDICATED = "dedicated"

  

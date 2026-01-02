import json
from typing import BinaryIO, Dict, List, TextIO, Union

class ExternalModelSchemas:
    """
    External model schema

    :ivar List[Dict] input: Model input data schema
    :ivar List[Dict] output: (optional) Model output data schema

    """
    def __init__(self,input: List[Dict],
                output:List[Dict]=None) -> None:

        """
        Initialize a ExternalModelSchemas object.

        :param List[Dict] input: Model input data schema
        :param List[Dict] output: (optional) Model output data schema
        
        """

        self.input = input
        self.output = output

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ExternalModelSchemas':
        """Initialize a DeploymentDetails object from a json dictionary."""
        args = {}
        if 'input' in _dict:
            args['input'] = _dict.get('input')
        else:
            raise ValueError('Required property \'deployment_id\' not present in ExternalModelSchemas JSON')
        if 'output' in _dict:
            args['output'] = _dict.get('output') #[convert_model(x) for x in metrics]
        else:
            raise ValueError('Required property \'output\' not present in ExternalModelSchemas JSON')
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a ExternalModelSchemas object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'input') and self.input is not None:
            _dict['input'] = self.input
        if hasattr(self, 'output') and self.output is not None:
            _dict['output'] = self.output
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ExternalModelSchemas object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'ExternalModelSchemas') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'ExternalModelSchemas') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other


class TrainingDataReference:
    """
    Training data schema definition

    :ivar str type: Type of training data reference. It has values as fs, url, data_asset or connection_asset.
    :ivar str id: ID of training data reference.
    :ivar Dict connection: (Optional) Connection details
    :ivar Dict location: (Optional) Location details
    :ivar Dict schema: Model training data schema

    If type is fs, the parameters that user needs to input are - location.path
    If type is url, the parameters that user needs to provide are - training_data_references[].id and connection.url
    If type is data_asset, then - location.href
    If type is connection_asset, then location.file_name or location.table_name, connection.href

    """ 

    def __init__(self, type: str=None, id: str=None, connection: Dict=None, location: Dict=None, schema:Dict=None) -> None:
        """
        Initialize a TrainingDataReference object.

        :param str type: Model training data type
        :param str id: Model training data id
        :param Dict connection: (Optional) Model training data connection
        :param Dict location: (Optional)  Model training data location
        :param Dict schema: Model training data schema

        """

        self.type = type
        self.id = id
        self.connection = connection
        self.location = location
        self.schema = schema

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'TrainingDataReference':
        """Initialize a TrainingDataReference object from a json dictionary."""
        args = {}

        if 'type' in _dict:
            args['type'] = _dict.get('type')
        else:
            raise ValueError('Required property \'type\' not present in TrainingDataReference JSON')
        if 'id' in _dict:
            args['id'] = _dict.get('id')
        else:
            raise ValueError('Required property \'id\' not present in TrainingDataReference JSON')
        if 'connection' in _dict:
            args['connection'] = _dict.get('connection')
        else:
            raise ValueError('Required property \'connection\' not present in TrainingDataReference JSON')
        if 'location' in _dict:
            args['location'] = _dict.get('location')
        else:
            raise ValueError('Required property \'location\' not present in TrainingDataReference JSON')
        if 'schema' in _dict:
            args['schema'] = _dict.get('schema')
        else:
            raise ValueError('Required property \'schema\' not present in TrainingDataReference JSON')
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a TrainingDataReference object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'type') and self.type is not None:
            _dict['type'] = self.type
        if hasattr(self, 'id') and self.id is not None:
            _dict['id'] = self.id
        if hasattr(self, 'connection') and self.connection is not None:
            _dict['connection'] = self.connection
        if hasattr(self, 'location') and self.location is not None:
            _dict['location'] = self.location
        if hasattr(self, 'schema') and self.schema is not None:
            _dict['schema'] = self.schema
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this TrainingDataReference object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'TrainingDataReference') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'TrainingDataReference') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other

class DeploymentDetails:
    """
    External model deployment details

    :ivar str identifier: Deployment identifier specific to providers.
    :ivar str name: Name of the deployment
    :ivar str deployment_type: Deployment type (i.e., online)
    :ivar str scoring_endpoint: Deployment scoring endpoint url.  
    :ivar str description: (Optional) Description of the deployment

    """

    def __init__(self,identifier: str,
                 name: str,
                 deployment_type: str,
                 scoring_endpoint: str = None, description: str = None) -> None:
        
        """
        Initialize a DeploymentDetails object.

        :param str identifier: Deployment identifier specific to ML providers
        :param str name: Name of the deployment
        :param str deployment_type: Deployment type (i.e., online)
        :param str scoring_endpoint: Deployment scoring endpoint url. 
        :param str description: (Optional) Deployment description.

        """
        
        self.id = identifier
        self.name = name
        self.type = deployment_type
        self.scoring_endpoint = scoring_endpoint
        self.description = description


    @classmethod
    def from_dict(cls, _dict: Dict) -> 'DeploymentDetails':
        """Initialize a DeploymentDetails object from a json dictionary."""
        args = {}
        if 'id' in _dict:
            args['id'] = _dict.get('id')
        else:
            raise ValueError('Required property \'id\' not present in DeploymentDetails JSON')
        if 'name' in _dict:
            args['name'] = _dict.get('name')
        else:
            raise ValueError('Required property \'name\' not present in DeploymentDetails JSON')
        if 'type' in _dict:
            args['type'] = _dict.get('type')
        else:
            raise ValueError('Required property \'type\' not present in DeploymentDetails JSON')
        if 'scoring_endpoint' in _dict:
            args['scoring_endpoint'] = _dict.get('scoring_endpoint')
        else:
            raise ValueError('Required property \'scoring_endpoint\' not present in DeploymentDetails JSON')
        if 'description' in _dict:
            args['description'] = _dict.get('description')
        else:
            raise ValueError('Required property \'description\' not present in DeploymentDetails JSON')
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a DeploymentDetails object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'id') and self.id is not None:
            _dict['id'] = self.id
        if hasattr(self, 'name') and self.name is not None:
            _dict['name'] = self.name
        if hasattr(self, 'type') and self.type is not None:
            _dict['type'] = self.type
        if hasattr(self, 'scoring_endpoint') and self.scoring_endpoint is not None:
            _dict['scoring_endpoint'] = self.scoring_endpoint
        if hasattr(self, 'description') and self.description is not None:
            _dict['description'] = self.description
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this DeploymentDetails object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'DeploymentDetails') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'DeploymentDetails') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other



class ModelEntryProps:
    """
    Model usecase Properties
        
    :ivar str model_entry_catalog_id: Catalog ID where model usecase exist.
    :ivar str asset_id: Published model/asset ID. It is optional for external models ONLY.
    :ivar str model_catalog_id: (Optional) Catalog Id where model exist.
    :ivar str model_entry_id: (Optional) Existing Model usecase to link with.
    :ivar str model_entry_name: (Optional) New model usecase name. Used only when creating new model usecase. 
    :ivar str model_entry_description: (Optional) New model usecase description. Used only when creating new model usecase. 
    :ivar str project_id: (Optional) Project ID where the model exist.Not applicable for external models.
    :ivar str space_id: (Optional) Space ID where model exist Not applicable for external models.
    :ivar str grc_model_id: (Optional) Openpages model id. Only applicable for CPD environments.  
    
    """

    def __init__(self,
                 model_entry_catalog_id: str,
                 asset_id: str=None,
                 model_catalog_id: str=None,
                 model_entry_id: str=None,
                 model_entry_name: str=None,
                 model_entry_desc: str = None,
                 project_id: str=None,
                 space_id: str=None,
                 grc_model_id: str=None) -> None:
        
        """
        Initialize a ModelEntryProps object.
        
        :param str model_entry_catalog_id: Catalog ID where model entry exist.
        :param str asset_id: Published model/asset ID. Optional for external models.
        :param str model_catalog_id: (Optional) Catalog Id where model exist.
        :param str model_entry_id: (Optional) Existing Model usecase to link with.
        :param str model_entry_name: (Optional) New model entry name. Used only when creating new model entry. 
        :param str model_entry_description: (Optional) New model entry description. Used only when creating new model entry. 
        :param str project_id: (Optional) Project ID where the model exist. Not applicable for external models.
        :param str space_id: (Optional) Space ID where model exist. Not applicable for external models.
        :param str grc_model_id: (Optional) Openpages model id. Only applied for CPD environments.  
        """
        
        self.asset_id=asset_id
        self.model_entry_catalog_id = model_entry_catalog_id
        self.model_catalog_id=model_catalog_id
        self.model_entry_id = model_entry_id
        self.model_entry_name = model_entry_name
        self.model_entry_desc = model_entry_desc
        self.project_id=project_id
        self.space_id=space_id
        self.grc_model_id=grc_model_id


    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ModelEntryProps':
        """Initialize a ModelEntryProps object from a json dictionary."""
        args = {}
        if 'model_entry_catalog_id' in _dict:
            args['model_entry_catalog_id'] = _dict.get('model_entry_catalog_id')
        else:
            raise ValueError('Required property \'model_entry_catalog_id\' not present in ModelEntryProps JSON')
        if 'asset_id' in _dict:
            args['asset_id'] = _dict.get('asset_id')
        else:
            raise ValueError('Required property \'asset_id\' not present in ModelEntryProps JSON')
        if 'model_catalog_id' in _dict:
            args['model_catalog_id'] = _dict.get('model_catalog_id')
        else:
            raise ValueError('Required property \'model_catalog_id\' not present in ModelEntryProps JSON')
        if 'model_entry_id' in _dict:
            args['model_entry_id'] = _dict.get('model_entry_id')
        else:
            raise ValueError('Required property \'model_entry_id\' not present in ModelEntryProps JSON')
        if 'model_entry_name' in _dict:
            args['model_entry_name'] = _dict.get('model_entry_name')
        else:
            raise ValueError('Required property \'model_entry_name\' not present in ModelEntryProps JSON')
        if 'model_entry_desc' in _dict:
            args['model_entry_desc'] = _dict.get('model_entry_desc')
        else:
            raise ValueError('Required property \'model_entry_desc\' not present in ModelEntryProps JSON')
        if 'project_id' in _dict:
            args['project_id'] = _dict.get('project_id')
        else:
            raise ValueError('Required property \'project_id\' not present in ModelEntryProps JSON')
        if 'space_id' in _dict:
            args['space_id'] = _dict.get('space_id')
        else:
            raise ValueError('Required property \'space_id\' not present in ModelEntryProps JSON')
        if 'grc_model_id' in _dict:
            args['grc_model_id'] = _dict.get('grc_model_id')
        else:
            raise ValueError('Required property \'grc_model_id\' not present in ModelEntryProps JSON')
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a ModelEntryProps object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'asset_id') and self.asset_id is not None:
            _dict['asset_id'] = self.asset_id
        if hasattr(self, 'model_entry_catalog_id') and self.model_entry_catalog_id is not None:
            _dict['model_entry_catalog_id'] = self.model_entry_catalog_id
        if hasattr(self, 'model_catalog_id') and self.model_catalog_id is not None:
            _dict['model_catalog_id'] = self.model_catalog_id
        if hasattr(self, 'model_entry_id') and self.model_entry_id is not None:
            _dict['model_entry_id'] = self.model_entry_id
        if hasattr(self, 'model_entry_name') and self.model_entry_name is not None:
            _dict['model_entry_name'] = self.model_entry_name
        if hasattr(self, 'model_entry_desc') and self.model_entry_desc is not None:
            _dict['model_entry_desc'] = self.model_entry_desc
        if hasattr(self, 'project_id') and self.project_id is not None:
            _dict['project_id'] = self.project_id
        if hasattr(self, 'space_id') and self.space_id is not None:
            _dict['space_id'] = self.space_id
        if hasattr(self, 'grc_model_id') and self.grc_model_id is not None:
            _dict['grc_model_id'] = self.grc_model_id
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this DeploymentDetails object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'ModelEntryProps') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'ModelEntryProps') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other







class ModelDetails:
    """
    External model model details

    :ivar str model_type: Value for model type
    :ivar str input_type: Value for inout type
    :ivar str algorithm: Value for algorithm
    :ivar str label_type: Value for label type
    :ivar str label_column: Value for label column
    :ivar str prediction_type: Value for prediction type
    :ivar str software_spec: Value for software_spec
    :ivar str software_spec_id: Value for software_spec_id
    :ivar str provider: Value for provider,Available options are in :func:`~ibm_aigov_facts_client.utils.enums.Provider`
    
    """

    def __init__(self,model_type: str=None,
                 input_type: str=None,
                 algorithm: str=None,
                 label_type: str=None,
                 label_column: str=None,
                 prediction_type: str=None,
                 software_spec: str=None,
                 software_spec_id: str=None,
                 provider: str=None
                 ) -> None:
        
        """
        Initialize a ModelDetails object.

        :param str model_type: Value for model type
        :param str input_type: Value for inout type
        :param str algorithm: Value for algorithm
        :param str label_type: Value for label type
        :param str label_column: Value for label column
        :param str prediction_type: Value for prediction type
        :param str software_spec: Value for software_spec
        :param str software_spec_id: Value for software_spec_id
        :param str provider: Value for provider

        """
        
        self.model_type = model_type
        self.input_type = input_type
        self.algorithm = algorithm
        self.label_type = label_type
        self.label_column = label_column
        self.prediction_type = prediction_type
        self.software_spec = software_spec
        self.software_spec_id = software_spec_id
        self.provider = provider

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'ModelDetails':
        """Initialize a ModelDetails object from a json dictionary."""
        args = {}
        if 'model_type' in _dict:
            args['model_type'] = _dict.get('model_type')

        if 'input_type' in _dict:
            args['input_type'] = _dict.get('input_type')

        if 'algorithm' in _dict:
            args['algorithm'] = _dict.get('algorithm')

        if 'label_type' in _dict:
            args['label_type'] = _dict.get('label_type')

        if 'label_column' in _dict:
            args['label_column'] = _dict.get('label_column')

        if 'prediction_type' in _dict:
            args['prediction_type'] = _dict.get('prediction_type')

        if 'software_spec' in _dict:
            args['software_spec'] = _dict.get('software_spec')

        if 'software_spec_id' in _dict:
            args['software_spec_id'] = _dict.get('software_spec_id')

        if 'provider' in _dict:
            args['provider'] = _dict.get('provider')

        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a ModelDetails object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'model_type') and self.model_type is not None:
            _dict['model_type'] = self.model_type
        if hasattr(self, 'input_type') and self.input_type is not None:
            _dict['input_type'] = self.input_type
        if hasattr(self, 'algorithm') and self.algorithm is not None:
            _dict['algorithm'] = self.algorithm
        if hasattr(self, 'label_type') and self.label_type is not None:
            _dict['label_type'] = self.label_type
        if hasattr(self, 'label_column') and self.label_column is not None:
            _dict['label_column'] = self.label_column
        if hasattr(self, 'prediction_type') and self.prediction_type is not None:
            _dict['prediction_type'] = self.prediction_type
        if hasattr(self, 'software_spec') and self.software_spec is not None:
            _dict['software_spec'] = self.software_spec
        if hasattr(self, 'software_spec_id') and self.software_spec_id is not None:
            _dict['software_spec_id'] = self.software_spec_id
        if hasattr(self, 'provider') and self.provider is not None:
            _dict['provider'] = self.provider
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ModelDetails object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'ModelDetails') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'ModelDetails') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other

class PromptTemplate:
    """
    Details of a PromptTemplate
    
    :ivar dict model_version: (Optional) Model version information and their respective values.
    :ivar dict prompt_variables: (Optional) Values for prompt variables in the format {prompt_variable: value}.
    :ivar str prompt_instruction: (Optional) Instruction for using the prompt.
    :ivar str input_prefix: (Optional) Prefix for input data.
    :ivar str output_prefix:  (Optional)Prefix for output data.
    :ivar dict structured_examples: (Optional) Values of examples in the format {example_input: example_output}.
    :ivar str input_prompt: (Optional)Prompt input value.
    :ivar dict model_parameters: (Optional)Model parameters and their respective values.
    """

    def __init__(self, model_version: dict=None, prompt_variables: dict=None, prompt_instruction: str=None, input_prefix: str=None, output_prefix: str=None, structured_examples: dict=None,input: str=None,model_parameters:dict=None):
        
        self.model_version = model_version
        self.prompt_variables = prompt_variables
        self.prompt_instruction = prompt_instruction
        self.input_prefix = input_prefix
        self.output_prefix = output_prefix
        self.structured_examples =structured_examples
        self.input=input
        self.model_parameters=model_parameters
        
        # # Model Parameters
        # self.decoding_method = decoding_method
        # self.max_new_tokens = max_new_tokens
        # self.min_new_tokens = min_new_tokens
        # self.random_seed = random_seed
        # self.stop_sequences = stop_sequences
        # self.temperature = temperature
        # self.top_k = top_k
        # self.top_p = top_p
        # self.repetition_penalty = repetition_penalty
    
        
    @classmethod
    def from_dict(cls, _dict: Dict) -> 'PromptTemplate':
        """Initialize a ModelDetails object from a json dictionary."""
        args = {}
        if 'input' in _dict:
            args['input'] = _dict.get('input')
        if 'model_version' in _dict:
            args['model_version'] = _dict.get('model_version')
        if 'prompt_variables' in _dict:
            args['prompt_variables'] = _dict.get('prompt_variables')
        if 'model_id' in _dict:
            args['model_id'] = _dict.get('model_id')
        if 'prompt_instruction' in _dict:
            args['prompt_instruction'] = _dict.get('prompt_instruction')
        if 'input_prefix' in _dict:
            args['input_prefix'] = _dict.get('input_prefix')
        if 'output_prefix' in _dict:
            args['output_prefix'] = _dict.get('output_prefix')
        if 'structered_examples' in _dict:
            args['structered_examples'] = _dict.get('structered_examples')
        if 'freeform_input' in _dict:
            args['freeform_input'] = _dict.get('freeform_input')
        if 'structered_input' in _dict:
            args['structered_input'] = _dict.get('structered_input')

        # # model paramters
        # if 'decoding_method' in _dict:
        #     args['decoding_method'] = _dict.get('decoding_method')
        # if 'max_new_tokens' in _dict:
        #     args['max_new_tokens'] = _dict.get('max_new_tokens')
        # if 'min_new_tokens' in _dict:
        #     args['min_new_tokens'] = _dict.get('min_new_tokens')
        # if 'random_seed' in _dict:
        #     args['random_seed'] = _dict.get('random_seed')
        # if 'stop_sequences' in _dict:
        #     args['stop_sequences'] = _dict.get('stop_sequences')
        # if 'temperature' in _dict:
        #     args['temperature'] = _dict.get('temperature')
        # if 'top_k' in _dict:
        #     args['top_k'] = _dict.get('top_k')
        # if 'top_p' in _dict:
        #     args['top_p'] = _dict.get('top_p')
        # if 'repetition_penalty' in _dict:
        #     args['repetition_penalty'] = _dict.get('repetition_penalty')
        
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a ModelDetails object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'input') and self.input is not None:
            _dict['input'] = self.input
        if hasattr(self, 'model_version') and self.model_version is not None:
            _dict['model_version'] = self.model_version
        if hasattr(self, 'prompt_variables') and self.prompt_variables is not None:
            _dict['prompt_variables'] = self.prompt_variables
        if hasattr(self, 'prompt_instruction') and self.prompt_instruction is not None:
            _dict['prompt_instruction'] = self.prompt_instruction
        if hasattr(self, 'input_prefix') and self.input_prefix is not None:
            _dict['input_prefix'] = self.input_prefix
        if hasattr(self, 'output_prefix') and self.output_prefix is not None:
            _dict['output_prefix'] = self.output_prefix
        if hasattr(self, 'structured_examples') and self.structured_examples is not None:
            _dict['examples'] = self.structured_examples
        
        # #model paramters
        # if hasattr(self, 'decoding_method') and self.decoding_method is not None:
        #     _dict['decoding_method'] = self.decoding_method
        # if hasattr(self, 'max_new_tokens') and self.max_new_tokens is not None:
        #     _dict['max_new_tokens'] = self.max_new_tokens
        # if hasattr(self, 'min_new_tokens') and self.min_new_tokens is not None:
        #     _dict['min_new_tokens'] = self.min_new_tokens
        # if hasattr(self, 'random_seed') and self.random_seed is not None:
        #     _dict['random_seed'] = self.random_seed
        # if hasattr(self, 'stop_sequences') and self.stop_sequences is not None:
        #     _dict['stop_sequences'] = self.stop_sequences
        # if hasattr(self, 'temperature') and self.temperature is not None:
        #     _dict['temperature'] = self.temperature
        # if hasattr(self, 'top_k') and self.top_k is not None:
        #     _dict['top_k'] = self.top_k
        # if hasattr(self, 'top_p') and self.top_p is not None:
        #     _dict['top_p'] = self.top_p
        # if hasattr(self, 'repetition_penalty') and self.repetition_penalty is not None:
        #     _dict['repetition_penalty'] = self.repetition_penalty
        # return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ModelDetails object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'PromptTemplate') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'PromptTemplate') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other

class DetachedPromptTemplate:
    """
        Details of a detached prompt template.

        :ivar str prompt_id: ID of the external prompt.
        :ivar str model_id: ID of the external model associated with the prompt.
        :ivar str model_provider: Provider of the external model.
        :ivar str model_name: (Optional) Name of the external model (optional).
        :ivar str model_url: URL of the external model (optional).
        :ivar str prompt_url: URL of the external prompt (optional).
        :ivar dict prompt_additional_info: Additional information related to the external prompt (optional).
    """ 
    def __init__(self, prompt_id: str, model_id: str, model_provider: str,model_name :str= None,model_url: str= None,prompt_url :str=None,prompt_additional_info:list= None):
        self.prompt_id = prompt_id
        self.model_id = model_id
        self.model_provider = model_provider
        self.model_name = model_name
        self.model_url = model_url
        self.prompt_url = prompt_url
        self.prompt_additional_info = prompt_additional_info
    

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'DetachedPromptTemplate':
        """Initialize a ModelDetails object from a json dictionary."""
        args = {}
        if 'external_prompt_id' in _dict:
            args['external_prompt_id'] = _dict.get('external_prompt_id')
        if 'external_model_id' in _dict:
            args['external_model_id'] = _dict.get('external_model_id')
        if 'external_model_provider' in _dict:
            args['external_model_provider'] = _dict.get('external_model_provider')
        if 'external_model_name' in _dict:
            args['external_model_name'] = _dict.get('external_model_name')
        if 'external_model_url' in _dict:
            args['external_model_url'] = _dict.get('external_model_url')
        if 'external_prompt_url' in _dict:
            args['external_prompt_url'] = _dict.get('external_prompt_url')
        if 'external_prompt_additional_info' in _dict:
            args['external_prompt_additional_info'] = _dict.get('external_prompt_additional_info')

        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a ModelDetails object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'external_prompt_id') and self.prompt_id is not None:
            _dict['external_prompt_id'] = self.prompt_id
        if hasattr(self, 'external_model_id') and self.model_id is not None:
            _dict['external_model_id'] = self.model_id
        if hasattr(self, 'external_model_provider') and self.model_provider is not None:
            _dict['external_model_provider'] = self.model_provider
        if hasattr(self, 'external_model_name') and self.model_name is not None:
            _dict['external_model_name'] = self.model_name
        if hasattr(self, 'external_model_url') and self.model_url is not None:
            _dict['external_model_url'] = self.model_url
        if hasattr(self, 'external_prompt_url') and self.prompt_url is not None:
            _dict['external_prompt_url'] = self.prompt_url
        if hasattr(self, 'external_prompt_additional_info') and self.prompt_additional_info is not None:
            _dict['external_prompt_additional_info'] = self.prompt_additional_info
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()

    def __str__(self) -> str:
        """Return a `str` version of this ModelDetails object."""
        return json.dumps(self.to_dict(), indent=2)

    def __eq__(self, other: 'DetachedPromptTemplate') -> bool:
        """Return `true` when self and other are equal, false otherwise."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other: 'DetachedPromptTemplate') -> bool:
        """Return `true` when self and other are not equal, false otherwise."""
        return not self == other

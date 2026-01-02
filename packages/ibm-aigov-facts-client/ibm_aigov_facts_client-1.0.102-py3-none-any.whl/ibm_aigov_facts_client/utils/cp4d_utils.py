import logging
from typing import BinaryIO, Dict, List, TextIO, Union

from ..utils.config import *


_logger = logging.getLogger(__name__)


class CloudPakforDataConfig:
    """
    Configurations for Cloud Pak for Data environment

    :ivar str service_url: Host URL of Cloud Pak for Data environment.
    :ivar str username: Environment username
    :ivar str password: Environment password
    :ivar str api_key: Environment api_key if IAM enabled
    :ivar bool disable_ssl_verification: Disable SSL verification. Default is True.
    :ivar str bedrock_url: (Optional) Foundational services (common-services-route ) url. User needs to get this url from CP4D admin. This url is required only when iam-integration is enabled on CP4D 4.0.x cluster.   
    """

    def __init__(self,service_url: str,
                 username: str,
                 password: str=None,
                 api_key:str=None,
                 disable_ssl_verification: bool = True,
                 bedrock_url:str = None
                 ) -> None:
        
        """
        Initialize a CloudPakforDataConfig object.

        :param str service_url: Host URL of Cloud Pak for Data environment.
        :param str username: Environment username
        :param str password: Environment password
        :param str api_key: Environment api_key if IAM enabled
        :param bool disable_ssl_verification: Disable SSL verification. Default is True 
        :param str bedrock_url: (Optional) Foundational services (common-services-route ) url. User needs to get this url from CP4D admin. This url is required only when iam-integration is enabled on CP4D 4.0.x cluster. 
        
        """
        
        self.url = service_url
        self.username = username
        self.password = password
        self.api_key=api_key
        self.disable_ssl_verification = disable_ssl_verification
        self.bedrock_url=bedrock_url


    @classmethod
    def from_dict(cls, _dict: Dict) -> 'CloudPakforDataConfig':
        """Initialize a DeploymentDetails object from a json dictionary."""
        args = {}
        if 'url' in _dict:
            args['url'] = _dict.get('url')
        else:
            raise ValueError('Required property \'url\' not present in CloudPakforDataConfig JSON')
        if 'username' in _dict:
            args['username'] = _dict.get('username')
        else:
            raise ValueError('Required property \'username\' not present in CloudPakforDataConfig JSON')
        if 'password' in _dict:
            args['password'] = _dict.get('password')
        else:
            raise ValueError('Required property \'password\' not present in CloudPakforDataConfig JSON')
        if 'api_key' in _dict:
            args['api_key'] = _dict.get('api_key')
        else:
            raise ValueError('Required property \'api_key\' not present in CloudPakforDataConfig JSON')
        if 'disable_ssl_verification' in _dict:
            args['disable_ssl_verification'] = _dict.get('disable_ssl_verification')
        else:
            raise ValueError('Required property \'disable_ssl_verification\' not present in CloudPakforDataConfig JSON')
        if 'bedrock_url' in _dict:
            args['bedrock_url'] = _dict.get('bedrock_url')
        else:
            raise ValueError('Required property \'bedrock_url\' not present in CloudPakforDataConfig JSON')    
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        """Initialize a DeploymentDetails object from a json dictionary."""
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'url') and self.url is not None:
            _dict['url'] = self.url
        if hasattr(self, 'username') and self.username is not None:
            _dict['username'] = self.username
        if hasattr(self, 'password') and self.password is not None:
            _dict['password'] = self.password
        if hasattr(self, 'api_key') and self.api_key is not None:
            _dict['api_key'] = self.api_key
        if hasattr(self, 'disable_ssl_verification') and self.disable_ssl_verification is not None:
            _dict['disable_ssl_verification'] = self.disable_ssl_verification
        if hasattr(self, 'bedrock_url') and self.bedrock_url is not None:
            _dict['bedrock_url'] = self.bedrock_url
        return _dict

    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()
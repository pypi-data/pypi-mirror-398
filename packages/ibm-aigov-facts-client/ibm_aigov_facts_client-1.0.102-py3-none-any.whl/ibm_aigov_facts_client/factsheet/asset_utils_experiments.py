
import logging
import os
import json
import collections
import itertools
import ibm_aigov_facts_client._wrappers.requests as requests

from typing import Optional

from typing import BinaryIO, Dict, List, TextIO, Union,Any
from ibm_aigov_facts_client.factsheet import assets,utils
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator,CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.factsheet.asset_utils_runs import NotebookExperimentRunsUtilities

from ibm_aigov_facts_client.factsheet import asset_utils_model
from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.metrics_utils import convert_metric_value_to_float_if_possible


_logger = logging.getLogger(__name__) 


class NotebookExperimentUtilities:

    """
        Model notebook experiment utilities. Running `client.assets.model()` makes all methods in NotebookExperimentUtilities object available to use.
    
    """
   
    def __init__(self,assets_client:'assets.Assets',exp_id:str=None,exp_name:str=None,facts_type: str=NOTEBOOK_EXP_FACTS) -> None:


        self._facts_type=facts_type
        self._exp_id=exp_id
        self._exp_name=exp_name

        self._assets_client=assets_client
        self._facts_client=self._assets_client._facts_client
        self._is_cp4d=self._assets_client._is_cp4d
        self._external_model=self._assets_client._external_model
        self._asset_id = self._assets_client._asset_id
        self._container_type=self._assets_client._container_type
        self._container_id=self._assets_client._container_id

        if self._is_cp4d:
            self._cpd_configs=self._assets_client._cpd_configs
        
        self._cur_exp_runs=None
        self.utils_client = utils.Utils(self._facts_client)
        self.asset_utils_model=asset_utils_model.ModelAssetUtilities(self._assets_client,model_id=self._asset_id,container_type=self._container_type,container_id=self._container_id,facts_type=self._facts_type)

    @classmethod
    def from_dict(cls, _dict: Dict) -> 'NotebookExperimentUtilities':
        """Initialize a ModelAssetUtilities object from a json dictionary."""
        args = {}
        if '_exp_id' in _dict:
            args['exp_id'] = _dict.get('_exp_id')
        if '_exp_name' in _dict:
            args['exp_name'] = _dict.get('_exp_name')  
        
        return cls(**args)

    @classmethod
    def _from_dict(cls, _dict):
        return cls.from_dict(_dict)

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, '_exp_id') and self._exp_id is not None:
            _dict['exp_id'] = self._exp_id
        if hasattr(self, '_exp_name') and self._exp_name is not None:
            _dict['exp_name'] = self._exp_name
        if hasattr(self, '_asset_id') and self._asset_id is not None:
            _dict['asset_id'] = self._asset_id
        if hasattr(self, '_container_id') and self._container_id is not None:
            _dict['container_id'] = self._container_id
        if hasattr(self, '_container_type') and self._container_type is not None:
            _dict['container_type'] = self._container_type
        
        return _dict
  
    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()
    
    def get_info(self):
        """
            Get experiment info. Supported for CPD version >=4.6.4


            A way to use me is:

            >>> exp=model.get_experiment()
            >>> exp.get_info()


        """
        
        return self._to_dict()

    def get_run(self,run_id:str=None)-> NotebookExperimentRunsUtilities:

        """
            Get run object available in notebook experiment. Supported for CPD version >=4.6.4


            A way to use me is:

            >>> run=exp.get_run() # returns latest run object available
            >>> run=exp.get_run(run_id=run_id) # you can get specific run object


        """
                
        self._cur_exp_runs=self._get_current_notebook_experiment_runs()
        if self._cur_exp_runs:
            if run_id:
                run_idx, run_info=self._get_latest_run_idx(self._cur_exp_runs,run_id=run_id)             
            else:
                run_idx, run_info=self._get_latest_run_idx(self._cur_exp_runs)
            
            return NotebookExperimentRunsUtilities(self,self._cur_exp_runs,run_id,run_idx,run_info)
               
        else:
            if run_id:
                raise ClientError("No information found for run {}".format(run_id))
            else:
                raise ClientError("Current run information is not found")

        
    def get_all_runs(self):

        """
            Get all runs available in notebook experiment. Supported for CPD version >=4.6.4


            A way to use me is:

            >>> exp.get_all_runs()


        """
        self._cur_exp_runs=self._get_current_notebook_experiment_runs()
        if self._cur_exp_runs:
            return self._cur_exp_runs
        else:
            raise ClientError("No runs associated with current experiment {}".format(self._exp_name))

    def _get_current_notebook_experiment_runs(self): 

        if self.asset_utils_model._is_new_usecase() and not self._external_model:
            get_notebook_exp_url= self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
        else:
            get_notebook_exp_url=self._get_url_by_factstype_container(type_name=NOTEBOOK_EXP_FACTS)
        cur_data = requests.get(get_notebook_exp_url,headers=self._get_headers())
        if cur_data.status_code==200:
            notebook_experiment_runs=cur_data.json()[NOTEBOOK_EXP_FACTS].get(RUNS_META_NAME)
            if notebook_experiment_runs:
                return notebook_experiment_runs
            else:
                return None
        else:
            return None

    def _get_url_by_factstype_container_mastercopy(self,type_name=None):

        master_copy_info=self.utils_client.get_master_copy_info(self._asset_id,self._container_type,self._container_id)
        master_copy_id=master_copy_info['master_copy_id']
        inventory_id=master_copy_info['inventory_id']
        container_type="catalog"
       

        facts_type= type_name or self._facts_type
        
        if self._is_cp4d:
           
           url = self._cpd_configs["url"] + \
                '/v2/assets/' + master_copy_id + "/attributes/" + \
            facts_type + "?" + container_type + "_id=" + inventory_id
        
        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                facts_type + "?" + container_type + "_id=" + inventory_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                facts_type + "?" + container_type + "_id=" + inventory_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/'+ master_copy_id + "/attributes/" + \
                facts_type + "?" + container_type + "_id=" +inventory_id
        
        return url


    def _get_url_by_factstype_container(self,type_name=None):

        facts_type= type_name or self._facts_type
        
        if self._is_cp4d:
           
           url = self._cpd_configs["url"] + \
                '/v2/assets/' + self._asset_id + "/attributes/" + \
            facts_type + "?" + self._container_type + "_id=" + self._container_id
        
        else:

            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes/" + \
                facts_type + "?" + self._container_type + "_id=" + self._container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + self._asset_id + "/attributes/" + \
                facts_type + "?" + self._container_type + "_id=" + self._container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/'+ self._asset_id + "/attributes/" + \
                facts_type + "?" + self._container_type + "_id=" + self._container_id
        
        return url
    
    def _get_latest_run_idx(self,data,run_id=None):
        
        get_run_idx=None

        if run_id:
            get_latest_runs=[item for item in data if item["run_id"] == run_id]
            if not get_latest_runs:
                raise ClientError("No run information available for run id {}".format(run_id))
            else:
                get_run_idx=next(idx for idx, item in enumerate(data) if item["run_id"] == run_id and item["created_date"]==max(get_latest_runs, key=(lambda item: item["created_date"]))["created_date"])
                get_run_metadata= data[get_run_idx]   
        else:
            get_run_idx=max(range(len(data)), key=lambda index: data[index]['created_date'])
            get_run_metadata= data[get_run_idx]
    
        return get_run_idx,get_run_metadata


    def _get_headers(self):
        
          
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers 
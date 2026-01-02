
import logging
import os
import json
import collections
import itertools
import ibm_aigov_facts_client._wrappers.requests as requests
import time
import datetime
import warnings
from functools import wraps
import builtins
from typing import Optional
import functools
import re


from typing import BinaryIO, Dict, List, TextIO, Union,Any
from ibm_aigov_facts_client.factsheet import assets,utils
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator,CloudPakForDataAuthenticator,MCSPV2Authenticator
from ibm_aigov_facts_client.utils.enums import AssetContainerSpaceMap, AssetContainerSpaceMapExternal,ContainerType, FactsType, ModelEntryContainerType, AllowedDefinitionType,FormatType, RenderingHints
from ibm_aigov_facts_client.utils.utils import validate_enum,validate_type,STR_TYPE
from ibm_aigov_facts_client.factsheet.asset_utils_me import ModelUsecaseUtilities
from ibm_cloud_sdk_core.utils import  convert_model
from ibm_aigov_facts_client.factsheet import asset_utils_model

from ibm_aigov_facts_client.utils.config import *
from ibm_aigov_facts_client.utils.client_errors import *
from ibm_aigov_facts_client.utils.constants import *
from ibm_aigov_facts_client.utils.metrics_utils import convert_metric_value_to_float_if_possible,convert_tag_value_to_float_if_possible


_logger = logging.getLogger(__name__) 


class NotebookExperimentRunsUtilities:

    """
        Model notebook experiment runs utilities. Running `client.assets.model()` makes all methods in NotebookExperimentUtilities object available to use.
    
    """
   
    def __init__(self,assets_client:'assets.Assets',cur_exp_runs=None,run_id:str=None,run_idx:str=None,run_info=None,facts_type: str=NOTEBOOK_EXP_FACTS) -> None:


        self._facts_type=facts_type
        
        self._cur_exp_runs=cur_exp_runs
        self._run_id=run_id
        self._run_idx=run_idx
        self._run_id=run_info.get(RUN_ID)
        self._run_date=run_info.get(RUN_DATE)
        self._metrics=run_info.get(METRICS_META_NAME)
        self._params=run_info.get(PARAMS_META_NAME)
        self._tags=run_info.get(TAGS_META_NAME)

        self._assets_client=assets_client
        self._facts_client=self._assets_client._facts_client
        self._is_cp4d=self._assets_client._is_cp4d
        self._external_model=self._assets_client._external_model
        self._asset_id = self._assets_client._asset_id
        self._container_type=self._assets_client._container_type
        self._container_id=self._assets_client._container_id

        if self._is_cp4d:
            self._cpd_configs=self._assets_client._cpd_configs
            self._cp4d_version = self._facts_client.get_CP4D_version()
        else:
            self._cp4d_version=None
        self._model_assets_client= assets_client
        self._model_assets_client._cp4d_version=self._cp4d_version
        self.utils_client = utils.Utils(self._facts_client)
        self.asset_utils_model=asset_utils_model.ModelAssetUtilities(self._model_assets_client,model_id=self._asset_id,container_type=self._container_type,container_id=self._container_id,facts_type=self._facts_type)
        self._get_notebook_exp_url=self._get_url_by_factstype_container(type_name=NOTEBOOK_EXP_FACTS)
    

    def to_dict(self) -> Dict:
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, '_run_id') and self._run_id is not None:
            _dict['run_id'] = self._run_id
        if hasattr(self, '_run_date') and self._run_date is not None:
            _dict['run_date'] = self._run_date
        if hasattr(self, '_metrics') and self._metrics is not None:
            _dict['metrics'] = self._metrics
        if hasattr(self, '_params') and self._params is not None:
            _dict['params'] = self._params
        if hasattr(self, '_tags') and self._tags is not None:
            _dict['tags'] = self._tags
        
        return _dict
  
    def _to_dict(self):
        """Return a json dictionary representing this model."""
        return self.to_dict()
    # def _check_if_op_enabled(self):
    #     url = self._cpd_configs["url"] + "/v1/aigov/model_inventory/grc/config"
    #     response = requests.get(url,
    #                             headers=self._get_headers()
    #                             )
    #     return response.json().get("grc_integration")

    #To check if hotfix image
    def _get_cpd_image_val(self):
        #_,cpd_image_val = self._facts_client.get_CP4D_version()
        cpd_image_val = self._facts_client._get_CPD_image_val()
        #print(f"cpd_image_val : {cpd_image_val}")
        if "hotfix483" in cpd_image_val or (self._is_cp4d and self._cp4d_version >= "5.1.2"): #conditions cpd hotfix 483, 485, 486,487, 512 and above, sas supported
            return True
        return False

    # For Debugging
    def debug_mode_print(debug_flag):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                debug = kwargs.get(debug_flag, False)
                original_print = builtins.print
                def conditional_print(*args, **kwargs):
                    if debug:
                        original_print(*args, **kwargs)

                builtins.print = conditional_print
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    builtins.print = original_print

            # wrapper.__name__ = func.__name__
            # print(f"wrapper.__name__:{wrapper.__name__}")
            return wrapper

        return decorator

    def _check_if_op_enabled(self):
        if self._is_cp4d:
            url = self._cpd_configs["url"] + "/v1/aigov/model_inventory/grc/config"
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    "/v1/aigov/model_inventory/grc/config"
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    "/v1/aigov/model_inventory/grc/config"
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    "/v1/aigov/model_inventory/grc/config"
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json().get("grc_integration")
        except requests.RequestException as e:
            _logger.warning("Failed to reach the URL: %s", e)
            warnings.warn("Failed to reach the URL, cannot sync notebook experiment facts", UserWarning)
            return False
        except json.JSONDecodeError as e:
            _logger.warning("Failed to parse JSON response: %s", e)
            warnings.warn("Failed to parse JSON response, cannot sync notebook experiment facts", UserWarning)
            return False

    def refresh_state_before_execution(method):
        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            self._refresh_state()
            return method(self, *args, **kwargs)
        return wrapper

    def _refresh_state(self):
        self._cur_exp_runs = self._get_current_notebook_experiment_runs()
        self._update_meta()
        # print(f"run state refreshed : {self._cur_exp_runs} ")

    @refresh_state_before_execution
    def get_info(self):
        """
            Get run info. Supported for CPD version >=4.6.4


            A way to use me is:

            >>> run=exp.get_run() # returns latest if run_id is not given
            >>> run.get_info()


        """
        return self._to_dict()
    
    def _get_assets_url(self, asset_id: str = None, container_type: str = None, container_id: str = None):

        asset_id = asset_id or self._asset_id
        container_type = container_type or self._container_type
        container_id = container_id or self._container_id

        if self._is_cp4d:
            url = self._cpd_configs["url"] + \
                '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + \
                    '/v2/assets/' + asset_id + '?' + container_type + '_id=' + container_id
        return url
    
    def set_custom_date(self, date: float = None) -> None:
        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")

        if date is None:
            timestamp = time.time()
            formatted_date = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(timestamp))
        else:
            formatted_date = date

        body = [
            {
                "op": REPLACE,
                "path": "/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, "created_date"),
                "value": formatted_date
            }
        ]

        response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
        if response.status_code == 200:
            _logger.info("Set custom date successfully to value {}".format(formatted_date))
        else:
            raise ClientError("Failed to set custom date {}. ERROR {}.{}".format(formatted_date, response.status_code, response.text))

    @refresh_state_before_execution
    def set_custom_metric(self, metric_id:str, value:'int | float')-> None:
        
        """ Set model training metric against run_id 

        :param metric_id: Metric key name
        :type metric_id: str
        :param value: Metric value
        :type value: float
        :raises ClientError: Raises client error for exceptions
        :return: None


        A way to use me is:

        >>> run.set_custom_metric(metric_key=<key>,value=<value>)

        """
        
        if not isinstance(value, (int, float)):
            raise TypeError(f"Expected 'value' to be an int or float, but the provided value is of type {type(value).__name__}.")
    
        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            metric_idx=self._get_item_idx(self._metrics,metric_id)
            if metric_idx is None:
                cur_len=(0 if len(self._metrics)==0 else len(self._metrics))

                                
            if self._run_idx is not None  and metric_idx is not None:
                body = [
                    {
                        "op": REPLACE, 
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,metric_idx),
                        "value": value
                    }
                    ]
            else:
                
                body = [
                        {
                            "op": ADD, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,cur_len),
                            "value": {"key":metric_id,"value":value}
                        }
                        ]
                
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)

            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
        
           
            if response.status_code==200:
                _logger.info("Set custom metric {} successfully to value {}".format(metric_id,value))
                self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to set custom metric {}. ERROR {}.{}".format(metric_id,response.status_code,response.text))   

    # def set_custom_metrics(self, metrics_dict: Dict[str, Any])-> None:
    #
    #     """ Set model training metrics against the run_id
    #
    #     :param metrics_dict: Metric key,value pairs.
    #     :type metrics_dict: dict
    #     :raises ClientError: Raises client error for exceptions
    #     :return: None
    #
    #     A way to use me is:
    #
    #     >>> run.set_custom_metrics(metrics_dict={"training_score":0.955, "training_mse":0.911})
    #
    #     """
    #     final_body=[]
    #
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #
    #         for key, val in metrics_dict.items():
    #             metric_value= convert_metric_value_to_float_if_possible(val)
    #
    #             metric_idx=self._get_item_idx(self._metrics,key)
    #
    #             if metric_idx is None:
    #                 cur_len=(0 if len(self._metrics)==0 else len(self._metrics))
    #
    #             if self._run_idx is not None  and metric_idx is not None:
    #                 body = {
    #                             "op": REPLACE,
    #                             "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,metric_idx),
    #                             "value": metric_value
    #                         }
    #
    #             else:
    #                 body = {
    #                             "op": ADD,
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,cur_len),
    #                             "value": {"key":key,"value":metric_value}
    #                         }
    #             final_body.append(body)
    #
    #
    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers())
    #         if response.status_code==200:
    #             _logger.info("Set custom metrics {} successfully to values {}".format(list(metrics_dict.keys()),list(metrics_dict.values())))
    #             self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to set custom metrics {}. ERROR {}.{}".format(key,response.status_code,response.text))
    #

    @refresh_state_before_execution
    def set_custom_param(self, param_id:str, value:str)-> None:
        
        """ Set model training param against the run_id 

        :param param_id: Param key name
        :type param_id: str
        :param value: Param value
        :type value: str
        :raises ClientError: Raises client error for exceptions
        :return: None

        A way to use me is:

        >>> run.set_custom_param(param_id=<key>,value=<value>)

        """

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            if value is None:
                value="None"
            param_idx=self._get_item_idx(self._params,param_id)
            
            if param_idx is None:
                cur_len=(0 if len(self._params)==0 else len(self._params))
                                
            if self._run_idx is not None  and param_idx is not None:
                body = [
                    {
                        "op": REPLACE, 
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,param_idx),
                        "value": value
                    }
                    ]
            else:
                
                body = [
                        {
                            "op": ADD, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,cur_len),
                            "value": {"key":param_id,"value":value}
                        }
                        ]
            
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
            if response.status_code==200:
                _logger.info("Set custom param {} successfully to value {}".format(param_id,value))
                self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to set custom param {}. ERROR {}.{}".format(param_id,response.status_code,response.text))   

    # def set_custom_params(self, params_dict: Dict[str, Any])-> None:
    #
    #     """ Set model training params against the run_id
    #
    #     :param params_dict: Params key,value pairs.
    #     :type params_dict: dict
    #     :raises ClientError: Raises client error for exceptions
    #     :return: None
    #
    #     A way to use me is:
    #
    #     >>> run.set_custom_params(params_dict={"num_class":3,"early_stopping_rounds":10})
    #
    #
    #     """
    #
    #     final_body=[]
    #
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #
    #         for key, val in params_dict.items():
    #             param_value= convert_metric_value_to_float_if_possible(val)
    #
    #             param_idx=self._get_item_idx(self._params,key)
    #
    #             if param_idx is None:
    #                 cur_len=(0 if len(self._params)==0 else len(self._params))
    #
    #             if self._run_idx is not None  and param_idx is not None:
    #                 body = {
    #                             "op": REPLACE,
    #                             "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,param_idx),
    #                             "value": param_value
    #                         }
    #
    #             else:
    #                 body = {
    #                             "op": ADD,
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,cur_len),
    #                             "value": {"key":key,"value":param_value}
    #                         }
    #             final_body.append(body)
    #
    #
    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers())
    #         if response.status_code==200:
    #             _logger.info("Set custom params {} successfully to values {}".format(list(params_dict.keys()),list(params_dict.values())))
    #             self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to set custom params {}. ERROR {}.{}".format(key,response.status_code,response.text))

    @refresh_state_before_execution
    def set_custom_tag(self, tag_id:str, value:str)-> None:
        
        """ Set model training tag against the run_id 

        :param tag_id: Tag key name
        :type tag_id: str
        :param value: Tag value
        :type value: str
        :raises ClientError: Raises client error for exceptions
        :return: None

        A way to use me is:

        >>> run.set_custom_tag(tag_id=<key>,value=<value>)

        """

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            # if the int-value > than 15-digits convert to string 
            if value is None:
                value="None"
            if isinstance(value, (int)):
              if abs(value) >= 1e15:
                value = str(value)
    
            tag_idx=self._get_item_idx(self._tags,tag_id)
            
            if tag_idx is None:
                cur_len=(0 if len(self._tags)==0 else len(self._tags))
                                
            if self._run_idx is not None  and tag_idx is not None:
                body = [
                    {
                        "op": REPLACE, 
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,tag_idx),
                        "value": value
                    }
                    ]
            else:
                
                body = [
                        {
                            "op": ADD, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,cur_len),
                            "value": {"key":tag_id,"value":value}
                        }
                        ]
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
            if response.status_code==200:
                _logger.info("Set custom tag {} successfully to value {}".format(tag_id,value))
                self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to set custom tag {}. ERROR {}.{}".format(tag_id,response.status_code,response.text))   

    # def set_custom_tags(self, tags_dict: Dict[str, Any])-> None:
    #
    #     """ Set model training tags against the run_id
    #
    #     :param tags_dict: Tags key,value pairs.
    #     :type tags_dict: dict
    #     :raises ClientError: Raises client error for exceptions
    #     :return: None
    #
    #     A way to use me is:
    #
    #     >>> run.set_custom_tags(tags_dict={"tag1":<value>,"tag2":<value>})
    #
    #     """
    #
    #     final_body=[]
    #
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #
    #         for key, val in tags_dict.items():
    #             # if the int-value > than 15-digits convert to string
    #             if isinstance(val,(int)):
    #               if abs(val) >= 1e15:
    #                   tag_value = str(val)
    #               else:
    #                   tag_value = val
    #             else:
    #               tag_value = convert_tag_value_to_float_if_possible(val)
    #
    #             tag_idx=self._get_item_idx(self._tags,key)
    #
    #             if tag_idx is None:
    #                 cur_len=(0 if len(self._tags)==0 else len(self._tags))
    #
    #             if self._run_idx is not None  and tag_idx is not None:
    #                 body = {
    #                             "op": REPLACE,
    #                             "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,tag_idx),
    #                             "value": tag_value
    #                         }
    #
    #             else:
    #                 body = {
    #                             "op": ADD,
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,cur_len),
    #                             "value": {"key":key,"value":tag_value}
    #                         }
    #             final_body.append(body)
    #
    #
    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers())
    #         if response.status_code==200:
    #             _logger.info("Set custom tags {} successfully to values {}".format(list(tags_dict.keys()),list(tags_dict.values())))
    #             self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to set custom tags {}. ERROR {}.{}".format(key,response.status_code,response.text))
    
    
    #
    # def set_custom_run_facts(self, metrics:Dict[str, Any]=None, params:Dict[str, Any]=None, tags:Dict[str, Any]=None):
    #     final_body = []
    #     empty_dicts = []
    #
    #     if metrics is None and params is None and tags is None:
    #         raise ClientError("At least one of metrics,params,or tags must be provided")
    #
    #     if metrics == {} or params == {} or tags == {}:
    #          empty_dicts = [name for name, dic in {'metrics': metrics, 'params': params, 'tags': tags}.items() if dic == {}]
    #     if empty_dicts:
    #         error_message = "No key-value pairs passed for: {}".format(", ".join(empty_dicts))
    #         raise ClientError(error_message)
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #
    #     if metrics:
    #        self._process_data(metrics, METRICS_META_NAME, final_body)
    #     if params:
    #        self._process_data(params, PARAMS_META_NAME, final_body)
    #     if tags:
    #        self._process_data(tags, TAGS_META_NAME, final_body)
    #
    #
    #     response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers())
    #     if response.status_code==200:
    #              output_msg = []
    #              if metrics:
    #                 output_msg.append("metrics: {}".format(list(metrics.keys())))
    #              if params:
    #                 output_msg .append("parameters: {}".format(list(params.keys())))
    #              if tags:
    #                 output_msg .append("tags: {}".format(list(tags.keys())))
    #
    #              msg = ", ".join(output_msg )
    #              _logger.info("Set custom {} successfully".format(msg))
    #              self._update_meta()
    #
    #     else:
    #          raise ClientError("Failed to set custom run facts. ERROR {}.{}".format(response.status_code, response.text))
    #
    #
    @refresh_state_before_execution
    def get_custom_metric(self, metric_id: str)->List:

        """
            Get custom metric value by id against the run_id 

            :param str metric_id: Custom metric id to retrieve.
            :rtype: list

            A way you might use me is:

            >>> run.get_custom_metric_by_id(metric_id="<metric_id>")

        """

        self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
        is_exists= any(item for item in self._metrics if item["key"] == metric_id)
        is_step_available= any(STEP in item for item in self._metrics)

        if not is_exists:
            if self._run_id:
                raise ClientError("Could not find value of metric_id {} in run {}".format(metric_id,self._run_id))
            else:
                raise ClientError("Could not find value of metric_id {}".format(metric_id))
        else:
            cur_item=[i for i in self._metrics if i["key"]==metric_id]
            final_output=[]
            if cur_item and is_step_available:
                final_output=[{row['key']: row['value'],STEP:row['step']} for row in cur_item]
            elif cur_item and not is_step_available :
                final_output.append({row['key']: row['value'] for row in cur_item})
            else:
                raise ClientError("Failed to get information for metric id {}".format(metric_id))
        return final_output

    @refresh_state_before_execution
    def get_custom_metrics(self,metric_ids: List[str]=None)->List:

        """
            Get all logged custom metrics against the run_id 

            :param list metrics_ids: (Optional) Metrics ids to get. If not provided, returns all metrics available for the latest run 
            :rtype: list[dict]

            A way you might use me is:

            >>> run.get_custom_metrics() # uses last logged run
            >>> run.get_custom_metrics(metric_ids=["id1","id2"]) # uses last logged run

        """
            
        self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
        is_step_available= any(STEP in item for item in self._metrics)

        if not self._metrics:
            if self._run_id:
                raise ClientError("Could not find metrics information in run {}".format(self._run_id))
            else:
                raise ClientError("Could not find metrics information")
        else:
            final_result=[]
            if metric_ids:
                for item in metric_ids:
                    get_results= [i for i in self._metrics if i["key"]==item]
                    if get_results and is_step_available:
                        format_result=[{row['key']: row['value'],"step":row['step']} for row in get_results]
                        final_result.append(format_result)
                    elif get_results and not is_step_available:
                        format_result={row['key']: row['value'] for row in get_results}
                        final_result.append(format_result)
                    else:
                        _logger.info("Escaping metric id {}. Failed to get metric information.".format(item))
                
            else:
                if self._metrics and is_step_available:
                    final_result=[{row['key']: row['value'],"step":row['step']} for row in self._metrics]
                elif self._metrics and not is_step_available: 
                    format_result={row['key']: row['value'] for row in self._metrics}
                    final_result.append(format_result)
                else:
                    raise ClientError("Failed to get metrics information")
            
            return final_result

    @refresh_state_before_execution
    def get_custom_param(self, param_id: str)->Dict:

        """
            Get custom param value by id against the run_id 

            :param str param_id: Custom param id to retrieve.
            :rtype: list

            A way you might use me is:

            >>> run.get_custom_param(param_id="<param_id>")

        """

        self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
        is_exists= any(item for item in self._params if item["key"] == param_id)

        if not is_exists:
            if self._run_id:
                raise ClientError("Could not find value of param_id {} in run {}".format(param_id,self._run_id))
            else:
                raise ClientError("Could not find value of param_id {}".format(param_id))
        else:
            cur_item=[i for i in self._params if i["key"]==param_id]
            final_val=None
            if cur_item:
                final_val={row['key']: row['value'] for row in cur_item}
                return final_val
            else:
                raise ClientError("Failed to get information for param id {}".format(param_id))

    @refresh_state_before_execution
    def get_custom_params(self,param_ids: List[str]=None)->List:

        """
            Get all logged params against the run_id 

            :param list param_ids: (Optional) Params ids to get. If not provided, returns all params available for the latest run 
            :rtype: list[dict]

            A way you might use me is:

            >>> run.get_custom_params() # uses last logged run
            >>> run.get_custom_params(param_ids=["id1","id2"]) # uses last logged run

        """ 

        self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
        if not self._params:
            if self._run_id:
                raise ClientError("Could not find params information in run {}".format(self._run_id))
            else:
                raise ClientError("Could not find params information")
        else:
            final_result=[]
            if param_ids:
                for item in param_ids:
                    get_results= [i for i in self._params if i["key"]==item]
                    if get_results:
                        format_result={row['key']: row['value'] for row in get_results}
                        final_result.append(format_result)
                    else:
                        _logger.info("Escaping param id {}. Failed to get param information.".format(item))
                
            else:
                if self._params:
                    format_result={row['key']: row['value'] for row in self._params}
                    final_result.append(format_result)
                else:
                    raise ClientError("Failed to get params information")
            
            return final_result

    @refresh_state_before_execution
    def get_custom_tag(self, tag_id: str)->Dict:

        """
            Get custom tag value by id against the run_id 

            :param str tag_id: Custom tag id to retrieve.
            :rtype: dict

            A way you might use me is:

            >>> run.get_custom_tag(tag_id="<tag_id>")

        """

        self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
        is_exists= any(item for item in self._tags if item["key"] == tag_id)

        if not is_exists:
            if self._run_id:
                raise ClientError("Could not find value of tag_id {} in run {}".format(tag_id,self._run_id))
            else:
                raise ClientError("Could not find value of tag_id {}".format(tag_id))
        else:
            cur_item=[i for i in self._tags if i["key"]==tag_id]
            final_val=None
            if cur_item:
                final_val={row['key']: row['value'] for row in cur_item}
                return final_val
            else:
                raise ClientError("Failed to get information for tag id {}".format(tag_id))

    @refresh_state_before_execution
    def get_custom_tags(self,tag_ids: List[str]=None)->List:

        """
            Get all logged tags against the run_id 

            :param list tag_ids: (Optional) Tags ids to get. If not provided, returns all tags available for the latest run 
            :rtype: list[dict]

            A way you might use me is:

            >>> run.get_custom_tags() # uses last logged run
            >>> run.get_custom_tags(tag_ids=["id1","id2"]) # uses last logged run

        """
        
        self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
        if not self._tags:
            if self._run_id:
                raise ClientError("Could not find tags information in run {}".format(self._run_id))
            else:
                raise ClientError("Could not find tags information")
        else:
            final_result=[]
            if tag_ids:
                for item in tag_ids:
                    get_results= [i for i in self._tags if i["key"]==item]
                    if get_results:
                        format_result={row['key']: row['value'] for row in get_results}
                        final_result.append(format_result)
                    else:
                        _logger.info("Escaping tag id {}. Failed to get tag information.".format(item))
                
            else:
                if self._tags:
                    format_result={row['key']: row['value'] for row in self._tags}
                    final_result.append(format_result)
                else:
                    raise ClientError("Failed to get tags information")
            
            return final_result

    @refresh_state_before_execution
    def remove_custom_metric(self, metric_id: str)->None:

        """
            Remove metric by id against the run_id 

            :param str metric_id: Metric id to remove.

            A way you might use me is:

            >>> run.remove_custom_metric(metric_id=<metric_id>)


        """

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            metric_idx=self._get_item_idx(self._metrics,metric_id)
            
            if self._run_idx is not None and metric_idx is not None:
                    body = [
                        {
                            "op": REMOVE, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,metric_idx)
                        }
                        ]
            else:
                raise ClientError("Failed to get metric details for id {}".format(metric_id))
                        
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
            if response.status_code==200:
                if self._run_id:
                    _logger.info("Deleted metric {} successfully from run {}".format(metric_id,self._run_id))     
                else:
                    _logger.info("Deleted metric {} successfully".format(metric_id))
                self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to delete metric {}. ERROR {}.{}".format(metric_id,response.status_code,response.text))   

            

    # def remove_custom_metrics(self, metric_ids:List[str])->None:

    #     """
    #         Remove multiple metrics against the run_id 

    #         :param list metric_ids: Metric ids to remove from run.

    #         A way you might use me is:

    #         >>> run.remove_custom_metrics(metric_ids=["id1","id2"]) #uses last logged run


    #     """
        
    #     final_body=[]

    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #         for key in metric_ids:
    #             metric_idx=self._get_item_idx(self._metrics,key)
    #             if self._run_idx is not None and metric_idx is not None:
    #                 body = {
    #                             "op": REMOVE, 
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,METRICS_META_NAME,metric_idx)
    #                         }
                            
    #                 final_body.append(body)
    #             else:
    #                 _logger.info("Escaping metric {}. Failed to find metric details".format(key))
    #                 metric_ids.remove(key)

    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers()) 
    #         if response.status_code==200:
    #             if self._run_id:
    #                 _logger.info("Deleted metrics {} successfully from run {}".format(metric_ids,self._run_id))
    #             else:
    #                 _logger.info("Deleted metrics {} successfully from latest available run".format(metric_ids))
    #             self._metrics= self._refresh_cur_run(METRICS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to delete custom metrics {}. ERROR {}.{}".format(key,response.status_code,response.text)) 
    @refresh_state_before_execution
    def remove_custom_metrics(self, metric_ids: List[str]) -> None:
        """
        Remove multiple metrics.

        :param metric_ids: List of metric ids to remove from run.
        :type metric_ids: list of str

        A way you might use me is:

        >>> model.remove_custom_metrics(metric_ids=["id1", "id2"])

        """
        #handle duplicate values in metrics_id
        metric_ids_set = set(metric_ids)

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")

        try:
            self._metrics = self._refresh_cur_run(METRICS_META_NAME, self._run_id)
            existing_metrics = self._metrics.copy()
            remaining_metrics = [metric for metric in existing_metrics if metric['key'] not in metric_ids_set]

            path = "/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, METRICS_META_NAME)
            body = [{"op": "replace", "path": path, "value": remaining_metrics}]
            
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers())

            if response.status_code == 200:
                    if self._run_id:
                        deleted_metrics = [key for key in metric_ids_set if key not in remaining_metrics]
                        _logger.info("Deleted metrics {} successfully from run {}".format(deleted_metrics, self._run_id))
                    else:
                        _logger.info("Deleted metrics {} successfully from latest available run".format(metric_ids_set))
                    self._metrics = self._refresh_cur_run(METRICS_META_NAME, self._run_id)
            else:
                    raise ClientError("Failed to delete custom metrics. ERROR {}.{}".format(response.status_code, response.text))
            # else:
            #     _logger.error("The following metrics could not be found for deletion: {}".format(metric_ids_set))

        except Exception as e:
            _logger.error(f"An error occurred while attempting to remove custom metrics: {str(e)}")
            raise ClientError(f"An unexpected error occurred: {str(e)}")

    @refresh_state_before_execution
    def remove_custom_param(self, param_id: str)->None:

        """
            Remove param by id against the run_id 

            :param str param_id: Param id to remove.

            A way you might use me is:

            >>> run.remove_custom_param(param_id=<param_id>)

        """

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            param_idx=self._get_item_idx(self._params,param_id)
            
            if self._run_idx is not None and param_idx is not None:
                    body = [
                        {
                            "op": REMOVE, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,param_idx)
                        }
                        ]
            else:
                raise ClientError("Failed to get param details for id {}".format(param_id))
            
                    
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
            if response.status_code==200:
                if self._run_id:
                    _logger.info("Deleted param {} successfully from run {}".format(param_id,self._run_id))     
                else:
                    _logger.info("Deleted param {} successfully".format(param_id))
                self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to delete param {}. ERROR {}.{}".format(param_id,response.status_code,response.text))   

            

    # def remove_custom_params(self, param_ids:List[str])->None:

        # """
        #     Remove multiple params against the run_id 

        #     :param list param_ids: Param ids to remove from run.

        #     A way you might use me is:

        #     >>> run.remove_custom_params(param_ids=["id1","id2"])

        # """
        
    #     final_body=[]

    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #         for key in param_ids:
    #             param_idx=self._get_item_idx(self._params,key)
    #             if self._run_idx is not None and param_idx is not None:
    #                 body = {
    #                             "op": REMOVE, 
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,PARAMS_META_NAME,param_idx)
    #                         }
                            
    #                 final_body.append(body)
    #             else:
    #                 _logger.info("Escaping param {}. Failed to find param details".format(key))
    #                 param_ids.remove(key)

    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers()) 
    #         if response.status_code==200:
    #             if self._run_id:
    #                 _logger.info("Deleted params {} successfully from run {}".format(param_ids,self._run_id))
    #             else:
    #                 _logger.info("Deleted params {} successfully from latest available run".format(param_ids))
    #             self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to delete custom params {}. ERROR {}.{}".format(key,response.status_code,response.text))     

    #
    # def remove_custom_params(self, param_ids: List[str]) -> None:
    #     """
    #         Remove multiple params against the run_id
    #
    #         :param list param_ids: Param ids to remove from run.
    #
    #         A way you might use me is:
    #
    #         >>> run.remove_custom_params(param_ids=["id1","id2"])
    #
    #     """
    #     #handle duplicate values in metrics_id
    #     param_ids_set = set(param_ids)
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #
    #     try:
    #         self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
    #         existing_params = self._params.copy()
    #         remaining_params = [params for params in existing_params if params['key'] not in param_ids_set]
    #
    #
    #         path = "/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, PARAMS_META_NAME)
    #         body = [{"op": "replace", "path": path, "value": remaining_params}]
    #
    #
    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers())
    #
    #         if response.status_code == 200:
    #                 if self._run_id:
    #                     deleted_params = [key for key in param_ids_set if key not in remaining_params]
    #                     _logger.info("Deleted params {} successfully from run {}".format(deleted_params, self._run_id))
    #                 else:
    #                     _logger.info("Deleted params {} successfully from latest available run".format(param_ids_set))
    #                 self._params= self._refresh_cur_run(PARAMS_META_NAME,self._run_id)
    #         else:
    #                 raise ClientError("Failed to delete custom params. ERROR {}.{}".format(response.status_code, response.text))
    #
    #     except Exception as e:
    #         _logger.error(f"An error occurred while attempting to remove custom metrics: {str(e)}")
    #         raise ClientError(f"An unexpected error occurred: {str(e)}")

    @refresh_state_before_execution
    def remove_custom_tag(self, tag_id: str)->None:
        
        """
            Remove tag by id against the run_id 

            :param str tag_id: Tag id to remove.
            
            A way you might use me is:

            >>> run.remove_custom_tag(tag_id=<tag_id>)

        """
       
        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")
        else:
            tag_idx=self._get_item_idx(self._tags,tag_id)
            
            if self._run_idx is not None and tag_idx is not None:
                    body = [
                        {
                            "op": REMOVE, 
                            "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,tag_idx)
                        }
                        ]
            else:
                raise ClientError("Failed to get tag details for id {}".format(tag_id))
        
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers()) 
            if response.status_code==200:
                if self._run_id:
                    _logger.info("Deleted tag {} successfully from run {}".format(tag_id,self._run_id))     
                else:
                    _logger.info("Deleted tag {} successfully".format(tag_id))
                self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
            else:
                raise ClientError("Failed to delete param {}. ERROR {}.{}".format(tag_id,response.status_code,response.text))   

            

    # def remove_custom_tags(self, tag_ids:List[str])->None:

    #     """
    #         Remove multiple tags against the run_id 

    #         :param list tag_ids: Tag ids to remove from run.

    #         A way you might use me is:

    #         >>> run.remove_custom_tags(tag_ids=["id1","id2"])

    #     """
        
    #     final_body=[]

    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #     else:
    #         for key in tag_ids:
    #             tag_idx=self._get_item_idx(self._tags,key)
    #             if self._run_idx is not None and tag_idx is not None:
    #                 body = {
    #                             "op": REMOVE, 
    #                             "path": "/{}/{}/{}/{}".format(RUNS_META_NAME,self._run_idx,TAGS_META_NAME,tag_idx)
    #                         }
                            
    #                 final_body.append(body)
    #             else:
    #                 _logger.info("Escaping tag {}. Failed to find tag details".format(key))
    #                 tag_ids.remove(key)

    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body), headers=self._get_headers()) 
    #         if response.status_code==200:
    #             if self._run_id:
    #                 _logger.info("Deleted tags {} successfully from run {}".format(tag_ids,self._run_id))
    #             else:
    #                 _logger.info("Deleted tags {} successfully from latest available run".format(tag_ids))
    #             self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
    #         else:
    #             raise ClientError("Failed to delete custom tags {}. ERROR {}.{}".format(key,response.status_code,response.text))  
    
    # def remove_custom_tags(self,tag_ids: List[str]) -> None:
    #     """
    #         Remove multiple tags against the run_id
    #
    #         :param list tag_ids: Tag ids to remove from run.
    #
    #         A way you might use me is:
    #
    #         >>> run.remove_custom_tags(tag_ids=["id1","id2"])
    #
    #     """
    #     #handle duplicate values in metrics_id
    #     tag_ids_set = set(tag_ids)
    #
    #     if not self._cur_exp_runs:
    #         raise ClientError("No associated runs info found under notebook experiment")
    #
    #     try:
    #         self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
    #         existing_tags = self._tags.copy()
    #         remaining_tags = [tags for tags in existing_tags if tags['key'] not in tag_ids_set]
    #
    #
    #
    #         path = "/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, TAGS_META_NAME)
    #         body = [{"op": "replace", "path": path, "value": remaining_tags}]
    #
    #
    #
    #         response = requests.patch(self._get_notebook_exp_url, data=json.dumps(body), headers=self._get_headers())
    #
    #         if response.status_code == 200:
    #                 if self._run_id:
    #                     deleted_tags= [key for key in tag_ids_set if key not in remaining_tags]
    #                     _logger.info("Deleted tags {} successfully from run {}".format(deleted_tags, self._run_id))
    #                 else:
    #                     _logger.info("Deleted tags {} successfully from latest available run".format(tag_ids_set))
    #                 self._tags= self._refresh_cur_run(TAGS_META_NAME,self._run_id)
    #         else:
    #                 raise ClientError("Failed to delete custom tags. ERROR {}.{}".format(response.status_code, response.text))
    #
    #
    #     except Exception as e:
    #         _logger.error(f"An error occurred while attempting to remove custom metrics: {str(e)}")
    #         raise ClientError(f"An unexpected error occurred: {str(e)}")
    
            
    def _get_item_idx(self,data,key):
        
        cur_item_idx=None
        key_exists=False
    
        if self._run_id:  
                key_exists= any(item for item in data if item["key"] == key)
        else:
            key_exists= any(item for item in data if item["key"] == key)
        
        is_step_required= any(STEP in item for item in data)
        
        if key_exists and is_step_required:
            raise ClientError("Runs with iterative steps are not allowed to patch (set/remove)")
        elif key_exists and not is_step_required :
            cur_item_idx=next(idx for idx, item in enumerate(data) if item["key"] == key)

        return  cur_item_idx

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


    
    def _get_url_by_factstype_container_mastercopy(self, type_name=None):

        master_copy_info=self.utils_client.get_master_copy_info(self._asset_id,self._container_type,self._container_id)
        master_copy_id=master_copy_info['master_copy_id']
        inventory_id=master_copy_info['inventory_id']
        container_type="catalog"
       

        facts_type = type_name or self._facts_type
       
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
                    '/v2/assets/' + master_copy_id + "/attributes/" + \
                    facts_type + "?" + container_type + "_id=" + inventory_id

        return url

    
    def _get_current_notebook_experiment_runs(self): 
        if self.asset_utils_model._is_new_usecase() and not self._external_model:
            get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
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
        
    def _refresh_cur_run(self,type,run_id:str=None):
        self._cur_exp_runs=self._get_current_notebook_experiment_runs()
        if self._cur_exp_runs:
            if run_id:
                _, run_info=self._get_latest_run_idx(self._cur_exp_runs,run_id=run_id)             
            else:
                _, run_info=self._get_latest_run_idx(self._cur_exp_runs)

            if type==METRICS_META_NAME:
                refreshed_data=run_info.get(METRICS_META_NAME)
            if type==PARAMS_META_NAME:
                refreshed_data=run_info.get(PARAMS_META_NAME)
            if type==TAGS_META_NAME:
                refreshed_data=run_info.get(TAGS_META_NAME)
            
            return refreshed_data
            
        else:
            raise ClientError("No run information is available")
        
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

    def _get_latest_run_and_item(self,data,run_id=None):
        if run_id:
            get_latest_runs=[item for item in data if item["run_id"] == run_id]
            get_run_idx=next(idx for idx, item in enumerate(data) if item["run_id"] == run_id and item["created_date"]==max(get_latest_runs, key=(lambda item: item["created_date"]))["created_date"])
            get_run= data[get_run_idx]
            get_type_info= data[get_run_idx].get(NOTEBOOK_EXP_FACTS)

        else:
            get_run_idx=max(range(len(data)), key=lambda index: data[index]['created_date'])
            get_run= data[get_run_idx]
            get_type_info= data[get_run_idx].get(NOTEBOOK_EXP_FACTS)

        return get_run, get_type_info
    
    def _get_headers(self):
          
        token = self._facts_client._authenticator.token_manager.get_token() if (isinstance(self._facts_client._authenticator, IAMAuthenticator) or (
                isinstance(self._facts_client.authenticator, CloudPakForDataAuthenticator)) or (
                isinstance(self._facts_client.authenticator, MCSPV2Authenticator))) else self._facts_client.authenticator.bearer_token
        iam_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token
        }
        return iam_headers 
    

    def _process_data(self, data_dict, data_type, final_body):
        data_list = getattr(self, '_' + data_type)
        for key, val in data_dict.items():
            if data_type == TAGS_META_NAME:
              if isinstance(val,int) and abs(val) >= 1e15:
                value = str(val)
              else:
                value =val if isinstance(val, (int)) else convert_tag_value_to_float_if_possible(val)
            else:
              value = convert_metric_value_to_float_if_possible(val)

            idx = self._get_item_idx(data_list, key)
            if idx is None:
                cur_len=(0 if len(data_list)==0 else len(data_list))
       
            if self._run_idx is not None and idx is not None:
                body = {
                    "op": REPLACE,
                    "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME, self._run_idx, data_type, idx),
                    "value": value
                }
            else:
                body = {
                    "op": ADD,
                    "path": "/{}/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, data_type, cur_len),
                    "value": {"key": key, "value": value}
                }
            final_body.append(body)
    
    def _update_meta(self):
        self._metrics = self._refresh_cur_run(METRICS_META_NAME, self._run_id)
        self._params = self._refresh_cur_run(PARAMS_META_NAME, self._run_id)
        self._tags = self._refresh_cur_run(TAGS_META_NAME, self._run_id)
    
    def _get_current_timestamp(self):
        return datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def _process_data_for_sync(self, data_dict, data_type, final_body, sync_dict_new_facts):
        data_list = getattr(self, '_' + data_type)
        for key, val in data_dict.items():
            if data_type == TAGS_META_NAME:
                if isinstance(val, int) and abs(val) >= 1e15:
                    value = str(val)
                else:
                    value = val if isinstance(
                        val, (int)) else convert_tag_value_to_float_if_possible(val)
            else:
                value = convert_metric_value_to_float_if_possible(val)

            idx = self._get_item_idx(data_list, key)
            if idx is None:
                cur_len = (0 if len(data_list) == 0 else len(data_list))

            if self._run_idx is not None and idx is not None:
                body = {
                    "op": REPLACE,
                    "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME, self._run_idx, data_type, idx),
                    "value": value
                }
            else:
                body = {
                    "op": ADD,
                    "path": "/{}/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, data_type, cur_len),
                    "value": {"key": key, "value": value}
                }

            if data_type == METRICS_META_NAME:
                sync_dict_new_facts["metrics"] = [{"key": key, "value": value}
                                        for key, value in data_dict.items()]
            elif data_type == PARAMS_META_NAME:
                sync_dict_new_facts["params"] = [{"key": key, "value": value}
                                       for key, value in data_dict.items()]
            elif data_type == TAGS_META_NAME:
                sync_dict_new_facts["tags"] = [{"key": key, "value": value}
                                     for key, value in data_dict.items()]
            final_body.append(body)

    def _prepare_data(self, data_dict, data_type):
        section_data = []
        for key, val in data_dict.items():
            if data_type == TAGS_META_NAME:
                if isinstance(val, int) and abs(val) >= 1e15:
                    value = str(val)
                else:
                    value = val if isinstance(
                        val, (int)) else convert_tag_value_to_float_if_possible(val)
            else:
                value = convert_metric_value_to_float_if_possible(val)
            section_data.append({"key": key, "value": value})
        return section_data

    def _create_payload_to_overwrite(self, run, index, metrics=None, params=None, tags=None):
        def prepare_and_append(data, meta_name):
            if data is not None:
                prepared_data = self._prepare_data(data, meta_name)
                payload[meta_name] = prepared_data
                final_body.append({
                    "op": REPLACE,
                    "path": f"/{RUNS_META_NAME}/{index}/{meta_name}",
                    "value": prepared_data
                })
                sync_data_prep[meta_name] = prepared_data

        payload = {
            "run_id": run["run_id"],
            "created_date": self._get_current_timestamp()
        }

        final_body = []
        sync_data_prep = {
            #"run_id": run["run_id"],
            "timestamp": self._get_current_timestamp()
        }

        # Prepare and append data for metrics, params, and tags
        prepare_and_append(metrics, METRICS_META_NAME)
        prepare_and_append(params, PARAMS_META_NAME)
        prepare_and_append(tags, TAGS_META_NAME)

        return final_body, sync_data_prep

    def _find_run_index(self, runs, target_run_id):
        try:
            latest_time = None    
            for run in runs:   
                if run["run_id"] == target_run_id:
                    run_time = datetime.datetime.now().strptime(run['created_date'], '%d/%m/%Y %H:%M:%S')
                    if not latest_time or run_time > latest_time:
                            latest_time = run_time
            latest_time=latest_time.strftime("%d/%m/%Y %H:%M:%S")
            for index, run in enumerate(runs):   
                    if run["run_id"] == target_run_id and run["created_date"]==latest_time:
                        return index
        except Exception as ex:     
            raise ValueError(f"Error occurred while finding run index :{ex}")
    def _get_sync_notebook_experiment_facts_url(self, model_id):

        append_url = '/v1/aigov/factsheet/models/' + \
            model_id + '/sync_notebook_experiment_facts'

        if self._is_cp4d:
            url = self._cpd_configs["url"] + append_url
        else:
            if get_env() == 'dev':
                url = dev_config["DEFAULT_DEV_SERVICE_URL"] + append_url
            elif get_env() == 'test':
                url = test_config["DEFAULT_TEST_SERVICE_URL"] + append_url
            else:
                url = prod_config["DEFAULT_SERVICE_URL"] + append_url

        return url

    def _sync_notebook_experiment_facts(self, data, asset_id, container_id, container_type, timeout_in_secs=200, debug=False):
        url = self._get_sync_notebook_experiment_facts_url(model_id=asset_id)
        params={}

        if container_id is not None:
            if container_type is not None and container_type == "project":
                params['project_id'] = container_id
            if container_type is not None and container_type == "catalog":
                params['catalog_id'] = container_id
            if container_type is not None and container_type == "space":
                params['space_id'] = container_id
        try:
            json_data = json.dumps(data)

            if debug:
                print("url:", url)
                print("headers:", self._get_headers())
                print("params:", params)
                print("data:", json.dumps(data, indent=2))
                print("timeout:", timeout_in_secs)

            response = requests.patch(
                url, data=json_data, params=params, headers=self._get_headers(), timeout=timeout_in_secs)

            if debug:
                print("status code:", response.status_code)
                print("response:", response.text)

            # response.raise_for_status()
            return response.status_code, response.text
        except Exception as e:
            print(f"Error encountered: {e}")
            return None, None

    def _merge_runs(self,existing_runs, sync_dict_new_facts, run_id):

        index=self._find_run_index(existing_runs,run_id)
        run=existing_runs[index]
        if run['run_id'] == run_id:
                # Merge metrics
                existing_metrics_keys = [metric['key'] for metric in sync_dict_new_facts['metrics']]
                for metric in run['metrics']:
                    if metric['key'] not in existing_metrics_keys:
                        sync_dict_new_facts['metrics'].append(metric)
                        
                # Merge params
                existing_params_keys = [param['key'] for param in sync_dict_new_facts['params']]
                for param in run['params']:
                    if param['key'] not in existing_params_keys:
                        sync_dict_new_facts['params'].append(param)
                       

                # Merge tags
                existing_tags_keys = [tag['key'] for tag in sync_dict_new_facts['tags']]
                for tag in run['tags']:
                    if tag['key'] not in existing_tags_keys:
                        sync_dict_new_facts['tags'].append(tag)
            
        return sync_dict_new_facts

    
    def _merge_runs_for_overwrite(self, existing_runs, sync_dict_new_facts, run_id):
        # Loads existing records if any  of the ksys is missing
            index=self._find_run_index(existing_runs,run_id)
            run=existing_runs[index]
            if run['run_id'] == run_id:
                if 'metrics' not in sync_dict_new_facts:
                    sync_dict_new_facts['metrics'] = run.get('metrics', [])

                if 'params' not in sync_dict_new_facts:
                    sync_dict_new_facts['params'] = run.get('params', [])

                if 'tags' not in sync_dict_new_facts:
                    sync_dict_new_facts['tags'] = run.get('tags', [])

            return sync_dict_new_facts


    @debug_mode_print('debug')
    @refresh_state_before_execution
    def set_custom_run_facts(self, metrics: Dict[str, Any] = None, params: Dict[str, Any] = None,
                             tags: Dict[str, Any] = None,
                             overwrite: bool = False,
                             debug: bool = False):
        """
                Set custom run facts for an experiment.

                :param metrics: A dictionary containing metrics.
                :type metrics: dict, optional
                :param params: A dictionary containing parameters.
                :type params: dict, optional
                :param tags: A dictionary containing tags.
                :type tags: dict, optional
                :param overwrite: Whether to overwrite existing facts for a selected run. Default is False.
                :type overwrite: bool, optional
                :param debug: Whether to display additional details for debugging purposes. Default is False.
                :type debug: bool, optional


                A way to use me is:

                >>> metrics = {"training_score": 0.955, "training_mse": 0.911}
                    params = {"batch_size": 32, "learning_rate": 0.001}
                    tags = {"experiment_type": "CNN", "dataset": "MNIST"}
                >>> run.set_custom_run_facts(metrics_dict=metrics, params_dict=params, tags_dict=tags, overwrite=False, debug=True)
        """

        final_body = []
        empty_dicts = {}
        cams_response = False
        sync_dict = {}

        # print(f"self.asset_id : {self._asset_id}, run_id : {self._run_id}")
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type


        if overwrite == True:
            # get the current payload and replace with the new payload
            runs = self._get_current_notebook_experiment_runs()
            # find index of the run id
            index = self._find_run_index(runs, run_id)

            #print(f"=============runs[index] : {runs[index]}")

            final_body,sync_dict_new_facts = self._create_payload_to_overwrite(
                runs[index], index, metrics, params, tags)

            #print(f"final_body : {final_body}")
            print(f"sync_dict_new_facts : {sync_dict_new_facts}")

            #update old metrics , params and tags
            existing_runs = self._get_current_notebook_experiment_runs()
            #print(f'existing_runs : {existing_runs}')
            sync_dict = self._merge_runs_for_overwrite(existing_runs, sync_dict_new_facts, run_id)
            #print(f"sync_dict_new_facts : {sync_dict_new_facts}")
            print(f"sync_dict : {sync_dict}")

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body),
                                      headers=self._get_headers())
            if response.status_code == 200:
                cams_response = True

                _logger.info(
                    f"Overwritten the custom fact details for run : {run_id} ")
            else:
                raise ClientError("Failed to overwrite custom run facts. ERROR {}.{}".format(
                    response.status_code, response.text))

        else:
            # overwrite = False condition #just patch the change
            if metrics is None and params is None and tags is None:
                raise ClientError(
                    "At least one of metrics,params,or tags must be provided")

            if not self._cur_exp_runs:
                raise ClientError(
                    "No associated runs info found under notebook experiment")

            sync_dict_new_facts = {
                "timestamp": self._get_current_timestamp(),
                "metrics": [],
                "params": [],
                "tags": []
            }

            if metrics:
                self._process_data_for_sync(
                    metrics, METRICS_META_NAME, final_body, sync_dict_new_facts)
            if params:
                self._process_data_for_sync(
                    params, PARAMS_META_NAME, final_body, sync_dict_new_facts)
            if tags:
                self._process_data_for_sync(
                    tags, TAGS_META_NAME, final_body, sync_dict_new_facts)

            print(f"final_body : {final_body}")
            print(f"sync_dict_new_facts : {sync_dict_new_facts}")

            #update old metrics , params and tags
           # print(f"self._get_current_notebook_experiment_runs : {self._get_current_notebook_experiment_runs()}")
            existing_runs = self._get_current_notebook_experiment_runs()
            #print(f'existing_runs : {existing_runs}')
            sync_dict = self._merge_runs(existing_runs, sync_dict_new_facts, run_id)
            #print(f"sync_dict : {sync_dict}")

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body),
                                      headers=self._get_headers())

            if response.status_code == 200:
                cams_response = True

                _logger.info(
                    f"Updated the custom fact details for run : {run_id} ")
                output_msg = []
                if metrics:
                    output_msg.append(
                        "metrics: {}".format(list(metrics.keys())))
                if params:
                    output_msg.append(
                        "parameters: {}".format(list(params.keys())))
                if tags:
                    output_msg.append("tags: {}".format(list(tags.keys())))

                msg = ", ".join(output_msg)
                _logger.info("Set custom facts successfully")
                self._update_meta()
            else:
                raise ClientError("Failed to set custom run facts. ERROR {}.{}".format(
                    response.status_code, response.text))
        #checking if hotfix image
        #if cams_response and (not self._is_cp4d or self._get_cpd_image_val()):
        if cams_response and (self._is_cp4d and self._get_cpd_image_val()):
            # op sync code
            # check1 : check for op enablement
            if not self._check_if_op_enabled():
                _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                return

            _logger.info(
                f"OP is enabled, continuing with the syncing process")

            # check2: check for tracking status
            flag = False

            try:
                try:
                    _logger.info(
                        f"Checking for the model asset tracking status....")
                    loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                       container_id=self._container_id,
                                                                       container_type=self._container_type)
                    linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                except ClientError as ce:
                    if ce.error_msg.endswith("lmid is missing") or (
                            not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                            warnings.warn(
                                "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                        return

                if "model_usecase_id" in linked_ai_usecase_info:
                    flag = True
                    linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                    if linked_ai_usecase:
                        _logger.info(
                            f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                        try:
                            if sync_dict:
                                print("op sync payload:",sync_dict)
                                sync_response_status_code, sync_response_response_text = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                     asset_id=asset_id,
                                                                                     container_id=container_id,
                                                                                     container_type=container_type)
                                if sync_response_status_code == 200:
                                    _logger.info(
                                        "OP Sync for notebook experiment facts was successful")
                                else:
                                    raise ClientError(
                                        f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                        except Exception as e:
                            raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                else:
                    _logger.info(
                        f"Failed to get the tracked model usecase id")
            except Exception as e:
                raise ClientError(
                    f"Exception encountered while syncing notebook experiment facts : {e}")

    @debug_mode_print('debug')
    @refresh_state_before_execution
    def set_custom_metrics(self, metrics_dict: Dict[str, Any], debug: bool = False) -> None:
        """
        Set model training metrics against the run_id.

        :param metrics_dict: Metric key, value pairs.
        :type metrics_dict: dict
        :param debug: Whether to display additional details for debugging purposes. Default is False.
        :type debug: bool, optional
        :raises ClientError: Raises client error for exceptions.
        :return: None

        A way to use me is:

        >>> run.set_custom_metrics(metrics_dict={"training_score": 0.955, "training_mse": 0.911})
        """

        final_body = []
        # print(f"self.asset_id : {self._asset_id}, run_id : {self._run_id}")
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type
        sync_dict = {}
        
        if not self._cur_exp_runs:
            raise ClientError(
                "No associated runs info found under notebook experiment")
        else:

        
            for key, val in metrics_dict.items():
                #  set_custom_metric same check is made - unification
                if not isinstance(val, (int, float)):
                        raise TypeError(f"Expected 'value' to be an int or float, but the provided value is of type {type(val).__name__}.")
                    
                metric_value = convert_metric_value_to_float_if_possible(
                    val)

                metric_idx = self._get_item_idx(self._metrics, key)

                if metric_idx is None:
                    cur_len = (0 if len(self._metrics) ==
                                    0 else len(self._metrics))

                if self._run_idx is not None and metric_idx is not None:
                    body = {
                        "op": REPLACE,
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME, self._run_idx, METRICS_META_NAME,
                                                            metric_idx),
                        "value": metric_value
                    }

                else:
                    body = {
                        "op": ADD,
                        "path": "/{}/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, METRICS_META_NAME, cur_len),
                        "value": {"key": key, "value": metric_value}
                    }
                final_body.append(body)

            sync_dict_new_facts = {
                "timestamp": self._get_current_timestamp(),
                "metrics": [{"key": key, "value": value} for key, value in metrics_dict.items()],
                "params": [],
                "tags": []
            }

            print(f"final_body : {final_body}")
            print(f"sync_dict_new_facts : {sync_dict_new_facts}")

            # update old metrics , params and tags
            print(f"self._get_current_notebook_experiment_runs : {self._get_current_notebook_experiment_runs()}")
            existing_runs = self._get_current_notebook_experiment_runs()
            print(f'existing_runs : {existing_runs}')
            sync_dict = self._merge_runs(existing_runs, sync_dict_new_facts, run_id)
            print(f"sync_dict : {sync_dict}")

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(
                final_body), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info("Set custom metrics successfully.")
                self._metrics = self._refresh_cur_run(
                    METRICS_META_NAME, self._run_id)

                #if not self._is_cp4d or self._get_cpd_image_val():
                if self._is_cp4d and self._get_cpd_image_val():
                    # op sync code
                        # check1 : check for op enablement
                    if not self._check_if_op_enabled():
                        _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                        warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                        return

                    _logger.info(
                        f"OP is enabled, continuing with the syncing process")

                    # check2: check for tracking status
                    flag = False

                    try:
                        try:
                            _logger.info(
                                f"Checking for the model asset tracking status....")
                            loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                               container_id=self._container_id,
                                                                               container_type=self._container_type)
                            linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                        except ClientError as ce:
                            if ce.error_msg.endswith("lmid is missing") or (
                                    not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                    warnings.warn(
                                        "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                return

                        if "model_usecase_id" in linked_ai_usecase_info:
                            flag = True
                            linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                            if linked_ai_usecase:
                                _logger.info(
                                    f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                try:
                                    if sync_dict:
                                        sync_response_status_code, sync_response_response_text = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                             asset_id=asset_id,
                                                                                             container_id=container_id,
                                                                                             container_type=container_type)
                                        if sync_response_status_code == 200:
                                            _logger.info(
                                                "OP Sync for notebook experiment facts was successful")
                                        else:
                                            raise ClientError(
                                                f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                except Exception as e:
                                    raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                        else:
                            _logger.info(
                                f"Failed to get the tracked model usecase id")
                    except Exception as e:
                        raise ClientError(
                            f"Exception encountered while syncing notebook experiment facts : {e}")


            else:
                raise ClientError("Failed to set custom metrics {}. ERROR {}.{}".format(
                    key, response.status_code, response.text))
    @debug_mode_print('debug')
    @refresh_state_before_execution
    def set_custom_tags(self, tags_dict: Dict[str, Any],debug:bool = False) -> None:
        """
        Set model training tags against the run_id.

        :param tags_dict: Tags key, value pairs.
        :type tags_dict: dict
        :param debug: Whether to display additional details for debugging purposes. Default is False.
        :type debug: bool, optional
        :raises ClientError: Raises client error for exceptions.
        :return: None

        A way to use me is:

        >>> run.set_custom_tags(tags_dict={"tag1": <value>, "tag2": <value>})
        """

        final_body = []
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type
        sync_dict = {}

        if not self._cur_exp_runs:
            raise ClientError(
                "No associated runs info found under notebook experiment")
        else:
   
            for key, val in tags_dict.items():
                if  val is None:
                        val="None"
                # if the int-value > than 15-digits convert to string
                if isinstance(val, (int)):
                    if abs(val) >= 1e15:
                        tag_value = str(val)
                    else:
                        tag_value = val
                else:
                    tag_value = convert_tag_value_to_float_if_possible(val)

                tag_idx = self._get_item_idx(self._tags, key)

                if tag_idx is None:
                    cur_len = (0 if len(self._tags) ==
                                    0 else len(self._tags))

                if self._run_idx is not None and tag_idx is not None:
                    body = {
                        "op": REPLACE,
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME, self._run_idx, TAGS_META_NAME, tag_idx),
                        "value": tag_value
                    }

                else:
                    body = {
                        "op": ADD,
                        "path": "/{}/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, TAGS_META_NAME, cur_len),
                        "value": {"key": key, "value": tag_value}
                    }
                final_body.append(body)

            sync_dict_new_facts = {
                "timestamp": self._get_current_timestamp(),
                "metrics": [],
                "params": [],
                "tags": [{"key": key, "value": value} for key, value in tags_dict.items()],
            }

            print(f"final_body : {final_body}")
            print(f"sync_dict_new_facts : {sync_dict_new_facts}")

            # update old metrics , params and tags
            print(f"self._get_current_notebook_experiment_runs : {self._get_current_notebook_experiment_runs()}")
            existing_runs = self._get_current_notebook_experiment_runs()
            print(f'existing_runs : {existing_runs}')
            sync_dict = self._merge_runs(existing_runs, sync_dict_new_facts, run_id)
            print(f"sync_dict : {sync_dict}")
            
            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(
                final_body), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info("Set custom tags successfully to values")
                _logger.info("Successfully synced with CAMS")
                self._tags = self._refresh_cur_run(
                    TAGS_META_NAME, self._run_id)

                #if not self._is_cp4d or self._get_cpd_image_val():
                if self._is_cp4d and self._get_cpd_image_val():
                    # op sync code
                        # check1 : check for op enablement
                    if not self._check_if_op_enabled():
                        _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                        warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                        return

                    _logger.info(
                        f"OP is enabled, continuing with the syncing process")

                    # check2: check for tracking status
                    flag = False

                    try:
                        try:
                            _logger.info(
                                f"Checking for the model asset tracking status....")
                            loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                               container_id=self._container_id,
                                                                               container_type=self._container_type)
                            linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                        except ClientError as ce:
                            if ce.error_msg.endswith("lmid is missing") or (
                                    not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                # Suppress traceback for this specific warning
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                    warnings.warn(
                                        "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                return

                        if "model_usecase_id" in linked_ai_usecase_info:
                            flag = True
                            linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                            if linked_ai_usecase:
                                _logger.info(
                                    f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                try:
                                    if sync_dict:
                                        sync_response_status_code, sync_response_response_text = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                             asset_id=asset_id,
                                                                                             container_id=container_id,
                                                                                             container_type=container_type)
                                        if sync_response_status_code == 200:
                                            _logger.info(
                                                "OP Sync for notebook experiment facts was successful")
                                        else:
                                            raise ClientError(
                                                f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                except Exception as e:
                                    raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                        else:
                            _logger.info(
                                f"Failed to get the tracked model usecase id")
                    except Exception as e:
                        raise ClientError(
                            f"Exception encountered while syncing notebook experiment facts : {e}")

            else:
                raise ClientError("Failed to set custom tags {}. ERROR {}.{}".format(
                    key, response.status_code, response.text))

    @debug_mode_print('debug')
    @refresh_state_before_execution
    def set_custom_params(self, params_dict: Dict[str, Any], debug: bool = False) -> None:
        """
        Set model training params against the run_id.

        :param params_dict: Params key, value pairs.
        :type params_dict: dict
        :param debug: Whether to display additional details for debugging purposes. Default is False.
        :type debug: bool, optional
        :raises ClientError: Raises client error for exceptions.
        :return: None

        A way to use me is:

        >>> run.set_custom_params(params_dict={"num_class": 3, "early_stopping_rounds": 10})
        """

        final_body = []
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type
        sync_dict = {}

        if not self._cur_exp_runs:
            raise ClientError(
                "No associated runs info found under notebook experiment")
        else:

            for key, val in params_dict.items():
                if  val is None:
                         val="None"
                param_value = convert_metric_value_to_float_if_possible(val)

                param_idx = self._get_item_idx(self._params, key)

                if param_idx is None:
                    cur_len = (0 if len(self._params) ==
                                    0 else len(self._params))

                if self._run_idx is not None and param_idx is not None:
                    body = {
                        "op": REPLACE,
                        "path": "/{}/{}/{}/{}/value".format(RUNS_META_NAME, self._run_idx, PARAMS_META_NAME, param_idx),
                        "value": param_value
                    }

                else:
                    body = {
                        "op": ADD,
                        "path": "/{}/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, PARAMS_META_NAME, cur_len),
                        "value": {"key": key, "value": param_value}
                    }
                final_body.append(body)

            sync_dict_new_facts = {
                "timestamp": self._get_current_timestamp(),
                "metrics": [],
                "params": [{"key": key, "value": value} for key, value in params_dict.items()],
                "tags": [],
            }
            print(f"final_body : {final_body}")
            print(f"sync_dict_new_facts : {sync_dict_new_facts}")

            # update old metrics , params and tags
            print(f"self._get_current_notebook_experiment_runs : {self._get_current_notebook_experiment_runs()}")
            existing_runs = self._get_current_notebook_experiment_runs()
            print(f'existing_runs : {existing_runs}')
            sync_dict = self._merge_runs(existing_runs, sync_dict_new_facts, run_id)
            print(f"sync_dict : {sync_dict}")

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(
                final_body), headers=self._get_headers())
            if response.status_code == 200:
                _logger.info("Set custom params successfully")
                self._params = self._refresh_cur_run(
                    PARAMS_META_NAME, self._run_id)

                #if not self._is_cp4d or self._get_cpd_image_val():
                if self._is_cp4d and self._get_cpd_image_val():
                    # op sync code
                        # check1 : check for op enablement
                    if not self._check_if_op_enabled():
                        _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                        warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                        return

                    _logger.info(
                        f"OP is enabled, continuing with the syncing process")

                    # check2: check for tracking status
                    flag = False

                    try:
                        try:
                            _logger.info(
                                f"Checking for the model asset tracking status....")
                            loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                               container_id=self._container_id,
                                                                               container_type=self._container_type)
                            linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                        except ClientError as ce:
                                if ce.error_msg.endswith("lmid is missing") or (
                                        not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore")
                                        _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                        warnings.warn(
                                            "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                    return

                        if "model_usecase_id" in linked_ai_usecase_info:
                            flag = True
                            linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                            if linked_ai_usecase:
                                _logger.info(
                                    f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                try:
                                    if sync_dict:
                                        sync_response_status_code, sync_response_response_text = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                             asset_id=asset_id,
                                                                                             container_id=container_id,
                                                                                             container_type=container_type)
                                        if sync_response_status_code == 200:

                                            _logger.info(
                                                "OP Sync for notebook experiment facts was successful")
                                        else:
                                            raise ClientError(
                                                f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                except Exception as e:
                                    raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                        else:
                            _logger.info(
                                f"Failed to get the tracked model usecase id")
                    except Exception as e:
                        raise ClientError(
                            f"Exception encountered while syncing notebook experiment facts : {e}")

            else:
                raise ClientError("Failed to set custom params {}. ERROR {}.{}".format(
                            key, response.status_code, response.text))

    @debug_mode_print('debug')
    @refresh_state_before_execution
    def remove_custom_tags(self, tag_ids: List[str],debug:bool=False) -> None:
        """
        Remove multiple tags against the run_id.

        :param tag_ids: List of tag ids to remove from run.
        :type tag_ids: list of str
        :param debug: Whether to display additional details for debugging purposes. Default is False.
        :type debug: bool, optional

        A way you might use me is:

        >>> run.remove_custom_tags(tag_ids=["id1", "id2"])

        """
        # handle duplicate values in metrics_id
        tag_ids_set = set(tag_ids)
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type
        sync_dict = {}

        if not self._cur_exp_runs:
            raise ClientError(
                "No associated runs info found under notebook experiment")

        try:
            self._tags = self._refresh_cur_run(TAGS_META_NAME, self._run_id)
            existing_tags = self._tags.copy()
            remaining_tags = [
                tags for tags in existing_tags if tags['key'] not in tag_ids_set]

            path = "/{}/{}/{}".format(RUNS_META_NAME,
                                      self._run_idx, TAGS_META_NAME)
            body = [{"op": "replace", "path": path, "value": remaining_tags}]
            
            existing_runs = self._get_current_notebook_experiment_runs()
            print(f'existing_runs : {existing_runs}')
            run_index = self._find_run_index(existing_runs, run_id)

            sync_dict = {
                "timestamp": self._get_current_timestamp(),
                "metrics": existing_runs[run_index]["metrics"].copy(), 
                "params": existing_runs[run_index]["params"].copy(),
                "tags": []
                }
            for tag in remaining_tags:
                sync_dict["tags"].append(tag)

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 200:
                if self._run_id:
                    deleted_tags = [
                        key for key in tag_ids_set if key not in remaining_tags]
                    _logger.info("Deleted tags {} successfully from run {}".format(
                        deleted_tags, self._run_id))
                else:
                    _logger.info(
                        "Deleted tags {} successfully from latest available run".format(tag_ids_set))
                self._tags = self._refresh_cur_run(
                    TAGS_META_NAME, self._run_id)

                #if not self._is_cp4d or self._get_cpd_image_val():
                if self._is_cp4d and self._get_cpd_image_val():
                    # sync at OP
                    # op sync code
                        # check1 : check for op enablement
                    if not self._check_if_op_enabled():
                        _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                        warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                        return

                    _logger.info(
                        f"OP is enabled, continuing with the syncing process")

                    # check2: check for tracking status
                    flag = False

                    try:
                        try:
                            _logger.info(
                                f"Checking for the model asset tracking status....")
                            loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                               container_id=self._container_id,
                                                                               container_type=self._container_type)
                            linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                        except ClientError as ce:
                            if ce.error_msg.endswith("lmid is missing") or (
                                    not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                    warnings.warn(
                                        "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                return

                        if "model_usecase_id" in linked_ai_usecase_info:
                            flag = True
                            linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                            if linked_ai_usecase:
                                _logger.info(
                                    f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                try:
                                    if sync_dict:
                                        sync_response_status_code, sync_response_response_text  = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                             asset_id=asset_id,
                                                                                             container_id=container_id,
                                                                                             container_type=container_type)
                                        if sync_response_status_code == 200:
                                            _logger.info(
                                                "OP Sync for notebook experiment facts was successful")
                                        else:
                                            raise ClientError(
                                                f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                except Exception as e:
                                    raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                        else:
                            _logger.info(
                                f"Failed to get the tracked model usecase id")
                    except Exception as e:
                        raise ClientError(
                            f"Exception encountered while syncing notebook experiment facts : {e}")

            else:
                raise ClientError("Failed to delete custom tags. ERROR {}.{}".format(
                    response.status_code, response.text))

        except Exception as e:
            _logger.error(
                f"An error occurred while attempting to remove custom metrics: {str(e)}")
            raise ClientError(f"An unexpected error occurred: {str(e)}")

    @debug_mode_print('debug')
    @refresh_state_before_execution
    def remove_custom_params(self, param_ids: List[str],debug:bool=False) -> None:
        """
        Remove multiple params against the run_id.

        :param param_ids: List of param ids to remove from run.
        :type param_ids: list of str
        :param debug: Whether to display additional details for debugging purposes. Default is False.
        :type debug: bool, optional

        A way you might use me is:

        >>> run.remove_custom_params(param_ids=["id1", "id2"])
       
        """
        # handle duplicate values in metrics_id
        param_ids_set = set(param_ids)
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type
        sync_dict = {}

        if not self._cur_exp_runs:
            raise ClientError(
                "No associated runs info found under notebook experiment")

        try:
            self._params = self._refresh_cur_run(
                PARAMS_META_NAME, self._run_id)
            existing_params = self._params.copy()
            remaining_params = [
                params for params in existing_params if params['key'] not in param_ids_set]

            path = "/{}/{}/{}".format(RUNS_META_NAME,
                                      self._run_idx, PARAMS_META_NAME)
            body = [{"op": "replace", "path": path, "value": remaining_params}]
            
            existing_runs = self._get_current_notebook_experiment_runs()
            # print(f'existing_runs : {existing_runs}')
            run_index = self._find_run_index(existing_runs, run_id)

            sync_dict = {
                "timestamp": self._get_current_timestamp(),
                "metrics": existing_runs[run_index]["metrics"].copy(), 
                "params": [],
                "tags": existing_runs[run_index]["tags"].copy()
                }
            for param in remaining_params:
                sync_dict["params"].append(param)

            if self.asset_utils_model._is_new_usecase() and not self._external_model:
                self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
            response = requests.patch(self._get_notebook_exp_url, data=json.dumps(
                body), headers=self._get_headers())

            if response.status_code == 200:
                if self._run_id:
                    deleted_params = [
                        key for key in param_ids_set if key not in remaining_params]
                    _logger.info("Deleted params {} successfully from run {}".format(
                        deleted_params, self._run_id))
                else:
                    _logger.info(
                        "Deleted params {} successfully from latest available run".format(param_ids_set))
                self._params = self._refresh_cur_run(
                    PARAMS_META_NAME, self._run_id)

                #if not self._is_cp4d or self._get_cpd_image_val():
                if self._is_cp4d and self._get_cpd_image_val():
                    # op sync code
                        # check1 : check for op enablement
                    if not self._check_if_op_enabled():
                        _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                        warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                        return
                    _logger.info(
                        f"OP is enabled, continuing with the syncing process")

                    # check2: check for tracking status
                    flag = False

                    try:
                        try:
                            _logger.info(
                                f"Checking for the model asset tracking status....")
                            loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                               container_id=self._container_id,
                                                                               container_type=self._container_type)
                            linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                        except ClientError as ce:
                            if ce.error_msg.endswith("lmid is missing") or (
                                    not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                with warnings.catch_warnings():
                                    warnings.simplefilter("ignore")
                                    _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                    warnings.warn(
                                        "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                return

                        if "model_usecase_id" in linked_ai_usecase_info:
                            flag = True
                            linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                            if linked_ai_usecase:
                                _logger.info(
                                    f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                try:
                                    if sync_dict:
                                        sync_response_status_code, sync_response_response_text = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                             asset_id=asset_id,
                                                                                             container_id=container_id,
                                                                                             container_type=container_type)
                                        if sync_response_status_code == 200:
                                            _logger.info(
                                                "OP Sync for notebook experiment facts was successful")
                                        else:
                                            raise ClientError(
                                                f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                except Exception as e:
                                    raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                        else:
                            _logger.info(
                                f"Failed to get the tracked model usecase id")
                    except Exception as e:
                        raise ClientError(
                            f"Exception encountered while syncing notebook experiment facts : {e}")

            else:
                raise ClientError("Failed to delete custom params. ERROR {}.{}".format(
                    response.status_code, response.text))

        except Exception as e:
            _logger.error(
                f"An error occurred while attempting to remove custom metrics: {str(e)}")
            raise ClientError(f"An unexpected error occurred: {str(e)}")

    @debug_mode_print('debug')
    @refresh_state_before_execution
    def remove_custom_run_facts(self, metric_ids: List[str] = None, param_ids: List[str] = None,
                                tag_ids: List[str] = None, debug:bool=False) -> None:
        """
        Remove multiple custom run facts (metrics,params or tags) from the run.

        :param tag_ids: List of tag IDs to remove.
        :param param_ids: List of parameter IDs to remove.
        :param metric_ids: List of metric IDs to remove.
        :param debug (bool, optional): Used to display additional details for debugging purpose. Default is False.

        At least one of `tag_ids`, `param_ids`, or `metric_ids` must be provided.

        Example usage:

        >>> run.remove_custom_run_facts(metric_ids=["metric1"], param_ids=["param1"],tag_ids=["tag1", "tag2"])

        """

        if tag_ids is None and param_ids is None and metric_ids is None:
            raise ClientError("At least one of metric_ids, param_ids, or tag_ids,  must be provided.")

        lists = [metric_ids, param_ids, tag_ids]
        empty_lists = [name for name, lst in zip(['metric_ids', 'param_ids', 'tag_ids'], lists) if
                       lst is not None and not lst]

        if empty_lists:
            raise ClientError("The Following List are empty: {}".format(", ".join(empty_lists)))

        metric_ids_set = set(metric_ids) if metric_ids else set()
        param_ids_set = set(param_ids) if param_ids else set()
        tag_ids_set = set(tag_ids) if tag_ids else set()

        if not self._cur_exp_runs:
            raise ClientError("No associated runs info found under notebook experiment")

        final_body = []
        asset_id = self._asset_id
        run_id = self._run_id
        container_id = self._container_id
        container_type = self._container_type

        _logger.info("Initiating removal of custom run facts.")
        try:

            # sync_dict = {
            #     "created_date": self._get_current_timestamp(),
            #     "metrics": [],
            #     "params": [],
            #     "tags": []
            # }

            # Process metrics
            if metric_ids_set:
                metrics = self._refresh_cur_run(METRICS_META_NAME, self._run_id)
                remaining_metrics = [metric for metric in metrics if metric['key'] not in metric_ids_set]
                self._removed_final_body(remaining_metrics, METRICS_META_NAME, final_body)

            # Process params
            if param_ids_set:
                params = self._refresh_cur_run(PARAMS_META_NAME, self._run_id)
                remaining_params = [param for param in params if param['key'] not in param_ids_set]
                self._removed_final_body(remaining_params, PARAMS_META_NAME, final_body)

            # Process tags
            if tag_ids_set:
                tags = self._refresh_cur_run(TAGS_META_NAME, self._run_id)
                remaining_tags = [tag for tag in tags if tag['key'] not in tag_ids_set]
                self._removed_final_body(remaining_tags, TAGS_META_NAME, final_body)

            if final_body:
                if self.asset_utils_model._is_new_usecase() and not self._external_model:
                    self._get_notebook_exp_url=self._get_url_by_factstype_container_mastercopy(type_name=NOTEBOOK_EXP_FACTS)
                response = requests.patch(self._get_notebook_exp_url, data=json.dumps(final_body),
                                          headers=self._get_headers())
                if response.status_code == 200:
                    output_msg = []
                    if metric_ids_set:
                        output_msg.append("metrics: {}".format(list(metric_ids_set)))
                    if param_ids_set:
                        output_msg.append("parameters: {}".format(list(param_ids_set)))
                    if tag_ids_set:
                        output_msg.append("tags: {}".format(list(tag_ids_set)))

                    msg = ", ".join(output_msg)
                    _logger.info("Removed custom {} successfully".format(msg))

                    #if not self._is_cp4d or self._get_cpd_image_val():
                    if self._is_cp4d and self._get_cpd_image_val():
                        #updating sync dict

                        existing_runs = self._get_current_notebook_experiment_runs()
                        print(f'existing_runs : {existing_runs}')
                        run_index = self._find_run_index(existing_runs, run_id)
                        sync_dict = {
                            "timestamp": self._get_current_timestamp(),
                            "metrics": existing_runs[run_index]["metrics"].copy(),
                            "params": existing_runs[run_index]["params"].copy(),
                            "tags": existing_runs[run_index]["tags"].copy()
                        }
                        for entry in final_body:
                            value = entry["value"]
                            if "metrics" in entry["path"]:
                                sync_dict["metrics"] = value if isinstance(value, list) else [value]
                            elif "params" in entry["path"]:
                                sync_dict["params"] = value if isinstance(value, list) else [value]
                            elif "tags" in entry["path"]:
                                sync_dict["tags"] = value if isinstance(value, list) else [value]

                        # for entry in final_body:
                        #     value = entry["value"]
                        #     if "metrics" in entry["path"]:
                        #         sync_dict["metrics"].extend(value if isinstance(value, list) else [value])
                        #     elif "params" in entry["path"]:
                        #         sync_dict["params"].extend(value if isinstance(value, list) else [value])
                        #     elif "tags" in entry["path"]:
                        #         sync_dict["tags"].extend(value if isinstance(value, list) else [value])

                        print("====================================")
                        print(f"final_body:{final_body}")
                        print(f"sync_dict:{sync_dict}")

                        print("====================================")
                        #self._update_meta()
                        # op sync code
                        # check1 : check for op enablement
                        if not self._check_if_op_enabled():
                            _logger.warning("OP is not enabled, cannot sync notebook experiment facts")
                            warnings.warn("OP is not enabled, cannot sync notebook experiment facts", UserWarning)
                            return

                        _logger.info(
                            f"OP is enabled, continuing with the syncing process")

                        # check2: check for tracking status
                        flag = False

                        try:
                            try:
                                _logger.info(
                                    f"Checking for the model asset tracking status....")
                                loaded_model = self._facts_client.assets.get_model(model_id=asset_id,
                                                                                   container_id=self._container_id,
                                                                                   container_type=self._container_type)
                                linked_ai_usecase_info = loaded_model.get_tracking_model_usecase().to_dict()
                            except ClientError as ce:
                                if ce.error_msg.endswith("lmid is missing") or (
                                        not flag and ce.error_msg.endswith("is not tracked by a model use case")):
                                    with warnings.catch_warnings():
                                        warnings.simplefilter("ignore")
                                        _logger.warning("The model is not tracked, cannot sync notebook experiment facts")
                                        warnings.warn(
                                            "The model is not tracked, cannot sync notebook experiment facts", UserWarning)
                                    return

                            if "model_usecase_id" in linked_ai_usecase_info:
                                flag = True
                                linked_ai_usecase = linked_ai_usecase_info['model_usecase_id']
                                if linked_ai_usecase:
                                    _logger.info(
                                        f"Model asset {asset_id} is tracked to ai usecase : {str(linked_ai_usecase)}")
                                    try:
                                        if sync_dict:
                                            sync_response_status_code, sync_response_response_text  = self._sync_notebook_experiment_facts(data=sync_dict,
                                                                                                 asset_id=asset_id,
                                                                                                 container_id=container_id,
                                                                                                 container_type=container_type)
                                            if sync_response_status_code == 200:
                                                _logger.info(
                                                    "OP Sync for notebook experiment facts was successful")
                                            else:
                                                raise ClientError(
                                                    f"Failed to sync notebook experiment facts. ERROR {sync_response_status_code}:{sync_response_response_text}")
                                    except Exception as e:
                                        raise ClientError(f"Failed to sync notebook experiment facts with OP, Error : {e}")

                            else:
                                _logger.info(
                                    f"Failed to get the tracked model usecase id")
                        except Exception as e:
                            raise ClientError(
                                f"Exception encountered while syncing notebook experiment facts : {e}")


                else:
                    raise ClientError(
                        "Failed to remove custom run facts. ERROR {}.{}".format(response.status_code, response.text))

        except Exception as e:
            _logger.error(f"An error occurred while attempting to remove custom run facts: {str(e)}")
            raise ClientError(f"An unexpected error occurred: {str(e)}")

    def _removed_final_body(self, remaining_entries: List[str], entry_meta_name: str, final_body: List[str]) -> None:
        path = "/{}/{}/{}".format(RUNS_META_NAME, self._run_idx, entry_meta_name)
        body = {"op": "replace", "path": path, "value": remaining_entries}
        final_body.append(body)
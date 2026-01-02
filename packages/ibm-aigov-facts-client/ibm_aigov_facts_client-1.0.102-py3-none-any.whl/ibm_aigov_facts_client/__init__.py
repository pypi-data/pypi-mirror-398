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

from operator import le
from .version import __version__
from ibm_aigov_facts_client.client.fact_trace import FactsClientAdapter as AIGovFactsClient
from ibm_aigov_facts_client.factsheet.factsheet_utility import FactSheetElements
from ibm_aigov_facts_client.utils.logging_utils import configure_facts_loggers, disable_module_logger
from ibm_aigov_facts_client.supporting_classes.factsheet_utils import *
from ibm_aigov_facts_client.utils.cp4d_utils import CloudPakforDataConfig
from ibm_aigov_facts_client.utils.cell_facts import CellFactsMagic
from IPython import get_ipython

ipy = get_ipython()
if ipy is not None:
    ipy.register_magics(CellFactsMagic)

configure_facts_loggers(root_module_name=__name__)
disable_module_logger()

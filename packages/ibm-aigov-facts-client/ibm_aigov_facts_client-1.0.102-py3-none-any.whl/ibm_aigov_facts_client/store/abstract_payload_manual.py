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

from abc import abstractmethod, ABCMeta


class AbstractPayloadStore:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def gen_payload(self, run_data, root_dir=None):
        pass

    @abstractmethod
    def get_payload_and_publish(self, run_id=None, parent_path=None, metric_name=None):
        pass

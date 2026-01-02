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

import logging
import sys


class ClientError(Exception):
    def __init__(self, error_msg, reason=None):
        self.error_msg = error_msg
        self.reason = reason
        # logging.getLogger(__name__).warning(self.__str__())
        logging.getLogger(__name__).debug(
            str(self.error_msg) + ('\nReason: ' + str(self.reason) if sys.exc_info()[0] is not None else ''))

    def __str__(self):
        return str(self.error_msg) + ('\nReason: ' + str(self.reason) if self.reason is not None else '')


class MissingValue(ClientError, ValueError):
    def __init__(self, value_name, reason=None):
        ClientError.__init__(self, 'No \"' + value_name +
                             '\" provided.', reason)

class MissingMetaProp(MissingValue):
    def __init__(self, name, reason=None):
        ClientError.__init__(self, 'Missing props with name: \'{}\'.'.format(name), reason)

class WrongProps(MissingValue):
    def __init__(self, reason=None):
        ClientError.__init__(self, "Wrong props used.", reason)

class MissingParams(MissingValue):
    def __init__(self, name, reason=None):
        ClientError.__init__(self, 'Missing params with name: \'{}\'.'.format(name), reason)

class WrongParams(MissingValue):
    def __init__(self, reason=None):
        ClientError.__init__(self, "Wrong params used.", reason)

class UnexpectedType(ClientError, ValueError):
    def __init__(self, el_name, expected_type, actual_type):
        ClientError.__init__(self, 'Unexpected type of \'{}\', expected: {}, actual: \'{}\'.'.format(
            el_name,
            '\'{}\''.format(
                expected_type) if type(
                expected_type) == type else expected_type,
            actual_type))


class UnexpectedValue(ClientError, ValueError):
    def __init__(self, msg, reason=None):
        ClientError.__init__(self, msg, reason)


class AuthorizationError(ClientError, ValueError):
    def __init__(self, msg, reason=None):
        ClientError.__init__(self, msg, reason)

class ApiRequestFailure(ClientError):
    def __init__(self, error_msg, response, reason=None):
        self.response = response
        ClientError.__init__(self, '{} ({} {})\nStatus code: {}, body: {}'.format(
            error_msg, response.request.method,
            response.request.url,
            response.status_code,
            response.text if response.apparent_encoding is not None else '[binary content, ' + str(
                len(
                    response.content)) + ' bytes]'),
                             reason)


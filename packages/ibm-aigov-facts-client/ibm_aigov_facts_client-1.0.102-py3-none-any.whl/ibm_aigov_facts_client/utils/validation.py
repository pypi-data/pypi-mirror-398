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

from ibm_aigov_facts_client.utils.client_errors import ClientError
import re
import posixpath
import numbers

_VALID_PARAM_AND_METRIC_NAMES = re.compile(r"^[/\w.\- ]*$")

# Regex for valid run IDs: must be an alphanumeric string of length 1 to 256.
_RUN_ID_REGEX = re.compile(r"^[a-zA-Z0-9][\w\-]{0,255}$")

_EXPERIMENT_ID_REGEX = re.compile(r"^[a-zA-Z0-9][\w\-]{0,63}$")

_BAD_CHARACTERS_MESSAGE = (
    "Names may only contain alphanumerics, underscores (_), dashes (-), periods (.),"
    " spaces ( ), and slashes (/)."
)


MAX_ENTITY_KEY_LENGTH = 250
MAX_PARAM_VAL_LENGTH = 250
MAX_TAG_VAL_LENGTH = 5000
MAX_EXPERIMENT_TAG_KEY_LENGTH = 250
MAX_EXPERIMENT_TAG_VAL_LENGTH = 5000


def is_string_type(item):
    return isinstance(item, str)


def writeable_value(tag_value):
    if tag_value is None:
        return ""
    elif is_string_type(tag_value):
        return tag_value
    else:
        return "%s" % tag_value


def path_not_unique(name):
    norm = posixpath.normpath(name)
    return norm != name or norm == "." or norm.startswith("..") or norm.startswith("/")


def bad_path_message(name):
    return (
        "Names may be treated as files in certain cases, and must not resolve to other names"
        " when treated as such. This name would resolve to '%s'"
    ) % posixpath.normpath(name)


def validate_run_id(run_id):
    """Check that `run_id` is a valid run ID and raise an exception if it isn't."""
    if _RUN_ID_REGEX.match(run_id) is None:
        raise ClientError("Invalid run ID: '%s'" % run_id)


def _validate_experiment_id(exp_id):
    """Check that `experiment_id`is a valid string or None, raise an exception if it isn't."""
    if exp_id is not None and _EXPERIMENT_ID_REGEX.match(exp_id) is None:
        raise ClientError(
            "Invalid experiment ID: '%s'" % exp_id
        )


def _validate_metric_name(name):
    """Check that `name` is a valid metric name and raise an exception if it isn't."""
    if name is None or not _VALID_PARAM_AND_METRIC_NAMES.match(name):
        raise ClientError(
            "Invalid metric name: '%s'. %s" % (name, _BAD_CHARACTERS_MESSAGE))
    if path_not_unique(name):
        raise ClientError(
            "Invalid metric name: '%s'. %s" % (name, bad_path_message(name))
        )


def _validate_param_name(name):
    """Check that `name` is a valid param name and raise an exception if it isn't."""
    if name is None or not _VALID_PARAM_AND_METRIC_NAMES.match(name):
        raise ClientError(
            "Invalid param name: '%s'. %s" % (name, _BAD_CHARACTERS_MESSAGE))
    if path_not_unique(name):
        raise ClientError(
            "Invalid param name: '%s'. %s" % (name, bad_path_message(name))
        )


def _validate_tag_name(name):
    """Check that `name` is a valid tag name and raise an exception if it isn't."""
    if name is None or not _VALID_PARAM_AND_METRIC_NAMES.match(name):
        raise ClientError(
            "Invalid tag name: '%s'. %s" % (name, _BAD_CHARACTERS_MESSAGE))
    if path_not_unique(name):
        raise ClientError(
            "Invalid tag name: '%s'. %s" % (name, bad_path_message(name))
        )


def _is_numeric(value):
    """
    Returns True if the passed-in value is numeric.
    """
    # Note that `isinstance(bool_value, numbers.Number)` returns `True` because `bool` is a
    # subclass of `int`.
    return not isinstance(value, bool) and isinstance(value, numbers.Number)


def validate_metric(key, value, timestamp, step):
    """
    Check that a param with the specified key, value, timestamp is valid and raise an exception if
    it isn't.
    """
    _validate_metric_name(key)
    # value must be a Number
    # since bool is an instance of Number check for bool additionally
    if not _is_numeric(value):
        raise ClientError(
            "Got invalid value %s for metric '%s' (timestamp=%s). Please specify value as a valid "
            "double (64-bit floating point)" % (value, key, timestamp)
        )

    if not isinstance(timestamp, numbers.Number) or timestamp < 0:
        raise ClientError(
            "Got invalid timestamp %s for metric '%s' (value=%s). Timestamp must be a nonnegative "
            "long (64-bit integer) " % (timestamp, key, value)
        )

    if not isinstance(step, numbers.Number):
        raise ClientError(
            "Got invalid step %s for metric '%s' (value=%s). Step must be a valid long "
            "(64-bit integer)." % (step, key, value)
        )


def _validate_length_limit(entity_name, limit, value):
    if len(value) > limit:
        raise ClientError(
            "%s '%s' had length %s, which exceeded length limit of %s"
            % (entity_name, value[:250], len(value), limit)
        )


def validate_param(key, value):
    """
    Check that a param with the specified key & value is valid and raise an exception if it
    isn't.
    """
    _validate_param_name(key)
    _validate_length_limit("Param key", MAX_ENTITY_KEY_LENGTH, key)
    _validate_length_limit("Param value", MAX_PARAM_VAL_LENGTH, value)


def validate_tag(key, value):
    """
    Check that a tag with the specified key & value is valid and raise an exception if it isn't.
    """
    _validate_tag_name(key)
    _validate_length_limit("Tag key", MAX_ENTITY_KEY_LENGTH, key)
    _validate_length_limit("Tag value", MAX_TAG_VAL_LENGTH, value)


def validate_experiment_tag(key, value):
    """
    Check that a tag with the specified key & value is valid and raise an exception if it isn't.
    """
    _validate_tag_name(key)
    _validate_length_limit("Tag key", MAX_EXPERIMENT_TAG_KEY_LENGTH, key)
    _validate_length_limit("Tag value", MAX_EXPERIMENT_TAG_VAL_LENGTH, value)


def validate_new_param_value(param_path, param_key, run_id, new_value):
    """
    When logging a parameter with a key that already exists, this function is used to
    enforce immutability by verifying that the specified parameter value matches the existing
    value.
    :raises: py:class:`mlflow.exceptions.MlflowException` if the specified new parameter value
                does not match the existing parameter value.
    """
    with open(param_path, "r") as param_file:
        current_value = param_file.read()
    if current_value != new_value:
        raise ClientError(
            "Changing param values is not allowed. Param with key='{}' was already"
            " logged with value='{}' for run ID='{}'. Attempted logging new value"
            " '{}'.".format(param_key, current_value, run_id, new_value)
        )

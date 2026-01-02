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
import logging.config
import sys
import os


LOGGING_LINE_FORMAT = "%(asctime)s %(levelname)s : %(message)s"
LOGGING_LINE_FILE_FORMAT = "%(asctime)s %(levelname)s - %(name)s : %(message)s"
LOGGING_LINE_ERROR_FORMAT = "'%(asctime)s-%(levelname)s-%(name)s-%(process)d::%(module)s|%(lineno)s:: %(message)s'"
LOGGING_DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"


class FactsLoggingStream:
    """
    A Python stream for use with event logging APIs throughout Facts_Client (`eprint()`,
    `logger.info()`, etc.). This stream wraps `sys.stderr`, forwarding `write()` and
    `flush()` calls to the stream referred to by `sys.stderr` at the time of the call.
    It also provides capabilities for disabling the stream to silence event logs.
    """

    def __init__(self):
        self._enabled = True

    def write(self, text):
        if self._enabled:
            sys.stdout.write(text)

    def flush(self):
        if self._enabled:
            sys.stdout.flush()

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        self._enabled = value


FACTS_LOGGING_STREAM = FactsLoggingStream()


def disable_logging():
    """
    Disables the `FactsLoggingStream` used by event logging.
    (`eprint()`, `logger.info()`, etc), silencing all subsequent event logs.
    """
    FACTS_LOGGING_STREAM.enabled = False


def enable_logging():
    """
    Enables the `FactsLoggingStream` used by event logging. This
    reverses the effects of `disable_logging()`.
    """
    FACTS_LOGGING_STREAM.enabled = True

def disable_debug():
    logging.disable('DEBUG')

def configure_facts_loggers(root_module_name, level="INFO", propagate=False):

    log_dir = './logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    if level =="DEBUG":
        disable_debug()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "facts_formatter": {
                    "format": LOGGING_LINE_FORMAT,
                    "datefmt": LOGGING_DATETIME_FORMAT,
                },
                # "error_formatter": {
                #     "format": LOGGING_LINE_ERROR_FORMAT,
                #     "datefmt": LOGGING_DATETIME_FORMAT,
                # },
                # "file_formatter": {
                #     "format": LOGGING_LINE_FILE_FORMAT,
                #     "datefmt": LOGGING_DATETIME_FORMAT,
                # }

            },
            "handlers": {

                "facts_handler": {
                    "level": level,
                    "formatter": "facts_formatter",
                    "class": "logging.StreamHandler",
                    "stream": FACTS_LOGGING_STREAM,
                },

                # "facts_err_handler": {
                #     "level": "WARNING",
                #     "formatter": "file_formatter",
                #     "class": "logging.StreamHandler",
                #     "stream": FACTS_LOGGING_ERR_STREAM,
                # },

                # "info_rotating_file_handler": {
                #     "level": level,
                #     "formatter": "file_formatter",
                #     "class": "logging.handlers.RotatingFileHandler",
                #     "filename": "./logs/info.log",
                #     "mode": "a",
                #     "maxBytes": 1048576,
                #     "backupCount": 10
                # },

                # "error_file_handler": {
                #     "level": "WARNING",
                #     "formatter": "error_formatter",
                #     "class": "logging.FileHandler",
                #     "filename": "./logs/error.log",
                #     "mode": "a",
                # }

            },
            "loggers": {
                root_module_name: {
                    "handlers": ["facts_handler"],
                    "level": level,
                    "propagate": propagate,
                },

            }
        }
    )


# def get_logger(name, specific_log_level=None):
#     logger = logging.getLogger(name)
#     logging.basicConfig(level="INFO", format=LOGGING_LINE_FORMAT,
#                         datefmt=LOGGING_DATETIME_FORMAT)
#     logger.setLevel("INFO")
#     return logger


def clear_up_handler():
    logger = logging.getLogger()
    # if there is already a handler, remove it.
    if logger.handlers:
        logger.handlers.pop()


# def eprint(*args, **kwargs):
#     print(*args, file=FACTS_LOGGING_STREAM, **kwargs)


def disable_module_logger():
    logging.getLogger('mlflow').setLevel(logging.CRITICAL)

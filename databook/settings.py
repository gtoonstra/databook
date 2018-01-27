# -*- coding: utf-8 -*-
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import atexit
import logging
import os
import sys
from logging.config import dictConfig

from databook import configuration as conf
from databook.exceptions import DatabookConfigException


log = logging.getLogger(__name__)


class DummyStatsLogger(object):
    @classmethod
    def incr(cls, stat, count=1, rate=1):
        pass

    @classmethod
    def decr(cls, stat, count=1, rate=1):
        pass

    @classmethod
    def gauge(cls, stat, value, rate=1, delta=False):
        pass

    @classmethod
    def timing(cls, stat, dt):
        pass


Stats = DummyStatsLogger

HEADER = """\
    ____        __        __                __  
   / __ \____ _/ /_____ _/ /_  ____  ____  / /__
  / / / / __ `/ __/ __ `/ __ \/ __ \/ __ \/ //_/
 / /_/ / /_/ / /_/ /_/ / /_/ / /_/ / /_/ / ,<   
/_____/\__,_/\__/\__,_/_.___/\____/\____/_/|_|  
 """

BASE_LOG_URL = '/admin/databook/log'
LOGGING_LEVEL = logging.INFO

# the prefix to append to gunicorn worker processes after init
GUNICORN_WORKER_READY_PREFIX = "[ready] "

LOG_FORMAT = conf.get('core', 'log_format')
SIMPLE_LOG_FORMAT = conf.get('core', 'simple_log_format')

DATABOOK_HOME = None


def prepare_classpath():
    config_path = os.path.join(conf.get('core', 'databook_home'), 'config')
    config_path = os.path.expanduser(config_path)

    if config_path not in sys.path:
        sys.path.append(config_path)


def configure_logging():
    logging_class_path = ''
    try:
        # Prepare the classpath so we are sure that the config folder
        # is on the python classpath and it is reachable
        prepare_classpath()

        logging_class_path = conf.get('core', 'logging_config_class')
    except DatabookConfigException:
        log.debug('Could not find key logging_config_class in config')

    if logging_class_path:
        try:
            logging_config = import_string(logging_class_path)

            # Make sure that the variable is in scope
            assert (isinstance(logging_config, dict))

            log.info(
                'Successfully imported user-defined logging config from %s',
                logging_class_path
            )
        except Exception as err:
            # Import default logging configurations.
            raise ImportError(
                'Unable to load custom logging from {} due to {}'
                .format(logging_class_path, err)
            )
    else:
        from databook.config_templates.databook_local_settings import (
            DEFAULT_LOGGING_CONFIG as logging_config
        )
        log.debug('Unable to load custom logging, using default config instead')

    try:
        # Try to init logging
        dictConfig(logging_config)
    except ValueError as e:
        log.warning('Unable to load the config, contains a configuration error.')
        # When there is an error in the config, escalate the exception
        # otherwise Databook would silently fall back on the default config
        raise e

    return logging_config


def configure_vars():
    global DATABOOK_HOME
    DATABOOK_HOME = os.path.expanduser(conf.get('core', 'DATABOOK_HOME'))


configure_logging()
configure_vars()

# Const stuff

KILOBYTE = 1024
MEGABYTE = KILOBYTE * KILOBYTE
WEB_COLORS = {'LIGHTBLUE': '#4d9de0',
              'LIGHTORANGE': '#FF9933'}

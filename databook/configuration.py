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

import copy
import errno
import os
import six
import subprocess
import warnings
import shlex
import sys

from future import standard_library

from six import iteritems

from databook.utils.logging_mixin import LoggingMixin

standard_library.install_aliases()

from builtins import str
from collections import OrderedDict
from six.moves import configparser

from databook.exceptions import DatabookConfigException


log = LoggingMixin().log

# show Databook's deprecation warnings
warnings.filterwarnings(
    action='default', category=DeprecationWarning, module='databook')
warnings.filterwarnings(
    action='default', category=PendingDeprecationWarning, module='databook')

if six.PY3:
    ConfigParser = configparser.ConfigParser
else:
    ConfigParser = configparser.SafeConfigParser


def expand_env_var(env_var):
    """
    Expands (potentially nested) env vars by repeatedly applying
    `expandvars` and `expanduser` until interpolation stops having
    any effect.
    """
    if not env_var:
        return env_var
    while True:
        interpolated = os.path.expanduser(os.path.expandvars(str(env_var)))
        if interpolated == env_var:
            return interpolated
        else:
            env_var = interpolated


def run_command(command):
    """
    Runs command and returns stdout
    """
    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True)
    output, stderr = [stream.decode(sys.getdefaultencoding(), 'ignore')
                      for stream in process.communicate()]

    if process.returncode != 0:
        raise DatabookConfigException(
            "Cannot execute {}. Error code is: {}. Output: {}, Stderr: {}"
            .format(command, process.returncode, output, stderr)
        )

    return output

_templates_dir = os.path.join(os.path.dirname(__file__), 'config_templates')
with open(os.path.join(_templates_dir, 'default_databook.cfg')) as f:
    DEFAULT_CONFIG = f.read()


class DatabookConfigParser(ConfigParser):

    # These configuration elements can be fetched as the stdout of commands
    # following the "{section}__{name}__cmd" pattern, the idea behind this
    # is to not store password on boxes in text files.
    as_command_stdout = {
        ('core', 'sql_alchemy_conn'),
        ('core', 'fernet_key'),
        ('celery', 'broker_url'),
        ('celery', 'result_backend')
    }

    def __init__(self, *args, **kwargs):
        ConfigParser.__init__(self, *args, **kwargs)
        self.read_string(parameterized_config(DEFAULT_CONFIG))
        self.is_validated = False

    def read_string(self, string, source='<string>'):
        """
        Read configuration from a string.

        A backwards-compatible version of the ConfigParser.read_string()
        method that was introduced in Python 3.
        """
        # Python 3 added read_string() method
        if six.PY3:
            ConfigParser.read_string(self, string, source=source)
        # Python 2 requires StringIO buffer
        else:
            import StringIO
            self.readfp(StringIO.StringIO(string))

    def _validate(self):
        if (
            self.getboolean("webserver", "authenticate") and
            self.get("webserver", "owner_mode") not in ['user', 'ldapgroup']
        ):
            raise DatabookConfigException(
                "error: owner_mode option should be either "
                "'user' or 'ldapgroup' when filtering by owner is set")

        elif (
            self.getboolean("webserver", "authenticate") and
            self.get("webserver", "owner_mode").lower() == 'ldapgroup' and
            self.get("webserver", "auth_backend") != (
                'databook.contrib.auth.backends.ldap_auth')
        ):
            raise DatabookConfigException(
                "error: attempt at using ldapgroup "
                "filtering without using the Ldap backend")

        self.is_validated = True

    def _get_env_var_option(self, section, key):
        # must have format DATABOOK__{SECTION}__{KEY} (note double underscore)
        env_var = 'DATABOOK__{S}__{K}'.format(S=section.upper(), K=key.upper())
        if env_var in os.environ:
            return expand_env_var(os.environ[env_var])

    def _get_cmd_option(self, section, key):
        fallback_key = key + '_cmd'
        # if this is a valid command key...
        if (section, key) in DatabookConfigParser.as_command_stdout:
            # if the original key is present, return it no matter what
            if self.has_option(section, key):
                return ConfigParser.get(self, section, key)
            # otherwise, execute the fallback key
            elif self.has_option(section, fallback_key):
                command = self.get(section, fallback_key)
                return run_command(command)

    def get(self, section, key, **kwargs):
        section = str(section).lower()
        key = str(key).lower()

        # first check environment variables
        option = self._get_env_var_option(section, key)
        if option is not None:
            return option

        # ...then the config file
        if self.has_option(section, key):
            return expand_env_var(
                ConfigParser.get(self, section, key, **kwargs))

        # ...then commands
        option = self._get_cmd_option(section, key)
        if option:
            return option

        else:
            log.warning(
                "section/key [{section}/{key}] not found in config".format(**locals())
            )

            raise DatabookConfigException(
                "section/key [{section}/{key}] not found "
                "in config".format(**locals()))

    def getboolean(self, section, key):
        val = str(self.get(section, key)).lower().strip()
        if '#' in val:
            val = val.split('#')[0].strip()
        if val.lower() in ('t', 'true', '1'):
            return True
        elif val.lower() in ('f', 'false', '0'):
            return False
        else:
            raise DatabookConfigException(
                'The value for configuration option "{}:{}" is not a '
                'boolean (received "{}").'.format(section, key, val))

    def getint(self, section, key):
        return int(self.get(section, key))

    def getfloat(self, section, key):
        return float(self.get(section, key))

    def read(self, filenames):
        ConfigParser.read(self, filenames)
        self._validate()

    def getsection(self, section):
        """
        Returns the section as a dict. Values are converted to int, float, bool
        as required.
        :param section: section from the config
        :return: dict
        """
        if section in self._sections:
            _section = self._sections[section]
            for key, val in iteritems(self._sections[section]):
                try:
                    val = int(val)
                except ValueError:
                    try:
                        val = float(val)
                    except ValueError:
                        if val.lower() in ('t', 'true'):
                            val = True
                        elif val.lower() in ('f', 'false'):
                            val = False
                _section[key] = val
            return _section

        return None

    def as_dict(self, display_source=False, display_sensitive=False):
        """
        Returns the current configuration as an OrderedDict of OrderedDicts.
        :param display_source: If False, the option value is returned. If True,
            a tuple of (option_value, source) is returned. Source is either
            'databook.cfg' or 'default'.
        :type display_source: bool
        :param display_sensitive: If True, the values of options set by env
            vars and bash commands will be displayed. If False, those options
            are shown as '< hidden >'
        :type display_sensitive: bool
        """
        cfg = copy.deepcopy(self._sections)

        # remove __name__ (affects Python 2 only)
        for options in cfg.values():
            options.pop('__name__', None)

        # add source
        if display_source:
            for section in cfg:
                for k, v in cfg[section].items():
                    cfg[section][k] = (v, 'databook config')

        # add env vars and overwrite because they have priority
        for ev in [ev for ev in os.environ if ev.startswith('DATABOOK__')]:
            try:
                _, section, key = ev.split('__')
                opt = self._get_env_var_option(section, key)
            except ValueError:
                opt = None
            if opt:
                if (
                        not display_sensitive
                        and ev != 'DATABOOK__CORE__UNIT_TEST_MODE'):
                    opt = '< hidden >'
                if display_source:
                    opt = (opt, 'env var')
                cfg.setdefault(section.lower(), OrderedDict()).update(
                    {key.lower(): opt})

        # add bash commands
        for (section, key) in DatabookConfigParser.as_command_stdout:
            opt = self._get_cmd_option(section, key)
            if opt:
                if not display_sensitive:
                    opt = '< hidden >'
                if display_source:
                    opt = (opt, 'bash cmd')
                cfg.setdefault(section, OrderedDict()).update({key: opt})

        return cfg

    def load_test_config(self):
        """
        Load the unit test configuration.

        Note: this is not reversible.
        """
        # override any custom settings with defaults
        self.read_string(parameterized_config(DEFAULT_CONFIG))
        # then read test config
        self.read_string(parameterized_config(TEST_CONFIG))
        # then read any "custom" test settings
        self.read(TEST_CONFIG_FILE)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise DatabookConfigException('Had trouble creating a directory')


# Setting DATABOOK_HOME and DATABOOK_CONFIG from environment variables, using
# "~/databook" and "~/databook/databook.cfg" respectively as defaults.

if 'DATABOOK_HOME' not in os.environ:
    DATABOOK_HOME = expand_env_var('~/databook')
else:
    DATABOOK_HOME = expand_env_var(os.environ['DATABOOK_HOME'])

mkdir_p(DATABOOK_HOME)

if 'DATABOOK_CONFIG' not in os.environ:
    if os.path.isfile(expand_env_var('~/databook.cfg')):
        DATABOOK_CONFIG = expand_env_var('~/databook.cfg')
    else:
        DATABOOK_CONFIG = DATABOOK_HOME + '/databook.cfg'
else:
    DATABOOK_CONFIG = expand_env_var(os.environ['DATABOOK_CONFIG'])


def parameterized_config(template):
    """
    Generates a configuration from the provided template + variables defined in
    current scope
    :param template: a config content templated with {{variables}}
    """
    all_vars = {k: v for d in [globals(), locals()] for k, v in d.items()}
    return template.format(**all_vars)


if not os.path.isfile(DATABOOK_CONFIG):
    log.info(
        'Creating new Databook config file in: %s',
        DATABOOK_CONFIG
    )
    with open(DATABOOK_CONFIG, 'w') as f:
        cfg = parameterized_config(DEFAULT_CONFIG)
        f.write(cfg.split(TEMPLATE_START)[-1].strip())

log.info("Reading the config from %s", DATABOOK_CONFIG)

conf = DatabookConfigParser()
conf.read(DATABOOK_CONFIG)


def get(section, key, **kwargs):
    return conf.get(section, key, **kwargs)


def getboolean(section, key):
    return conf.getboolean(section, key)


def getfloat(section, key):
    return conf.getfloat(section, key)


def getint(section, key):
    return conf.getint(section, key)


def getsection(section):
    return conf.getsection(section)


def has_option(section, key):
    return conf.has_option(section, key)


def remove_option(section, option):
    return conf.remove_option(section, option)


def as_dict(display_source=False, display_sensitive=False):
    return conf.as_dict(
        display_source=display_source, display_sensitive=display_sensitive)
as_dict.__doc__ = conf.as_dict.__doc__


def set(section, option, value):  # noqa
    return conf.set(section, option, value)

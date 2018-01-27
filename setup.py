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

from setuptools import setup, find_packages, Command
from setuptools.command.test import test as TestCommand

import imp
import logging
import os
import pip
import sys

logger = logging.getLogger(__name__)

# Kept manually in sync with airflow.__version__
version = imp.load_source(
    'databook.version', os.path.join('databook', 'version.py')).version

devel = [
    'nose',
    'nose-ignore-docstring==0.2',
    'nose-timer',
    'rednose'
]


def do_setup():
    setup(
        name='databook',
        description='Data Portal',
        license='Apache License 2.0',
        version=version,
        packages=find_packages(),
        package_data={'': [version]},
        include_package_data=True,
        zip_safe=False,
        scripts=['databook/bin/databook'],
        install_requires=[
            'click==6.7',
            'elasticsearch==5.4.0',
            'flask-admin==1.5.0',
            'flask-login==0.4.0',
            'flask-wtf==0.14.2',
            'flask==0.12.2',
            'future>=0.16.0, <0.17',
            'itsdangerous==0.24',
            'jinja2==2.9.6',
            'markupsafe==1.0',
            'neo4j-driver==1.5.0',
            'python-dateutil>=2.3, <3',
            'sqlineage==0.2.2',
            'urllib3==1.22',
            'urlparse3==1.1',
            'werkzeug==0.12.2',
            'wtforms==2.1'
        ],
        extras_require={
            'devel': devel,
        },
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: Python :: 3.4',
            'Topic :: System :: Monitoring',
        ],
        author='gtoonstra',
        author_email='',
        url='https://github.com/gtoonstra/databook/',
        cmdclass={},
    )


if __name__ == "__main__":
    do_setup()

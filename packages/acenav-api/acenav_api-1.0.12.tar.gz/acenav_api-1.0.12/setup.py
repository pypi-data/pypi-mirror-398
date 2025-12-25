# Copyright (C) 2018 Aceinna Navigation System Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.
import json
import os
from setuptools import find_packages, setup
from acenav_api.package import (PACKAGE_NAME, VERSION)

def load_json_file_path_under_configs_folder():
    json_file_paths = []
    setting_root_path = os.path.join(os.getcwd(), PACKAGE_NAME, 'configs')
    for root, dirs, files in os.walk(setting_root_path):
        for item in files:
            if not item.__contains__('.json'):
                continue

            json_file_path = os.path.join(root.replace(
                setting_root_path, 'configs'), item)
            json_file_paths.append(json_file_path)

    return json_file_paths

def load_resources():
    resources = []
    json_files = load_json_file_path_under_configs_folder()
    resources.extend(json_files)
    return resources

PACKAGE_DESCRIPTION = "Aceinna Navigation System API"

INSTALL_REQUIRES = []

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    author="Aceinna, Inc",
    author_email="info@aceinna.com",
    description=PACKAGE_DESCRIPTION,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Aceinna",
    license="Apache 2.0",
    python_requires=">=2.7, !=3.0.*, !=3.1.*",
    install_requires=INSTALL_REQUIRES,
    packages=find_packages(".", exclude=['test', 'tests']),
    package_dir={"": "."},
    package_data={
        PACKAGE_NAME: load_resources()
    },
    classifiers=[],
    entry_points={}
)

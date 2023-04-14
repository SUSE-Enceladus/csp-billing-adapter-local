#
# Copyright 2023 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import json
import os

import csp_billing_adapter

from csp_billing_adapter.config import Config

cache_file = os.path.expanduser('~/csp-adapter/cache.json')
csp_config_file = os.path.expanduser('~/csp-adapter/csp-config.json')


@csp_billing_adapter.hookimpl(trylast=True)
def save_cache(config: Config, cache: dict):
    update_cache(config, cache, replace=True)


@csp_billing_adapter.hookimpl(trylast=True)
def get_cache(config: Config):
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    return cache


@csp_billing_adapter.hookimpl(trylast=True)
def update_cache(config: Config, cache: dict, replace: bool = False):
    if not replace:
        cache = {**get_cache(config), **cache}

    with open(cache_file, 'w') as f:
        json.dump(cache, f)


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_config(config: Config):
    try:
        with open(csp_config_file, 'r') as f:
            csp_config = json.load(f)
    except FileNotFoundError:
        csp_config = {}

    return csp_config


@csp_billing_adapter.hookimpl(trylast=True)
def update_csp_config(config: Config, csp_config: Config, replace: bool = False):
    if not replace:
        csp_config = {**get_csp_config(config), **csp_config}

    with open(csp_config_file, 'w') as f:
        json.dump(csp_config, f)


@csp_billing_adapter.hookimpl(trylast=True)
def save_csp_config(
    config: Config,
    csp_config: Config
):
    update_csp_config(config, csp_config, replace=True)

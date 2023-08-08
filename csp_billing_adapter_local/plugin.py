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
"""
plugin.py is part of csp-billing-adapter-local and provides the local storage
plugin
"""

import json
import logging

from json.decoder import JSONDecodeError
from pathlib import Path

import csp_billing_adapter

from csp_billing_adapter.config import Config

ADAPTER_DATA_DIR = '/var/lib/csp-billing-adapter'
CACHE_FILE = 'cache.json'
CSP_CONFIG_FILE = 'csp-config.json'
CSP_LOG_FILEPATH = '/var/log/csp_billing_adapter.log'
LOGGER_NAME = 'CSPBillingAdapter'

log = logging.getLogger(LOGGER_NAME)


def get_local_path(filename):
    """Return the requested data file path"""
    local_storage_path = Path(ADAPTER_DATA_DIR)
    if not local_storage_path.exists():
        local_storage_path.mkdir(parents=True, exist_ok=True)
    local_storage_path.joinpath(filename)
    return local_storage_path


@csp_billing_adapter.hookimpl(trylast=True)
def setup_adapter(config: Config):
    log_to_file = logging.FileHandler(CSP_LOG_FILEPATH)
    csp_log = logging.getLogger(LOGGER_NAME)
    csp_log.addHandler(log_to_file)


@csp_billing_adapter.hookimpl(trylast=True)
def save_cache(config: Config, cache: dict):
    """Save specified content as new local cache contents."""
    update_cache(config, cache, replace=True)


@csp_billing_adapter.hookimpl(trylast=True)
def get_cache(config: Config):
    """Retrieve cache content from local storage cache"""
    try:
        with open(get_local_path(CACHE_FILE), 'r', encoding='utf-8') as f:
            cache = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        cache = {}

    log.info("Retrieved Cache Content: %s", cache)

    return cache


@csp_billing_adapter.hookimpl(trylast=True)
def update_cache(config: Config, cache: dict, replace: bool):
    """Update local storage cache with new content, replacing if specified."""
    if not replace:
        cache = {**get_cache(config), **cache}

    with open(get_local_path(CACHE_FILE), 'w', encoding='utf-8') as f:
        json.dump(cache, f)

    log.info("Updated Cache Content: %s", cache)


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_config(config: Config):
    """Retrieve csp_config content from local storage csp_config."""
    try:
        with open(get_local_path(CSP_CONFIG_FILE), 'r', encoding='utf-8') as f:
            csp_config = json.load(f)
    except (FileNotFoundError, JSONDecodeError):
        csp_config = {}

    log.info("Retrieved CSP Config Content: %s", csp_config)

    return csp_config


@csp_billing_adapter.hookimpl(trylast=True)
def update_csp_config(config: Config, csp_config: Config, replace: bool):
    """
    Update local storage csp_config with new content, replacing if specified.
    """
    if not replace:
        csp_config = {**get_csp_config(config), **csp_config}

    with open(get_local_path(CSP_CONFIG_FILE), 'w', encoding='utf-8') as f:
        json.dump(csp_config, f)

    log.info("Updated CSP Config Content: %s", csp_config)


@csp_billing_adapter.hookimpl(trylast=True)
def save_csp_config(
    config: Config,
    csp_config: Config
):
    """Save specified content as local storage csp_config contents."""
    update_csp_config(config, csp_config, replace=True)

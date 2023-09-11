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
import urllib.request
import urllib.error

from json.decoder import JSONDecodeError
from pathlib import Path

import csp_billing_adapter

from csp_billing_adapter.adapter import (
    LOGGER_NAME,
    LOGGING_FORMAT,
    LOGGING_DATE_FMT
)
from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import (
    get_now, date_to_string
)
from csp_billing_adapter.exceptions import CSPBillingAdapterException

ADAPTER_DATA_DIR = '/var/lib/csp-billing-adapter'
CACHE_FILE = 'cache.json'
CSP_CONFIG_FILE = 'csp-config.json'
CSP_LOG_FILEPATH = '/var/log/csp_billing_adapter.log'

log = logging.getLogger(LOGGER_NAME)


def get_local_path(filename: str):
    """Return the requested data file path"""
    local_storage_path = Path(ADAPTER_DATA_DIR)
    if not local_storage_path.exists():
        local_storage_path.mkdir(parents=True, exist_ok=True)
    return local_storage_path.joinpath(filename)


@csp_billing_adapter.hookimpl
def setup_adapter(config: Config):
    formatter = logging.Formatter(
        fmt=LOGGING_FORMAT,
        datefmt=LOGGING_DATE_FMT
    )
    log_to_file = logging.FileHandler(CSP_LOG_FILEPATH)
    log_to_file.setFormatter(formatter)
    log.addHandler(log_to_file)
    log.info(f'Logger file handler set to {CSP_LOG_FILEPATH}')


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


@csp_billing_adapter.hookimpl(trylast=True)
def get_usage_data(config: Config):
    """
    Retrieves the current usage report from the application API

    :param config: The application configuration dictionary
    :return: Return a dict with the current usage report
    """
    now = date_to_string(get_now())
    usage_data = _make_request(config.get('api'))
    metrics_key = 'usage_metrics'

    try:
        usage_data_items = usage_data[metrics_key]
    except KeyError:
        raise CSPBillingAdapterException(
            'Unrecognized application API response'
        )

    try:
        config_usage_metrics_info = config[metrics_key]
    except KeyError:
        raise CSPBillingAdapterException(
            'Config missing usage metrics section'
        )

    return _extract_usage(usage_data_items, config_usage_metrics_info, now)


def _extract_usage(
    api_usage_metrics: list,
    config_usage_metrics: dict,
    reporting_time
):
    """
    Parse the response from the application API to the expected structure.
    """
    usage_metrics = {}
    missing_metrics = []
    for usage_metric_info in api_usage_metrics:
        usage_metric_name = usage_metric_info.get('usage_metric')
        if usage_metric_name not in config_usage_metrics:
            missing_metrics.append(usage_metric_name)
        try:
            usage_metrics[usage_metric_name] = usage_metric_info['count']
        except KeyError:
            log.warning('Missing "count" info in the application API response')
            usage_metrics[usage_metric_name] = 0

    if missing_metrics:
        message = f"Usage metric(s) {', '.join(missing_metrics)} not in config"
        log.error(message)
        raise CSPBillingAdapterException(message)

    usage_metrics['reporting_time'] = reporting_time

    return usage_metrics


def _make_request(url: str):
    """
    Make a request to the application API
    returns response or raise exception.
    """
    request = urllib.request.Request(url)
    for attempt in range(0, 5):
        message = None
        try:
            with urllib.request.urlopen(request) as f:
                response = f.read().decode()
        except urllib.error.URLError as err:
            message = f'Error making the request to {url}: {err.reason}'

        if not message:
            break

    if message:
        raise CSPBillingAdapterException(message)
    try:
        return json.loads(response)
    except json.JSONDecodeError as err:
        raise CSPBillingAdapterException(
            f'Could not deserialized JSON from application API: {err}'
        )

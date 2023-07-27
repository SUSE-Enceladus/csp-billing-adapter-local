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

#
# Unit tests for the csp_billing_adapter.memory_csp_config when called
# via hooks
#
"""
test_plugin.py is part of csp-billing-adapter-local and provides units tests
for the local plugin functions.
"""
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from csp_billing_adapter.config import Config
from csp_billing_adapter.adapter import get_plugin_manager


from csp_billing_adapter_local.plugin import (
    get_local_path,
    get_cache,
    get_csp_config,
    update_cache,
    update_csp_config,
    save_cache,
    save_csp_config
)

config_file = 'tests/data/config.yaml'
pm = get_plugin_manager()
local_config = Config.load_from_file(
        config_file,
        pm.hook
    )


def test_local_get_local_path():
    """Test get_local_path(filename) in local plugin"""
    expected_path = Path('/var/lib/csp-billing-adapter/foo')
    assert get_local_path('foo') == expected_path


def test_local_get_cache():
    """Test get_cache() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/good/cache.json')
    ):
        local_cache = get_cache(config=local_config)
        assert local_cache.get('adapter_start_time')
        assert local_cache.get('next_bill_time')
        assert local_cache.get('next_reporting_time')


def test_local_get_cache_json_decoder_exception():
    """Test get_cache() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/bad/cache.json')
    ):
        assert get_cache(config=local_config) == {}


def test_local_get_cache_file_not_found_exception():
    """Test get_cache() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/bad/cache1.json')
    ):
        assert get_cache(config=local_config) == {}


def test_local_cache_update_merge():
    """Test update_cache() with merge in local plugin"""

    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'a': 10, 'c': 12}
            test_data3 = {**test_data1, **test_data2}

            # local cache should initially be empty
            assert get_cache(config=local_config) == {}

            update_cache(
                config=local_config,
                cache=test_data1,
                replace=False
            )

            assert get_cache(config=local_config) == test_data1

            update_cache(
                config=local_config,
                cache=test_data2,
                replace=False
            )

            assert get_cache(config=local_config)['a'] != test_data1['a']
            assert get_cache(config=local_config)['b'] == test_data1['b']
            assert get_cache(config=local_config)['c'] == test_data2['c']
            assert get_cache(config=local_config) == test_data3


def test_local_cache_update_replace():
    """Test update_cache() with replace in local plugin"""

    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local cache should initially be empty
            assert get_cache(config=local_config) == {}

            update_cache(
                config=local_config,
                cache=test_data1,
                replace=False
            )

            assert get_cache(config=local_config) == test_data1

            update_cache(
                config=local_config,
                cache=test_data2,
                replace=True
            )

            assert get_cache(config=local_config) == test_data2


def test_local_cache_save():
    """Test save_cache() in local plugin"""
    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local cache should initially be empty
            assert get_cache(config=local_config) == {}

            save_cache(
                config=local_config,
                cache=test_data1,
            )

            assert get_cache(config=local_config) == test_data1

            save_cache(
                config=local_config,
                cache=test_data2,
            )

            assert get_cache(config=local_config) == test_data2


def test_local_get_csp_config():
    """Test csp_config() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/good/csp_config.json')
    ):
        local_csp_config = get_csp_config(local_config)
        assert local_csp_config.get('billing_api_access_ok')
        assert local_csp_config.get('timestamp')
        assert local_csp_config.get('expire')


def test_local_get_csp_config_json_decoder_exception():
    """Test csp_config() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/bad/csp_config.json')
    ):
        assert get_csp_config(local_config) == {}


def test_local_get_csp_config_file_not_found_exception():
    """Test csp_config() in local plugin"""
    with patch(
        'csp_billing_adapter_local.plugin.get_local_path',
        return_value=Path('tests/data/bad/csp_config1.json')
    ):
        assert get_csp_config(local_config) == {}


def test_local_csp_config_update_merge():
    """Test update_cache() with merge in local plugin"""

    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'a': 10, 'c': 12}
            test_data3 = {**test_data1, **test_data2}

            # local csp_config should initially be empty
            assert get_csp_config(config=local_config) == {}

            update_csp_config(
                config=local_config,
                csp_config=test_data1,
                replace=False
            )

            assert get_csp_config(config=local_config) == test_data1

            update_csp_config(
                config=local_config,
                csp_config=test_data2,
                replace=False
            )

            assert get_csp_config(config=local_config)['a'] != test_data1['a']
            assert get_csp_config(config=local_config)['b'] == test_data1['b']
            assert get_csp_config(config=local_config)['c'] == test_data2['c']
            assert get_csp_config(config=local_config) == test_data3


def test_local_csp_config_update_replace():
    """Test update_cache() with replace in local plugin"""

    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):

            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local csp_config should initially be empty
            assert get_csp_config(config=local_config) == {}

            update_csp_config(
                config=local_config,
                csp_config=test_data1,
                replace=False
            )

            assert get_csp_config(config=local_config) == test_data1

            update_csp_config(
                config=local_config,
                csp_config=test_data2,
                replace=True
            )

            assert get_csp_config(config=local_config) == test_data2


def test_local_csp_config_save():
    """Test save_cache() in local plugin"""
    with NamedTemporaryFile() as temp_file:
        with patch(
            'csp_billing_adapter_local.plugin.get_local_path',
            return_value=Path(temp_file.name)
        ):

            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local csp_config should initially be empty
            assert get_csp_config(config=local_config) == {}

            save_csp_config(
                config=local_config,
                csp_config=test_data1,
            )

            assert get_csp_config(config=local_config) == test_data1

            save_csp_config(
                config=local_config,
                csp_config=test_data2,
            )

            assert get_csp_config(config=local_config) == test_data2

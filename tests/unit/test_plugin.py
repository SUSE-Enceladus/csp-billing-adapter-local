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
import datetime
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch
from pytest import raises

import urllib.error

from csp_billing_adapter.config import Config
from csp_billing_adapter.adapter import get_plugin_manager
from csp_billing_adapter.exceptions import CSPBillingAdapterException


from csp_billing_adapter_local.plugin import (
    get_local_path,
    get_cache,
    get_csp_config,
    update_cache,
    update_csp_config,
    save_cache,
    save_csp_config,
    get_usage_data,
    setup_adapter,
    get_version
)


@patch('csp_billing_adapter_local.plugin.get_local_path')
class TestCSPBillingAdapterLocal(object):
    def setup_method(self):
        self.config_file = 'tests/data/config.yaml'
        self.pm = get_plugin_manager()
        self.local_config = Config.load_from_file(
            self.config_file, self.pm.hook
        )
        self.json_data = {
            "usage_metrics": [
                {"usage_metric": "managed_node_count", "count": 42},
                {"usage_metric": "monitoring", "count": 99}
            ]
        }
        self.json_response = json.dumps(
            self.json_data, indent=2
        ).encode('utf-8')

    @patch('csp_billing_adapter_local.plugin.Path', return_value=Path('foo'))
    def test_local_get_local_path(self, mock_path, mock_get_local_path):
        """Test get_local_path(filename) in local plugin"""
        expected_path = Path('foo/bar')
        assert get_local_path('bar') == expected_path
        Path('foo').rmdir()

    def test_local_get_cache(self, mock_get_local_path):
        """Test get_cache() in local plugin"""
        mock_get_local_path.return_value = Path('tests/data/good/cache.json')
        local_cache = get_cache(config=self.local_config)
        assert local_cache.get('adapter_start_time')
        assert local_cache.get('next_bill_time')
        assert local_cache.get('next_reporting_time')

    def test_local_get_cache_json_decoder_exception(
        self, mock_get_local_path
    ):
        """Test get_cache() in local plugin"""
        mock_get_local_path.return_value = Path('tests/data/bad/cache.json')
        assert get_cache(config=self.local_config) == {}

    def test_local_get_cache_file_not_found_exception(
        self, mock_get_local_path
    ):
        """Test get_cache() in local plugin"""
        mock_get_local_path.return_value = Path('tests/data/bad/cache1.json')
        assert get_cache(config=self.local_config) == {}

    def test_local_cache_update_merge(self, mock_get_local_path):
        """Test update_cache() with merge in local plugin"""
        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'a': 10, 'c': 12}
            test_data3 = {**test_data1, **test_data2}

            # local cache should initially be empty
            assert get_cache(config=self.local_config) == {}

            update_cache(
                config=self.local_config,
                cache=test_data1,
                replace=False
            )

            assert get_cache(config=self.local_config) == test_data1

            update_cache(
                config=self.local_config,
                cache=test_data2,
                replace=False
            )

            assert get_cache(config=self.local_config)['a'] != test_data1['a']
            assert get_cache(config=self.local_config)['b'] == test_data1['b']
            assert get_cache(config=self.local_config)['c'] == test_data2['c']
            assert get_cache(config=self.local_config) == test_data3

    def test_local_cache_update_replace(self, mock_get_local_path):
        """Test update_cache() with replace in local plugin"""
        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local cache should initially be empty
            assert get_cache(config=self.local_config) == {}

            update_cache(
                config=self.local_config,
                cache=test_data1,
                replace=False
            )

            assert get_cache(config=self.local_config) == test_data1

            update_cache(
                config=self.local_config,
                cache=test_data2,
                replace=True
            )

            assert get_cache(config=self.local_config) == test_data2

    def test_local_cache_save(self, mock_get_local_path):
        """Test save_cache() in local plugin"""
        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local cache should initially be empty
            assert get_cache(config=self.local_config) == {}

            save_cache(
                config=self.local_config,
                cache=test_data1,
            )

            assert get_cache(config=self.local_config) == test_data1

            save_cache(
                config=self.local_config,
                cache=test_data2,
            )

            assert get_cache(config=self.local_config) == test_data2

    def test_local_get_csp_config(self, mock_get_local_path):
        """Test csp_config() in local plugin"""
        mock_get_local_path.return_value = Path(
            'tests/data/good/csp_config.json'
        )
        local_csp_config = get_csp_config(self.local_config)
        assert local_csp_config.get('billing_api_access_ok')
        assert local_csp_config.get('timestamp')
        assert local_csp_config.get('expire')

    def test_local_get_csp_config_json_decoder_exception(
        self, mock_get_local_path
    ):
        """Test csp_config() in local plugin"""
        mock_get_local_path.return_value = Path(
            'tests/data/bad/csp_config.json'
        )
        assert get_csp_config(self.local_config) == {}

    def test_local_get_csp_config_file_not_found_exception(
        self,
        mock_get_local_path
    ):
        """Test csp_config() in local plugin"""
        mock_get_local_path.return_value = Path(
            'tests/data/bad/csp_config1.json'
        )
        assert get_csp_config(self.local_config) == {}

    def test_local_csp_config_update_merge(self, mock_get_local_path):
        """Test update_cache() with merge in local plugin"""
        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'a': 10, 'c': 12}
            test_data3 = {**test_data1, **test_data2}

            # local csp_config should initially be empty
            assert get_csp_config(config=self.local_config) == {}

            update_csp_config(
                config=self.local_config,
                csp_config=test_data1,
                replace=False
            )

            assert get_csp_config(config=self.local_config) == test_data1

            update_csp_config(
                config=self.local_config,
                csp_config=test_data2,
                replace=False
            )

            config_result = get_csp_config(config=self.local_config)
            assert config_result['a'] != test_data1['a']
            assert config_result['b'] == test_data1['b']
            assert config_result['c'] == test_data2['c']
            assert config_result == test_data3

    def test_local_csp_config_update_replace(self, mock_get_local_path):
        """Test update_cache() with replace in local plugin"""

        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local csp_config should initially be empty
            assert get_csp_config(config=self.local_config) == {}

            update_csp_config(
                config=self.local_config,
                csp_config=test_data1,
                replace=False
            )

            assert get_csp_config(config=self.local_config) == test_data1

            update_csp_config(
                config=self.local_config,
                csp_config=test_data2,
                replace=True
            )

            assert get_csp_config(config=self.local_config) == test_data2

    def test_local_csp_config_save(self, mock_get_local_path):
        """Test save_cache() in local plugin"""
        with NamedTemporaryFile() as temp_file:
            mock_get_local_path.return_value = Path(temp_file.name)
            test_data1 = {'a': 1, 'b': 2}
            test_data2 = {'c': 3, 'd': 4}

            # local csp_config should initially be empty
            assert get_csp_config(config=self.local_config) == {}

            save_csp_config(
                config=self.local_config,
                csp_config=test_data1,
            )

            assert get_csp_config(config=self.local_config) == test_data1

            save_csp_config(
                config=self.local_config,
                csp_config=test_data2,
            )

            assert get_csp_config(config=self.local_config) == test_data2

    @patch('csp_billing_adapter_local.plugin.date_to_string')
    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data(
        self, mock_urlopen, mock_request,
        mock_date_to_string, mock_get_local_path,

    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            self.json_response

        mock_date_to_string.return_value = '1992-09-02T01:02:03.123456+00:00'

        response = get_usage_data(config=self.local_config)
        expected_response = {
            'reporting_time': '1992-09-02T01:02:03.123456+00:00',
            'managed_node_count': 42,
            'monitoring': 99
        }
        assert response == expected_response

    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_wrong_response(
        self, mock_urlopen, mock_request, mock_get_local_path
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps({'foo': []}, indent=2).encode('utf-8')
        with raises(CSPBillingAdapterException):
            get_usage_data(config=self.local_config)

    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_different_config_key(
        self, mock_urlopen, mock_request, mock_get_local_path
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps({'product_code': []}, indent=2).encode('utf-8')
        with raises(CSPBillingAdapterException):
            get_usage_data(config=self.local_config)

    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_no_usage_metrics(
        self, mock_urlopen, mock_request, mock_get_local_path
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps({'usage_metrics': []}, indent=2).encode('utf-8')
        with raises(CSPBillingAdapterException):
            self.local_config_no_metrics = dict(self.local_config)
            del self.local_config_no_metrics['usage_metrics']
            get_usage_data(config=self.local_config_no_metrics)

    @patch('csp_billing_adapter_local.plugin.json.loads')
    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_json_decode_error(
        self, mock_urlopen, mock_request,
        mock_json_loads, mock_get_local_path
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps({'usage_metrics': []}, indent=2).encode('utf-8')
        mock_json_loads.side_effect = json.JSONDecodeError(
            'error', '\n\n', 1
        )
        with raises(CSPBillingAdapterException):
            get_usage_data(config=self.local_config)

    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_config_missing_metrics(
        self, mock_urlopen, mock_request, mock_get_local_path, caplog
    ):
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps(self.json_data, indent=2).encode('utf-8')
        with caplog.at_level(logging.INFO, 'CSPBillingAdapter'):
            with raises(CSPBillingAdapterException):
                self.local_config_missing_metrics = Config.load_from_file(
                    self.config_file,
                    self.pm.hook
                )
                del (self.local_config_missing_metrics['usage_metrics']
                                                      ['monitoring'])
                del (self.local_config_missing_metrics['usage_metrics']
                                                      ['managed_node_count'])
                get_usage_data(config=self.local_config_missing_metrics)
            error_message = "Usage metric(s) managed_node_count, " \
                "monitoring not in config"
            assert error_message in caplog.text

    @patch('csp_billing_adapter_local.plugin.date_to_string')
    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_config_missing_count(
        self, mock_urlopen, mock_request, mock_get_now,
        mock_get_local_path, caplog
    ):
        self.json_data_no_count = {
            "usage_metrics": [
                {"usage_metric": "managed_node_count", "count": 42},
                {"usage_metric": "monitoring"}
            ]
        }
        mock_urlopen.return_value.__enter__.return_value.read.return_value = \
            json.dumps(self.json_data_no_count, indent=2).encode('utf-8')

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mock_get_now.return_value = now

        usage_data = get_usage_data(config=self.local_config)
        expected_usage_data = {
            'reporting_time': now,
            'managed_node_count': 42,
            'monitoring': 0
        }
        assert usage_data == expected_usage_data
        error_message = 'Missing "count" info in the application API response'
        assert error_message in caplog.text

    @patch('csp_billing_adapter_local.plugin.urllib.request.Request')
    @patch('csp_billing_adapter_local.plugin.urllib.request.urlopen')
    def test_local_csp_usage_data_errors(
            self, mock_urlopen, mock_request, mock_get_local_path
    ):
        mock_urlopen.side_effect = urllib.error.URLError('Unknown host')
        with raises(CSPBillingAdapterException):
            get_usage_data(config=self.local_config)
            # check request is retried 5 times
            assert mock_urlopen.call_count == 5

    @patch('csp_billing_adapter_local.plugin.logging.Logger.info')
    @patch('csp_billing_adapter_local.plugin.logging.Logger.addHandler')
    @patch('csp_billing_adapter_local.plugin.logging.FileHandler')
    def test_local_csp_setup_adapter_log_with_config_settings(
        self, mock_logging_file_handler, mock_logger_add_handler,
            mock_logging_info, mock_get_local_path
    ):
        file_handler = logging.FileHandler('foo')
        log = logging.getLogger('CSPBillingAdapter')
        mock_logging_file_handler.return_value = file_handler

        setup_adapter(config=self.local_config)

        log.addHandler.assert_called_with(file_handler)
        mock_logging_file_handler.assert_called_with(
            '/var/log/csp_billing_adapter.log'
        )
        mock_logging_info.assert_called_with(
            'Logger file handler set to /var/log/csp_billing_adapter.log'
        )

    def test_get_version(self, mock_get_local_path):
        version = get_version()
        assert version[0] == 'local_plugin'
        assert version[1]

import os
from unittest.mock import MagicMock, patch
import pytest

import fetch_vault_credentials

VAULT_ENV_VARS = {
    "VAULT_DEPLOYMENT_TOKEN": "abc123",
    "VAULT_ADDRESS": "https://vault.test:1000",
    "VAULT_NAMESPACE": "ns",
    "VAULT_KV_STORE": "kv",
    "VAULT_SECRET": "secret",
}

def secret_mock():
    cm = MagicMock()
    cm.getcode.return_value = 200
    cm.read.return_value = '''{
        "data": {
            "data": {
                "KEY1": "VALUE1",
                "KEY2": "VALUE2"
            }
        }
    }'''.encode()
    return cm

@pytest.mark.parametrize("omit_env_var", ["VAULT_DEPLOYMENT_TOKEN", "VAULT_ADDRESS", "VAULT_NAMESPACE", "VAULT_KV_STORE", "VAULT_SECRET"])
def test_env_vars_are_required(omit_env_var):
    with patch.dict(os.environ, {k: v for k, v in VAULT_ENV_VARS.items() if k != omit_env_var}, clear=True):
        with pytest.raises(OSError, match=f"The environment variable {omit_env_var} must be set."):
            fetch_vault_credentials.main()

@patch('urllib.request')
@patch('builtins.print')
@patch('sys.stdout')
def test_secret_fetched_correctly(mock_stdout, mock_print, mock_request):
    mock_request.urlopen.return_value = secret_mock()
    mock_stdout.isatty.return_value = False

    with patch.dict(os.environ, VAULT_ENV_VARS):
        fetch_vault_credentials.main()

    mock_print.assert_called_once_with("KEY1=VALUE1\nKEY2=VALUE2")

@patch('urllib.request')
def test_secret_fetching_failed(mock_request):
    cm = MagicMock()
    cm.getcode.return_value = 403
    mock_request.urlopen.return_value = cm

    with patch.dict(os.environ, VAULT_ENV_VARS):
        with pytest.raises(Exception, match=f"Request to Vault failed with status code 403"):
            fetch_vault_credentials.main()

@patch('urllib.request')
@patch('builtins.print')
@patch('sys.stdout')
def test_does_not_write_if_stdout_is_a_tty(mock_stdout, mock_print, mock_request):
    mock_request.urlopen.return_value = secret_mock()
    mock_stdout.isatty.return_value = True

    with patch.dict(os.environ, VAULT_ENV_VARS):
        fetch_vault_credentials.main()

    mock_print.assert_not_called()

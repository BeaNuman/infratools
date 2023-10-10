import os
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib.error import HTTPError

import fetch_vault_credentials
import pytest

VAULT_ENV_VARS = {
    "VAULT_ROLE_NAMESPACE": "namespace",
    "VAULT_ROLE_ID": "abc-123",
    "VAULT_ROLE_SECRET": "def-456",
    "VAULT_ADDRESS": "https://vault.test:1000",
    "VAULT_NAMESPACE": "namespace/nested",
    "VAULT_KV_STORE": "kv",
    "VAULT_SECRET": "secret",
}


@pytest.mark.parametrize("omit_env_var", VAULT_ENV_VARS.keys())
def test_env_vars_are_required(omit_env_var):
    with patch.dict(
        os.environ,
        {k: v for k, v in VAULT_ENV_VARS.items() if k != omit_env_var},
        clear=True,
    ):
        with pytest.raises(
            OSError, match=f"The environment variable {omit_env_var} must be set."
        ):
            fetch_vault_credentials.main()


@patch("urllib.request.urlopen")
def test_token_fetched_correctly(mock_urlopen):
    token_mock = MagicMock()
    token_mock.read.return_value = b'{ "auth": { "client_token": "xyz-789" } }'
    mock_urlopen.return_value = token_mock

    token_payload = fetch_vault_credentials.fetch_token(
        "https://vault.test:1000", "namespace", "abc-123", "def-345"
    )
    assert token_payload == {"client_token": "xyz-789", "x_vault_index": None}


@patch("urllib.request.urlopen")
def test_token_fetching_fails(mock_urlopen):
    mock_urlopen.side_effect = HTTPError(
        "https://vault.test:1000/v1/auth/approle/login", 403, "Unauthorized", {}, None
    )

    with pytest.raises(
        Exception,
        match="Error fetching Vault AppRole token: HTTP Error 403: Unauthorized",
    ):
        fetch_vault_credentials.fetch_token(
            "https://vault.test:1000", "namespace", "abc-123", "def-345"
        )


@patch("urllib.request.urlopen")
def test_token_json_decoding_fails(mock_urlopen):
    token_mock = MagicMock()
    token_mock.read.return_value = b'{ "auth": { "client_token": "xyz-789" }'
    mock_urlopen.return_value = token_mock

    with pytest.raises(
        Exception, match="Error decoding Vault AppRole token from response"
    ):
        fetch_vault_credentials.fetch_token(
            "https://vault.test:1000", "namespace", "abc-123", "def-345"
        )


@patch("urllib.request")
def test_secret_fetched_correctly(mock_request):
    secret_mock = MagicMock()
    secret_mock.read.return_value = b"""{
        "data": {
            "data": {
                "KEY1": "VALUE1",
                "KEY2": "VALUE2"
            }
        }
    }"""
    mock_request.urlopen.return_value = secret_mock

    with patch.dict(os.environ, VAULT_ENV_VARS):
        secret = fetch_vault_credentials.fetch_secret(
            "https://vault.test:1000", "xyz-789", "namespace", "kv", "secret"
        )

    assert secret == {"KEY1": "VALUE1", "KEY2": "VALUE2"}


@patch("urllib.request.urlopen")
def test_secret_fetching_fails(mock_urlopen):
    mock_urlopen.side_effect = HTTPError(
        "https://vault.test:1000/v1/kv/data/secret", 403, "Unauthorized", {}, None
    )

    with pytest.raises(
        Exception, match="Error fetching Vault secret: HTTP Error 403: Unauthorized"
    ):
        fetch_vault_credentials.fetch_secret(
            "https://vault.test:1000", "xyz-789", "namespace", "kv", "secret"
        )


@patch("urllib.request.urlopen")
def test_secret_json_decoding_fails(mock_urlopen):
    secret_mock = MagicMock()
    secret_mock.read.return_value = b"""{
        "data": {
            "data": {
                "KEY1": "VALUE1",
                "KEY2": "VALUE2"
            }
    }"""
    mock_urlopen.return_value = secret_mock

    with pytest.raises(Exception, match="Error decoding Vault secret from response"):
        fetch_vault_credentials.fetch_secret(
            "https://vault.test:1000", "xyz-789", "namespace", "kv", "secret"
        )


@patch(
    "fetch_vault_credentials.fetch_token",
    return_value={"client_token": "xyz-789", "x_vault_index": None},
)
@patch(
    "fetch_vault_credentials.fetch_secret",
    return_value={"KEY1": "VALUE1", "KEY2": "VALUE2"},
)
@patch("builtins.print")
@patch("sys.stdout")
def test_secret_is_printed_when_stdout_is_not_a_tty(mock_stdout, mock_print, _, __):
    mock_stdout.isatty.return_value = False

    with patch.dict(os.environ, VAULT_ENV_VARS):
        fetch_vault_credentials.main()

    mock_print.assert_has_calls(
        [
            call("echo \"Setting environment variables from Vault: 'KEY1', 'KEY2'\""),
            call("export 'KEY1'='VALUE1' 'KEY2'='VALUE2'"),
        ]
    )


@patch(
    "fetch_vault_credentials.fetch_token",
    return_value={"client_token": "xyz-789", "x_vault_index": None},
)
@patch(
    "fetch_vault_credentials.fetch_secret",
    return_value={"KEY1": "VALUE1", "KEY2": "VALUE2"},
)
@patch("builtins.print")
@patch("sys.stdout")
def test_secret_is_not_printed_when_stdout_is_a_tty(mock_stdout, mock_print, _, __):
    mock_stdout.isatty.return_value = True

    with patch.dict(os.environ, VAULT_ENV_VARS):
        fetch_vault_credentials.main()

    mock_print.assert_not_called()


@patch(
    "fetch_vault_credentials.fetch_token",
    return_value={"client_token": "xyz-789", "x_vault_index": None},
)
@patch(
    "fetch_vault_credentials.fetch_secret",
    return_value={"KEY1": "VALUE1", "Key2": "VALUE2"},
)
def test_returned_secret_with_invalid_keyword_set(_, __):

    with patch.dict(os.environ, VAULT_ENV_VARS):
        with pytest.raises(
            ValueError,
            match="The supplied keyword Key2 is invalid, and must "
            "consist only of uppercase letters, numbers and underscores",
        ):
            fetch_vault_credentials.main()

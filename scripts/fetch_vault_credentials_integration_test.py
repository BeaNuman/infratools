import os
import subprocess

VAULT_ENV_VARS = {
    "VAULT_ROLE_NAMESPACE": "namespace",
    "VAULT_ROLE_ID": "abc-123",
    "VAULT_ROLE_SECRET": "def-456",
    "VAULT_NAMESPACE": "namespace/nested",
    "VAULT_KV_STORE": "kv",
    "VAULT_SECRET": "secret",
}


def test_variables_are_sourced_correctly(httpserver):
    """Source the script with a stub Vault server and check that the secret
    data is available as env vars."""

    httpserver.expect_request("/v1/auth/approle/login").respond_with_json(
        {"auth": {"client_token": "xyz-789"}}
    )
    httpserver.expect_request(
        f"/v1/{VAULT_ENV_VARS['VAULT_KV_STORE']}/data/{VAULT_ENV_VARS['VAULT_SECRET']}"
    ).respond_with_json({"data": {"data": {"KEY1": "VALUE1", "KEY2": "VALUE2"}}})
    env = {"VAULT_ADDRESS": httpserver.url_for("")} | VAULT_ENV_VARS

    stdout = subprocess.run(
        [
            (
                f"bash -c '"
                f"source {os.path.dirname(__file__)}/fetch_vault_credentials.sh &&"
                f'echo "KEY1 value is $KEY1, KEY2 value is $KEY2"'
                f"'"
            )
        ],
        check=True,
        shell=True,
        capture_output=True,
        env=env,
    ).stdout
    assert "Setting environment variables from Vault: 'KEY1', 'KEY2'" in str(stdout)
    assert "KEY1 value is VALUE1" in str(stdout)
    assert "KEY2 value is VALUE2" in str(stdout)


def test_variables_are_not_printed(httpserver):
    httpserver.expect_request("/v1/auth/approle/login").respond_with_json(
        {"auth": {"client_token": "xyz-789"}}
    )
    httpserver.expect_request(
        f"/v1/{VAULT_ENV_VARS['VAULT_KV_STORE']}/data/{VAULT_ENV_VARS['VAULT_SECRET']}"
    ).respond_with_json({"data": {"data": {"KEY1": "VALUE1", "KEY2": "VALUE2"}}})
    env = {"VAULT_ADDRESS": httpserver.url_for("")} | VAULT_ENV_VARS

    stdout = subprocess.run(
        [f"bash -c 'source {os.path.dirname(__file__)}/fetch_vault_credentials.sh'"],
        check=True,
        shell=True,
        capture_output=True,
        env=env,
    ).stdout
    assert "VALUE1" not in str(stdout)
    assert "VALUE2" not in str(stdout)

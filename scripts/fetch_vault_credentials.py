#!/usr/bin/env python3
"""
Fetch secrets from Vault for source-ing into the application environment

This script connects to a Vault instance via its HTTP API and attempts
to pull sensitive environment variables from a namespace as specified by
the VAULT_* environment variables.
"""
import json
import os
import sys
from urllib.error import HTTPError

import urllib.request

def main():
    for env_var in ["VAULT_ROLE_NAMESPACE", "VAULT_ROLE_ID", "VAULT_ROLE_SECRET", "VAULT_ADDRESS", "VAULT_NAMESPACE", "VAULT_KV_STORE", "VAULT_SECRET"]:
        if env_var not in os.environ:
            raise OSError(f"The environment variable {env_var} must be set.")

    VAULT_ROLE_NAMESPACE = os.getenv("VAULT_ROLE_NAMESPACE")
    VAULT_ROLE_ID = os.getenv("VAULT_ROLE_ID")
    VAULT_ROLE_SECRET = os.getenv("VAULT_ROLE_SECRET")
    VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")
    VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE")
    VAULT_KV_STORE = os.getenv("VAULT_KV_STORE")
    VAULT_SECRET = os.getenv("VAULT_SECRET")

    vault_token = fetch_token(VAULT_ADDRESS, VAULT_ROLE_NAMESPACE, VAULT_ROLE_ID, VAULT_ROLE_SECRET)
    secret = fetch_secret(VAULT_ADDRESS, vault_token, VAULT_NAMESPACE, VAULT_KV_STORE, VAULT_SECRET)

    if not sys.stdout.isatty():
        print('\n'.join(f"{key}={value}" for key, value in secret.items()))

def fetch_token(vault_address, role_namespace, role_id, role_secret):
    try:
        req = urllib.request.Request(
            method='POST',
            url=f"{vault_address}/v1/auth/approle/login",
            headers={"X-Vault-Namespace": role_namespace},
            data=json.dumps({'role_id': role_id, 'secret_id': role_secret}).encode('utf-8')
        )
        vault_token_resp = urllib.request.urlopen(req).read()
        return json.loads(vault_token_resp.decode("utf-8"))["auth"]["client_token"]
    except json.JSONDecodeError as e:
        raise Exception("Error decoding Vault AppRole token from response")
    except Exception as e:
        raise Exception(f"Error fetching Vault AppRole token: {e}")

def fetch_secret(vault_address, vault_token, namespace, kv_store, secret):
    try:
        req = urllib.request.Request(
            method='GET',
            url=f"{vault_address}/v1/{kv_store}/data/{secret}",
            headers={
                "X-Vault-Namespace": namespace,
                "X-Vault-Token": vault_token,
            },
        )
        vault_secret_response = urllib.request.urlopen(req)
        return json.loads(vault_secret_response.read().decode("utf-8"))["data"]["data"]
    except json.JSONDecodeError as e:
        raise Exception("Error decoding Vault secret from response")
    except Exception as e:
        raise Exception(f"Error fetching Vault secret: {e}")

if __name__ == "__main__":
    main()

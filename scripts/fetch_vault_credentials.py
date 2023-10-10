#!/usr/bin/env python3
"""
Fetch secrets from Vault for source-ing into the application environment.

This script connects to a Vault instance via its HTTP API and attempts
to pull sensitive environment variables from a namespace as specified by
the VAULT_* environment variables.
"""
import json
import os
import re
import shlex
import sys
import time
import urllib.request
import urllib.error

MAX_CONSISTENCY_RETRIES = 5
RETRY_BACKOFF_FACTOR = 2

def main():
    for env_var in [
        "VAULT_ROLE_NAMESPACE",
        "VAULT_ROLE_ID",
        "VAULT_ROLE_SECRET",
        "VAULT_ADDRESS",
        "VAULT_NAMESPACE",
        "VAULT_KV_STORE",
        "VAULT_SECRET",
    ]:
        if env_var not in os.environ:
            raise OSError(f"The environment variable {env_var} must be set.")

    VAULT_ROLE_NAMESPACE = os.getenv("VAULT_ROLE_NAMESPACE")
    VAULT_ROLE_ID = os.getenv("VAULT_ROLE_ID")
    VAULT_ROLE_SECRET = os.getenv("VAULT_ROLE_SECRET")
    VAULT_ADDRESS = os.getenv("VAULT_ADDRESS")
    VAULT_NAMESPACE = os.getenv("VAULT_NAMESPACE")
    VAULT_KV_STORE = os.getenv("VAULT_KV_STORE")
    VAULT_SECRET = os.getenv("VAULT_SECRET")

    vault_token_payload = fetch_token(
        VAULT_ADDRESS, VAULT_ROLE_NAMESPACE, VAULT_ROLE_ID, VAULT_ROLE_SECRET
    )

    vault_token = vault_token_payload["client_token"]
    x_vault_index = vault_token_payload.get('x_vault_index')
    
    secret = fetch_secret(
        VAULT_ADDRESS, vault_token, VAULT_NAMESPACE, VAULT_KV_STORE, VAULT_SECRET, x_vault_index=x_vault_index
    )

    if not sys.stdout.isatty():
        print(
            'echo "Setting environment variables from Vault: '
            + ", ".join(validate_and_sanitise_key(key) for key in secret.keys())
            + '"'
        )
        print(
            "export "
            + " ".join(
                f"{validate_and_sanitise_key(key)}={sanitise_value(value)}"
                for key, value in secret.items()
            )
        )


def validate_and_sanitise_key(input):
    if re.search("^[A-Z0-9_]+$", input):
        return f"'{input}'"
    else:
        raise ValueError(
            f"The supplied keyword {input} is invalid, and must consist only of "
            "uppercase letters, numbers and underscores"
        )


def sanitise_value(input):
    input = shlex.quote(input)

    if all((input.startswith("'"), input.endswith("'"))):
        return input
    else:
        return f"'{input}'"


def fetch_token(vault_address, role_namespace, role_id, role_secret):
    try:
        req = urllib.request.Request(
            method="POST",
            url=f"{vault_address}/v1/auth/approle/login",
            headers={"X-Vault-Namespace": role_namespace},
            data=json.dumps({"role_id": role_id, "secret_id": role_secret}).encode(
                "utf-8"
            ),
        )
        vault_token_opener = urllib.request.urlopen(req)
        vault_token_response_headers = dict(vault_token_opener.getheaders())
        vault_token_response_body = vault_token_opener.read()

        client_token = json.loads(vault_token_response_body.decode("utf-8"))["auth"]["client_token"]
        token_payload = {
            'client_token': client_token,
            'x_vault_index': vault_token_response_headers.get('X-Vault-Index')
        }

        return token_payload

    except json.JSONDecodeError:
        raise Exception("Error decoding Vault AppRole token from response")
    except Exception as e:
        raise Exception(f"Error fetching Vault AppRole token: {e}")


def fetch_secret(vault_address, vault_token, namespace, kv_store, secret, x_vault_index=None):
    
    retry_count = 0

    secret_request_headers = {
                "X-Vault-Namespace": namespace,
                "X-Vault-Token": vault_token,
            }

    if x_vault_index:
        secret_request_headers.update({"X-Vault-Index": x_vault_index})

    while retry_count < MAX_CONSISTENCY_RETRIES:
        
        try:
            req = urllib.request.Request(
                method="GET",
                url=f"{vault_address}/v1/{kv_store}/data/{secret}",
                headers={
                    "X-Vault-Namespace": namespace,
                    "X-Vault-Token": vault_token,
                },
            )
            vault_secret_response = urllib.request.urlopen(req)
            return json.loads(vault_secret_response.read().decode("utf-8"))["data"]["data"]
        except urllib.error.HTTPError as e:
            if e.code == 412:
                print(f"Vault cluster not yet consistent, retry attempt number: {retry_count}")
                retry_count += 1
                sleep_time = RETRY_BACKOFF_FACTOR * retry_count
                if retry_count < MAX_CONSISTENCY_RETRIES:
                    time.sleep(sleep_time)  # sleep before retrying
                else:
                    raise Exception(f"Error fetching Vault secret after {MAX_CONSISTENCY_RETRIES} attempts: {e}")
            else:
                raise Exception(f"Error fetching Vault secret: {e}")
                            
        except json.JSONDecodeError:
            raise Exception("Error decoding Vault secret from response")
        except Exception as e:
            raise Exception(f"Error fetching Vault secret: {e}")


if __name__ == "__main__":
    main()

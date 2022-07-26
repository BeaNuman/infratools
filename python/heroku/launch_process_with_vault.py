#!/usr/bin/env python3
"""
Launch a process with an environment partially populated from Vault.

This script connects to a Vault instance via its HTTP API and attempts
to pull sensitive environment variables from a namespace as specified by
the command line arguments. A process is then spawned with the sensitive
environment variables set.
"""
import argparse
import json
import os
import subprocess

import urllib3


def main():
    if "VAULT_DEPLOYMENT_TOKEN" not in os.environ:
        raise OSError("The environment variable VAULT_DEPLOYMENT_TOKEN must be set.")

    VAULT_DEPLOYMENT_TOKEN = os.getenv("VAULT_DEPLOYMENT_TOKEN")

    parser = argparse.ArgumentParser()

    parser.add_argument("--vault-address", type=str, required=True)
    parser.add_argument("--vault-namespace-path", type=str, required=True)
    parser.add_argument("--vault-secret-path", type=str, required=True)
    parser.add_argument("--launch-command", type=str, required=True)

    arguments = parser.parse_args()

    http_pool = urllib3.PoolManager()

    try:
        vault_secret_request = http_pool.request(
            "GET",
            f"{arguments.vault_address}/v1/{arguments.vault_secret_path}",
            headers={
                "X-Vault-Namespace": arguments.vault_namespace_path,
                "X-Vault-Token": VAULT_DEPLOYMENT_TOKEN,
            },
        )
    except Exception as e:
        raise Exception(f"Attempt to reach Vault failed with error: {e}")

    if vault_secret_request.status != 200:
        raise Exception(
            f"Request to Vault failed with status code {vault_secret_request.status}"
        )

    try:
        payload = json.loads(vault_secret_request.data.decode("utf-8"))["data"]["data"]
    except Exception as e:
        raise Exception(f"Failed to parse Vault payload with error: {e}")

    heroku_subprocess_environment = os.environ.copy()
    heroku_subprocess_environment.update(payload)

    subprocess_command = arguments.launch_command.split(" ")

    subprocess.run(subprocess_command, env=heroku_subprocess_environment)


if __name__ == "__main__":
    main()

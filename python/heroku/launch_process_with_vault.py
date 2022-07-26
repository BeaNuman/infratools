#!/usr/bin/env python3
import argparse
import json
import os
import subprocess

import urllib3

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

secret_payload = json.loads(vault_secret_request.data.decode("utf-8"))["data"]["data"]

heroku_subprocess_environment = os.environ.copy()
heroku_subprocess_environment.update(secret_payload)

subprocess_command = arguments.launch_command.split(" ")

subprocess.run(subprocess_command, env=heroku_subprocess_environment)

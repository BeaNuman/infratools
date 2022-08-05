#!/usr/bin/env bash

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
set -euo pipefail
PYTHON_SCRIPT_OUTPUT="$($SCRIPTPATH/fetch_vault_credentials.py)"
eval "$PYTHON_SCRIPT_OUTPUT"

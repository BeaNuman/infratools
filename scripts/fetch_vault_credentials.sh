#!/usr/bin/env bash

set -euo pipefail

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT_OUTPUT="$($SCRIPTPATH/fetch_vault_credentials.py)"
eval "$PYTHON_SCRIPT_OUTPUT"

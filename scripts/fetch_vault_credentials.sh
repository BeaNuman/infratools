#!/usr/bin/env bash

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_SCRIPT_OUTPUT=$($SCRIPTPATH/fetch_vault_credentials.py)
PYTHON_SCRIPT_EXIT_CODE=$?

if [ ${PYTHON_SCRIPT_EXIT_CODE} == 0 ]; then
    eval "${PYTHON_SCRIPT_OUTPUT}"
else
    exit ${PYTHON_SCRIPT_EXIT_CODE}
fi

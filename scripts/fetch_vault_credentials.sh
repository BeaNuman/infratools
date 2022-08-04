#!/usr/bin/env bash

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCRIPT_OUTPUT=$($SCRIPTPATH/fetch_vault_credentials.py)

if [ $? == 0 ]; then
    eval "${SCRIPT_OUTPUT}"
else
    exit $?
fi

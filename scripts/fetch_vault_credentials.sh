#!/usr/bin/env bash

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$($SCRIPTPATH/fetch_vault_credentials.py)"

#!/usr/bin/env bash

SCRIPTPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for var in $($SCRIPTPATH/fetch_vault_credentials.py); do
  export $var
done

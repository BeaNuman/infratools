#!/usr/bin/env bash

SCRIPT_DIR=$(cd "$(dirname "${0:-}")"; pwd)
for var in $($SCRIPT_DIR/fetch-vault-credentials.py); do
  export $var
done

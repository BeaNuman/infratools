#!/usr/bin/env bash

for var in $(/app/.profile.d/fetch_vault_credentials.py); do
  export $var
done

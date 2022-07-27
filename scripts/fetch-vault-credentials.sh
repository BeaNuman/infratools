#!/usr/bin/env bash

for var in $(/app/.profile.d/fetch-vault-credentials.py); do
  export $var
done

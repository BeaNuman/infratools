# Heroku Buildpack: Populate `bash` environment from Vault

This buildpack populates `$BUILD_DIR/.profile.d` (with $BUILD_DIR set by the upstream build platform) 
with a number of utility scripts to fetch secrets from a Vault cluster and `export` them into a system's 
environment.

## Requirements

Python 3

## Configuration

The scripts expect the following environment variables to be set:

| Environment Variable   | Required? | Description                                           |
|------------------------|-----------|-------------------------------------------------------|
| `VAULT_ADDRESS`        | Yes       | The URI of the target Vault cluster                   |
| `VAULT_ROLE_ID`        | Yes       | The AppRole's ID                                      |
| `VAULT_ROLE_SECRET`    | Yes       | The AppRole's 'Secret ID'                             |
| `VAULT_ROLE_NAMESPACE` | Yes       | The Vault namespace against which to authenticate     |
| `VAULT_NAMESPACE`      | Yes       | The Vault namespace from which to pull secrets        |
| `VAULT_KV_STORE`       | Yes       | The Vault key-value store from which to pull secrets  |
| `VAULT_SECRET`         | Yes       | The secret name within the specified key-value store  |

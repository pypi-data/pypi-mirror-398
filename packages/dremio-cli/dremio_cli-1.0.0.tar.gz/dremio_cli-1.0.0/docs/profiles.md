# Profile Management Guide

This guide covers how to create and manage Dremio CLI profiles using both YAML configuration files and environment variables.

## Overview

Profiles store connection information for Dremio instances. The CLI supports two methods:

1. **YAML Configuration** - Stored in `~/.dremio/profiles.yaml`
2. **Environment Variables** - Loaded from `.env` file or shell environment

Environment variables take precedence over YAML profiles.

## YAML Configuration

### Location

Profiles are stored in: `~/.dremio/profiles.yaml`

### Creating Profiles via CLI

```bash
# Create a Dremio Cloud profile
dremio profile create \
  --name cloud-prod \
  --type cloud \
  --base-url https://api.dremio.cloud/v0 \
  --auth-type pat \
  --token YOUR_PERSONAL_ACCESS_TOKEN \
  --project-id YOUR_PROJECT_ID

# Create a Dremio Software profile
dremio profile create \
  --name software-dev \
  --type software \
  --base-url https://dremio.company.com/api/v3 \
  --auth-type pat \
  --token YOUR_PERSONAL_ACCESS_TOKEN
```

### Manual YAML Configuration

Edit `~/.dremio/profiles.yaml`:

```yaml
profiles:
  cloud-prod:
    type: cloud
    base_url: https://api.dremio.cloud/v0
    project_id: 788baab4-3c3b-42da-9f1d-5cc6dc03147d
    auth:
      type: pat
      token: YOUR_ENCRYPTED_TOKEN
    testing_folder: testing
  
  software-dev:
    type: software
    base_url: https://dremio.company.com/api/v3
    auth:
      type: pat
      token: YOUR_ENCRYPTED_TOKEN
    testing_folder: '"dremio-catalog".alexmerced.testing'
  
  software-local:
    type: software
    base_url: http://localhost:9047/api/v3
    auth:
      type: username_password
      username: admin
      password: YOUR_ENCRYPTED_PASSWORD

default_profile: cloud-prod
```

### Profile Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | `cloud` or `software` |
| `base_url` | Yes | API endpoint URL |
| `project_id` | Cloud only | Project UUID |
| `auth.type` | Yes | `pat`, `oauth`, or `username_password` |
| `auth.token` | For PAT | Personal Access Token |
| `auth.username` | For user/pass | Username |
| `auth.password` | For user/pass | Password |
| `testing_folder` | No | Default folder for testing |

## Environment Variable Configuration

### Pattern

Environment variables follow the pattern:
```
DREMIO_{PROFILE}_{KEY}=value
```

### Example .env File

Create a `.env` file in your project directory or home directory:

```bash
# Cloud Profile
DREMIO_CLOUD_TYPE=cloud
DREMIO_CLOUD_BASE_URL=https://api.dremio.cloud/v0
DREMIO_CLOUD_PROJECTID=788baab4-3c3b-42da-9f1d-5cc6dc03147d
DREMIO_CLOUD_TOKEN=s3JcLOqFTR6qnurWp09epkXfy0+06N9i5oSwG0KbRthqmgiL1DvMgd2+LSNgUA==
DREMIO_CLOUD_TESTING_FOLDER=testing

# Software Profile
DREMIO_SOFTWARE_TYPE=software
DREMIO_SOFTWARE_BASE_URL=https://v26.dremio.org/api/v3
DREMIO_SOFTWARE_TOKEN=Q/ToosxORAuvy2zBLL+Q9O9JCnJL/8KKrsiC1Np3UL8yxQ3IyzGzgoBo2LwzvQ==
DREMIO_SOFTWARE_TESTING_FOLDER='"dremio-catalog".alexmerced.testing'

# Local Development Profile
DREMIO_LOCAL_TYPE=software
DREMIO_LOCAL_BASE_URL=http://localhost:9047/api/v3
DREMIO_LOCAL_USERNAME=admin
DREMIO_LOCAL_PASSWORD=password123
```

### Supported Environment Variables

| Variable Pattern | Description | Example |
|-----------------|-------------|---------|
| `DREMIO_{PROFILE}_TYPE` | Profile type | `cloud` or `software` |
| `DREMIO_{PROFILE}_BASE_URL` | API endpoint | `https://api.dremio.cloud/v0` |
| `DREMIO_{PROFILE}_PROJECTID` | Project ID (Cloud) | `788baab4-...` |
| `DREMIO_{PROFILE}_TOKEN` | Personal Access Token | `s3JcLOqFTR...` |
| `DREMIO_{PROFILE}_USERNAME` | Username (user/pass auth) | `admin` |
| `DREMIO_{PROFILE}_PASSWORD` | Password (user/pass auth) | `password123` |
| `DREMIO_{PROFILE}_TESTING_FOLDER` | Default test folder | `testing` |

### Loading Environment Variables

The CLI automatically loads `.env` files from:
1. Current working directory
2. Home directory (`~/.env`)

You can also set environment variables in your shell:

```bash
export DREMIO_PROD_TYPE=cloud
export DREMIO_PROD_BASE_URL=https://api.dremio.cloud/v0
export DREMIO_PROD_TOKEN=your_token_here
```

## Profile Management Commands

### List Profiles

```bash
# List all profiles (YAML + environment variables)
dremio profile list

# Output formats
dremio --output json profile list
dremio --output yaml profile list
```

### View Current Profile

```bash
# Show the default profile
dremio profile current
```

### Set Default Profile

```bash
# Set default profile in YAML
dremio profile set-default cloud-prod
```

### Delete Profile

```bash
# Delete a YAML profile
dremio profile delete software-dev
```

**Note:** Environment variable profiles cannot be deleted via CLI.

## Using Profiles

### Specify Profile for Commands

```bash
# Use specific profile
dremio --profile cloud-prod catalog list
dremio --profile software-dev sql execute "SELECT 1"

# Use default profile (no --profile flag)
dremio catalog list
```

### Profile Priority

When multiple profiles exist with the same name:

1. **Environment Variables** (highest priority)
2. **YAML Configuration**

Example:
```bash
# If both exist, environment variable wins
DREMIO_CLOUD_TOKEN=env_token  # This is used
# vs
profiles.yaml: cloud.auth.token: yaml_token  # This is ignored
```

## Security Best Practices

### 1. Never Commit Credentials

Add to `.gitignore`:
```gitignore
.env
.env.*
!.env.example
.dremio/
```

### 2. Use Environment Variables for CI/CD

```yaml
# GitHub Actions example
env:
  DREMIO_PROD_TYPE: cloud
  DREMIO_PROD_BASE_URL: ${{ secrets.DREMIO_BASE_URL }}
  DREMIO_PROD_TOKEN: ${{ secrets.DREMIO_TOKEN }}
  DREMIO_PROD_PROJECTID: ${{ secrets.DREMIO_PROJECT_ID }}
```

### 3. Token Encryption

YAML profiles automatically encrypt tokens. Environment variables are stored as-is.

### 4. Rotate Tokens Regularly

```bash
# Update token in YAML
dremio profile create --name cloud-prod --token NEW_TOKEN

# Update environment variable
export DREMIO_CLOUD_TOKEN=NEW_TOKEN
```

## Example Workflows

### Development Workflow

```bash
# .env file for local development
DREMIO_DEV_TYPE=software
DREMIO_DEV_BASE_URL=http://localhost:9047/api/v3
DREMIO_DEV_USERNAME=admin
DREMIO_DEV_PASSWORD=password123

# Use in commands
dremio --profile dev catalog list
dremio --profile dev sql execute "SELECT * FROM my_table LIMIT 10"
```

### Production Workflow

```bash
# profiles.yaml for production
profiles:
  prod:
    type: cloud
    base_url: https://api.dremio.cloud/v0
    project_id: YOUR_PROJECT_ID
    auth:
      type: pat
      token: ENCRYPTED_TOKEN

# Use in commands
dremio --profile prod job list
dremio --profile prod view create --path '["Analytics", "Summary"]' --sql "..."
```

### Multi-Environment Setup

```bash
# .env file with multiple environments
DREMIO_DEV_TYPE=software
DREMIO_DEV_BASE_URL=http://localhost:9047/api/v3
DREMIO_DEV_TOKEN=dev_token

DREMIO_STAGING_TYPE=cloud
DREMIO_STAGING_BASE_URL=https://api.dremio.cloud/v0
DREMIO_STAGING_PROJECTID=staging_project_id
DREMIO_STAGING_TOKEN=staging_token

DREMIO_PROD_TYPE=cloud
DREMIO_PROD_BASE_URL=https://api.dremio.cloud/v0
DREMIO_PROD_PROJECTID=prod_project_id
DREMIO_PROD_TOKEN=prod_token

# Switch between environments
dremio --profile dev catalog list
dremio --profile staging catalog list
dremio --profile prod catalog list
```

## Troubleshooting

### Profile Not Found

```bash
# List all available profiles
dremio profile list

# Check environment variables
env | grep DREMIO_
```

### Authentication Errors

```bash
# Verify token is valid
dremio --profile cloud-prod --verbose catalog list

# Check base URL is correct
dremio profile list
```

### Environment Variables Not Loading

```bash
# Verify .env file location
ls -la .env

# Check .env file format (no spaces around =)
cat .env

# Manually load .env
export $(cat .env | xargs)
```

## Advanced Configuration

### Custom .env Location

```bash
# Set custom .env file path
export DREMIO_ENV_FILE=/path/to/custom/.env
```

### Profile Inheritance

Environment variables can override specific YAML fields:

```yaml
# profiles.yaml
profiles:
  cloud:
    type: cloud
    base_url: https://api.dremio.cloud/v0
    project_id: default_project
```

```bash
# Override project_id via environment
export DREMIO_CLOUD_PROJECTID=different_project

# Now uses different_project instead of default_project
dremio --profile cloud catalog list
```

## Summary

- **YAML**: Best for persistent, encrypted profiles
- **Environment Variables**: Best for CI/CD, temporary configs, and overrides
- **Priority**: Environment variables > YAML
- **Security**: Never commit credentials, use `.gitignore`
- **Flexibility**: Mix and match YAML and environment variables as needed

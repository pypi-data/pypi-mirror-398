# Source Management

This guide covers source management operations for connecting to and managing external data sources in Dremio.

## Overview

**Sources** are connections to external data systems like databases, object storage, and data lakes. Dremio supports many source types including:

- **Databases**: PostgreSQL, MySQL, Oracle, SQL Server, MongoDB
- **Object Storage**: S3, Azure Blob Storage, Google Cloud Storage
- **Data Lakes**: Hive, Iceberg, Delta Lake
- **Cloud Warehouses**: Snowflake, Redshift, BigQuery

## Commands

### List Sources

List all configured sources.

```bash
dremio source list
```

**Examples:**

```bash
# List all sources
dremio source list

# JSON output
dremio --output json source list

# YAML output
dremio --output yaml source list
```

### Get Source

Retrieve source details by ID.

```bash
dremio source get <SOURCE_ID>
```

**Arguments:**
- `SOURCE_ID` - The source ID (UUID)

**Examples:**

```bash
# Get source details
dremio source get 791ee75c-956e-40fe-b2cc-0922a0f9b0b4

# Get in JSON format
dremio --output json source get 791ee75c-956e-40fe-b2cc-0922a0f9b0b4
```

### Create Source

Create a new data source.

```bash
dremio source create --name <NAME> --type <TYPE> --config-file <FILE>
```

**Options:**
- `--name TEXT` - Source name (required)
- `--type TEXT` - Source type (required, e.g., POSTGRES, S3, MONGO)
- `--config-file PATH` - JSON configuration file (required)

**Examples:**

```bash
# Create PostgreSQL source
dremio source create --name MyPostgres --type POSTGRES --config-file postgres.json

# Create S3 source
dremio source create --name MyS3 --type S3 --config-file s3.json

# Create MongoDB source
dremio source create --name MyMongo --type MONGO --config-file mongo.json
```

### Update Source

Update an existing source configuration.

```bash
dremio source update <SOURCE_ID> --config-file <FILE>
```

**Arguments:**
- `SOURCE_ID` - The source ID (UUID)

**Options:**
- `--config-file PATH` - Updated JSON configuration file (required)

**Examples:**

```bash
# Update source configuration
dremio source update abc-123 --config-file updated_postgres.json
```

### Refresh Source

Refresh source metadata to discover new tables/files.

```bash
dremio source refresh <SOURCE_ID>
```

**Arguments:**
- `SOURCE_ID` - The source ID (UUID)

**Examples:**

```bash
# Refresh source metadata
dremio source refresh 791ee75c-956e-40fe-b2cc-0922a0f9b0b4
```

### Delete Source

Delete a source.

```bash
dremio source delete <SOURCE_ID>
```

**Arguments:**
- `SOURCE_ID` - The source ID (UUID)

**Options:**
- `--tag TEXT` - Version tag for optimistic concurrency control

**Examples:**

```bash
# Delete source (with confirmation)
dremio source delete abc-123

# Delete without confirmation
dremio source delete abc-123 --yes
```

### Test Connection

Test a source configuration before creating.

```bash
dremio source test-connection --config-file <FILE>
```

**Options:**
- `--config-file PATH` - JSON configuration file to test (required)

**Examples:**

```bash
# Test PostgreSQL connection
dremio source test-connection --config-file postgres.json

# Test S3 connection
dremio source test-connection --config-file s3.json
```

## Configuration Examples

### PostgreSQL

```json
{
  "hostname": "postgres.company.com",
  "port": 5432,
  "databaseName": "analytics",
  "username": "dremio_user",
  "password": "secure_password",
  "authenticationType": "MASTER"
}
```

### S3

```json
{
  "credentialType": "ACCESS_KEY",
  "accessKey": "AKIAIOSFODNN7EXAMPLE",
  "accessSecret": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "secure": true,
  "externalBucketList": ["my-bucket"],
  "enableAsync": true
}
```

### MongoDB

```json
{
  "host": "mongodb.company.com",
  "port": 27017,
  "authenticationType": "MASTER",
  "username": "dremio_user",
  "password": "secure_password",
  "authDatabase": "admin",
  "useSsl": true
}
```

### Azure Blob Storage

```json
{
  "accountKind": "STORAGE_V2",
  "accountName": "mystorageaccount",
  "accessKey": "account_access_key",
  "secure": true,
  "containers": ["data-container"]
}
```

## Scenarios

### Creating a New PostgreSQL Source

```bash
# 1. Create configuration file
cat > postgres.json <<EOF
{
  "hostname": "postgres.company.com",
  "port": 5432,
  "databaseName": "analytics",
  "username": "dremio_user",
  "password": "secure_password",
  "authenticationType": "MASTER"
}
EOF

# 2. Test connection
dremio source test-connection --config-file postgres.json

# 3. Create source
dremio source create --name Analytics_DB --type POSTGRES --config-file postgres.json

# 4. Get source ID
SOURCE_ID=$(dremio --output json source list | jq -r '.[] | select(.path[0] == "Analytics_DB") | .id')

# 5. Refresh metadata
dremio source refresh $SOURCE_ID
```

### Updating Source Credentials

```bash
# 1. Get current source
dremio --output json source get abc-123 > current_config.json

# 2. Edit configuration
cat current_config.json | jq '.config.password = "new_password"' > updated_config.json

# 3. Update source
dremio source update abc-123 --config-file updated_config.json

# 4. Test connection
dremio source refresh abc-123
```

### Migrating Sources

```bash
# 1. Export source from old environment
dremio --profile old --output json source get abc-123 > source_export.json

# 2. Extract configuration
cat source_export.json | jq '.config' > source_config.json

# 3. Create in new environment
dremio --profile new source create \
  --name $(cat source_export.json | jq -r '.path[0]') \
  --type $(cat source_export.json | jq -r '.type') \
  --config-file source_config.json
```

## Common Workflows

### 1. Bulk Source Creation

```bash
#!/bin/bash
# create_sources.sh

# Define sources
declare -A SOURCES=(
  ["Postgres_Prod"]="POSTGRES:postgres_prod.json"
  ["S3_DataLake"]="S3:s3_datalake.json"
  ["Mongo_Events"]="MONGO:mongo_events.json"
)

# Create each source
for name in "${!SOURCES[@]}"; do
  IFS=':' read -r type config <<< "${SOURCES[$name]}"
  
  echo "Creating source: $name"
  dremio source create --name "$name" --type "$type" --config-file "$config"
done
```

### 2. Source Health Check

```bash
#!/bin/bash
# check_sources.sh

# Get all sources
SOURCES=$(dremio --output json source list | jq -r '.[].id')

for source_id in $SOURCES; do
  echo "Checking source: $source_id"
  
  # Try to refresh
  if dremio source refresh $source_id 2>/dev/null; then
    echo "  ✓ Healthy"
  else
    echo "  ✗ Unhealthy"
  fi
done
```

### 3. Automated Refresh

```bash
#!/bin/bash
# refresh_all_sources.sh

# Refresh all sources nightly
dremio --output json source list | jq -r '.[].id' | while read source_id; do
  echo "Refreshing source: $source_id"
  dremio source refresh $source_id
  sleep 5  # Rate limiting
done
```

### 4. Source Inventory

```bash
# Export source inventory
dremio --output json source list | jq '[.[] | {
  name: .path[0],
  type: .type,
  id: .id,
  created: .createdAt
}]' > source_inventory.json

# Generate report
cat source_inventory.json | jq -r '.[] | "\(.name) (\(.type))"'
```

## Tips

1. **Test before creating**: Always test connections first
   ```bash
   dremio source test-connection --config-file config.json
   ```

2. **Store configs securely**: Don't commit credentials to git
   ```bash
   # Add to .gitignore
   echo "*.source.json" >> .gitignore
   ```

3. **Use environment variables**: For sensitive data
   ```bash
   # In config file, use placeholders
   cat > postgres.json <<EOF
   {
     "hostname": "${POSTGRES_HOST}",
     "username": "${POSTGRES_USER}",
     "password": "${POSTGRES_PASSWORD}"
   }
   EOF
   
   # Substitute before use
   envsubst < postgres.json > postgres_final.json
   ```

4. **Regular refreshes**: Keep metadata up-to-date
   ```bash
   # Cron job for daily refresh
   0 2 * * * dremio source refresh abc-123
   ```

## Error Handling

### Connection Test Failed

```bash
$ dremio source test-connection --config-file postgres.json
✗ Connection test failed
  Error: Connection refused
```

**Solution**: Check hostname, port, and network access:
```bash
# Test connectivity
telnet postgres.company.com 5432

# Check credentials
psql -h postgres.company.com -U dremio_user -d analytics
```

### Source Already Exists

```bash
$ dremio source create --name MyDB --type POSTGRES --config-file config.json
Error: Source with name 'MyDB' already exists
```

**Solution**: Use a different name or update existing source:
```bash
# Get existing source ID
SOURCE_ID=$(dremio --output json source list | jq -r '.[] | select(.path[0] == "MyDB") | .id')

# Update instead
dremio source update $SOURCE_ID --config-file config.json
```

### Invalid Configuration

```bash
$ dremio source create --name MyS3 --type S3 --config-file s3.json
Error: Invalid configuration: missing required field 'accessKey'
```

**Solution**: Verify configuration format:
```bash
# Check required fields for source type
cat s3.json | jq '.'
```

## Platform Differences

### Software
- Full source management support
- All source types available
- Local file sources supported

### Cloud
- Managed sources (some types)
- Cloud-native sources (S3, Azure, GCS)
- Some source types may be restricted

## Best Practices

1. **Test connections**: Always test before creating
2. **Secure credentials**: Use secrets management
3. **Regular refreshes**: Keep metadata current
4. **Monitor health**: Check source status regularly
5. **Version control configs**: Track configuration changes
6. **Document sources**: Add wiki documentation
7. **Tag sources**: Organize with tags
8. **Backup configs**: Export source configurations

## Source Types Reference

### Databases
- `POSTGRES` - PostgreSQL
- `MYSQL` - MySQL
- `ORACLE` - Oracle Database
- `MSSQL` - Microsoft SQL Server
- `MONGO` - MongoDB

### Object Storage
- `S3` - Amazon S3
- `ADLS` - Azure Data Lake Storage
- `GCS` - Google Cloud Storage

### Data Lakes
- `HIVE` - Apache Hive
- `ICEBERG` - Apache Iceberg
- `DELTALAKE` - Delta Lake

### Cloud Warehouses
- `SNOWFLAKE` - Snowflake
- `REDSHIFT` - Amazon Redshift
- `BIGQUERY` - Google BigQuery

## Advanced Usage

### Dynamic Configuration

```bash
#!/bin/bash
# generate_source_config.sh

# Generate config from environment
cat > source.json <<EOF
{
  "hostname": "${DB_HOST}",
  "port": ${DB_PORT},
  "databaseName": "${DB_NAME}",
  "username": "${DB_USER}",
  "password": "${DB_PASSWORD}",
  "authenticationType": "MASTER"
}
EOF

# Create source
dremio source create --name "$SOURCE_NAME" --type POSTGRES --config-file source.json

# Clean up
rm source.json
```

### Source Monitoring

```bash
#!/bin/bash
# monitor_sources.sh

while true; do
  # Check each source
  dremio --output json source list | jq -r '.[].id' | while read id; do
    # Try to get source
    if ! dremio source get $id >/dev/null 2>&1; then
      echo "Alert: Source $id is unavailable"
      # Send notification
    fi
  done
  
  sleep 300  # Check every 5 minutes
done
```

## Summary

- **List**: View all configured sources
- **Get**: Retrieve source details
- **Create**: Add new data sources
- **Update**: Modify source configuration
- **Refresh**: Update metadata
- **Delete**: Remove sources
- **Test**: Validate configuration before creating

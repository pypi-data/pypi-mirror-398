# Table Operations

This guide covers table operations for managing physical datasets in Dremio.

## Overview

**Table Operations** allow you to promote datasets to physical datasets (tables), configure file formats, and update table metadata.

## Commands

### Promote Dataset

Promote a dataset to a physical dataset (table).

```bash
dremio table promote <DATASET_ID>
```

**Arguments:**
- `DATASET_ID` - The dataset ID (UUID)

**Examples:**

```bash
# Promote a dataset to table
dremio table promote abc-123-def-456
```

### Configure Format

Configure the file format for a physical dataset.

```bash
dremio table format <DATASET_ID> --type <FORMAT> [--from-file <FILE>]
```

**Arguments:**
- `DATASET_ID` - The dataset ID (UUID)

**Options:**
- `--type` - Format type: CSV, JSON, Parquet, etc. (required)
- `--from-file` - Load format configuration from JSON file

**Examples:**

```bash
# Set CSV format
dremio table format abc-123 --type CSV

# Set format with configuration file
dremio table format abc-123 --type CSV --from-file csv_format.json

# Set JSON format
dremio table format abc-123 --type JSON
```

### Update Table

Update table metadata.

```bash
dremio table update <DATASET_ID> --from-file <FILE>
```

**Arguments:**
- `DATASET_ID` - The dataset ID (UUID)

**Options:**
- `--from-file` - Updated table JSON file (required)

**Examples:**

```bash
# Update table metadata
dremio table update abc-123 --from-file updated_table.json
```

## Format Configuration Examples

### CSV Format

```json
{
  "type": "CSV",
  "fieldDelimiter": ",",
  "lineDelimiter": "\n",
  "quote": "\"",
  "escape": "\\",
  "skipFirstLine": true,
  "extractHeader": true
}
```

### JSON Format

```json
{
  "type": "JSON"
}
```

### Parquet Format

```json
{
  "type": "Parquet",
  "autoCorrectCorruptDates": true
}
```

## Scenarios

### Promoting and Configuring a CSV File

```bash
# 1. Get dataset ID
DATASET_ID=$(dremio --output json catalog get-by-path "MySource.data.customers.csv" | jq -r '.id')

# 2. Promote to table
dremio table promote $DATASET_ID

# 3. Configure CSV format
cat > csv_format.json <<EOF
{
  "type": "CSV",
  "fieldDelimiter": ",",
  "skipFirstLine": true,
  "extractHeader": true
}
EOF

dremio table format $DATASET_ID --type CSV --from-file csv_format.json
```

### Working with JSON Files

```bash
# Get JSON file dataset
DATASET_ID=$(dremio --output json catalog get-by-path "MySource.data.events.json" | jq -r '.id')

# Promote and set format
dremio table promote $DATASET_ID
dremio table format $DATASET_ID --type JSON
```

## Common Workflows

### 1. Bulk Dataset Promotion

```bash
#!/bin/bash
# promote_all_csv.sh - Promote all CSV files in a source

SOURCE="MySource"

# Find all CSV files
dremio --output json catalog list | jq -r ".data[] | select(.path[0] == \"$SOURCE\" and (.path[-1] | endswith(\".csv\"))) | .id" | while read dataset_id; do
  echo "Promoting: $dataset_id"
  dremio table promote $dataset_id
  dremio table format $dataset_id --type CSV --from-file csv_format.json
done
```

### 2. Format Configuration Templates

```bash
#!/bin/bash
# apply_format.sh - Apply format template

DATASET_ID=$1
FORMAT_TYPE=$2

case $FORMAT_TYPE in
  csv)
    cat > format.json <<EOF
{
  "type": "CSV",
  "fieldDelimiter": ",",
  "skipFirstLine": true,
  "extractHeader": true
}
EOF
    ;;
  tsv)
    cat > format.json <<EOF
{
  "type": "CSV",
  "fieldDelimiter": "\t",
  "skipFirstLine": true,
  "extractHeader": true
}
EOF
    ;;
  json)
    cat > format.json <<EOF
{
  "type": "JSON"
}
EOF
    ;;
esac

dremio table format $DATASET_ID --type ${FORMAT_TYPE^^} --from-file format.json
rm format.json
```

## Tips

1. **Promote before formatting**: Always promote datasets before configuring format
   ```bash
   dremio table promote $ID
   dremio table format $ID --type CSV
   ```

2. **Test format settings**: Verify format with a query
   ```bash
   dremio sql execute "SELECT * FROM dataset LIMIT 10"
   ```

3. **Use format files**: Store format configurations for reuse
   ```bash
   dremio table format $ID --type CSV --from-file standard_csv.json
   ```

## Error Handling

### Dataset Already Promoted

```bash
$ dremio table promote abc-123
Error: Dataset is already a physical dataset
```

**Solution**: Skip promotion, proceed with format configuration.

### Invalid Format Configuration

```bash
$ dremio table format abc-123 --type CSV --from-file bad_format.json
Error: Invalid format configuration
```

**Solution**: Verify JSON format and required fields.

## Platform Differences

### Software
- Full table operations support
- All format types available
- Promotion and format configuration

### Cloud
- Table operations available
- Format types may vary
- Project-scoped operations

## Best Practices

1. **Promote systematically**: Promote datasets as part of source setup
2. **Document formats**: Keep format configurations in version control
3. **Test configurations**: Verify format settings with sample queries
4. **Use templates**: Standardize format configurations
5. **Automate promotion**: Script bulk dataset promotion

## Format Types Reference

- **CSV** - Comma-separated values
- **TSV** - Tab-separated values
- **JSON** - JSON documents
- **Parquet** - Columnar format
- **Avro** - Row-based format
- **Excel** - Excel spreadsheets

## Summary

- **Promote**: Convert datasets to physical datasets
- **Format**: Configure file format settings
- **Update**: Modify table metadata
- **Automate**: Use scripts for bulk operations
- **Test**: Verify format with queries

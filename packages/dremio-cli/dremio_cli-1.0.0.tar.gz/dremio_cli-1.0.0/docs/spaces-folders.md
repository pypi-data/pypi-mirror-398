# Space and Folder Management

This guide covers space and folder management operations for organizing your Dremio catalog.

## Overview

**Spaces** and **Folders** are containers for organizing your data:

- **Cloud**: Spaces are top-level folders in the project catalog
- **Software**: Spaces are traditional SPACE containers, folders are FOLDER containers

The CLI handles these differences transparently.

## Space Commands

### Create Space

Create a new space.

```bash
dremio space create --name <NAME> [OPTIONS]
```

**Options:**
- `--name TEXT` - Space name (required)
- `--description TEXT` - Space description

**Examples:**

```bash
# Create simple space
dremio space create --name "Analytics"

# Create with description
dremio space create --name "Sales" --description "Sales data and reports"

# Cloud: Creates top-level folder
dremio --profile cloud space create --name "Marketing"

# Software: Creates traditional SPACE
dremio --profile software space create --name "DataScience"
```

### List Spaces

List all spaces.

```bash
dremio space list
```

**Examples:**

```bash
# List all spaces
dremio space list

# JSON output
dremio --output json space list

# YAML output
dremio --output yaml space list
```

### Get Space

Retrieve space details by ID.

```bash
dremio space get <SPACE_ID>
```

**Arguments:**
- `SPACE_ID` - The space ID (UUID)

**Examples:**

```bash
# Get space details
dremio space get 66c76a3e-0335-463b-8622-1720f8546537

# Get in JSON format
dremio --output json space get 66c76a3e-0335-463b-8622-1720f8546537
```

### Delete Space

Delete a space.

```bash
dremio space delete <SPACE_ID> [OPTIONS]
```

**Arguments:**
- `SPACE_ID` - The space ID (UUID)

**Options:**
- `--tag TEXT` - Version tag for optimistic concurrency control

**Examples:**

```bash
# Delete space (with confirmation)
dremio space delete 66c76a3e-0335-463b-8622-1720f8546537

# Delete without confirmation
dremio space delete 66c76a3e-0335-463b-8622-1720f8546537 --yes

# Delete with specific tag
dremio space delete 66c76a3e-0335-463b-8622-1720f8546537 --tag "version-tag-123"
```

## Folder Commands

### Create Folder

Create a new folder.

```bash
dremio folder create --path <PATH> [OPTIONS]
```

**Options:**
- `--path TEXT` - Folder path as JSON array or slash-separated (required)
- `--description TEXT` - Folder description

**Examples:**

```bash
# Create folder with slash-separated path
dremio folder create --path "Analytics/Reports"

# Create with JSON array path
dremio folder create --path '["Analytics", "Reports", "2024"]'

# Create with description
dremio folder create --path "Sales/Data" --description "Sales data folder"

# Create nested folders
dremio folder create --path "Analytics/Reports/Monthly"
dremio folder create --path "Analytics/Reports/Quarterly"
```

### List Folders

List folders.

```bash
dremio folder list [OPTIONS]
```

**Options:**
- `--parent TEXT` - Parent folder/space ID or path

**Examples:**

```bash
# List all folders
dremio folder list

# List folders in specific parent
dremio folder list --parent "Analytics"

# List by parent ID
dremio folder list --parent abc-123-def-456

# JSON output
dremio --output json folder list
```

### Get Folder

Retrieve folder details by ID.

```bash
dremio folder get <FOLDER_ID>
```

**Arguments:**
- `FOLDER_ID` - The folder ID (UUID)

**Examples:**

```bash
# Get folder details
dremio folder get 116f8103-159d-4640-b64a-68469bcb21b1

# Get in JSON format
dremio --output json folder get 116f8103-159d-4640-b64a-68469bcb21b1
```

### Get Folder by Path

Retrieve folder details by path.

```bash
dremio folder get-by-path <PATH>
```

**Arguments:**
- `PATH` - The folder path (dot-separated or slash-separated)

**Examples:**

```bash
# Get by slash-separated path
dremio folder get-by-path "Analytics/Reports"

# Get by dot-separated path
dremio folder get-by-path "Analytics.Reports.Monthly"

# Get by JSON array path
dremio folder get-by-path '["Analytics", "Reports", "2024"]'
```

### Delete Folder

Delete a folder.

```bash
dremio folder delete <FOLDER_ID> [OPTIONS]
```

**Arguments:**
- `FOLDER_ID` - The folder ID (UUID)

**Options:**
- `--tag TEXT` - Version tag for optimistic concurrency control

**Examples:**

```bash
# Delete folder (with confirmation)
dremio folder delete 116f8103-159d-4640-b64a-68469bcb21b1

# Delete without confirmation
dremio folder delete 116f8103-159d-4640-b64a-68469bcb21b1 --yes
```

## Scenarios

### Creating an Organized Catalog

```bash
# 1. Create top-level spaces
dremio space create --name "Raw" --description "Raw data from sources"
dremio space create --name "Curated" --description "Cleaned and transformed data"
dremio space create --name "Analytics" --description "Business analytics views"

# 2. Create folder structure in Raw
dremio folder create --path "Raw/Customers"
dremio folder create --path "Raw/Orders"
dremio folder create --path "Raw/Products"

# 3. Create folder structure in Curated
dremio folder create --path "Curated/Dimensions"
dremio folder create --path "Curated/Facts"

# 4. Create folder structure in Analytics
dremio folder create --path "Analytics/Sales"
dremio folder create --path "Analytics/Marketing"
dremio folder create --path "Analytics/Finance"
```

### Medallion Architecture

```bash
# Bronze layer (raw data)
dremio space create --name "Bronze" --description "Raw data ingestion"
dremio folder create --path "Bronze/source_system_1"
dremio folder create --path "Bronze/source_system_2"

# Silver layer (cleaned data)
dremio space create --name "Silver" --description "Cleaned and validated data"
dremio folder create --path "Silver/customers"
dremio folder create --path "Silver/orders"
dremio folder create --path "Silver/products"

# Gold layer (business aggregates)
dremio space create --name "Gold" --description "Business-ready datasets"
dremio folder create --path "Gold/customer_360"
dremio folder create --path "Gold/sales_metrics"
dremio folder create --path "Gold/inventory_status"
```

### Department-Based Organization

```bash
# Create department spaces
dremio space create --name "Sales" --description "Sales department data"
dremio space create --name "Marketing" --description "Marketing department data"
dremio space create --name "Finance" --description "Finance department data"

# Create project folders within departments
dremio folder create --path "Sales/Q1_2024"
dremio folder create --path "Sales/Q2_2024"
dremio folder create --path "Marketing/Campaigns"
dremio folder create --path "Marketing/Analytics"
dremio folder create --path "Finance/Reports"
dremio folder create --path "Finance/Forecasts"
```

### Migration and Cleanup

```bash
# List all spaces
dremio --output json space list > spaces.json

# List all folders
dremio --output json folder list > folders.json

# Find empty folders
cat folders.json | jq '.[] | select(.datasetCount == 0)'

# Delete empty folders
for folder_id in $(cat folders.json | jq -r '.[] | select(.datasetCount == 0) | .id'); do
  dremio folder delete $folder_id --yes
done
```

## Common Workflows

### 1. Create Hierarchical Structure

```bash
# Create parent space
dremio space create --name "DataWarehouse"

# Create level 1 folders
dremio folder create --path "DataWarehouse/Staging"
dremio folder create --path "DataWarehouse/Production"

# Create level 2 folders
dremio folder create --path "DataWarehouse/Staging/Daily"
dremio folder create --path "DataWarehouse/Staging/Weekly"
dremio folder create --path "DataWarehouse/Production/Current"
dremio folder create --path "DataWarehouse/Production/Archive"

# Create level 3 folders
dremio folder create --path "DataWarehouse/Production/Current/2024"
dremio folder create --path "DataWarehouse/Production/Current/2023"
```

### 2. Batch Folder Creation

```bash
# Create folders from list
FOLDERS=(
  "Analytics/Reports/Daily"
  "Analytics/Reports/Weekly"
  "Analytics/Reports/Monthly"
  "Analytics/Dashboards/Executive"
  "Analytics/Dashboards/Operational"
)

for folder in "${FOLDERS[@]}"; do
  dremio folder create --path "$folder"
done
```

### 3. Folder Inventory

```bash
# Export folder structure
dremio --output json folder list > folder_inventory.json

# Generate tree view
cat folder_inventory.json | jq -r '.[] | .path | join("/")' | sort

# Count folders by parent
cat folder_inventory.json | jq -r '.[] | .path[0]' | sort | uniq -c
```

### 4. Space and Folder Cleanup

```bash
# Get space ID
SPACE_ID=$(dremio --output json space list | jq -r '.[] | select(.path[0] == "OldSpace") | .id')

# List all folders in space
dremio --output json folder list --parent $SPACE_ID > space_folders.json

# Delete all folders (bottom-up)
cat space_folders.json | jq -r '.[] | .id' | tac | while read folder_id; do
  dremio folder delete $folder_id --yes
done

# Delete space
dremio space delete $SPACE_ID --yes
```

## Tips

1. **Plan your structure**: Design folder hierarchy before creating
   ```
   Space/
   ├── Category1/
   │   ├── Subcategory1/
   │   └── Subcategory2/
   └── Category2/
   ```

2. **Use consistent naming**: Follow naming conventions
   ```bash
   dremio space create --name "analytics"  # lowercase
   dremio folder create --path "analytics/reports"  # lowercase
   ```

3. **Document structure**: Keep a README or diagram
   ```bash
   dremio --output json folder list | jq -r '.[] | .path | join("/")' > structure.txt
   ```

4. **Clean up regularly**: Remove unused folders
   ```bash
   dremio folder list | grep "old_"
   ```

## Error Handling

### Space Already Exists

```bash
$ dremio space create --name "Analytics"
Error: Space already exists
```

**Solution**: Use a different name or delete existing space.

### Parent Not Found

```bash
$ dremio folder create --path "NonExistent/folder"
Error: Parent path does not exist
```

**Solution**: Create parent first:
```bash
dremio space create --name "NonExistent"
dremio folder create --path "NonExistent/folder"
```

### Cannot Delete Non-Empty

```bash
$ dremio space delete abc-123
Error: Cannot delete non-empty space
```

**Solution**: Delete contents first:
```bash
# Delete all folders in space
dremio folder list --parent abc-123
# Delete each folder, then delete space
```

## Platform Differences

### Cloud
- Spaces are top-level folders
- Path: `source.namespace.folder`
- Example: `evangelism-2026.Analytics.Reports`

### Software
- Spaces are SPACE containers
- Folders are FOLDER containers
- Path: `space.folder` or `catalog.namespace.folder`
- Example: `Analytics.Reports` or `dremio-catalog.namespace.folder`

## Best Practices

1. **Organize by purpose**: Group related data together
2. **Use descriptive names**: Make structure self-documenting
3. **Limit nesting depth**: Keep hierarchy manageable (3-4 levels max)
4. **Document structure**: Maintain documentation of organization
5. **Regular cleanup**: Remove unused spaces and folders
6. **Consistent naming**: Follow naming conventions
7. **Plan for growth**: Design scalable structure
8. **Use folders for projects**: Separate temporary from permanent data

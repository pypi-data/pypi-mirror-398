# Tag and Wiki Management

This guide covers tag and wiki management for documenting and organizing catalog objects in Dremio.

## Overview

**Tags** and **Wiki** provide collaboration features:

- **Tags**: Labels for categorizing and organizing datasets (views and tables only)
- **Wiki**: Markdown documentation for any catalog object

## Tag Commands

### Set Tags

Set tags on a catalog object (views and tables only).

```bash
dremio tag set <CATALOG_ID> --tags <TAGS>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--tags TEXT` - Comma-separated list of tags (required)

**Examples:**

```bash
# Set single tag
dremio tag set abc-123 --tags analytics

# Set multiple tags
dremio tag set abc-123 --tags analytics,production,sensitive

# Set tags with spaces
dremio tag set abc-123 --tags "customer data,pii,gdpr compliant"
```

### Get Tags

Retrieve tags from a catalog object.

```bash
dremio tag get <CATALOG_ID>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Examples:**

```bash
# Get tags
dremio tag get abc-123

# Get in JSON format
dremio --output json tag get abc-123
```

### Delete Tags

Remove all tags from a catalog object.

```bash
dremio tag delete <CATALOG_ID>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Examples:**

```bash
# Delete tags (with confirmation)
dremio tag delete abc-123

# Delete without confirmation
dremio tag delete abc-123 --yes
```

## Wiki Commands

### Set Wiki

Set wiki documentation on a catalog object.

```bash
dremio wiki set <CATALOG_ID> --text <TEXT>
dremio wiki set <CATALOG_ID> --file <FILE>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--text TEXT` - Wiki markdown text
- `--file PATH` - Load wiki from file

**Examples:**

```bash
# Set wiki with inline text
dremio wiki set abc-123 --text "# My Dataset\n\nThis dataset contains customer information."

# Set wiki from file
dremio wiki set abc-123 --file README.md

# Set comprehensive wiki
cat > dataset_wiki.md <<EOF
# Customer Dataset

## Overview
This dataset contains customer information for analytics.

## Schema
- id: Customer ID
- name: Customer name
- email: Customer email
- region: Geographic region

## Usage
Use this dataset for customer segmentation and analysis.

## Owners
- Data Team: data@company.com
EOF

dremio wiki set abc-123 --file dataset_wiki.md
```

### Get Wiki

Retrieve wiki documentation from a catalog object.

```bash
dremio wiki get <CATALOG_ID> [OPTIONS]
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--output-file PATH` - Save wiki to file

**Examples:**

```bash
# Get wiki
dremio wiki get abc-123

# Save wiki to file
dremio wiki get abc-123 --output-file README.md

# Get in JSON format
dremio --output json wiki get abc-123
```

### Delete Wiki

Remove wiki documentation from a catalog object.

```bash
dremio wiki delete <CATALOG_ID>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Examples:**

```bash
# Delete wiki (with confirmation)
dremio wiki delete abc-123

# Delete without confirmation
dremio wiki delete abc-123 --yes
```

## Scenarios

### Documenting a View

```bash
# 1. Create a view
dremio view create --path "Analytics.customer_summary" --sql "SELECT * FROM customers"

# 2. Get view ID
VIEW_ID=$(dremio --output json view get-by-path "Analytics.customer_summary" | jq -r '.id')

# 3. Add tags
dremio tag set $VIEW_ID --tags "analytics,customer-data,production"

# 4. Add wiki documentation
cat > view_docs.md <<EOF
# Customer Summary View

## Purpose
Provides a summary of customer data for analytics dashboards.

## Source
- Base table: customers
- Refresh: Daily at 2 AM UTC

## Columns
- customer_id: Unique identifier
- name: Customer name
- total_orders: Lifetime order count
- total_spent: Lifetime revenue

## Usage Examples
\`\`\`sql
-- Top customers by revenue
SELECT * FROM Analytics.customer_summary 
ORDER BY total_spent DESC 
LIMIT 10
\`\`\`

## Owners
- Analytics Team: analytics@company.com
EOF

dremio wiki set $VIEW_ID --file view_docs.md

# 5. Verify
dremio tag get $VIEW_ID
dremio wiki get $VIEW_ID
```

### Organizing with Tags

```bash
# Tag datasets by environment
dremio tag set dev-view-id --tags development,testing
dremio tag set staging-view-id --tags staging,pre-production
dremio tag set prod-view-id --tags production,critical

# Tag by data classification
dremio tag set customer-view-id --tags pii,sensitive,gdpr
dremio tag set public-view-id --tags public,non-sensitive

# Tag by team ownership
dremio tag set sales-view-id --tags sales-team,revenue
dremio tag set marketing-view-id --tags marketing-team,campaigns
```

### Documentation Workflow

```bash
# 1. Create documentation template
cat > template.md <<EOF
# {DATASET_NAME}

## Overview
{DESCRIPTION}

## Schema
{SCHEMA_INFO}

## Usage
{USAGE_EXAMPLES}

## Owners
{OWNER_INFO}

## Last Updated
{DATE}
EOF

# 2. Fill in template for each dataset
sed "s/{DATASET_NAME}/Customer Data/g; s/{DESCRIPTION}/Customer information/g" template.md > customer_wiki.md

# 3. Apply to datasets
dremio wiki set <customer-view-id> --file customer_wiki.md

# 4. Export all wikis for backup
for id in $(dremio --output json view list | jq -r '.[].id'); do
  dremio wiki get $id --output-file "wikis/${id}.md"
done
```

## Common Workflows

### 1. Data Governance

```bash
# Tag sensitive datasets
SENSITIVE_VIEWS=$(dremio --output json view list | jq -r '.[] | select(.path[] | contains("customer")) | .id')

for view_id in $SENSITIVE_VIEWS; do
  dremio tag set $view_id --tags "pii,sensitive,restricted"
done

# Add compliance documentation
for view_id in $SENSITIVE_VIEWS; do
  dremio wiki set $view_id --text "# Data Classification\n\n**Classification**: Sensitive\n**Compliance**: GDPR, CCPA\n**Access**: Restricted to authorized personnel only"
done
```

### 2. Dataset Catalog

```bash
# Create comprehensive catalog
dremio --output json view list | jq -r '.[] | .id' | while read view_id; do
  # Get view details
  VIEW=$(dremio --output json view get $view_id)
  NAME=$(echo $VIEW | jq -r '.path | join(".")')
  
  # Create documentation
  cat > "catalog/${view_id}.md" <<EOF
# $NAME

## Tags
$(dremio tag get $view_id)

## Wiki
$(dremio wiki get $view_id)

## SQL
\`\`\`sql
$(echo $VIEW | jq -r '.sql')
\`\`\`
EOF
done
```

### 3. Migration Documentation

```bash
# Export tags and wikis before migration
mkdir -p migration/tags migration/wikis

dremio --output json view list | jq -r '.[] | .id' | while read id; do
  dremio --output json tag get $id > "migration/tags/${id}.json"
  dremio wiki get $id --output-file "migration/wikis/${id}.md"
done

# After migration, restore
for id_file in migration/tags/*.json; do
  id=$(basename $id_file .json)
  tags=$(cat $id_file | jq -r '.tags | join(",")')
  dremio tag set $id --tags "$tags"
  dremio wiki set $id --file "migration/wikis/${id}.md"
done
```

## Tips

1. **Use consistent tag naming**: Establish conventions
   ```bash
   # Good: lowercase, hyphenated
   dremio tag set $id --tags "customer-data,production,pii"
   
   # Avoid: mixed case, spaces
   dremio tag set $id --tags "Customer Data,PRODUCTION,PII"
   ```

2. **Document in Markdown**: Use proper formatting
   ```markdown
   # Dataset Name
   
   ## Overview
   Brief description
   
   ## Schema
   | Column | Type | Description |
   |--------|------|-------------|
   | id     | INT  | Primary key |
   
   ## Examples
   \`\`\`sql
   SELECT * FROM dataset LIMIT 10
   \`\`\`
   ```

3. **Version control wikis**: Store in git
   ```bash
   dremio wiki get $id --output-file docs/datasets/my_dataset.md
   git add docs/datasets/my_dataset.md
   git commit -m "Update dataset documentation"
   ```

4. **Automate tagging**: Use scripts for consistency
   ```bash
   # Tag all views in Analytics space
   dremio --output json view list --space Analytics | jq -r '.[].id' | \
     xargs -I {} dremio tag set {} --tags "analytics,production"
   ```

## Important Notes

### Tag Limitations

⚠️ **Tags can only be set on views and tables**, not on:
- Spaces
- Folders
- Sources

Attempting to tag other objects will result in:
```
Error: Labels may only be set on views and tables
```

### Wiki Support

✅ **Wiki can be set on any catalog object**:
- Spaces
- Folders
- Views
- Tables
- Sources

## Error Handling

### Cannot Tag Spaces

```bash
$ dremio tag set space-id --tags analytics
Error: Labels may only be set on views and tables
```

**Solution**: Only tag views and tables:
```bash
# Get view ID instead
VIEW_ID=$(dremio --output json view get-by-path "MySpace.MyView" | jq -r '.id')
dremio tag set $VIEW_ID --tags analytics
```

### Object Not Found

```bash
$ dremio tag get invalid-id
Error: Resource not found
```

**Solution**: Verify the object ID:
```bash
dremio catalog get-by-path "MySpace.MyView"
```

## Platform Differences

### Software
- Full tag and wiki support
- Tags work on views and tables
- Wiki works on all objects

### Cloud
- Full tag and wiki support
- Same limitations as Software
- Project-scoped endpoints

## Best Practices

1. **Establish tagging conventions**: Define standard tags
2. **Document all production datasets**: Add wikis to important views
3. **Use tags for governance**: Mark sensitive data
4. **Version control documentation**: Store wikis in git
5. **Automate tagging**: Script common patterns
6. **Regular audits**: Review and update documentation
7. **Team ownership**: Assign dataset owners in wiki
8. **Include examples**: Add SQL examples in wikis

## Advanced Usage

### Bulk Tagging

```bash
#!/bin/bash
# bulk_tag.sh - Tag multiple datasets

TAG_LIST="analytics,production,verified"

# Tag all views in a space
dremio --output json view list --space Analytics | jq -r '.[].id' | \
while read view_id; do
  echo "Tagging $view_id..."
  dremio tag set $view_id --tags "$TAG_LIST"
done
```

### Documentation Generator

```bash
#!/bin/bash
# generate_docs.sh - Auto-generate documentation

VIEW_ID=$1

# Get view details
VIEW=$(dremio --output json view get $VIEW_ID)
NAME=$(echo $VIEW | jq -r '.path | join(".")')
SQL=$(echo $VIEW | jq -r '.sql')

# Generate wiki
cat > wiki.md <<EOF
# $NAME

## SQL Definition
\`\`\`sql
$SQL
\`\`\`

## Created
$(date)

## Owner
Data Team

## Usage
This view is used for analytics and reporting.
EOF

# Set wiki
dremio wiki set $VIEW_ID --file wiki.md
```

### Tag-Based Search

```bash
# Find all production datasets
dremio --output json view list | jq -r '.[] | .id' | while read id; do
  TAGS=$(dremio --output json tag get $id 2>/dev/null | jq -r '.tags[]' 2>/dev/null)
  if echo "$TAGS" | grep -q "production"; then
    echo "Production dataset: $id"
  fi
done
```

## Summary

- **Tags**: Categorize views and tables
- **Wiki**: Document any catalog object
- **Markdown**: Use rich formatting in wikis
- **Governance**: Use tags for data classification
- **Automation**: Script tagging and documentation
- **Version Control**: Store wikis in git

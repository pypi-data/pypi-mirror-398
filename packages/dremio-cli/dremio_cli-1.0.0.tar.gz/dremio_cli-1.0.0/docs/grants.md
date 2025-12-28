# Grant and Privilege Management

This guide covers grant and privilege management for controlling access to catalog objects in Dremio.

## Overview

**Grants** control who can access catalog objects and what operations they can perform. Grants can be assigned to:

- **Users**: Individual user accounts
- **Roles**: Groups of users with shared permissions

## Privilege Types

Common privileges include:

- `SELECT` - Read data from datasets
- `VIEW_REFLECTION` - View reflection metadata
- `ALTER` - Modify object metadata
- `MODIFY` - Modify object data/structure
- `MANAGE_GRANTS` - Manage permissions on the object
- `READ_METADATA` - Read object metadata
- `CREATE_TABLE` - Create tables in the object
- `DROP` - Delete the object

## Commands

### List Grants

List all grants for a catalog object.

```bash
dremio grant list <CATALOG_ID>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Examples:**

```bash
# List grants for a space
dremio grant list abc-123-def-456

# List in JSON format
dremio --output json grant list abc-123-def-456
```

### Add Grant

Add a grant to a catalog object.

```bash
dremio grant add <CATALOG_ID> --grantee-type <TYPE> --grantee-id <ID> --privileges <PRIVS>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--grantee-type` - Grantee type: `USER` or `ROLE` (required)
- `--grantee-id` - User or role ID (required)
- `--privileges` - Comma-separated privileges (required)

**Examples:**

```bash
# Grant SELECT to a user
dremio grant add abc-123 --grantee-type USER --grantee-id user-456 --privileges SELECT

# Grant multiple privileges to a role
dremio grant add abc-123 --grantee-type ROLE --grantee-id role-789 --privileges SELECT,ALTER,MODIFY

# Grant read-only access
dremio grant add abc-123 --grantee-type USER --grantee-id user-456 --privileges SELECT,VIEW_REFLECTION,READ_METADATA
```

### Remove Grant

Remove a grant from a catalog object.

```bash
dremio grant remove <CATALOG_ID> --grantee-type <TYPE> --grantee-id <ID>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--grantee-type` - Grantee type: `USER` or `ROLE` (required)
- `--grantee-id` - User or role ID (required)

**Examples:**

```bash
# Remove grant from user
dremio grant remove abc-123 --grantee-type USER --grantee-id user-456

# Remove grant from role (with confirmation)
dremio grant remove abc-123 --grantee-type ROLE --grantee-id role-789

# Remove without confirmation
dremio grant remove abc-123 --grantee-type USER --grantee-id user-456 --yes
```

### Set Grants

Set all grants for a catalog object (replaces existing).

```bash
dremio grant set <CATALOG_ID> --from-file <FILE>
```

**Arguments:**
- `CATALOG_ID` - The catalog object ID (UUID)

**Options:**
- `--from-file` - JSON file with complete grants definition (required)

**Examples:**

```bash
# Set grants from file
dremio grant set abc-123 --from-file grants.json
```

## Grant File Format

### Example grants.json

```json
{
  "grants": [
    {
      "granteeType": "USER",
      "granteeId": "user-123",
      "privileges": ["SELECT", "VIEW_REFLECTION"]
    },
    {
      "granteeType": "ROLE",
      "granteeId": "role-456",
      "privileges": ["SELECT", "ALTER", "MODIFY"]
    },
    {
      "granteeType": "ROLE",
      "granteeId": "admin-role",
      "privileges": ["SELECT", "ALTER", "MODIFY", "MANAGE_GRANTS", "DROP"]
    }
  ]
}
```

## Scenarios

### Granting Read Access to a Dataset

```bash
# 1. Get dataset ID
DATASET_ID=$(dremio --output json view get-by-path "Analytics.sales_data" | jq -r '.id')

# 2. Grant SELECT to analyst role
dremio grant add $DATASET_ID --grantee-type ROLE --grantee-id analyst-role --privileges SELECT,VIEW_REFLECTION

# 3. Verify grant
dremio grant list $DATASET_ID
```

### Setting Up Role-Based Access

```bash
# Create grants file for a space
cat > space_grants.json <<EOF
{
  "grants": [
    {
      "granteeType": "ROLE",
      "granteeId": "analyst",
      "privileges": ["SELECT", "VIEW_REFLECTION", "READ_METADATA"]
    },
    {
      "granteeType": "ROLE",
      "granteeId": "data_engineer",
      "privileges": ["SELECT", "ALTER", "MODIFY", "CREATE_TABLE"]
    },
    {
      "granteeType": "ROLE",
      "granteeId": "admin",
      "privileges": ["SELECT", "ALTER", "MODIFY", "MANAGE_GRANTS", "DROP", "CREATE_TABLE"]
    }
  ]
}
EOF

# Apply grants
SPACE_ID=$(dremio --output json space list | jq -r '.[] | select(.path[0] == "Analytics") | .id')
dremio grant set $SPACE_ID --from-file space_grants.json
```

### Migrating Grants

```bash
# Export grants from source
SOURCE_ID=$(dremio --profile source --output json view get-by-path "Analytics.summary" | jq -r '.id')
dremio --profile source --output json grant list $SOURCE_ID > grants_export.json

# Apply to target
TARGET_ID=$(dremio --profile target --output json view get-by-path "Analytics.summary" | jq -r '.id')
dremio --profile target grant set $TARGET_ID --from-file grants_export.json
```

## Common Workflows

### 1. Audit Access

```bash
#!/bin/bash
# audit_access.sh - Audit grants across catalog

# Get all spaces
dremio --output json space list | jq -r '.[].id' | while read space_id; do
  echo "Space: $space_id"
  dremio --output json grant list $space_id | jq '.grants[] | "\(.granteeType): \(.granteeId) - \(.privileges | join(", "))"'
  echo ""
done
```

### 2. Bulk Grant Assignment

```bash
#!/bin/bash
# grant_to_all_views.sh - Grant access to all views in a space

SPACE="Analytics"
ROLE_ID="analyst-role"
PRIVILEGES="SELECT,VIEW_REFLECTION"

# Get all views in space
dremio --output json view list --space $SPACE | jq -r '.[].id' | while read view_id; do
  echo "Granting to view: $view_id"
  dremio grant add $view_id --grantee-type ROLE --grantee-id $ROLE_ID --privileges $PRIVILEGES
done
```

### 3. Remove User Access

```bash
#!/bin/bash
# revoke_user_access.sh - Remove all grants for a user

USER_ID="user-123"

# Find all objects with grants
dremio --output json catalog list | jq -r '.data[].id' | while read object_id; do
  # Check if user has grants
  if dremio --output json grant list $object_id | jq -e ".grants[] | select(.granteeId == \"$USER_ID\")" > /dev/null; then
    echo "Removing grant from: $object_id"
    dremio grant remove $object_id --grantee-type USER --grantee-id $USER_ID --yes
  fi
done
```

### 4. Grant Templates

```bash
#!/bin/bash
# apply_grant_template.sh - Apply standard grant template

TEMPLATE=$1  # read-only, read-write, or admin
OBJECT_ID=$2

case $TEMPLATE in
  read-only)
    cat > grants.json <<EOF
{
  "grants": [
    {
      "granteeType": "ROLE",
      "granteeId": "viewer",
      "privileges": ["SELECT", "VIEW_REFLECTION", "READ_METADATA"]
    }
  ]
}
EOF
    ;;
  read-write)
    cat > grants.json <<EOF
{
  "grants": [
    {
      "granteeType": "ROLE",
      "granteeId": "editor",
      "privileges": ["SELECT", "ALTER", "MODIFY", "CREATE_TABLE"]
    }
  ]
}
EOF
    ;;
  admin)
    cat > grants.json <<EOF
{
  "grants": [
    {
      "granteeType": "ROLE",
      "granteeId": "admin",
      "privileges": ["SELECT", "ALTER", "MODIFY", "MANAGE_GRANTS", "DROP", "CREATE_TABLE"]
    }
  ]
}
EOF
    ;;
esac

dremio grant set $OBJECT_ID --from-file grants.json
rm grants.json
```

## Tips

1. **Use roles over users**: Assign grants to roles for easier management
   ```bash
   dremio grant add $ID --grantee-type ROLE --grantee-id analyst --privileges SELECT
   ```

2. **Principle of least privilege**: Grant minimum necessary permissions
   ```bash
   # Good: specific privileges
   dremio grant add $ID --grantee-type USER --grantee-id user-123 --privileges SELECT
   
   # Avoid: excessive privileges
   dremio grant add $ID --grantee-type USER --grantee-id user-123 --privileges SELECT,ALTER,MODIFY,DROP
   ```

3. **Document grant decisions**: Add wiki documentation
   ```bash
   dremio wiki set $ID --text "# Access Control\n\nAnalyst role has read-only access"
   ```

4. **Regular audits**: Review grants periodically
   ```bash
   # Export current grants for review
   dremio --output json grant list $ID > grants_$(date +%Y%m%d).json
   ```

## Error Handling

### Insufficient Permissions

```bash
$ dremio grant add abc-123 --grantee-type USER --grantee-id user-456 --privileges SELECT
Error: Insufficient permissions to manage grants
```

**Solution**: Ensure you have `MANAGE_GRANTS` privilege on the object.

### Invalid Privilege

```bash
$ dremio grant add abc-123 --grantee-type USER --grantee-id user-456 --privileges INVALID
Error: Invalid privilege: INVALID
```

**Solution**: Use valid privilege names (SELECT, ALTER, MODIFY, etc.).

### Grantee Not Found

```bash
$ dremio grant add abc-123 --grantee-type USER --grantee-id invalid-user --privileges SELECT
Error: User not found: invalid-user
```

**Solution**: Verify the user/role ID exists.

## Platform Differences

### Software
- Full grant management support
- User and role-based grants
- All privilege types available

### Cloud
- Grant management available
- May have different privilege types
- Project-scoped permissions

## Best Practices

1. **Use role-based access control**: Assign grants to roles, not individual users
2. **Least privilege principle**: Grant minimum necessary permissions
3. **Regular audits**: Review and update grants periodically
4. **Document access policies**: Use wiki to document why grants exist
5. **Test before production**: Verify grants in dev/staging first
6. **Backup grants**: Export grant configurations before changes
7. **Automate common patterns**: Use scripts for standard grant templates
8. **Monitor access**: Track who has access to sensitive data

## Privilege Reference

### Data Access
- `SELECT` - Query data
- `VIEW_REFLECTION` - View reflection metadata
- `READ_METADATA` - Read object metadata

### Data Modification
- `ALTER` - Modify metadata
- `MODIFY` - Modify data/structure
- `CREATE_TABLE` - Create tables
- `DROP` - Delete objects

### Administration
- `MANAGE_GRANTS` - Manage permissions
- `OWNERSHIP` - Full control

## Advanced Usage

### Conditional Grants

```bash
#!/bin/bash
# conditional_grants.sh - Grant based on conditions

OBJECT_ID=$1
ENVIRONMENT=$2

if [ "$ENVIRONMENT" == "production" ]; then
  # Production: read-only for most users
  dremio grant add $OBJECT_ID --grantee-type ROLE --grantee-id analyst --privileges SELECT
else
  # Development: read-write
  dremio grant add $OBJECT_ID --grantee-type ROLE --grantee-id analyst --privileges SELECT,ALTER,MODIFY
fi
```

### Grant Inheritance

```bash
#!/bin/bash
# inherit_grants.sh - Apply parent grants to children

PARENT_ID=$1

# Get parent grants
dremio --output json grant list $PARENT_ID > parent_grants.json

# Apply to all children
dremio --output json catalog list | jq -r ".data[] | select(.path[0] == \"$PARENT_NAME\") | .id" | while read child_id; do
  dremio grant set $child_id --from-file parent_grants.json
done
```

### Grant Reporting

```bash
#!/bin/bash
# grant_report.sh - Generate grant report

echo "# Grant Report - $(date)"
echo ""

dremio --output json catalog list | jq -r '.data[] | select(.containerType == "SPACE") | .id' | while read space_id; do
  SPACE_NAME=$(dremio --output json catalog get $space_id | jq -r '.path[0]')
  echo "## Space: $SPACE_NAME"
  echo ""
  
  dremio --output json grant list $space_id | jq -r '.grants[] | "- \(.granteeType): \(.granteeId) - \(.privileges | join(", "))"'
  echo ""
done
```

## Summary

- **List**: View all grants on an object
- **Add**: Grant privileges to users/roles
- **Remove**: Revoke access
- **Set**: Replace all grants with new configuration
- **Use roles**: Simplify management
- **Audit regularly**: Maintain security
- **Document**: Explain access decisions

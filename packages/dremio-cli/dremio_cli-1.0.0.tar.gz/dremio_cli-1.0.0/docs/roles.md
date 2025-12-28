# Role Management

This guide covers role management operations for administering roles and role memberships in Dremio.

## Overview

**Role Management** allows administrators to create roles, assign users to roles, and manage role-based access control. This is primarily available in Dremio Software.

## Commands

### List Roles

```bash
dremio role list
```

### Get Role

```bash
dremio role get <ROLE_ID>
```

### Create Role

```bash
dremio role create --name "Analyst"
dremio role create --from-file role.json
```

### Update Role

```bash
dremio role update <ROLE_ID> --from-file updated_role.json
```

### Delete Role

```bash
dremio role delete <ROLE_ID>
```

### Add Member

```bash
dremio role add-member <ROLE_ID> --user <USER_ID>
```

### Remove Member

```bash
dremio role remove-member <ROLE_ID> --user <USER_ID>
```

## Examples

```bash
# List all roles
dremio role list

# Create role
dremio role create --name "Data Analyst"

# Add user to role
dremio role add-member role-123 --user user-456

# Remove user from role
dremio role remove-member role-123 --user user-456

# Delete role
dremio role delete role-123
```

## Role File Format

```json
{
  "name": "Data Analyst",
  "description": "Analysts with read access to datasets"
}
```

## Workflows

### Role-Based Access Control

```bash
# 1. Create roles
dremio role create --name "Analyst"
dremio role create --name "Engineer"

# 2. Add users to roles
dremio role add-member analyst-role-id --user user-1
dremio role add-member engineer-role-id --user user-2

# 3. Grant permissions to roles
dremio grant add dataset-id --grantee-type ROLE --grantee-id analyst-role-id --privileges SELECT
dremio grant add dataset-id --grantee-type ROLE --grantee-id engineer-role-id --privileges SELECT,ALTER,MODIFY
```

## Notes

- Role management requires administrative privileges
- Primarily available in Dremio Software
- Cloud has different role management (via cloud console)
- Use roles with grant management for access control

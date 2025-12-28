# User Management

This guide covers user management operations for administering user accounts in Dremio.

## Overview

**User Management** allows administrators to create, update, and manage user accounts. This is primarily available in Dremio Software.

## Commands

### List Users

```bash
dremio user list
```

### Get User

```bash
dremio user get <USER_ID>
```

### Create User

```bash
dremio user create --name "John Doe" --email john@company.com [--username john] [--password secret]
dremio user create --from-file user.json
```

### Update User

```bash
dremio user update <USER_ID> --from-file updated_user.json
```

### Delete User

```bash
dremio user delete <USER_ID>
```

## Examples

```bash
# List all users
dremio user list

# Create user
dremio user create --name "Jane Analyst" --email jane@company.com

# Get user details
dremio user get user-123

# Delete user
dremio user delete user-123
```

## User File Format

```json
{
  "name": "John Doe",
  "email": "john@company.com",
  "userName": "john",
  "password": "initial_password"
}
```

## Notes

- User management requires administrative privileges
- Primarily available in Dremio Software
- Cloud has different user management (via cloud console)

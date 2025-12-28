# Quick Start Guide

## 1. Create Your First Profile

### For Dremio Cloud

```bash
dremio profile create production \
  --type cloud \
  --base-url https://api.dremio.cloud/v0 \
  --project-id your-project-id \
  --auth-type pat \
  --token your-personal-access-token
```

### For Dremio Software

```bash
dremio profile create local \
  --type software \
  --base-url http://localhost:9047/api/v3 \
  --auth-type username_password \
  --username dremio \
  --password dremio123
```

## 2. Verify Your Profile

```bash
# List all profiles
dremio profile list

# Show current profile
dremio profile current
```

## 3. Run Your First Commands

### List Catalog

```bash
dremio catalog list
```

### Execute SQL

```bash
dremio sql execute "SELECT * FROM MySource.MyTable LIMIT 10"
```

### List Sources

```bash
dremio source list
```

## 4. Try Interactive Mode

```bash
dremio repl
```

In REPL mode, you can run commands without the `dremio` prefix:

```
dremio> catalog list
dremio> sql execute "SELECT COUNT(*) FROM MyTable"
dremio> exit
```

## 5. Explore More Commands

```bash
# Get help for any command
dremio --help
dremio catalog --help
dremio source --help

# Use different output formats
dremio catalog list --output json
dremio catalog list --output yaml
```

## Next Steps

- Browse the [Command Reference](commands/) for detailed documentation
- Check out [Examples](examples/) for common use cases
- Learn about [Profile Management](commands/profile.md)

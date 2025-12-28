# View Management

This guide covers view management operations including creating, updating, and managing virtual datasets (views) in Dremio.

## Commands

### Create View

Create a new view with a SQL query.

```bash
dremio view create --path <PATH> --sql <SQL> [OPTIONS]
dremio view create --from-file <FILE>
```

**Options:**
- `--path TEXT` - View path as JSON array or dot-separated (required unless using `--from-file`)
- `--sql TEXT` - SQL query for the view
- `--from-file PATH` - Load view definition from JSON file

**Examples:**

```bash
# Create simple view
dremio view create \
  --path '["MySpace", "MyView"]' \
  --sql "SELECT * FROM customers WHERE active = true"

# Create with dot-separated path
dremio view create \
  --path "Analytics.active_customers" \
  --sql "SELECT * FROM customers WHERE active = true"

# Create from file
cat > view.json <<EOF
{
  "entityType": "dataset",
  "type": "VIRTUAL_DATASET",
  "path": ["Analytics", "monthly_sales"],
  "sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as total FROM orders GROUP BY 1"
}
EOF
dremio view create --from-file view.json

# Create complex view
dremio view create \
  --path "Reports.customer_summary" \
  --sql "SELECT c.id, c.name, COUNT(o.id) as order_count, SUM(o.amount) as total_spent FROM customers c LEFT JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name"
```

### Get View

Retrieve view details by ID.

```bash
dremio view get <VIEW_ID> [OPTIONS]
```

**Arguments:**
- `VIEW_ID` - The view ID (UUID)

**Options:**
- `--include TEXT` - Include additional fields (e.g., `sql`, `permissions`)

**Examples:**

```bash
# Get view details
dremio view get 4cc92138-34e8-4c84-ad03-abfb23b6d5f3

# Get view with SQL
dremio view get 4cc92138-34e8-4c84-ad03-abfb23b6d5f3 --include sql

# Get in JSON format
dremio --output json view get 4cc92138-34e8-4c84-ad03-abfb23b6d5f3
```

### Get View by Path

Retrieve view details by path.

```bash
dremio view get-by-path <PATH> [OPTIONS]
```

**Arguments:**
- `PATH` - The view path (dot-separated or slash-separated)

**Options:**
- `--include TEXT` - Include additional fields

**Examples:**

```bash
# Get by dot-separated path
dremio view get-by-path "Analytics.monthly_sales"

# Get by slash-separated path
dremio view get-by-path "Analytics/Reports/summary"

# Get with SQL definition
dremio view get-by-path "Analytics.monthly_sales" --include sql
```

### Update View

Update an existing view's SQL or definition.

```bash
dremio view update <VIEW_ID> --sql <SQL>
dremio view update <VIEW_ID> --from-file <FILE>
```

**Arguments:**
- `VIEW_ID` - The view ID (UUID)

**Options:**
- `--sql TEXT` - New SQL query for the view
- `--from-file PATH` - Load updated definition from JSON file

**Examples:**

```bash
# Update view SQL
dremio view update 4cc92138-34e8-4c84-ad03-abfb23b6d5f3 \
  --sql "SELECT * FROM customers WHERE active = true AND created_at > '2024-01-01'"

# Update from file
cat > updated_view.json <<EOF
{
  "entityType": "dataset",
  "type": "VIRTUAL_DATASET",
  "id": "4cc92138-34e8-4c84-ad03-abfb23b6d5f3",
  "path": ["Analytics", "monthly_sales"],
  "sql": "SELECT DATE_TRUNC('month', order_date) as month, SUM(amount) as total, COUNT(*) as count FROM orders GROUP BY 1"
}
EOF
dremio view update 4cc92138-34e8-4c84-ad03-abfb23b6d5f3 --from-file updated_view.json
```

### Delete View

Delete a view.

```bash
dremio view delete <VIEW_ID> [OPTIONS]
```

**Arguments:**
- `VIEW_ID` - The view ID (UUID)

**Options:**
- `--tag TEXT` - Version tag for optimistic concurrency control

**Examples:**

```bash
# Delete view (with confirmation)
dremio view delete 4cc92138-34e8-4c84-ad03-abfb23b6d5f3

# Delete without confirmation
dremio view delete 4cc92138-34e8-4c84-ad03-abfb23b6d5f3 --yes

# Delete with specific tag
dremio view delete 4cc92138-34e8-4c84-ad03-abfb23b6d5f3 --tag "version-tag-123"
```

### List Views

List all views in the catalog.

```bash
dremio view list [OPTIONS]
```

**Options:**
- `--space TEXT` - Filter views by space name

**Examples:**

```bash
# List all views
dremio view list

# List views in specific space
dremio view list --space Analytics

# List in JSON format
dremio --output json view list
```

## Scenarios

### Creating a Data Mart

```bash
# 1. Create base views
dremio view create \
  --path "DataMart.dim_customers" \
  --sql "SELECT id, name, email, created_at FROM raw.customers"

dremio view create \
  --path "DataMart.dim_products" \
  --sql "SELECT id, name, category, price FROM raw.products"

dremio view create \
  --path "DataMart.fact_orders" \
  --sql "SELECT id, customer_id, product_id, amount, order_date FROM raw.orders"

# 2. Create summary view
dremio view create \
  --path "DataMart.sales_summary" \
  --sql "SELECT c.name as customer, p.name as product, SUM(o.amount) as total FROM DataMart.fact_orders o JOIN DataMart.dim_customers c ON o.customer_id = c.id JOIN DataMart.dim_products p ON o.product_id = p.id GROUP BY 1, 2"
```

### Iterative View Development

```bash
# 1. Create initial view
dremio view create \
  --path "Analytics.sales" \
  --sql "SELECT * FROM orders"

# 2. Test the view
dremio sql execute "SELECT * FROM Analytics.sales LIMIT 10"

# 3. Get view ID
VIEW_ID=$(dremio --output json view get-by-path "Analytics.sales" | jq -r '.id')

# 4. Update with filters
dremio view update $VIEW_ID \
  --sql "SELECT * FROM orders WHERE order_date >= '2024-01-01'"

# 5. Test again
dremio sql execute "SELECT COUNT(*) FROM Analytics.sales"

# 6. Add aggregations
dremio view update $VIEW_ID \
  --sql "SELECT DATE_TRUNC('day', order_date) as day, SUM(amount) as total FROM orders WHERE order_date >= '2024-01-01' GROUP BY 1"
```

### View Migration

```bash
# 1. Export view from source
dremio --profile source --output json view get-by-path "Analytics.summary" > view_export.json

# 2. Modify for target environment
cat view_export.json | jq '.path = ["NewAnalytics", "summary"]' > view_import.json

# 3. Create in target
dremio --profile target view create --from-file view_import.json
```

### View Documentation

```bash
# Export all views with SQL
dremio --output json view list | jq '.[] | {path: .path, sql: .sql}' > view_documentation.json

# Generate markdown documentation
cat view_documentation.json | jq -r '.[] | "## \(.path | join("."))\n\n```sql\n\(.sql)\n```\n"' > views.md
```

## Common Workflows

### 1. Create View Hierarchy

```bash
# Level 1: Raw data views
dremio view create --path "Bronze.customers" --sql "SELECT * FROM source.customers"
dremio view create --path "Bronze.orders" --sql "SELECT * FROM source.orders"

# Level 2: Cleaned data views
dremio view create --path "Silver.customers" --sql "SELECT id, TRIM(name) as name, LOWER(email) as email FROM Bronze.customers WHERE id IS NOT NULL"

# Level 3: Business logic views
dremio view create --path "Gold.customer_metrics" --sql "SELECT c.id, c.name, COUNT(o.id) as order_count, SUM(o.amount) as lifetime_value FROM Silver.customers c LEFT JOIN Bronze.orders o ON c.id = o.customer_id GROUP BY c.id, c.name"
```

### 2. View Versioning

```bash
# Create v1
dremio view create --path "Analytics.metrics_v1" --sql "SELECT * FROM data"

# Create v2 with improvements
dremio view create --path "Analytics.metrics_v2" --sql "SELECT *, additional_field FROM data"

# Update production view to v2
VIEW_ID=$(dremio --output json view get-by-path "Analytics.metrics" | jq -r '.id')
dremio view update $VIEW_ID --sql "SELECT * FROM Analytics.metrics_v2"
```

### 3. View Testing

```bash
# Create test view
dremio view create --path "Testing.new_metric" --sql "SELECT customer_id, SUM(amount) as total FROM orders GROUP BY customer_id"

# Test with sample data
dremio sql execute "SELECT * FROM Testing.new_metric LIMIT 10"

# Validate results
dremio sql execute "SELECT COUNT(*), SUM(total) FROM Testing.new_metric"

# Promote to production
dremio view create --path "Production.customer_totals" --sql "SELECT customer_id, SUM(amount) as total FROM orders GROUP BY customer_id"

# Delete test view
VIEW_ID=$(dremio --output json view get-by-path "Testing.new_metric" | jq -r '.id')
dremio view delete $VIEW_ID --yes
```

## Tips

1. **Use meaningful names**: Make view paths descriptive
   ```bash
   dremio view create --path "Analytics.monthly_revenue_by_region" --sql "..."
   ```

2. **Document complex SQL**: Add comments in SQL
   ```sql
   -- Calculate customer lifetime value
   SELECT 
     c.id,
     c.name,
     SUM(o.amount) as ltv
   FROM customers c
   LEFT JOIN orders o ON c.id = o.customer_id
   GROUP BY c.id, c.name
   ```

3. **Test before updating**: Always test SQL before updating production views
   ```bash
   dremio sql execute "SELECT * FROM (YOUR_NEW_SQL) LIMIT 10"
   ```

4. **Use version control**: Store view definitions in git
   ```bash
   dremio --output json view get-by-path "Analytics.summary" > views/analytics_summary.json
   git add views/analytics_summary.json
   git commit -m "Update analytics summary view"
   ```

## Error Handling

### View Already Exists

```bash
$ dremio view create --path "Analytics.summary" --sql "SELECT 1"
Error: View already exists
```

**Solution**: Update instead of create:
```bash
VIEW_ID=$(dremio --output json view get-by-path "Analytics.summary" | jq -r '.id')
dremio view update $VIEW_ID --sql "SELECT 1"
```

### Invalid SQL

```bash
$ dremio view create --path "Analytics.bad" --sql "SELECT * FORM table"
Error: SQL syntax error
```

**Solution**: Test SQL first:
```bash
dremio sql execute "SELECT * FROM table LIMIT 1"
```

### Path Not Found

```bash
$ dremio view create --path "NonExistent.view" --sql "SELECT 1"
Error: Parent path does not exist
```

**Solution**: Create parent space/folder first:
```bash
dremio space create --name "NonExistent"
dremio view create --path "NonExistent.view" --sql "SELECT 1"
```

## Platform Differences

### Cloud
- Views created in project catalog
- Path: `source.namespace.view`

### Software
- Views created in spaces or catalog
- Path: `space.view` or `catalog.namespace.view`

## Best Practices

1. **Organize views logically**: Use spaces/folders for organization
2. **Keep SQL readable**: Format and comment complex queries
3. **Test thoroughly**: Validate views before production use
4. **Version control**: Track view definitions in git
5. **Document dependencies**: Note which views depend on others
6. **Use consistent naming**: Follow naming conventions
7. **Clean up unused views**: Delete obsolete views regularly

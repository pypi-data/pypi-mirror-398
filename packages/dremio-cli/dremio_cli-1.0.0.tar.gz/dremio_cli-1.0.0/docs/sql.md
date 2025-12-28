# SQL Operations

This guide covers SQL query execution, including file-based queries, context management, async execution, and query analysis.

## Commands

### Execute SQL Query

Execute a SQL query and return results.

```bash
dremio sql execute <QUERY> [OPTIONS]
dremio sql execute --file <FILE> [OPTIONS]
```

**Arguments:**
- `QUERY` - SQL query string (optional if using `--file`)

**Options:**
- `--file PATH` - Execute SQL from file
- `--context TEXT` - Query context (comma-separated path)
- `--async` - Execute asynchronously (return job ID immediately)
- `--output-file PATH` - Save results to file

**Examples:**

```bash
# Execute simple query
dremio sql execute "SELECT * FROM customers LIMIT 10"

# Execute from file
dremio sql execute --file query.sql

# Execute with context
dremio sql execute "SELECT * FROM table" --context "MySpace"

# Async execution (for long-running queries)
dremio sql execute "SELECT * FROM large_table" --async

# Save results to file
dremio sql execute "SELECT * FROM table" --output-file results.json

# Combine options
dremio sql execute --file complex_query.sql --context "Analytics" --output-file results.json
```

### Explain Query

Generate and display the execution plan for a query.

```bash
dremio sql explain <QUERY> [OPTIONS]
dremio sql explain --file <FILE> [OPTIONS]
```

**Arguments:**
- `QUERY` - SQL query string (optional if using `--file`)

**Options:**
- `--file PATH` - Explain SQL from file
- `--context TEXT` - Query context

**Examples:**

```bash
# Explain simple query
dremio sql explain "SELECT * FROM customers WHERE region = 'US'"

# Explain from file
dremio sql explain --file query.sql

# Explain with context
dremio sql explain "SELECT * FROM table" --context "MySpace"
```

### Validate Query

Validate SQL query syntax without executing.

```bash
dremio sql validate <QUERY> [OPTIONS]
dremio sql validate --file <FILE> [OPTIONS]
```

**Arguments:**
- `QUERY` - SQL query string (optional if using `--file`)

**Options:**
- `--file PATH` - Validate SQL from file
- `--context TEXT` - Query context

**Examples:**

```bash
# Validate query syntax
dremio sql validate "SELECT * FROM customers"

# Validate from file
dremio sql validate --file query.sql

# Validate with context
dremio sql validate "SELECT * FROM table" --context "MySpace"
```

## Scenarios

### Interactive Query Development

```bash
# 1. Start with a simple query
dremio sql execute "SELECT * FROM customers LIMIT 5"

# 2. Validate more complex query
dremio sql validate "SELECT c.*, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"

# 3. Explain to check performance
dremio sql explain "SELECT c.*, o.total FROM customers c JOIN orders o ON c.id = o.customer_id"

# 4. Execute and save results
dremio sql execute "SELECT c.*, o.total FROM customers c JOIN orders o ON c.id = o.customer_id" --output-file results.json
```

### File-Based Query Management

```bash
# Create query file
cat > monthly_sales.sql <<EOF
SELECT 
  DATE_TRUNC('month', order_date) as month,
  SUM(amount) as total_sales,
  COUNT(*) as order_count
FROM orders
WHERE order_date >= '2024-01-01'
GROUP BY 1
ORDER BY 1 DESC
EOF

# Validate the query
dremio sql validate --file monthly_sales.sql

# Execute and save results
dremio sql execute --file monthly_sales.sql --output-file monthly_sales.json

# Explain for optimization
dremio sql explain --file monthly_sales.sql
```

### Async Execution for Long Queries

```bash
# Submit long-running query
dremio sql execute "SELECT * FROM huge_table" --async
# Output: Job ID: abc-123-def-456

# Check job status
dremio job get abc-123-def-456

# Get results when ready
dremio job results abc-123-def-456 --output-file results.json
```

### Context-Aware Queries

```bash
# Set context to avoid fully-qualified names
dremio sql execute "SELECT * FROM customers" --context "Sales"

# Instead of:
dremio sql execute "SELECT * FROM Sales.customers"

# Multi-level context
dremio sql execute "SELECT * FROM table" --context "Analytics,Reports"
```

### Batch Query Execution

```bash
# Execute multiple queries
for query_file in queries/*.sql; do
  echo "Executing $query_file..."
  dremio sql execute --file "$query_file" --output-file "results/$(basename $query_file .sql).json"
done
```

## Common Workflows

### 1. Query Development Cycle

```bash
# Step 1: Validate syntax
dremio sql validate "SELECT * FROM customers WHERE region = 'US'"

# Step 2: Check execution plan
dremio sql explain "SELECT * FROM customers WHERE region = 'US'"

# Step 3: Test with small dataset
dremio sql execute "SELECT * FROM customers WHERE region = 'US' LIMIT 10"

# Step 4: Execute full query
dremio sql execute "SELECT * FROM customers WHERE region = 'US'" --output-file us_customers.json
```

### 2. Performance Analysis

```bash
# Get execution plan
dremio sql explain "SELECT c.*, SUM(o.amount) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id" > plan.txt

# Execute and time
time dremio sql execute "SELECT c.*, SUM(o.amount) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id" --async

# Get job details for analysis
dremio job get <job-id>

# Download profile
dremio job profile <job-id> --download profile.zip
```

### 3. Data Export

```bash
# Export to JSON
dremio sql execute "SELECT * FROM customers" --output-file customers.json

# Export to YAML
dremio --output yaml sql execute "SELECT * FROM customers" --output-file customers.yaml

# Convert to CSV using jq
dremio --output json sql execute "SELECT * FROM customers" | jq -r '.rows[] | @csv' > customers.csv
```

### 4. Scheduled Queries

```bash
#!/bin/bash
# daily_report.sh

# Execute daily sales query
dremio sql execute --file daily_sales.sql --output-file "reports/sales_$(date +%Y%m%d).json"

# Execute customer metrics
dremio sql execute --file customer_metrics.sql --output-file "reports/customers_$(date +%Y%m%d).json"

# Send notification
echo "Daily reports generated" | mail -s "Dremio Reports" admin@company.com
```

## SQL File Format

### Basic Query File

```sql
-- monthly_sales.sql
SELECT 
  DATE_TRUNC('month', order_date) as month,
  SUM(amount) as total_sales
FROM orders
GROUP BY 1
ORDER BY 1 DESC
```

### Complex Query File

```sql
-- customer_analysis.sql
WITH customer_orders AS (
  SELECT 
    customer_id,
    COUNT(*) as order_count,
    SUM(amount) as total_spent
  FROM orders
  WHERE order_date >= '2024-01-01'
  GROUP BY customer_id
),
customer_segments AS (
  SELECT 
    customer_id,
    CASE 
      WHEN total_spent > 10000 THEN 'Premium'
      WHEN total_spent > 1000 THEN 'Standard'
      ELSE 'Basic'
    END as segment
  FROM customer_orders
)
SELECT 
  c.name,
  c.email,
  co.order_count,
  co.total_spent,
  cs.segment
FROM customers c
JOIN customer_orders co ON c.id = co.customer_id
JOIN customer_segments cs ON c.id = cs.customer_id
ORDER BY co.total_spent DESC
```

## Output Formats

### Table (Default)

```bash
dremio sql execute "SELECT * FROM customers LIMIT 5"
```

Output:
```
┌────┬──────────┬─────────────────┬────────┐
│ ID │ Name     │ Email           │ Region │
├────┼──────────┼─────────────────┼────────┤
│ 1  │ John Doe │ john@email.com  │ US     │
│ 2  │ Jane Doe │ jane@email.com  │ EU     │
└────┴──────────┴─────────────────┴────────┘
```

### JSON

```bash
dremio --output json sql execute "SELECT * FROM customers LIMIT 2"
```

Output:
```json
{
  "rows": [
    {"id": 1, "name": "John Doe", "email": "john@email.com"},
    {"id": 2, "name": "Jane Doe", "email": "jane@email.com"}
  ],
  "rowCount": 2
}
```

### YAML

```bash
dremio --output yaml sql execute "SELECT * FROM customers LIMIT 2"
```

Output:
```yaml
rows:
  - id: 1
    name: John Doe
    email: john@email.com
  - id: 2
    name: Jane Doe
    email: jane@email.com
rowCount: 2
```

## Tips

1. **Use files for complex queries**: Store reusable queries in files
   ```bash
   dremio sql execute --file queries/monthly_report.sql
   ```

2. **Validate before executing**: Catch syntax errors early
   ```bash
   dremio sql validate --file query.sql && dremio sql execute --file query.sql
   ```

3. **Use async for long queries**: Don't block on large queries
   ```bash
   dremio sql execute "SELECT * FROM huge_table" --async
   ```

4. **Set context to simplify queries**: Avoid repeating paths
   ```bash
   dremio sql execute "SELECT * FROM table" --context "MySpace"
   ```

5. **Export results for analysis**: Save to files for further processing
   ```bash
   dremio sql execute "SELECT * FROM data" --output-file data.json
   ```

## Error Handling

### Syntax Error

```bash
$ dremio sql execute "SELECT * FORM table"
Error: SQL syntax error: Encountered "FORM" at line 1, column 10
```

**Solution**: Fix the SQL syntax:
```bash
dremio sql execute "SELECT * FROM table"
```

### Table Not Found

```bash
$ dremio sql execute "SELECT * FROM nonexistent"
Error: Table 'nonexistent' not found
```

**Solution**: Verify table exists:
```bash
dremio catalog list | grep "nonexistent"
```

### Job Still Running

```bash
$ dremio sql execute "SELECT * FROM large_table"
⚠ Could not fetch results: Job may still be running
```

**Solution**: Use async mode or check job status:
```bash
dremio sql execute "SELECT * FROM large_table" --async
dremio job get <job-id>
```

## Platform Differences

### Software
- Full SQL support via `/api/v3/sql`
- Explain and validate work
- All features available

### Cloud
- Limited SQL execution via API
- May require different endpoints
- Some features may not be available

## Best Practices

1. **Validate queries before execution**: Catch errors early
2. **Use explain for optimization**: Understand query plans
3. **Store queries in files**: Version control and reusability
4. **Use async for long queries**: Better resource management
5. **Set appropriate context**: Simplify query writing
6. **Export results for analysis**: Enable downstream processing
7. **Monitor job status**: Track query execution
8. **Use limits during development**: Test with small datasets first

## Advanced Usage

### Parameterized Queries

```bash
# Create template
cat > query_template.sql <<EOF
SELECT * FROM customers WHERE region = '{REGION}' AND created_at >= '{DATE}'
EOF

# Replace parameters and execute
REGION="US"
DATE="2024-01-01"
sed "s/{REGION}/$REGION/g; s/{DATE}/$DATE/g" query_template.sql | dremio sql execute --file /dev/stdin
```

### Query Pipeline

```bash
# Extract
dremio sql execute "SELECT * FROM source_table" --output-file extracted.json

# Transform (using jq)
cat extracted.json | jq '.rows[] | {id, name, email}' > transformed.json

# Load (create view with results)
dremio view create --path "Processed.customers" --sql "SELECT * FROM transformed_data"
```

### Monitoring and Alerts

```bash
#!/bin/bash
# monitor_query.sh

# Execute query
RESULT=$(dremio sql execute "SELECT COUNT(*) as count FROM errors WHERE created_at > NOW() - INTERVAL '1 hour'")

# Parse result
ERROR_COUNT=$(echo $RESULT | jq -r '.rows[0].count')

# Alert if threshold exceeded
if [ $ERROR_COUNT -gt 100 ]; then
  echo "High error count: $ERROR_COUNT" | mail -s "Alert" admin@company.com
fi
```

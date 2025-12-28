# Advanced Features

This guide covers advanced CLI features for power users.

## Query History

The CLI automatically tracks your query execution history in a local SQLite database.

### List History

```bash
dremio history list
dremio history list --limit 10
```

### Re-run from History

```bash
# List history to find ID
dremio history list

# Re-run command
dremio history run 5
```

### Clear History

```bash
dremio history clear
```

**Storage Location:** `~/.dremio/history.db`

## Favorite Queries

Save frequently used queries as favorites for quick access.

### Add Favorite

```bash
dremio favorite add daily_report --sql "SELECT * FROM sales WHERE date = CURRENT_DATE"

dremio favorite add customer_count --sql "SELECT COUNT(*) FROM customers" \
  --description "Total customer count"
```

### List Favorites

```bash
dremio favorite list
```

### Run Favorite

```bash
dremio favorite run daily_report
```

### Delete Favorite

```bash
dremio favorite delete daily_report
```

## Interactive Mode

Launch an interactive REPL for executing multiple commands.

```bash
dremio repl
```

**Features:**
- Execute commands interactively
- Built-in help system
- Command history (up/down arrows)
- Exit with `exit`, `quit`, or Ctrl+D

**Built-in Commands:**
- `help` - Show available commands
- `help <command>` - Show detailed help for specific command
- `exit` or `quit` - Exit REPL

**Example Session:**

```
$ dremio repl
Dremio CLI - Interactive Mode
Type 'help' for available commands, 'exit' or 'quit' to exit.

Using profile: default

dremio> help
┌──────────────────┬─────────────────────────────┐
│ Command          │ Description                 │
├──────────────────┼─────────────────────────────┤
│ catalog          │ Browse and navigate catalog │
│ sql              │ Execute SQL queries         │
│ job              │ Manage jobs                 │
│ view             │ Manage views                │
│ source           │ Manage sources              │
│ space            │ Manage spaces               │
│ folder           │ Manage folders              │
│ grant            │ Manage permissions          │
│ history          │ View command history        │
│ favorite         │ Manage favorite queries     │
│ help [command]   │ Show help for command       │
│ exit/quit        │ Exit REPL                   │
└──────────────────┴─────────────────────────────┘

Examples:
  catalog list
  sql execute "SELECT * FROM table LIMIT 10"
  help sql

dremio> help sql
Usage: dremio sql [OPTIONS] COMMAND [ARGS]...

  SQL operations.

Options:
  --help  Show this message and exit.

Commands:
  execute   Execute a SQL query.
  explain   Explain a SQL query.
  validate  Validate SQL syntax.

dremio> catalog list
┌─────────────┬──────────┬─────────┐
│ Path        │ Type     │ ID      │
├─────────────┼──────────┼─────────┤
│ Analytics   │ SPACE    │ abc-123 │
│ MySource    │ SOURCE   │ def-456 │
└─────────────┴──────────┴─────────┘

dremio> exit
Goodbye!
```


## Shell Auto-Completion

Enable Tab completion for commands and options.

### Bash

```bash
# Install completion
source <(cat completions/dremio-completion.bash)

# Or add to ~/.bashrc
echo 'source /path/to/dremio-cli/completions/dremio-completion.bash' >> ~/.bashrc
```

### Zsh

```bash
# Install completion
source completions/dremio-completion.zsh

# Or add to ~/.zshrc
echo 'source /path/to/dremio-cli/completions/dremio-completion.zsh' >> ~/.zshrc
```

### Usage

```bash
# Tab completion for commands
dremio <TAB>
catalog  profile  source  space  ...

# Tab completion for subcommands
dremio catalog <TAB>
list  get  get-by-path

# Tab completion for options
dremio --<TAB>
--profile  --output  --verbose  --help
```

## Workflows

### Daily Reporting Workflow

```bash
# 1. Save daily report as favorite
dremio favorite add daily_sales --sql "
SELECT 
  date,
  SUM(amount) as total_sales,
  COUNT(*) as transaction_count
FROM sales
WHERE date = CURRENT_DATE
GROUP BY date
"

# 2. Run daily
dremio favorite run daily_sales

# 3. Check history
dremio history list --limit 5
```

### Interactive Exploration

```bash
# Launch REPL
dremio repl

# Explore catalog
dremio> catalog list
dremio> catalog get-by-path "Analytics.sales"

# Execute queries
dremio> sql execute "SELECT * FROM Analytics.sales LIMIT 10"

# Save useful query
dremio> favorite add sales_summary --sql "SELECT region, SUM(amount) FROM Analytics.sales GROUP BY region"
```

### Batch Operations with History

```bash
# Execute multiple queries
dremio sql execute "SELECT COUNT(*) FROM table1"
dremio sql execute "SELECT COUNT(*) FROM table2"
dremio sql execute "SELECT COUNT(*) FROM table3"

# Review history
dremio history list

# Re-run if needed
dremio history run 2
```

## Tips

1. **Use favorites for complex queries** - Save time on frequently used queries
   ```bash
   dremio favorite add monthly_report --sql "$(cat report.sql)"
   ```

2. **History for debugging** - Review past commands when troubleshooting
   ```bash
   dremio history list --limit 20
   ```

3. **REPL for exploration** - Use interactive mode when learning the API
   ```bash
   dremio repl
   ```

4. **Completion for speed** - Enable shell completion to type faster
   ```bash
   source completions/dremio-completion.bash
   ```

5. **Combine with pipes** - Use standard Unix tools
   ```bash
   dremio history list --output json | jq '.[] | select(.success == 1)'
   ```

## Configuration

### History Database Location

Default: `~/.dremio/history.db`

To use a different location, set the `DREMIO_HISTORY_DB` environment variable:

```bash
export DREMIO_HISTORY_DB=/custom/path/history.db
```

### History Retention

History is stored indefinitely. Clear periodically:

```bash
# Clear all history
dremio history clear

# Or manually delete database
rm ~/.dremio/history.db
```

## Summary

- **History** - Automatic tracking of all commands
- **Favorites** - Save and reuse common queries
- **REPL** - Interactive command execution
- **Completion** - Tab completion for faster typing

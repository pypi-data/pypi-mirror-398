"""SQL execution commands."""

import json
import click
from rich.console import Console
from pathlib import Path

from dremio_cli.config import ProfileManager
from dremio_cli.client.factory import create_client
from dremio_cli.formatters.table import format_as_table
from dremio_cli.formatters.json import format_as_json
from dremio_cli.formatters.yaml import format_as_yaml

console = Console()


@click.group()
def sql() -> None:
    """SQL execution operations."""
    pass


@sql.command("execute")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Execute SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.option("--async", "async_mode", is_flag=True, help="Execute asynchronously (return job ID immediately)")
@click.option("--output-file", type=click.Path(), help="Save results to file")
@click.pass_context
def execute_sql(ctx, query: str, sql_file: str, context: str, async_mode: bool, output_file: str) -> None:
    """Execute a SQL query.
    
    Examples:
        dremio sql execute "SELECT * FROM table LIMIT 10"
        dremio sql execute --file query.sql
        dremio sql execute "SELECT * FROM table" --context "MySpace"
        dremio sql execute "SELECT * FROM large_table" --async
        dremio sql execute "SELECT * FROM table" --output-file results.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL query
        if sql_file:
            with open(sql_file, 'r') as f:
                query = f.read()
        elif not query:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Execute SQL
        with console.status(f"[bold green]Executing SQL query..."):
            result = client.execute_sql(query, context=sql_context)
        
        job_id = result.get("id")
        
        if async_mode:
            # Return job ID immediately
            console.print(f"[green]✓[/green] Query submitted")
            console.print(f"  Job ID: {job_id}")
            console.print(f"\n[dim]Use 'dremio job get {job_id}' to check status[/dim]")
            console.print(f"[dim]Use 'dremio job results {job_id}' to get results[/dim]")
        else:
            # Wait for results
            console.print(f"[green]✓[/green] Query executed")
            console.print(f"  Job ID: {job_id}")
            
            # Get job results
            if job_id:
                try:
                    with console.status(f"[bold green]Fetching results..."):
                        results = client.get_job_results(job_id)
                    
                    rows = results.get("rows", [])
                    row_count = results.get("rowCount", len(rows))
                    
                    # Save to file if requested
                    if output_file:
                        output_path = Path(output_file)
                        if output_path.suffix == '.json':
                            output_path.write_text(json.dumps(results, indent=2))
                        elif output_path.suffix in ['.yaml', '.yml']:
                            import yaml
                            output_path.write_text(yaml.dump(results))
                        else:
                            # Default to JSON
                            output_path.write_text(json.dumps(results, indent=2))
                        
                        console.print(f"\n[green]✓[/green] Results saved to {output_file}")
                        console.print(f"  Rows: {row_count}")
                    else:
                        # Display results
                        output_format = ctx.obj.output_format
                        
                        if output_format == "json":
                            console.print(format_as_json(results))
                        elif output_format == "yaml":
                            console.print(format_as_yaml(results))
                        else:
                            if rows:
                                format_as_table(rows, title=f"Query Results ({row_count} rows)")
                            else:
                                console.print("[yellow]No results returned[/yellow]")
                
                except Exception as e:
                    console.print(f"\n[yellow]⚠[/yellow] Could not fetch results: {e}")
                    console.print(f"[dim]Job may still be running. Use 'dremio job results {job_id}' to check later[/dim]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@sql.command("explain")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Explain SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.pass_context
def explain_sql(ctx, query: str, sql_file: str, context: str) -> None:
    """Explain a SQL query execution plan.
    
    Examples:
        dremio sql explain "SELECT * FROM table"
        dremio sql explain --file query.sql
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL query
        if sql_file:
            with open(sql_file, 'r') as f:
                query = f.read()
        elif not query:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Explain query (execute with EXPLAIN prefix)
        explain_query = f"EXPLAIN PLAN FOR {query}"
        
        with console.status(f"[bold green]Generating execution plan..."):
            result = client.execute_sql(explain_query, context=sql_context)
        
        job_id = result.get("id")
        
        console.print(f"[green]✓[/green] Execution plan generated")
        console.print(f"  Job ID: {job_id}")
        
        # Get results
        if job_id:
            try:
                with console.status(f"[bold green]Fetching plan..."):
                    results = client.get_job_results(job_id)
                
                rows = results.get("rows", [])
                
                # Display plan
                output_format = ctx.obj.output_format
                
                if output_format == "json":
                    console.print(format_as_json(results))
                elif output_format == "yaml":
                    console.print(format_as_yaml(results))
                else:
                    if rows:
                        console.print("\n[bold]Execution Plan:[/bold]\n")
                        for row in rows:
                            # Plan is usually in first column
                            plan_text = list(row.values())[0] if row else ""
                            console.print(plan_text)
                    else:
                        console.print("[yellow]No plan returned[/yellow]")
            
            except Exception as e:
                console.print(f"\n[yellow]⚠[/yellow] Could not fetch plan: {e}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@sql.command("validate")
@click.argument("query", required=False)
@click.option("--file", "sql_file", type=click.Path(exists=True), help="Validate SQL from file")
@click.option("--context", help="Query context (space or folder path)")
@click.pass_context
def validate_sql(ctx, query: str, sql_file: str, context: str) -> None:
    """Validate SQL query syntax.
    
    Examples:
        dremio sql validate "SELECT * FROM table"
        dremio sql validate --file query.sql
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Get SQL query
        if sql_file:
            with open(sql_file, 'r') as f:
                query = f.read()
        elif not query:
            console.print("[red]Error: Either provide a query or use --file[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Parse context
        sql_context = None
        if context:
            sql_context = [c.strip() for c in context.split(",")]
        
        # Validate by doing EXPLAIN (doesn't execute, just validates)
        explain_query = f"EXPLAIN PLAN FOR {query}"
        
        with console.status(f"[bold green]Validating SQL syntax..."):
            try:
                result = client.execute_sql(explain_query, context=sql_context)
                job_id = result.get("id")
                
                # If we got a job ID, syntax is valid
                console.print(f"[green]✓[/green] SQL syntax is valid")
                console.print(f"  Job ID: {job_id}")
                
            except Exception as e:
                error_msg = str(e)
                console.print(f"[red]✗[/red] SQL syntax error")
                console.print(f"\n[red]{error_msg}[/red]")
                raise click.Abort()
        
    except click.Abort:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

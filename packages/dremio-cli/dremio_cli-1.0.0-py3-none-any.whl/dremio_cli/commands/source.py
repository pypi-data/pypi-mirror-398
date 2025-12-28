"""Source management commands."""

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
def source() -> None:
    """Source management operations."""
    pass


@source.command("list")
@click.pass_context
def list_sources(ctx) -> None:
    """List all sources.
    
    Examples:
        dremio source list
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get catalog
        with console.status(f"[bold green]Fetching sources..."):
            data = client.get_catalog()
        
        items = data.get("data", [])
        
        # Filter for sources
        sources = [
            item for item in items
            if item.get("containerType") == "SOURCE"
        ]
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(sources))
        elif output_format == "yaml":
            console.print(format_as_yaml(sources))
        else:
            if sources:
                format_as_table(sources, title=f"Sources ({profile_name})")
            else:
                console.print("[yellow]No sources found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("get")
@click.argument("source_id")
@click.pass_context
def get_source(ctx, source_id: str) -> None:
    """Get source by ID.
    
    Examples:
        dremio source get abc-123-def-456
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get source
        with console.status(f"[bold green]Fetching source {source_id}..."):
            data = client.get_catalog_item(source_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Source: {source_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("create")
@click.option("--name", required=True, help="Source name")
@click.option("--type", "source_type", required=True, help="Source type (e.g., POSTGRES, S3, MONGO)")
@click.option("--config-file", type=click.Path(exists=True), required=True, help="Source configuration JSON file")
@click.pass_context
def create_source(ctx, name: str, source_type: str, config_file: str) -> None:
    """Create a new source.
    
    Examples:
        dremio source create --name MyPostgres --type POSTGRES --config-file postgres.json
        dremio source create --name MyS3 --type S3 --config-file s3.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Load config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Create client
        client = create_client(profile)
        
        # Create source data
        source_data = {
            "entityType": "source",
            "name": name,
            "type": source_type,
            "config": config
        }
        
        with console.status(f"[bold green]Creating source '{name}'..."):
            result = client.create_source(source_data)
        
        source_id = result.get("id")
        
        console.print(f"[green]✓[/green] Source created successfully")
        console.print(f"  ID: {source_id}")
        console.print(f"  Name: {name}")
        console.print(f"  Type: {source_type}")
        
        # Display full result if verbose
        if ctx.obj.verbose:
            output_format = ctx.obj.output_format
            if output_format == "json":
                console.print(format_as_json(result))
            elif output_format == "yaml":
                console.print(format_as_yaml(result))
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("update")
@click.argument("source_id")
@click.option("--config-file", type=click.Path(exists=True), required=True, help="Updated source configuration JSON file")
@click.pass_context
def update_source(ctx, source_id: str, config_file: str) -> None:
    """Update an existing source.
    
    Examples:
        dremio source update abc-123 --config-file updated_config.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get current source for tag
        current_source = client.get_catalog_item(source_id)
        
        # Load new config
        with open(config_file, 'r') as f:
            new_config = json.load(f)
        
        # Update source data
        source_data = {
            "entityType": "source",
            "id": source_id,
            "name": current_source.get("name"),
            "type": current_source.get("type"),
            "tag": current_source.get("tag"),
            "config": new_config
        }
        
        with console.status(f"[bold green]Updating source {source_id}..."):
            result = client.update_source(source_id, source_data)
        
        console.print(f"[green]✓[/green] Source updated successfully")
        console.print(f"  ID: {source_id}")
        
        # Display full result if verbose
        if ctx.obj.verbose:
            output_format = ctx.obj.output_format
            if output_format == "json":
                console.print(format_as_json(result))
            elif output_format == "yaml":
                console.print(format_as_yaml(result))
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("refresh")
@click.argument("source_id")
@click.pass_context
def refresh_source(ctx, source_id: str) -> None:
    """Refresh source metadata.
    
    Examples:
        dremio source refresh abc-123-def-456
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Refresh source
        with console.status(f"[bold green]Refreshing source {source_id}..."):
            result = client.refresh_source(source_id)
        
        console.print(f"[green]✓[/green] Source refresh initiated")
        console.print(f"  Source ID: {source_id}")
        
        if result:
            job_id = result.get("id")
            if job_id:
                console.print(f"  Job ID: {job_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("delete")
@click.argument("source_id")
@click.option("--tag", help="Version tag for optimistic concurrency control")
@click.confirmation_option(prompt="Are you sure you want to delete this source?")
@click.pass_context
def delete_source(ctx, source_id: str, tag: str) -> None:
    """Delete a source.
    
    Examples:
        dremio source delete abc-123-def-456
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Create client
        client = create_client(profile)
        
        # Get tag if not provided
        if not tag:
            source = client.get_catalog_item(source_id)
            tag = source.get("tag")
        
        # Delete source
        with console.status(f"[bold yellow]Deleting source {source_id}..."):
            client.delete_source(source_id, tag)
        
        console.print(f"[green]✓[/green] Source deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@source.command("test-connection")
@click.option("--config-file", type=click.Path(exists=True), required=True, help="Source configuration JSON file to test")
@click.pass_context
def test_connection(ctx, config_file: str) -> None:
    """Test source connection configuration.
    
    Examples:
        dremio source test-connection --config-file postgres.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Load config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Create client
        client = create_client(profile)
        
        # Test connection
        with console.status(f"[bold green]Testing connection..."):
            result = client.test_source_connection(config)
        
        success = result.get("success", False)
        
        if success:
            console.print(f"[green]✓[/green] Connection test successful")
        else:
            console.print(f"[red]✗[/red] Connection test failed")
            error = result.get("error", "Unknown error")
            console.print(f"  Error: {error}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

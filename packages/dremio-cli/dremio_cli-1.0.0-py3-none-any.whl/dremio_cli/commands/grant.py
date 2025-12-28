"""Grant and privilege management commands."""

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
def grant() -> None:
    """Grant and privilege management operations."""
    pass


@grant.command("list")
@click.argument("catalog_id")
@click.pass_context
def list_grants(ctx, catalog_id: str) -> None:
    """List grants for a catalog object.
    
    Examples:
        dremio grant list abc-123-def-456
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
        
        # Get grants
        with console.status(f"[bold green]Fetching grants for {catalog_id}..."):
            data = client.list_grants(catalog_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            grants = data.get("grants", [])
            if grants:
                format_as_table(grants, title=f"Grants for {catalog_id}")
            else:
                console.print("[yellow]No grants found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@grant.command("add")
@click.argument("catalog_id")
@click.option("--grantee-type", required=True, type=click.Choice(["USER", "ROLE"]), help="Grantee type")
@click.option("--grantee-id", required=True, help="User or role ID")
@click.option("--privileges", required=True, help="Comma-separated privileges (e.g., SELECT,ALTER,VIEW)")
@click.pass_context
def add_grant(ctx, catalog_id: str, grantee_type: str, grantee_id: str, privileges: str) -> None:
    """Add a grant to a catalog object.
    
    Examples:
        dremio grant add abc-123 --grantee-type USER --grantee-id user-456 --privileges SELECT,VIEW
        dremio grant add abc-123 --grantee-type ROLE --grantee-id role-789 --privileges SELECT,ALTER,MODIFY
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
        
        # Parse privileges
        privilege_list = [p.strip() for p in privileges.split(",")]
        
        # Create grant data
        grant_data = {
            "granteeType": grantee_type,
            "granteeId": grantee_id,
            "privileges": privilege_list
        }
        
        # Add grant
        with console.status(f"[bold green]Adding grant..."):
            client.add_grant(catalog_id, grant_data)
        
        console.print(f"[green]✓[/green] Grant added successfully")
        console.print(f"  Grantee: {grantee_type} {grantee_id}")
        console.print(f"  Privileges: {', '.join(privilege_list)}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@grant.command("remove")
@click.argument("catalog_id")
@click.option("--grantee-type", required=True, type=click.Choice(["USER", "ROLE"]), help="Grantee type")
@click.option("--grantee-id", required=True, help="User or role ID")
@click.confirmation_option(prompt="Are you sure you want to remove this grant?")
@click.pass_context
def remove_grant(ctx, catalog_id: str, grantee_type: str, grantee_id: str) -> None:
    """Remove a grant from a catalog object.
    
    Examples:
        dremio grant remove abc-123 --grantee-type USER --grantee-id user-456
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
        
        # Remove grant
        with console.status(f"[bold yellow]Removing grant..."):
            client.remove_grant(catalog_id, grantee_type, grantee_id)
        
        console.print(f"[green]✓[/green] Grant removed successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@grant.command("set")
@click.argument("catalog_id")
@click.option("--from-file", "grant_file", type=click.Path(exists=True), required=True, help="JSON file with grants")
@click.pass_context
def set_grants(ctx, catalog_id: str, grant_file: str) -> None:
    """Set all grants for a catalog object (replaces existing).
    
    Examples:
        dremio grant set abc-123 --from-file grants.json
    """
    try:
        # Get profile
        manager = ProfileManager()
        profile_name = ctx.obj.profile_name
        profile = manager.get_profile(profile_name)
        
        if not profile:
            console.print(f"[red]Profile '{profile_name}' not found[/red]")
            raise click.Abort()
        
        # Load grants
        with open(grant_file, 'r') as f:
            grants_data = json.load(f)
        
        # Create client
        client = create_client(profile)
        
        # Set grants
        with console.status(f"[bold green]Setting grants..."):
            client.set_grants(catalog_id, grants_data)
        
        grant_count = len(grants_data.get("grants", []))
        console.print(f"[green]✓[/green] Grants set successfully")
        console.print(f"  Total grants: {grant_count}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

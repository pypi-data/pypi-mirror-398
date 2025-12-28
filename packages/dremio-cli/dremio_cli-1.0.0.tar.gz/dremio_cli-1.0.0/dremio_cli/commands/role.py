"""Role management commands."""

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
def role() -> None:
    """Role management operations."""
    pass


@role.command("list")
@click.pass_context
def list_roles(ctx) -> None:
    """List all roles.
    
    Examples:
        dremio role list
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
        
        # List roles
        with console.status(f"[bold green]Fetching roles..."):
            data = client.list_roles()
        
        roles = data.get("roles", data.get("data", []))
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(roles))
        elif output_format == "yaml":
            console.print(format_as_yaml(roles))
        else:
            if roles:
                format_as_table(roles, title=f"Roles ({profile_name})")
            else:
                console.print("[yellow]No roles found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("get")
@click.argument("role_id")
@click.pass_context
def get_role(ctx, role_id: str) -> None:
    """Get role by ID.
    
    Examples:
        dremio role get role-123-456
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
        
        # Get role
        with console.status(f"[bold green]Fetching role {role_id}..."):
            data = client.get_role(role_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"Role: {role_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("create")
@click.option("--name", required=True, help="Role name")
@click.option("--from-file", "role_file", type=click.Path(exists=True), help="Load role from JSON file")
@click.pass_context
def create_role(ctx, name: str, role_file: str) -> None:
    """Create a new role.
    
    Examples:
        dremio role create --name "Analyst"
        dremio role create --from-file role.json
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
        
        # Build role data
        if role_file:
            with open(role_file, 'r') as f:
                role_data = json.load(f)
        else:
            role_data = {
                "name": name
            }
        
        # Create role
        with console.status(f"[bold green]Creating role..."):
            result = client.create_role(role_data)
        
        role_id = result.get("id")
        
        console.print(f"[green]✓[/green] Role created successfully")
        console.print(f"  ID: {role_id}")
        console.print(f"  Name: {result.get('name', name)}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("update")
@click.argument("role_id")
@click.option("--from-file", "role_file", type=click.Path(exists=True), required=True, help="Updated role JSON file")
@click.pass_context
def update_role(ctx, role_id: str, role_file: str) -> None:
    """Update an existing role.
    
    Examples:
        dremio role update role-123 --from-file updated_role.json
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
        
        # Load role data
        with open(role_file, 'r') as f:
            role_data = json.load(f)
        
        # Update role
        with console.status(f"[bold green]Updating role {role_id}..."):
            result = client.update_role(role_id, role_data)
        
        console.print(f"[green]✓[/green] Role updated successfully")
        console.print(f"  ID: {role_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("delete")
@click.argument("role_id")
@click.confirmation_option(prompt="Are you sure you want to delete this role?")
@click.pass_context
def delete_role(ctx, role_id: str) -> None:
    """Delete a role.
    
    Examples:
        dremio role delete role-123-456
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
        
        # Delete role
        with console.status(f"[bold yellow]Deleting role {role_id}..."):
            client.delete_role(role_id)
        
        console.print(f"[green]✓[/green] Role deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("add-member")
@click.argument("role_id")
@click.option("--user", "user_id", required=True, help="User ID to add")
@click.pass_context
def add_member(ctx, role_id: str, user_id: str) -> None:
    """Add a user to a role.
    
    Examples:
        dremio role add-member role-123 --user user-456
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
        
        # Add member
        with console.status(f"[bold green]Adding user to role..."):
            client.add_role_member(role_id, user_id)
        
        console.print(f"[green]✓[/green] User added to role successfully")
        console.print(f"  Role: {role_id}")
        console.print(f"  User: {user_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@role.command("remove-member")
@click.argument("role_id")
@click.option("--user", "user_id", required=True, help="User ID to remove")
@click.confirmation_option(prompt="Are you sure you want to remove this user from the role?")
@click.pass_context
def remove_member(ctx, role_id: str, user_id: str) -> None:
    """Remove a user from a role.
    
    Examples:
        dremio role remove-member role-123 --user user-456
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
        
        # Remove member
        with console.status(f"[bold yellow]Removing user from role..."):
            client.remove_role_member(role_id, user_id)
        
        console.print(f"[green]✓[/green] User removed from role successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

"""User management commands."""

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
def user() -> None:
    """User management operations."""
    pass


@user.command("list")
@click.pass_context
def list_users(ctx) -> None:
    """List all users.
    
    Examples:
        dremio user list
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
        
        # List users
        with console.status(f"[bold green]Fetching users..."):
            data = client.list_users()
        
        users = data.get("users", data.get("data", []))
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(users))
        elif output_format == "yaml":
            console.print(format_as_yaml(users))
        else:
            if users:
                format_as_table(users, title=f"Users ({profile_name})")
            else:
                console.print("[yellow]No users found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@user.command("get")
@click.argument("user_id")
@click.pass_context
def get_user(ctx, user_id: str) -> None:
    """Get user by ID.
    
    Examples:
        dremio user get user-123-456
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
        
        # Get user
        with console.status(f"[bold green]Fetching user {user_id}..."):
            data = client.get_user(user_id)
        
        # Format output
        output_format = ctx.obj.output_format
        
        if output_format == "json":
            console.print(format_as_json(data))
        elif output_format == "yaml":
            console.print(format_as_yaml(data))
        else:
            format_as_table(data, title=f"User: {user_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@user.command("create")
@click.option("--name", required=True, help="User full name")
@click.option("--email", required=True, help="User email")
@click.option("--username", help="Username (defaults to email)")
@click.option("--password", help="Initial password")
@click.option("--from-file", "user_file", type=click.Path(exists=True), help="Load user from JSON file")
@click.pass_context
def create_user(ctx, name: str, email: str, username: str, password: str, user_file: str) -> None:
    """Create a new user.
    
    Examples:
        dremio user create --name "John Doe" --email john@company.com
        dremio user create --from-file user.json
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
        
        # Build user data
        if user_file:
            with open(user_file, 'r') as f:
                user_data = json.load(f)
        else:
            user_data = {
                "name": name,
                "email": email,
                "userName": username or email
            }
            if password:
                user_data["password"] = password
        
        # Create user
        with console.status(f"[bold green]Creating user..."):
            result = client.create_user(user_data)
        
        user_id = result.get("id")
        
        console.print(f"[green]✓[/green] User created successfully")
        console.print(f"  ID: {user_id}")
        console.print(f"  Name: {result.get('name', name)}")
        console.print(f"  Email: {result.get('email', email)}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@user.command("update")
@click.argument("user_id")
@click.option("--from-file", "user_file", type=click.Path(exists=True), required=True, help="Updated user JSON file")
@click.pass_context
def update_user(ctx, user_id: str, user_file: str) -> None:
    """Update an existing user.
    
    Examples:
        dremio user update user-123 --from-file updated_user.json
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
        
        # Load user data
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        # Update user
        with console.status(f"[bold green]Updating user {user_id}..."):
            result = client.update_user(user_id, user_data)
        
        console.print(f"[green]✓[/green] User updated successfully")
        console.print(f"  ID: {user_id}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()


@user.command("delete")
@click.argument("user_id")
@click.confirmation_option(prompt="Are you sure you want to delete this user?")
@click.pass_context
def delete_user(ctx, user_id: str) -> None:
    """Delete a user.
    
    Examples:
        dremio user delete user-123-456
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
        
        # Delete user
        with console.status(f"[bold yellow]Deleting user {user_id}..."):
            client.delete_user(user_id)
        
        console.print(f"[green]✓[/green] User deleted successfully")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if ctx.obj.verbose:
            import traceback
            traceback.print_exc()
        raise click.Abort()

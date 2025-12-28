"""Profile management commands."""

import click
from rich.console import Console
from rich.table import Table

from dremio_cli.config import ProfileManager
from dremio_cli.utils.exceptions import DremioCliError
from dremio_cli.utils.validators import validate_profile_type, validate_auth_type, validate_url

console = Console()


@click.group()
def profile() -> None:
    """Manage Dremio CLI profiles."""
    pass


@profile.command("list")
def list_profiles() -> None:
    """List all profiles."""
    try:
        manager = ProfileManager()
        profiles = manager.list_profiles()
        default = manager.get_default_profile()
        
        if not profiles:
            console.print("[yellow]No profiles configured.[/yellow]")
            console.print("\nCreate a profile with: [cyan]dremio profile create <name>[/cyan]")
            return
        
        table = Table(title="Dremio Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Base URL", style="blue")
        table.add_column("Auth Type", style="magenta")
        table.add_column("Default", style="yellow")
        
        for name, profile in profiles.items():
            is_default = "✓" if name == default else ""
            table.add_row(
                name,
                profile.get("type", "N/A"),
                profile.get("base_url", "N/A"),
                profile.get("auth", {}).get("type", "N/A"),
                is_default,
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@profile.command("current")
def current_profile() -> None:
    """Show current default profile."""
    try:
        manager = ProfileManager()
        default = manager.get_default_profile()
        
        if not default:
            console.print("[yellow]No default profile set.[/yellow]")
            return
        
        profile_data = manager.get_profile(default)
        
        console.print(f"\n[bold]Current Profile:[/bold] [cyan]{default}[/cyan]\n")
        console.print(f"  Type: {profile_data.get('type')}")
        console.print(f"  Base URL: {profile_data.get('base_url')}")
        console.print(f"  Auth Type: {profile_data.get('auth', {}).get('type')}")
        
        if "project_id" in profile_data:
            console.print(f"  Project ID: {profile_data['project_id']}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@profile.command("create")
@click.argument("name")
@click.option("--type", "profile_type", required=True, type=click.Choice(["cloud", "software"]))
@click.option("--base-url", required=True, help="Base URL for Dremio API")
@click.option("--project-id", help="Project ID (required for cloud)")
@click.option("--auth-type", required=True, type=click.Choice(["pat", "oauth", "username_password"]))
@click.option("--token", help="Authentication token")
@click.option("--username", help="Username (for username_password auth)")
@click.option("--password", help="Password (for username_password auth)")
def create_profile(
    name: str,
    profile_type: str,
    base_url: str,
    project_id: str,
    auth_type: str,
    token: str,
    username: str,
    password: str,
) -> None:
    """Create a new profile."""
    try:
        # Validate inputs
        validate_profile_type(profile_type)
        validate_auth_type(auth_type)
        validate_url(base_url)
        
        # Validate cloud-specific requirements
        if profile_type == "cloud" and not project_id:
            raise DremioCliError("--project-id is required for cloud profiles")
        
        # Validate auth requirements
        if auth_type == "pat" and not token:
            raise DremioCliError("--token is required for PAT authentication")
        
        if auth_type == "username_password" and (not username or not password):
            raise DremioCliError("--username and --password are required for username_password authentication")
        
        manager = ProfileManager()
        manager.create_profile(
            name=name,
            profile_type=profile_type,
            base_url=base_url,
            auth_type=auth_type,
            project_id=project_id,
            token=token,
            username=username,
            password=password,
        )
        
        console.print(f"[green]✓[/green] Profile '[cyan]{name}[/cyan]' created successfully")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@profile.command("delete")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to delete this profile?")
def delete_profile(name: str) -> None:
    """Delete a profile."""
    try:
        manager = ProfileManager()
        manager.delete_profile(name)
        console.print(f"[green]✓[/green] Profile '[cyan]{name}[/cyan]' deleted")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()


@profile.command("set-default")
@click.argument("name")
def set_default(name: str) -> None:
    """Set the default profile."""
    try:
        manager = ProfileManager()
        manager.set_default_profile(name)
        console.print(f"[green]✓[/green] Default profile set to '[cyan]{name}[/cyan]'")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

"""
SOLAR CLI - Config Command
Configure SOLAR CLI settings
"""

import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from solar.utils.config import get_config, set_config, CONFIG_PATH

console = Console()


@click.group('config')
def config_command():
    """
    Configure SOLAR CLI settings.
    """
    pass


@config_command.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key: str, value: str):
    """
    Set a configuration value.
    
    \b
    Available keys:
      api_key       - Google Gemini API key
      model_name    - Gemini model to use (e.g., gemini-2.5-flash-lite)
      default_org   - Default organization name for new projects
      theme         - Output theme (dark/light)
    
    \b
    Examples:
      solx config set api_key YOUR_GEMINI_API_KEY
      solx config set default_org com.mycompany
    """
    set_config(key, value)
    
    display_value = value if key != 'api_key' else f"{value[:8]}...{value[-4:]}"
    console.print(f"[green]✓ Set {key} = {display_value}[/green]")


@config_command.command('get')
@click.argument('key', required=False)
def config_get(key: str = None):
    """
    Get configuration value(s).
    
    \b
    Examples:
      solx config get           # Show all settings
      solx config get api_key   # Show specific setting
    """
    config = get_config()
    
    if key:
        value = config.get(key)
        if value:
            if key == 'api_key':
                value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            console.print(f"[cyan]{key}[/cyan] = {value}")
        else:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")
    else:
        table = Table(title="SOLAR Configuration", border_style="cyan")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="white")
        
        for k, v in config.items():
            if k == 'api_key' and v:
                v = f"{v[:8]}...{v[-4:]}" if len(v) > 12 else "***"
            table.add_row(k, str(v) if v else "[dim]not set[/dim]")
        
        console.print(table)
        console.print(f"\n[dim]Config file: {CONFIG_PATH}[/dim]")


@config_command.command('init')
def config_init():
    """
    Interactive configuration setup.
    """
    console.print(Panel.fit(
        "[bold yellow]☀️ SOLAR[/bold yellow] - Configuration Setup",
        border_style="cyan"
    ))
    
    console.print("\n[dim]Let's configure SOLAR CLI[/dim]\n")
    
    # API Key
    console.print("[bold]1. Google Gemini API Key[/bold]")
    console.print("[dim]   Get your key at: https://makersuite.google.com/app/apikey[/dim]")
    api_key = click.prompt("   Enter API key", hide_input=True)
    set_config('api_key', api_key)
    console.print("[green]   ✓ API key saved[/green]\n")
    
    # Default org
    console.print("[bold]2. Default Organization[/bold]")
    console.print("[dim]   Used for new Flutter projects (e.g., com.yourcompany)[/dim]")
    default_org = click.prompt("   Enter organization", default="com.solarapp")
    set_config('default_org', default_org)
    console.print("[green]   ✓ Organization saved[/green]\n")
    
    console.print(Panel(
        """[green]✅ Configuration complete![/green]

[dim]You can now create your first app:[/dim]
  [cyan]solx new myapp[/cyan]
""",
        title="[bold yellow]☀️ SOLAR[/bold yellow]",
        border_style="green"
    ))

"""
SOLAR CLI - Run Command
Run the Flutter application
"""

import os
import subprocess
import click
from rich.console import Console
from rich.panel import Panel

from solar.utils.project import get_solar_project

console = Console()


@click.command('run')
@click.option('--device', '-d', default=None, help='Target device (e.g., chrome, ios, android)')
@click.option('--release', '-r', is_flag=True, help='Run in release mode')
@click.option('--hot-reload/--no-hot-reload', default=True, help='Enable hot reload')
def run_command(device: str, release: bool, hot_reload: bool):
    """
    Run the Flutter application.
    
    \b
    Examples:
      solx run
      solx run -d chrome
      solx run -d ios --release
    """
    # Check if we're in a SOLAR project
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        console.print("[dim]Run 'solx new <name>' to create a project first, or cd into solar_app[/dim]")
        return
    
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Running [cyan]{project['name']}[/cyan]",
        border_style="cyan"
    ))
    
    # Build command
    cmd = ['flutter', 'run']
    
    if device:
        cmd.extend(['-d', device])
    
    if release:
        cmd.append('--release')
    
    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]\n")
    console.print("[dim]Press 'r' for hot reload, 'R' for hot restart, 'q' to quit[/dim]\n")
    
    # Run Flutter
    try:
        subprocess.run(cmd, cwd=project['path'])
    except KeyboardInterrupt:
        console.print("\n[yellow]App stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error running app: {e}[/red]")

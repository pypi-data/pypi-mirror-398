"""
SOLAR CLI - List Command
List all pages, widgets and services in the project
"""

import os
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from solar.utils.project import get_solar_project

console = Console()

@click.command('list')
def list_command():
    """
    List all components in the current SOLAR project.
    """
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        return
    
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Project: [cyan]{project['name']}[/cyan]",
        border_style="cyan"
    ))
    
    # List Pages
    _display_component_table("Pages", os.path.join(project['path'], 'lib', 'pages'), "magenta")
    
    # List Widgets
    _display_component_table("Widgets", os.path.join(project['path'], 'lib', 'widgets'), "blue")
    
    # List Services
    _display_component_table("Services", os.path.join(project['path'], 'lib', 'services'), "green")

def _display_component_table(title: str, directory: str, color: str):
    """Internal helper to display a table of components"""
    if not os.path.exists(directory):
        return
    
    files = [f for f in os.listdir(directory) if f.endswith('.dart')]
    
    if not files:
        return
    
    table = Table(title=f"[bold {color}]{title}[/bold {color}]", border_style=color)
    table.add_column("Name", style="cyan")
    table.add_column("File", style="dim")
    table.add_column("Size", justify="right")
    
    for f in sorted(files):
        path = os.path.join(directory, f)
        size = os.path.getsize(path)
        # Convert snake_case_page.dart back to PascalCase
        name = f.replace('.dart', '').replace('_page', '').replace('_widget', '').replace('_service', '')
        name = ''.join(word.title() for word in name.split('_'))
        
        table.add_row(name, f, f"{size} bytes")
    
    console.print(table)
    console.print()

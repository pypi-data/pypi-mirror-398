"""
SOLAR CLI - Delete Command
Remove pages, widgets or services from the project
"""

import os
import click
import shutil
from rich.console import Console
from rich.panel import Panel

from solar.utils.project import get_solar_project, get_component_path

console = Console()

@click.command('delete')
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to delete this component?')
def delete_command(name: str):
    """
    Delete a component from the current project.
    
    \b
    Examples:
      solar delete LoginPage
      solar delete ProductCard
    """
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        return
    
    component_path = get_component_path(project['path'], name)
    
    if not component_path:
        console.print(f"[red]❌ Component '{name}' not found[/red]")
        return
    
    try:
        # Get relative path for display
        rel_path = os.path.relpath(component_path, project['path'])
        
        # Delete the file
        os.remove(component_path)
        
        # If it's a page, we should ideally remove it from routes too
        if '_page.dart' in component_path:
            _remove_from_routes(project['path'], name)
        
        console.print(f"[green]✅ Successfully deleted [bold]{name}[/bold][/green]")
        console.print(f"[dim]Removed file: {rel_path}[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Error deleting component: {e}[/red]")

def _remove_from_routes(project_path: str, page_name: str):
    """Try to remove page from app_routes.dart"""
    routes_path = os.path.join(project_path, 'lib', 'routes', 'app_routes.dart')
    if not os.path.exists(routes_path):
        return
    
    try:
        with open(routes_path, 'r') as f:
            lines = f.readlines()
        
        # This is a bit tricky as we don't want to break the file
        # For now, let's just comment it out or leave a TODO
        # A more robust solution would use regex to remove the blocks
        
        import re
        content = "".join(lines)
        
        # Convert name to snake_case for route name
        from solar.utils.project import _to_snake_case
        snake_name = _to_snake_case(page_name)
        
        # Remove import
        content = re.sub(f"import '../pages/{snake_name}_page.dart';\n", "", content)
        
        # Remove route constant
        content = re.sub(f"  static const String {snake_name} = '.*';\n", "", content)
        
        # Remove case block
        case_pattern = rf"      case {snake_name}:.*?\n\s+return MaterialPageRoute\(.*?settings: settings,.*?\);\n\s+"
        content = re.sub(case_pattern, "", content, flags=re.DOTALL)
        
        with open(routes_path, 'w') as f:
            f.write(content)
            
        console.print(f"[dim]Removed [bold]{page_name}[/bold] from routes[/dim]")
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not automatically update app_routes.dart: {e}[/yellow]")

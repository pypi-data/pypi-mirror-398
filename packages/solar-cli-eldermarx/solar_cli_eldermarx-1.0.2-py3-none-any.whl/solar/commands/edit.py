"""
SOLAR CLI - Edit Command
Edit existing pages/components using natural language
"""

import os
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from solar.ai import get_ai
from solar.utils.project import get_solar_project, get_component_path
from solar.generator.page import PageGenerator
from solar.utils.flutter import add_flutter_packages, check_flutter_installed

console = Console()


@click.command('edit')
@click.argument('component_name')
@click.argument('changes')
@click.option('--preview', '-p', is_flag=True, help='Preview changes before applying')
def edit_command(component_name: str, changes: str, preview: bool):
    """
    Edit an existing page or component using natural language.
    
    \b
    Examples:
      solx edit Home "add a floating action button"
      solx edit ProductList "make the cards bigger with shadows"
      solx edit Login "add forgot password link"
      solx edit Cart "change the button color to green"
    """
    # Check if we're in a SOLAR project
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        console.print("[dim]Run 'solx new <name>' to create a project first[/dim]")
        return
    
    # Find the component file
    component_path = get_component_path(project['path'], component_name)
    
    if not component_path:
        console.print(f"[red]❌ Component '{component_name}' not found[/red]")
        console.print("[dim]Available components:[/dim]")
        list_components(project['path'])
        return
    
    # Read current code
    with open(component_path, 'r') as f:
        current_code = f.read()
    
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Editing [cyan]{component_name}[/cyan]",
        border_style="cyan"
    ))
    console.print(f"[dim]Changes: \"{changes}\"[/dim]\n")
    # Read app_routes to give context to AI
    routes_context = ""
    routes_path = os.path.join(project['path'], 'lib', 'routes', 'app_routes.dart')
    if os.path.exists(routes_path):
        with open(routes_path, 'r') as f:
            routes_content = f.read()
            # Extract basic route info for context
            import re
            routes = re.findall(r'static const String (\w+) = [\'"](.+)[\'"];', routes_content)
            if routes:
                routes_context = "Available routes:\n" + "\n".join([f"- {name}: {path}" for name, path in routes])

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Step 1: Analyze changes with AI
        task1 = progress.add_task("[cyan]🤖 Analyzing your changes...", total=None)
        
        ai = get_ai()
        
        progress.update(task1, description="[green]✓ Changes analyzed")
        
        # Step 2: Generate updated code
        task2 = progress.add_task("[cyan]⚡ Generating updated code...", total=None)
        
        result = ai.edit_flutter_code(current_code, changes, component_name, context=routes_context)
        
        if not result:
            console.print("[red]❌ Could not generate updated code[/red]")
            return
            
        new_code = result.get('code', '')
        dependencies = result.get('dependencies', [])
            
        if new_code.strip() == current_code.strip():
            console.print("[yellow]⚠️ No changes were made.[/yellow]")
            console.print("[dim]The AI returned the same code. Try being more specific with your request.[/dim]")
            return
            
        progress.update(task2, description="[green]✓ Code updated")

        # Step 3: Install new dependencies
        if dependencies:
            task_dep = progress.add_task(f"[cyan]📦 Installing dependencies: {', '.join(dependencies)}...", total=None)
            add_flutter_packages(project['path'], dependencies)
            
            # Ensure pub get is run to resolve everything
            import subprocess
            subprocess.run(['flutter', 'pub', 'get'], cwd=project['path'], capture_output=True)
            
            progress.update(task_dep, description="[green]✓ Dependencies installed & resolved")
    
    # Preview mode
    if preview:
        console.print("\n[bold]Preview of changes:[/bold]\n")
        syntax = Syntax(new_code, "dart", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[cyan]{component_name}.dart[/cyan]", border_style="dim"))
        
        if not click.confirm("\n[yellow]Apply these changes?[/yellow]", default=True):
            console.print("[dim]Changes discarded[/dim]")
            return
    
    # Save changes
    with open(component_path, 'w') as f:
        f.write(new_code)
    
    console.print()
    console.print(Panel(
        f"""[green]✅ '[bold]{component_name}[/bold]' updated successfully![/green]

[dim]File modified:[/dim]
  [cyan]• {os.path.relpath(component_path, project['path'])}[/cyan]

[dim]To see the changes:[/dim]
  [cyan]solx run[/cyan]

[dim]To undo (if using git):[/dim]
  [cyan]git checkout -- {os.path.relpath(component_path, project['path'])}[/cyan]
""",
        title="[bold yellow]☀️ SOLAR[/bold yellow]",
        border_style="green"
    ))


def list_components(project_path: str):
    """List all available components in the project"""
    pages_dir = os.path.join(project_path, 'lib', 'pages')
    widgets_dir = os.path.join(project_path, 'lib', 'widgets')
    
    if os.path.exists(pages_dir):
        for f in os.listdir(pages_dir):
            if f.endswith('.dart'):
                name = f.replace('.dart', '').replace('_page', '').replace('_', ' ').title().replace(' ', '')
                console.print(f"  [cyan]• {name}[/cyan] (page)")
    
    if os.path.exists(widgets_dir):
        for f in os.listdir(widgets_dir):
            if f.endswith('.dart'):
                name = f.replace('.dart', '').replace('_widget', '').replace('_', ' ').title().replace(' ', '')
                console.print(f"  [cyan]• {name}[/cyan] (widget)")

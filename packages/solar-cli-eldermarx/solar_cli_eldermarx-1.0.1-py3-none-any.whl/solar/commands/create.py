"""
SOLAR CLI - Create Command
Create new pages/components using natural language
"""

import os
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.syntax import Syntax

from solar.generator.page import PageGenerator
from solar.ai import get_ai
from solar.utils.project import get_solar_project, update_solar_config
from solar.utils.flutter import add_flutter_packages

console = Console()


@click.command('create')
@click.argument('description')
@click.option('--type', '-t', 'component_type', default='page', 
              type=click.Choice(['page', 'widget', 'service']),
              help='Type of component to create')
def create_command(description: str, component_type: str):
    """
    Create a new page or component using natural language.
    
    \b
    Examples:
      solar create "a login page with email and password fields"
      solar create "a product list with cards showing image and price"
      solar create "a shopping cart page" --type page
      solar create "a custom button widget" --type widget
    """
    # Check if we're in a SOLAR project
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        console.print("[dim]Run 'solar new <name>' to create a project first[/dim]")
        return
    
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Creating {component_type}",
        border_style="cyan"
    ))
    console.print(f"[dim]Description: \"{description}\"[/dim]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Step 1: Analyze description with AI
        task1 = progress.add_task("[cyan]🤖 Analyzing your description...", total=None)
        
        ai = get_ai()
        analysis = ai.analyze_component(description, component_type)
        
        if not analysis:
            console.print("[red]❌ Could not analyze description. Check your API key.[/red]")
            return
        
        progress.update(task1, description=f"[green]✓ Analyzed: Creating '{analysis['name']}'")
        
        # Step 2: Generate Flutter code
        task2 = progress.add_task("[cyan]⚡ Generating Flutter code...", total=None)
        
        code = ai.generate_flutter_code(analysis, component_type)
        
        if not code:
            console.print("[red]❌ Could not generate code[/red]")
            return
        
        progress.update(task2, description="[green]✓ Code generated")
        
        # Step 3: Install dependencies
        all_dependencies = list(set(analysis.get('dependencies', []) + code.get('dependencies', [])))
        if all_dependencies:
            task_dep = progress.add_task("[cyan]📦 Installing dependencies...", total=None)
            add_flutter_packages(project['path'], all_dependencies)
            progress.update(task_dep, description="[green]✓ Dependencies installed")

        # Step 4: Save files
        task3 = progress.add_task("[cyan]💾 Saving files...", total=None)
        
        generator = PageGenerator(project['path'])
        files_created = generator.save_component(analysis['name'], code, component_type)
        
        # Update routes if it's a page
        if component_type == 'page':
            generator.update_routes(analysis['name'], analysis.get('route', f"/{analysis['name'].lower()}"))
        
        # Update SOLAR config
        update_solar_config(project['path'], analysis['name'], {
            'type': component_type,
            'description': description,
            'created_at': str(os.popen('date').read().strip())
        })
        
        progress.update(task3, description="[green]✓ Files saved")
    
    # Show result
    console.print()
    console.print(Panel(
        f"""[green]✅ {component_type.title()} '[bold]{analysis['name']}[/bold]' created![/green]

[dim]Files created:[/dim]
{chr(10).join(f'  [cyan]• {f}[/cyan]' for f in files_created)}

[dim]To edit this {component_type}:[/dim]
  [cyan]solar edit {analysis['name']} "your changes here"[/cyan]

[dim]To run the app:[/dim]
  [cyan]solar run[/cyan]
""",
        title="[bold yellow]☀️ SOLAR[/bold yellow]",
        border_style="green"
    ))
    
    # Preview code
    if click.confirm("\n[dim]Show generated code?[/dim]", default=False):
        console.print("\n")
        syntax = Syntax(code['main'], "dart", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"[cyan]{analysis['name']}.dart[/cyan]", border_style="dim"))

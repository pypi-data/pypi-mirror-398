"""
SOLAR CLI - New Command
Create a new Flutter application
"""

import os
import subprocess
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from solar.generator.project import ProjectGenerator
from solar.utils.flutter import check_flutter_installed

console = Console()


@click.command('new')
@click.argument('name')
@click.option('--template', '-t', default='default', help='Project template to use')
@click.option('--org', '-o', default='com.solarapp', help='Organization name (e.g., com.example)')
def new_command(name: str, template: str, org: str):
    """
    Create a new Flutter application.
    
    \b
    Examples:
      solar new myapp
      solar new ecommerce --org com.mycompany
    """
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Creating new app: [cyan]{name}[/cyan]",
        border_style="cyan"
    ))
    
    # Check Flutter installation
    if not check_flutter_installed():
        console.print("[red]❌ Flutter is not installed or not in PATH[/red]")
        console.print("[dim]Please install Flutter: https://docs.flutter.dev/get-started/install[/dim]")
        return
    
    # Create project directory
    project_dir = os.path.join(os.getcwd(), name)
    
    if os.path.exists(project_dir):
        if not click.confirm(f"[yellow]Directory '{name}' already exists. Overwrite?[/yellow]"):
            console.print("[dim]Operation cancelled[/dim]")
            return
        import shutil
        shutil.rmtree(project_dir)
    
    # Ensure directory exists
    os.makedirs(project_dir, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Step 1: Create Flutter project
        task = progress.add_task("[cyan]Creating Flutter project...", total=None)
        
        try:
            result = subprocess.run(
                ['flutter', 'create', '--org', org, '-e', '.'],
                capture_output=True,
                text=True,
                cwd=project_dir
            )
            
            if result.returncode != 0:
                console.print(f"[red]❌ Error creating Flutter project:[/red]\n{result.stderr}")
                return
            
            progress.update(task, description="[green]✓ Flutter project created")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")
            return
        
        # Step 2: Setup SOLAR structure
        task2 = progress.add_task("[cyan]Setting up SOLAR structure...", total=None)
        
        generator = ProjectGenerator(project_dir, name)
        generator.setup_structure()
        generator.create_base_files()
        generator.create_solar_config()
        
        progress.update(task2, description="[green]✓ SOLAR structure configured")
        
        # Step 3: Install dependencies
        task3 = progress.add_task("[cyan]Installing dependencies...", total=None)
        
        subprocess.run(
            ['flutter', 'pub', 'get'],
            capture_output=True,
            cwd=project_dir
        )
        
        progress.update(task3, description="[green]✓ Dependencies installed")
    
    console.print()
    console.print(Panel(
        f"""[green]✅ App '[bold]{name}[/bold]' created successfully![/green]

[dim]Next steps:[/dim]
  [cyan]cd solar_app[/cyan]
  [cyan]solar create 'uma página de login'[/cyan]
  [cyan]solar run[/cyan]

[dim]Or run directly:[/dim]
  [cyan]flutter run[/cyan]
""",
        title="[bold yellow]☀️ SOLAR[/bold yellow]",
        border_style="green"
    ))

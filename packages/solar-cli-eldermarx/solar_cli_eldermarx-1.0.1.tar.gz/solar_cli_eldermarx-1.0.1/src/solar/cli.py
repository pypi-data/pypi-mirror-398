"""
SOLAR CLI - Main entry point
Create Flutter apps with natural language
"""

import os

# Suppress annoying warnings and logs
import warnings
warnings.filterwarnings("ignore")
os.environ['GRPC_VERBOSITY'] = 'NONE'
os.environ['GLOG_minloglevel'] = '3'

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from solar import __version__, __author__
from solar.commands.new import new_command
from solar.commands.create import create_command
from solar.commands.edit import edit_command
from solar.commands.run import run_command
from solar.commands.config import config_command
from solar.commands.list import list_command
from solar.commands.delete import delete_command
from solar.commands.style import style_command
from solar.commands.init import init_command

console = Console()


def show_banner():
    """Display the SOLAR CLI banner"""
    ascii_art = r"""
   _____  ____  _             _____  
  / ____|/ __ \| |           |  __ \ 
 | (___ | |  | | |      /\   | |__) |
  \___ \| |  | | |     /  \  |  _  / 
  ____) | |__| | |____/ /\ \ | | \ \ 
 |_____/ \____/|______/_/  \_\_|  \_\
    """
    banner = Text()
    banner.append(ascii_art, style="bold #FF8C00") # Neon orange
    console.print(banner)
    console.print(f"      [bold yellow]SOLAR[/bold yellow] [dim white]Version {__version__}[/dim white]")
    console.print(f"      [dim magenta]Created by {__author__}[/dim magenta]\n")


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version')
@click.pass_context
def main(ctx, version):
    """
    ☀️ SOLAR CLI by Elder Marx
    
    Create Flutter apps using natural language commands.
    
    \b
    Examples:
      solar init                   Initialize the CLI
      solar new myapp              Create a new Flutter app
      solar create "a login page"  Create a new page/component
      solar edit Home "add a drawer"  Edit an existing page
      solar run                    Run the Flutter app
    """
    if version:
        console.print(f"[bold yellow]SOLAR[/bold yellow] version [cyan]{__version__}[/cyan]")
        return
    
    if ctx.invoked_subcommand is None:
        show_banner()
        console.print("[dim]Use [bold]solar --help[/bold] to see available commands[/dim]\n")


# Register commands
main.add_command(init_command, name='init')
main.add_command(new_command, name='new')
main.add_command(create_command, name='create')
main.add_command(edit_command, name='edit')
main.add_command(run_command, name='run')
main.add_command(config_command, name='config')
main.add_command(list_command, name='list')
main.add_command(delete_command, name='delete')
main.add_command(style_command, name='style')


if __name__ == '__main__':
    main()

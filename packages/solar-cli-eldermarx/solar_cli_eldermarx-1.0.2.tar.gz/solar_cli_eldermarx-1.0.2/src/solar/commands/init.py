"""
SOLAR CLI - Init Command
Initialize the SOLAR environment
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from solar.utils.config import set_config, get_config

console = Console()

def show_neon_solar():
    banner = Text()
    # SOLAR in ASCII art - Blocky and Neon
    ascii_art = r"""
   _____  ____  _             _____  
  / ____|/ __ \| |           |  __ \ 
 | (___ | |  | | |      /\   | |__) |
  \___ \| |  | | |     /  \  |  _  / 
  ____) | |__| | |____/ /\ \ | | \ \ 
 |_____/ \____/|______/_/  \_\_|  \_\
    """
    banner.append(ascii_art, style="bold #FF6600") # Vivid Neon Orange
    console.print(banner)

def show_examples():
    console.print("\n[bold]Eis o que você pode fazer:[/bold]")
    console.print("  [bold #FF6600]solx new [myapp][/bold #FF6600]       [dim]- Cria um novo app Flutter do zero[/dim]")
    console.print("  [bold #FF6600]solx create [desc][/bold #FF6600]    [dim]- Gera uma nova página ou widget[/dim]")
    console.print("  [bold #FF6600]solx edit [page] [desc][/bold #FF6600] [dim]- Modifica código existente[/dim]")
    console.print("  [bold #FF6600]solx run[/bold #FF6600]              [dim]- Roda seu app no simulador[/dim]\n")

@click.command()
def init_command():
    """Inicializa o SOLAR CLI"""
    show_neon_solar()
    console.print("[bold yellow]Bem-vindo ao SOLAR - O Futuro do Desenvolvimento Flutter[/bold yellow]\n")
    
    show_examples()
    
    console.print("[bold]Configuração do Modelo de IA[/bold]")
    provider = Prompt.ask("Escolha o provedor de IA", choices=["gemini", "openai"], default="gemini")
    
    if provider == "gemini":
        api_key = Prompt.ask("Insira sua Gemini API Key")
        model = "gemini-2.0-flash-lite"
    else:
        api_key = Prompt.ask("Insira sua OpenAI API Key")
        model = "gpt-4o-mini"
        console.print("[dim]Configurando modelo OpenAI 4.1-mini (mapeado para gpt-4o-mini)...[/dim]")

    set_config("ai_provider", provider)
    set_config("api_key", api_key)
    set_config("model_name", model)
    
    console.print(f"\n[bold green]✅ Configuração salva com sucesso![/bold green]")
    console.print(f"Provedor: [cyan]{provider}[/cyan]")
    console.print(f"Modelo: [cyan]{model}[/cyan]")
    console.print("\nAgora você pode começar com: [bold]solx new nomedoapp[/bold]\n")

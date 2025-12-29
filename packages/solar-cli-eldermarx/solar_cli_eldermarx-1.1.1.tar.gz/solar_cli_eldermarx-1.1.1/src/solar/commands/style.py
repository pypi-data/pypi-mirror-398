"""
SOLAR CLI - Style Command
Update app theme and styles using natural language
"""

import os
import click
from rich.console import Console
from rich.panel import Panel

from solar.ai.gemini import GeminiAI
from solar.utils.project import get_solar_project

console = Console()

@click.command('style')
@click.argument('description')
def style_command(description: str):
    """
    Update the application theme/style using natural language.
    
    \b
    Examples:
      solx style "mude a cor primária para um azul escuro"
      solx style "faça os botões terem bordas mais arredondadas"
      solx style "adicione um tema escuro com tons de roxo"
    """
    project = get_solar_project()
    if not project:
        console.print("[red]❌ Not in a SOLAR project directory[/red]")
        return
    
    theme_path = os.path.join(project['path'], 'lib', 'theme', 'app_theme.dart')
    
    if not os.path.exists(theme_path):
        console.print("[red]❌ lib/theme/app_theme.dart not found[/red]")
        return
        
    with open(theme_path, 'r') as f:
        current_theme = f.read()
    
    console.print(Panel.fit(
        f"[bold yellow]☀️ SOLAR[/bold yellow] - Updating Style",
        border_style="cyan"
    ))
    console.print(f"[dim]Request: \"{description}\"[/dim]\n")
    
    ai = GeminiAI()
    
    # We can reuse edit_flutter_code or create a specialized prompt
    # Using a specialized prompt for theme might be better
    
    prompt = f"""You are a Flutter UI/UX expert. You are editing the 'app_theme.dart' file of a Flutter project.
    
Current theme code:
```dart
{current_theme}
```

User request: "{description}"

Modify the theme code to satisfy the user request. 
Requirements:
1. Maintain the Material 3 structure
2. Keep the existing class name 'AppTheme'
3. Only change colors, shapes, or themes related to the request
4. Return ONLY the complete updated Dart code, no explanations or markdown.

Return the code now:
"""
    
    with console.status("[cyan]🤖 Updating theme..."):
        new_theme = ai._call_gemini(prompt)
        
        if not new_theme:
            console.print("[red]❌ Could not generate updated theme[/red]")
            return
            
        # Clean response
        if new_theme.startswith('```'):
            import re
            new_theme = re.sub(r'^```\w*\n?', '', new_theme)
            new_theme = re.sub(r'\n?```$', '', new_theme)
            
        with open(theme_path, 'w') as f:
            f.write(new_theme)
            
    console.print("[green]✅ Theme updated successfully![/green]")
    console.print("[dim]Check lib/theme/app_theme.dart to see the changes[/dim]")

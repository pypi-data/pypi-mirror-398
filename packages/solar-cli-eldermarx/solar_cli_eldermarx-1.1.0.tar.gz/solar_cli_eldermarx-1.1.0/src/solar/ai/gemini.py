"""
SOLAR CLI - Gemini AI Integration
Uses Google Gemini for natural language to Flutter code generation
"""

import os
import json
import re
from typing import Optional, Dict, Any
from rich.console import Console
import warnings
import logging

# Suppress annoying warnings from google-generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
# Suppress gRPC logs
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

from solar.utils.config import get_config, set_config
from solar.ai.base import BaseAI
import click

# Try to import google.generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiAI(BaseAI):
    """AI-powered Flutter code generation using Google Gemini"""
    
    def __init__(self):
        self.console = Console()
        self.api_key = get_config().get('api_key') or os.getenv('GEMINI_API_KEY')
        self.model_name = get_config().get('model_name') or 'gemini-2.0-flash-lite'
        self.model = None
        
        if not self.api_key:
            self.console.print("\n[yellow]⚠️  Google Gemini API Key needed[/yellow]")
            self.console.print("[dim]The key is stored locally in ~/.solar/config.yaml[/dim]")
            try:
                self.api_key = click.prompt(click.style("Enter your Gemini API Key", fg="cyan"), hide_input=True)
                set_config('api_key', self.api_key)
                self.console.print("[green]API Key saved![/green]\n")
            except click.Abort:
                self.console.print("\n[red]Operation cancelled.[/red]")
                return

        if self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)
            try:
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={
                        "temperature": 0.7,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096,
                    }
                )
            except Exception as e:
                self.console.print(f"[red]Error initializing Gemini model ({self.model_name}):[/red] {e}")
                self.model = None
            
    SYSTEM_PROMPT = """Você é o SOLAR AI, um especialista sênior em Flutter criado por Elder Marx.
Sua missão é ajudar desenvolvedores a criarem aplicativos incríveis usando linguagem natural.

Diretrizes:
1. Gere código Dart moderno, limpo e bem estruturado.
2. Use Material 3 por padrão.
3. Siga as melhores práticas da comunidade Flutter.
4. Adicione comentários úteis e explicativos em Português (Brasil).
5. Se for criar uma página, use Scaffold, AppBar e SafeArea.
6. Garanta que o design seja visualmente atraente e responsivo.
7. IMPORTANTE: Ao usar cores Hex, use a sintaxe correta: Color(0xFF123456). NUNCA coloque aspas dentro do parênteses.
   Errado: Color(0xFF123456'), Color('0xFF123456')
   Correto: Color(0xFF123456)
8. Verifique se todas as strings e parênteses estão fechados corretamente.
9. IMPORTANTE: Sempre que você usar um pacote externo (como table_calendar, intl, http, shared_preferences, etc), certifique-se de retornar os nomes exatos desses pacotes no campo 'dependencies' para que o sistema possa instalá-los automaticamente.
10. Se usar pacotes que acessam hardware ou armazenamento local (como shared_preferences), lembre o usuário no código que é necessário inicializar o binding ou que o app precisa de um restart completo.
"""
    
    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Gemini API with a prompt"""
        if not self.api_key:
            self.console.print("\n[red]❌ Google Gemini API Key not found![/red]")
            self.console.print("[dim]Please set it using: [cyan]solar config set api_key YOUR_KEY[/cyan][/dim]\n")
            return None

        if not GEMINI_AVAILABLE:
            self.console.print("\n[red]❌ 'google-generativeai' package not installed.[/red]")
            self.console.print("[dim]Please install it: [cyan]pip install google-generativeai[/cyan][/dim]\n")
            return None

        if not self.model:
            self.console.print("\n[red]❌ Gemini model not initialized.[/red]")
            return None
        
        try:
            full_prompt = f"{self.SYSTEM_PROMPT}\n\nTarefa: {prompt}"
            response = self.model.generate_content(full_prompt)
            
            # Check if we have a valid response text
            try:
                if response.text:
                    return response.text
            except ValueError:
                # If the response doesn't have text (e.g. blocked by safety)
                self.console.print("[red]Gemini API error:[/red] Response was blocked/empty.")
                if hasattr(response, 'prompt_feedback'):
                    self.console.print(f"[dim]Note: {response.prompt_feedback}[/dim]")
                return None
                
            return None
        except Exception as e:
            self.console.print(f"[red]Gemini API error:[/red] {e}")
            return None
    
    def _fallback_response(self, prompt: str) -> str:
        """Fallback when API is not available"""
        # Extract component name from prompt if possible
        return None
    
    def analyze_component(self, description: str, component_type: str) -> Optional[Dict[str, Any]]:
        """Analyze a natural language description and extract component details"""
        prompt = f"""Analyze this Flutter {component_type} description and extract the following information.
Return ONLY a valid JSON object with no markdown formatting.

Description: "{description}"

Return JSON with these fields:
- name: PascalCase name for the {component_type} (e.g., "ProductList", "LoginPage", "CartButton")
- route: URL route for the page if it's a page (e.g., "/products", "/login")
- features: array of features/elements to include
- colors: suggested color scheme (primary, secondary, accent)
- state_variables: array of state variables needed
- dependencies: array of Flutter packages that might be useful

Example response:
{{"name": "ProductList", "route": "/products", "features": ["grid of products", "product cards", "price display"], "colors": {{"primary": "blue", "secondary": "white"}}, "state_variables": ["products", "isLoading"], "dependencies": []}}
"""
        
        response = self._call_gemini(prompt)
        
        if not response:
            # Fallback: generate basic analysis from description
            name = self._extract_name(description, component_type)
            return {
                'name': name,
                'route': f"/{name.lower()}",
                'features': [description],
                'colors': {'primary': 'blue', 'secondary': 'white'},
                'state_variables': [],
                'dependencies': []
            }
        
        try:
            # Clean response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```'):
                clean_response = re.sub(r'^```\w*\n?', '', clean_response)
                clean_response = re.sub(r'\n?```$', '', clean_response)
            
            return json.loads(clean_response)
        except json.JSONDecodeError:
            name = self._extract_name(description, component_type)
            return {
                'name': name,
                'route': f"/{name.lower()}",
                'features': [description],
                'colors': {'primary': 'blue', 'secondary': 'white'},
                'state_variables': [],
                'dependencies': []
            }
    
    def _extract_name(self, description: str, component_type: str) -> str:
        """Extract a component name from description"""
        # Common patterns
        patterns = [
            r"(?:página|page|tela|screen)\s+(?:de\s+)?(\w+)",
            r"(\w+)\s+(?:página|page|tela|screen)",
            r"(?:lista|list)\s+(?:de\s+)?(\w+)",
            r"(\w+)\s+(?:lista|list)",
            r"(?:chamada?|called?)\s+(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(1)
                return name.title().replace(' ', '')
        
        # Fallback: use first significant word
        words = description.split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                return word.title()
        
        return f"New{component_type.title()}"
    
    def generate_flutter_code(self, analysis: Dict[str, Any], component_type: str) -> Optional[Dict[str, Any]]:
        """Generate Flutter code based on analysis"""
        prompt = f"""Generate Flutter code for a {component_type} with these specifications:

Name: {analysis['name']}
Features: {', '.join(analysis.get('features', []))}
Colors: {analysis.get('colors', {})}
State Variables: {analysis.get('state_variables', [])}

Requirements:
1. Use modern Flutter best practices
2. Use StatefulWidget if state is needed, otherwise StatelessWidget
3. Include proper imports
4. Add helpful comments in Portuguese (Brazilian)
5. Make the UI beautiful and modern with proper spacing, shadows, and colors
6. Use Material 3 design principles
7. Make it responsive

Return a JSON with:
- code: The Dart code
- dependencies: Array of strings with needed packages (e.g. ["table_calendar", "intl"])
"""
        
        response = self._call_gemini(prompt)
        
        if response:
            try:
                # Clean response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```'):
                    clean_response = re.sub(r'^```\w*\n?', '', clean_response)
                    clean_response = re.sub(r'\n?```$', '', clean_response)
                
                data = json.loads(clean_response)
                return {
                    'main': data.get('code', ''),
                    'dependencies': data.get('dependencies', [])
                }
            except:
                # Fallback to direct code extraction
                return {
                    'main': self._extract_code(response),
                    'dependencies': analysis.get('dependencies', [])
                }
        
        # Fallback: generate template code
        return {'main': self._generate_template(analysis, component_type), 'dependencies': []}
    
    def _generate_template(self, analysis: Dict[str, Any], component_type: str) -> str:
        """Generate template Flutter code"""
        name = analysis['name']
        
        if component_type == 'page':
            return f'''import 'package:flutter/material.dart';

/// {name} Page
/// Criado com SOLAR CLI by Elder Marx
class {name}Page extends StatefulWidget {{
  const {name}Page({{super.key}});

  @override
  State<{name}Page> createState() => _{name}PageState();
}}

class _{name}PageState extends State<{name}Page> {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: const Text('{name}'),
        centerTitle: true,
        elevation: 0,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // TODO: Implementar {', '.join(analysis.get('features', ['conteúdo']))}
              const Center(
                child: Text(
                  'Página {name}',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              const Expanded(
                child: Center(
                  child: Text(
                    '☀️ Criado com SOLAR CLI',
                    style: TextStyle(color: Colors.grey),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }}
}}
'''
        elif component_type == 'widget':
            return f'''import 'package:flutter/material.dart';

/// {name} Widget
/// Criado com SOLAR CLI by Elder Marx
class {name}Widget extends StatelessWidget {{
  const {name}Widget({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: const Text('{name}'),
    );
  }}
}}
'''
        else:
            return f'''/// {name} Service
/// Criado com SOLAR CLI by Elder Marx
class {name}Service {{
  // TODO: Implementar serviço
  
  Future<void> init() async {{
    // Inicialização
  }}
}}
'''
    
    def edit_flutter_code(self, current_code: str, changes: str, component_name: str, context: str = "") -> Optional[Dict[str, Any]]:
        """Edit existing Flutter code based on natural language changes"""
        prompt = f"""You are editing a Flutter component called '{component_name}'.

Current code:
```dart
{current_code}
```

Context (Available routes/pages):
{context}

User requested changes: "{changes}"

Apply the requested changes to the code. Requirements:
1. Maintain the existing code structure
2. Only modify what's necessary for the requested changes
3. Keep all existing functionality unless explicitly asked to remove
4. Use modern Flutter best practices
5. Add comments in Portuguese for new code
6. If navigating to another page, use Navigator.pushNamed(context, '/route_name') using the routes from Context.
7. DO NOT add new class definitions for pages that already exist in other files. Import them or use named routes.

Return a JSON with:
- code: The complete updated Dart code
- dependencies: Array of strings with any NEW packages needed (e.g. ["table_calendar", "intl"])
"""
        
        response = self._call_gemini(prompt)
        
        if response:
            try:
                # Clean response - remove markdown code blocks if present
                clean_response = response.strip()
                if clean_response.startswith('```'):
                    clean_response = re.sub(r'^```\w*\n?', '', clean_response)
                    clean_response = re.sub(r'\n?```$', '', clean_response)
                
                data = json.loads(clean_response)
                return {
                    'code': data.get('code', ''),
                    'dependencies': data.get('dependencies', [])
                }
            except:
                # Fallback to direct code extraction
                return {
                    'code': self._extract_code(response),
                    'dependencies': []
                }
        
        # If API fails, return None so the caller knows it failed
        return None

    def _extract_code(self, response: str) -> str:
        """Extract code block from response"""
        # Try to find code between backticks
        match = re.search(r'```(?:dart)?\n?(.*?)\n?```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no backticks, return the whole thing cleaned
        return response.strip()

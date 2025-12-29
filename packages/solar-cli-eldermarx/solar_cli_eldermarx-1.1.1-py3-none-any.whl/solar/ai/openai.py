"""
SOLAR CLI - OpenAI Integration
Uses OpenAI for natural language to Flutter code generation
"""

import os
import json
import re
from typing import Optional, Dict, Any
from rich.console import Console
from solar.utils.config import get_config
from solar.ai.base import BaseAI

# Try to import openai
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAI(BaseAI):
    """AI-powered Flutter code generation using OpenAI"""
    
    def __init__(self):
        self.console = Console()
        self.api_key = get_config().get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model_name = get_config().get('model_name') or 'gpt-4o-mini'
        self.client = None
        
        if self.api_key and OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=self.api_key)

    SYSTEM_PROMPT = """Você é o SOLAR AI, um especialista sênior em Flutter criado por Elder Marx.
Sua missão é ajudar desenvolvedores a criarem aplicativos incríveis usando linguagem natural.

Diretrizes:
1. Gere código Dart moderno, limpo e bem estruturado.
2. Use Material 3 por padrão.
3. Siga as melhores práticas da comunidade Flutter.
4. Adicione comentários úteis e explicativos em Português (Brasil).
5. Se for criar uma página, use Scaffold, AppBar e SafeArea.
8. Verifique se todas as strings e parênteses estão fechados corretamente.
9. PRESTE MUITA ATENÇÃO a dependências e pacotes.
   - Se o usuário pedir "calendário", você DEVE usar o pacote `table_calendar` e listá-lo em dependencies.
   - Se pedir "mapa", use `google_maps_flutter`.
   - Se pedir "ícones", use `font_awesome_flutter` se necessário.
   - Sua resposta DEVE ser um JSON válido.
10. Se usar pacotes que acessam hardware ou armazenamento local (como shared_preferences), lembre o usuário no código que é necessário inicializar o binding ou que o app precisa de um restart completo.
11. SUPABASE: Ao usar supabase_flutter, use a sintaxe MODERNA (sem .execute()):
    ✅ CORRETO: final data = await supabase.from('users').select();
    ❌ ERRADO: final data = await supabase.from('users').select().execute();
    - Para INSERT: await supabase.from('tabela').insert({'campo': 'valor'});
    - Para UPDATE: await supabase.from('tabela').update({'campo': 'novo'}).eq('id', 1);
    - Para DELETE: await supabase.from('tabela').delete().eq('id', 1);
    - Inicializar Supabase no main.dart: await Supabase.initialize(url: 'URL', anonKey: 'KEY');
    - Obter client: final supabase = Supabase.instance.client;
"""

    def _call_openai(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Call OpenAI API with a prompt"""
        if not self.api_key:
            self.console.print("\n[red]❌ OpenAI API Key not found![/red]")
            self.console.print("[dim]Please set it using: [cyan]solar init[/cyan][/dim]\n")
            return None

        if not OPENAI_AVAILABLE:
            self.console.print("\n[red]❌ 'openai' package not installed.[/red]")
            self.console.print("[dim]Please install it: [cyan]pip install openai[/cyan][/dim]\n")
            return None

        if not self.client:
            self.console.print("\n[red]❌ OpenAI client not initialized.[/red]")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt or self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.console.print(f"[red]OpenAI API error:[/red] {e}")
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
"""
        
        response = self._call_openai(prompt)
        
        if not response:
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
5. Make the UI beautiful and modern
6. Use Material 3 design principles
7. Make it responsive

Your response MUST be a raw JSON object (no markdown, no backticks):
{{
  "dependencies": ["package_name_1", "package_name_2"],
  "code": "import 'package:flutter/material.dart';\\n..."
}}
"""
        
        response = self._call_openai(prompt)
        
        if response:
            try:
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
                return {'main': self._extract_code(response), 'dependencies': []}
        
        return None

    def edit_flutter_code(self, current_code: str, changes: str, component_name: str, context: str = "") -> Optional[Dict[str, Any]]:
        """Edit existing Flutter code based on natural language changes"""
        prompt = f"""You are editing a Flutter component called '{component_name}'.
        
Task: Analyze the user request and the current code. 
1. Identify if any NEW Flutter packages are needed (e.g. 'table_calendar', 'google_fonts').
2. Edit the code to implement the features.
3. Return a strict JSON object.

Current code:
```dart
{current_code}
```

Context (Available routes/pages):
{context}

User requested changes: "{changes}"

Apply the requested changes.
Return a valid JSON object with:
- "code": The complete updated Dart code (including all imports, no markdown)
- "dependencies": A list of STRINGS with the new package names.

Example JSON response:
{{
  "dependencies": ["table_calendar", "intl"],
  "code": "import 'package:flutter/material.dart';\\nimport 'package:table_calendar/table_calendar.dart';\\n..."
}}
"""
        
        response = self._call_openai(prompt)
        
        if response:
            try:
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
                return {'code': self._extract_code(response), 'dependencies': []}
        
        return None

    def _extract_code(self, response: str) -> str:
        """Extract code block from response"""
        match = re.search(r'```(?:dart)?\n?(.*?)\n?```', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()

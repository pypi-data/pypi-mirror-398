"""
SOLAR CLI - Page Generator
Generates and manages Flutter pages and widgets
"""

import os
import re
from typing import Dict, List, Optional


class PageGenerator:
    """Generates Flutter pages and widgets"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.lib_path = os.path.join(project_path, 'lib')
    
    def save_component(self, name: str, code: Dict[str, str], component_type: str) -> List[str]:
        """Save a component to the project"""
        files_created = []
        
        # Determine directory based on type
        if component_type == 'page':
            directory = os.path.join(self.lib_path, 'pages')
            suffix = '_page'
            # Remove suffix if already present to avoid double suffix
            clean_name = self._to_snake_case(name).replace('_page', '')
            filename = f"{clean_name}{suffix}.dart"
        elif component_type == 'widget':
            directory = os.path.join(self.lib_path, 'widgets')
            suffix = '_widget'
            clean_name = self._to_snake_case(name).replace('_widget', '')
            filename = f"{clean_name}{suffix}.dart"
        else:
            directory = os.path.join(self.lib_path, 'services')
            suffix = '_service'
            clean_name = self._to_snake_case(name).replace('_service', '')
            filename = f"{clean_name}{suffix}.dart"
        
        os.makedirs(directory, exist_ok=True)
        
        # Save main file
        file_path = os.path.join(directory, filename)
        with open(file_path, 'w') as f:
            f.write(code['main'])
        
        files_created.append(os.path.relpath(file_path, self.project_path))
        
        return files_created
    
    def update_routes(self, page_name: str, route: str):
        """Update app_routes.dart with a new page route"""
        routes_file = os.path.join(self.lib_path, 'routes', 'app_routes.dart')
        
        if not os.path.exists(routes_file):
            return
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        snake_name = self._to_snake_case(page_name).replace('_page', '')
        pascal_name = self._to_pascal_case(snake_name)
        class_name = f"{pascal_name}Page"
        
        # Add import
        import_line = f"import '../pages/{snake_name}_page.dart';\n"
        if import_line not in content:
            # Find last import and add after it
            last_import = content.rfind("import '")
            if last_import != -1:
                end_of_import = content.find(";\n", last_import) + 2
                content = content[:end_of_import] + import_line + content[end_of_import:]
        
        # Add route constant
        route_const = f"  static const String {snake_name} = '{route}';\n"
        if route_const not in content:
            # Find where to add the constant (after home constant)
            home_const = content.find("static const String home = '/';\n")
            if home_const != -1:
                insert_pos = home_const + len("static const String home = '/';\n")
                content = content[:insert_pos] + route_const + content[insert_pos:]
        
        # Add case in switch
        case_code = f'''      case {snake_name}:
        return MaterialPageRoute(
          builder: (_) => const {class_name}(),
          settings: settings,
        );
      
'''
        if f"case {snake_name}:" not in content:
            # Find default case and add before it
            default_case = content.find("      default:")
            if default_case != -1:
                content = content[:default_case] + case_code + content[default_case:]
        
        with open(routes_file, 'w') as f:
            f.write(content)
    
    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase"""
        return ''.join(word.title() for word in name.split('_'))

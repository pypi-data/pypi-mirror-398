"""
SOLAR CLI - Project Utilities
"""

import os
import yaml
from typing import Dict, Any, Optional

def get_solar_project() -> Optional[Dict[str, Any]]:
    """
    Check if the current directory or its parents is a SOLAR project.
    Returns a dictionary with project info or None if not found.
    """
    current_dir = os.getcwd()
    
    # Check current directory and parents
    while current_dir != os.path.dirname(current_dir):
        config_path = os.path.join(current_dir, '.solar', 'config.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                return {
                    'path': current_dir,
                    'name': config.get('name', 'Unknown'),
                    'config': config
                }
            except Exception:
                pass
        
        # Also check for solar_app subdirectory (convenience)
        solar_app_dir = os.path.join(current_dir, 'solar_app')
        config_path = os.path.join(solar_app_dir, '.solar', 'config.yaml')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                return {
                    'path': solar_app_dir,
                    'name': config.get('name', 'Unknown'),
                    'config': config
                }
            except Exception:
                pass
                
        current_dir = os.path.dirname(current_dir)
        
    return None

def update_solar_config(project_path: str, component_name: str, info: Dict[str, Any]):
    """Update the .solar/config.yaml file with new component info"""
    config_path = os.path.join(project_path, '.solar', 'config.yaml')
    
    if not os.path.exists(config_path):
        return
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        
        if 'components' not in config:
            config['components'] = {'pages': [], 'widgets': [], 'services': []}
        
        comp_type = info.get('type', 'page')
        plural_type = f"{comp_type}s"
        
        if plural_type not in config['components']:
            config['components'][plural_type] = []
            
        if component_name not in config['components'][plural_type]:
            config['components'][plural_type].append(component_name)
            
        # Add history or metadata if needed
        if 'history' not in config:
            config['history'] = []
            
        config['history'].append({
            'component': component_name,
            'type': comp_type,
            'action': 'create',
            'timestamp': info.get('created_at', '')
        })
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
            
    except Exception as e:
        print(f"Error updating solar config: {e}")

def get_component_path(project_path: str, component_name: str) -> Optional[str]:
    """Find the file path for a component by its name"""
    # Try different directories
    search_dirs = [
        os.path.join(project_path, 'lib', 'pages'),
        os.path.join(project_path, 'lib', 'widgets'),
        os.path.join(project_path, 'lib', 'services'),
    ]
    
    # Try snake_case names
    snake_name = _to_snake_case(component_name)
    possible_filenames = [
        f"{snake_name}.dart",
        f"{snake_name}_page.dart",
        f"{snake_name}_widget.dart",
        f"{snake_name}_service.dart",
    ]
    
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
            
        for filename in possible_filenames:
            full_path = os.path.join(directory, filename)
            if os.path.exists(full_path):
                return full_path
    
    return None

def _to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case"""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

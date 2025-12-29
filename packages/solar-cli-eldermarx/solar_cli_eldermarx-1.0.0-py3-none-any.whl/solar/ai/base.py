"""
SOLAR CLI - Base AI Class
"""

from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

class BaseAI(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def analyze_component(self, description: str, component_type: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def generate_flutter_code(self, analysis: Dict[str, Any], component_type: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def edit_flutter_code(self, current_code: str, changes: str, component_name: str, context: str = "") -> Optional[Dict[str, Any]]:
        pass

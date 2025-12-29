"""
SOLAR CLI - AI Factory
"""

from solar.utils.config import get_config
from .gemini import GeminiAI
from .openai import OpenAI
from .base import BaseAI

def get_ai() -> BaseAI:
    """Return the configured AI provider"""
    config = get_config()
    provider = config.get('ai_provider', 'gemini')
    
    if provider == 'openai':
        return OpenAI()
    else:
        return GeminiAI()

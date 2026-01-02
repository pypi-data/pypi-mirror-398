"""
nlpcmd-ai: A true NLP-powered command line assistant

This package provides an AI-powered CLI assistant that understands
natural language commands and executes system operations intelligently.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .engine import AIEngine, CommandIntent, AIProvider
from .base_handler import BaseHandler, CommandResult, HandlerRegistry
from .config import Config

__all__ = [
    'AIEngine',
    'CommandIntent',
    'AIProvider',
    'BaseHandler',
    'CommandResult',
    'HandlerRegistry',
    'Config',
]

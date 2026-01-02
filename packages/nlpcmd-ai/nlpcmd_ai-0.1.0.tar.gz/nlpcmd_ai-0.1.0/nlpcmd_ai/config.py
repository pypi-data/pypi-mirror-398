"""
Configuration Management

Handles loading and managing configuration from files and environment variables.
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Config:
    """Application configuration"""
    
    # AI Settings
    ai_provider: str = "openai"
    ai_model: Optional[str] = None
    ai_temperature: float = 0.3
    
    # Safety Settings
    require_confirmation: bool = True
    dry_run_mode: bool = False
    dangerous_patterns: List[str] = field(default_factory=lambda: [
        "rm -rf",
        "dd if=",
        "mkfs",
        "format",
        "> /dev/",
        "sudo rm",
        "del /f /s /q",
    ])
    allowed_directories: List[str] = field(default_factory=list)
    
    # Logging Settings
    log_commands: bool = True
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Handler Settings
    custom_handlers_path: Optional[str] = None
    
    # API Keys (loaded from environment)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        Load configuration from file and environment
        
        Priority (highest to lowest):
        1. Environment variables
        2. Config file specified by --config
        3. ~/.nlpcmd_ai/config.yaml
        4. Default values
        """
        config = cls()
        
        # Try to load from file
        if config_path:
            config._load_from_file(config_path)
        else:
            # Try default location
            default_config = Path.home() / ".nlpcmd_ai" / "config.yaml"
            if default_config.exists():
                config._load_from_file(str(default_config))
        
        # Override with environment variables
        config._load_from_env()
        
        return config
    
    def _load_from_file(self, path: str):
        """Load configuration from YAML file"""
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return
            
            # AI settings
            if 'ai' in data:
                ai_config = data['ai']
                self.ai_provider = ai_config.get('provider', self.ai_provider)
                self.ai_model = ai_config.get('model', self.ai_model)
                self.ai_temperature = ai_config.get('temperature', self.ai_temperature)
            
            # Safety settings
            if 'safety' in data:
                safety_config = data['safety']
                self.require_confirmation = safety_config.get('require_confirmation', self.require_confirmation)
                self.dangerous_patterns = safety_config.get('dangerous_patterns', self.dangerous_patterns)
                self.allowed_directories = safety_config.get('allowed_directories', self.allowed_directories)
            
            # Logging settings
            if 'logging' in data:
                log_config = data['logging']
                self.log_commands = log_config.get('enabled', self.log_commands)
                self.log_level = log_config.get('level', self.log_level)
                self.log_file = log_config.get('file', self.log_file)
            
            # Handler settings
            if 'handlers' in data:
                handler_config = data['handlers']
                self.custom_handlers_path = handler_config.get('custom_path', self.custom_handlers_path)
                
        except Exception as e:
            print(f"Warning: Failed to load config from {path}: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # AI provider
        if os.getenv('NLP_PROVIDER'):
            self.ai_provider = os.getenv('NLP_PROVIDER')
        
        if os.getenv('NLP_MODEL'):
            self.ai_model = os.getenv('NLP_MODEL')
        
        # API Keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Safety settings
        if os.getenv('REQUIRE_CONFIRMATION'):
            self.require_confirmation = os.getenv('REQUIRE_CONFIRMATION').lower() == 'true'
        
        if os.getenv('DRY_RUN_MODE'):
            self.dry_run_mode = os.getenv('DRY_RUN_MODE').lower() == 'true'
        
        if os.getenv('LOG_COMMANDS'):
            self.log_commands = os.getenv('LOG_COMMANDS').lower() == 'true'
        
        # Custom handlers
        if os.getenv('CUSTOM_HANDLERS_PATH'):
            self.custom_handlers_path = os.getenv('CUSTOM_HANDLERS_PATH')
    
    def save(self, path: Optional[str] = None):
        """Save configuration to YAML file"""
        if not path:
            config_dir = Path.home() / ".nlpcmd_ai"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = str(config_dir / "config.yaml")
        
        config_data = {
            'ai': {
                'provider': self.ai_provider,
                'model': self.ai_model,
                'temperature': self.ai_temperature,
            },
            'safety': {
                'require_confirmation': self.require_confirmation,
                'dangerous_patterns': self.dangerous_patterns,
                'allowed_directories': self.allowed_directories,
            },
            'logging': {
                'enabled': self.log_commands,
                'level': self.log_level,
                'file': self.log_file,
            },
            'handlers': {
                'custom_path': self.custom_handlers_path,
            }
        }
        
        with open(path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
    
    def is_dangerous_command(self, command: str) -> bool:
        """Check if a command contains dangerous patterns"""
        command_lower = command.lower()
        return any(pattern.lower() in command_lower for pattern in self.dangerous_patterns)

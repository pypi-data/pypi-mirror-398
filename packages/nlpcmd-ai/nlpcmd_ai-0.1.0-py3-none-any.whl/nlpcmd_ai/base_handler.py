"""
Base Handler and Handler Registry

Handlers are responsible for executing specific types of commands.
Each handler knows how to execute commands in its domain (files, network, etc.)
"""

import os
import subprocess
import platform
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result from executing a command"""
    success: bool
    output: str
    error: Optional[str] = None
    exit_code: int = 0
    command: Optional[str] = None


class BaseHandler(ABC):
    """Base class for all command handlers"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.is_windows = self.os_type == "Windows"
        self.is_linux = self.os_type == "Linux"
        self.is_mac = self.os_type == "Darwin"
    
    @abstractmethod
    def can_handle(self, category: str, action: str) -> bool:
        """
        Determine if this handler can process the given category/action
        
        Args:
            category: Command category (e.g., "file_operation")
            action: Specific action (e.g., "delete")
            
        Returns:
            True if this handler can process the command
        """
        pass
    
    @abstractmethod
    def execute(
        self, 
        command: str, 
        parameters: Dict, 
        dry_run: bool = False
    ) -> CommandResult:
        """
        Execute the command
        
        Args:
            command: The system command to execute
            parameters: Additional parameters
            dry_run: If True, don't actually execute
            
        Returns:
            CommandResult with execution details
        """
        pass
    
    def run_command(
        self, 
        command: str, 
        shell: bool = True,
        capture_output: bool = True,
        timeout: int = 30
    ) -> CommandResult:
        """
        Run a system command
        
        Args:
            command: Command to execute
            shell: Run in shell
            capture_output: Capture stdout/stderr
            timeout: Timeout in seconds
            
        Returns:
            CommandResult
        """
        try:
            # On Windows, if command contains PowerShell cmdlets, run via PowerShell
            if self.is_windows and any(ps_cmd in command for ps_cmd in ['Get-', 'Set-', 'New-', 'Remove-']):
                # Use PowerShell to execute
                command = f'powershell -Command "{command}"'
            
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout.strip() if result.stdout else "",
                error=result.stderr.strip() if result.stderr else None,
                exit_code=result.returncode,
                command=command
            )
            
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds",
                exit_code=-1,
                command=command
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                command=command
            )
    
    def validate_path(self, path: str) -> bool:
        """Validate that a path is safe to operate on"""
        # Prevent operations on critical system directories
        dangerous_paths = [
            "/",
            "/bin",
            "/boot",
            "/dev",
            "/etc",
            "/lib",
            "/proc",
            "/sys",
            "/usr",
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\System32"
        ]
        
        abs_path = os.path.abspath(path)
        for dangerous in dangerous_paths:
            if abs_path.startswith(dangerous):
                return False
        
        return True


class HandlerRegistry:
    """Registry for managing command handlers"""
    
    def __init__(self):
        self.handlers: List[BaseHandler] = []
        self._load_default_handlers()
    
    def register(self, handler: BaseHandler):
        """Register a new handler"""
        self.handlers.append(handler)
    
    def get_handler(self, category: str, action: str) -> Optional[BaseHandler]:
        """Find the appropriate handler for a command"""
        for handler in self.handlers:
            if handler.can_handle(category, action):
                return handler
        return None
    
    def _load_default_handlers(self):
        """Load built-in handlers"""
        # These will be imported from separate modules
        from .handlers import (
            FileHandler,
            NetworkHandler,
            SystemInfoHandler,
            ProcessHandler,
            DevelopmentHandler
        )
        
        self.register(FileHandler())
        self.register(NetworkHandler())
        self.register(SystemInfoHandler())
        self.register(ProcessHandler())
        self.register(DevelopmentHandler())
    
    def load_custom_handlers(self, handler_dir: str):
        """Load custom handlers from a directory"""
        import importlib.util
        import sys
        from pathlib import Path
        
        handler_path = Path(handler_dir)
        if not handler_path.exists():
            return
        
        for py_file in handler_path.glob("*.py"):
            if py_file.stem.startswith("_"):
                continue
            
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[py_file.stem] = module
                spec.loader.exec_module(module)
                
                # Find and register handler classes
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (isinstance(item, type) and 
                        issubclass(item, BaseHandler) and 
                        item is not BaseHandler):
                        try:
                            self.register(item())
                        except Exception as e:
                            print(f"Failed to load handler {item_name}: {e}")
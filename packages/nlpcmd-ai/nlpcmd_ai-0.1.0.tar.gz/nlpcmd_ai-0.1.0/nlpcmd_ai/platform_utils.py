"""
Cross-Platform Utilities

Provides OS-agnostic functions and command translation for Windows, Linux, and macOS.
"""

import os
import platform
import subprocess
from typing import Optional, List, Tuple
from pathlib import Path


class PlatformUtils:
    """Utilities for cross-platform command handling"""
    
    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_linux = self.system == "Linux"
        self.is_mac = self.system == "Darwin"
        self.is_unix = self.is_linux or self.is_mac
        
        # Determine shell
        if self.is_windows:
            self.shell = os.getenv("COMSPEC", "cmd.exe")
            self.is_powershell = "powershell" in self.shell.lower() or "pwsh" in self.shell.lower()
        else:
            self.shell = os.getenv("SHELL", "/bin/bash")
    
    def get_platform_info(self) -> dict:
        """Get detailed platform information"""
        return {
            "system": self.system,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "shell": self.shell,
        }
    
    def translate_command(self, command: str, category: str) -> str:
        """
        Translate commands to platform-specific equivalents
        
        Args:
            command: Original command
            category: Command category for context
            
        Returns:
            Platform-appropriate command
        """
        # If command is already platform-specific, return as-is
        if self._is_platform_specific(command):
            return command
        
        # Common translations
        translations = {
            # File operations
            "ls": "dir" if self.is_windows else "ls",
            "ls -la": "dir /a" if self.is_windows else "ls -la",
            "pwd": "cd" if self.is_windows else "pwd",
            "cat": "type" if self.is_windows else "cat",
            "cp": "copy" if self.is_windows else "cp",
            "mv": "move" if self.is_windows else "mv",
            "rm": "del" if self.is_windows else "rm",
            "mkdir": "mkdir" if self.is_windows else "mkdir",
            "rmdir": "rmdir" if self.is_windows else "rmdir",
            
            # Network
            "ifconfig": "ipconfig" if self.is_windows else "ifconfig",
            "ping": "ping" if self.is_windows else "ping",
            
            # Process
            "ps": "tasklist" if self.is_windows else "ps",
            "kill": "taskkill /F /PID" if self.is_windows else "kill",
        }
        
        for unix_cmd, platform_cmd in translations.items():
            if command.startswith(unix_cmd):
                return command.replace(unix_cmd, platform_cmd, 1)
        
        return command
    
    def _is_platform_specific(self, command: str) -> bool:
        """Check if command is already platform-specific"""
        windows_commands = [
            "dir", "type", "copy", "move", "del", "ipconfig", 
            "tasklist", "taskkill", "where", "Get-", "Set-"
        ]
        unix_commands = [
            "ls", "cat", "cp", "mv", "rm", "ifconfig",
            "ps", "kill", "grep", "awk", "sed", "find"
        ]
        
        cmd_lower = command.lower()
        
        if self.is_windows:
            return any(cmd in cmd_lower for cmd in windows_commands)
        else:
            return any(cmd in cmd_lower for cmd in unix_commands)
    
    def get_path_separator(self) -> str:
        """Get OS-specific path separator"""
        return "\\" if self.is_windows else "/"
    
    def normalize_path(self, path: str) -> str:
        """Normalize path for current OS"""
        return str(Path(path))
    
    def get_home_directory(self) -> str:
        """Get user's home directory"""
        return str(Path.home())
    
    def get_temp_directory(self) -> str:
        """Get temporary directory"""
        import tempfile
        return tempfile.gettempdir()
    
    def run_cross_platform_command(
        self,
        command: str,
        timeout: int = 30,
        check: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run command in platform-appropriate way
        
        Args:
            command: Command to run
            timeout: Timeout in seconds
            check: Raise exception on non-zero exit
            
        Returns:
            CompletedProcess result
        """
        if self.is_windows:
            # On Windows, use shell=True for cmd.exe compatibility
            return subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check
            )
        else:
            # On Unix, safer to use shell=True for complex commands
            return subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check,
                executable=self.shell
            )


class CommandMapper:
    """Maps common operations to platform-specific commands"""
    
    def __init__(self):
        self.platform = PlatformUtils()
    
    def get_ip_command(self) -> str:
        """Get command to retrieve IP address"""
        if self.platform.is_windows:
            return "ipconfig | findstr IPv4"
        else:
            return "ip addr show | grep inet || ifconfig | grep inet"
    
    def get_disk_usage_command(self, path: str = ".") -> str:
        """Get disk usage command"""
        if self.platform.is_windows:
            return f'powershell "Get-PSDrive -PSProvider FileSystem"'
        else:
            return f"df -h {path}"
    
    def get_memory_command(self) -> str:
        """Get memory info command"""
        if self.platform.is_windows:
            return "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value"
        elif self.platform.is_linux:
            return "free -h"
        else:  # macOS
            return "vm_stat"
    
    def get_process_list_command(self) -> str:
        """Get process list command"""
        if self.platform.is_windows:
            return "tasklist"
        else:
            return "ps aux"
    
    def get_network_interfaces_command(self) -> str:
        """Get network interfaces command"""
        if self.platform.is_windows:
            return "ipconfig /all"
        else:
            return "ip addr || ifconfig -a"
    
    def get_find_files_command(
        self,
        pattern: str,
        path: str = ".",
        recursive: bool = True
    ) -> str:
        """Get command to find files"""
        if self.platform.is_windows:
            recurse = "/s" if recursive else ""
            return f'dir "{path}" /b {recurse} | findstr "{pattern}"'
        else:
            return f'find "{path}" -name "{pattern}"'
    
    def get_grep_command(self, pattern: str, file: str) -> str:
        """Get grep/search command"""
        if self.platform.is_windows:
            return f'findstr "{pattern}" "{file}"'
        else:
            return f'grep "{pattern}" "{file}"'
    
    def get_kill_process_command(self, pid_or_name: str) -> str:
        """Get command to kill a process"""
        if self.platform.is_windows:
            # Try as PID first, then as name
            if pid_or_name.isdigit():
                return f"taskkill /F /PID {pid_or_name}"
            else:
                return f"taskkill /F /IM {pid_or_name}"
        else:
            if pid_or_name.isdigit():
                return f"kill -9 {pid_or_name}"
            else:
                return f"pkill -9 {pid_or_name}"
    
    def get_environment_variable_command(self, var_name: str) -> str:
        """Get command to show environment variable"""
        if self.platform.is_windows:
            return f"echo %{var_name}%"
        else:
            return f"echo ${var_name}"
    
    def get_set_environment_variable_command(
        self,
        var_name: str,
        value: str
    ) -> str:
        """Get command to set environment variable"""
        if self.platform.is_windows:
            return f'setx {var_name} "{value}"'
        else:
            return f'export {var_name}="{value}"'
    
    def get_current_directory_command(self) -> str:
        """Get command to show current directory"""
        if self.platform.is_windows:
            return "cd"
        else:
            return "pwd"
    
    def get_list_directory_command(self, path: str = ".", detailed: bool = False) -> str:
        """Get command to list directory contents"""
        if self.platform.is_windows:
            flags = "/a" if detailed else ""
            return f'dir "{path}" {flags}'
        else:
            flags = "-la" if detailed else ""
            return f'ls {flags} "{path}"'
    
    def get_copy_file_command(self, source: str, dest: str) -> str:
        """Get command to copy file"""
        if self.platform.is_windows:
            return f'copy "{source}" "{dest}"'
        else:
            return f'cp "{source}" "{dest}"'
    
    def get_move_file_command(self, source: str, dest: str) -> str:
        """Get command to move file"""
        if self.platform.is_windows:
            return f'move "{source}" "{dest}"'
        else:
            return f'mv "{source}" "{dest}"'
    
    def get_delete_file_command(self, path: str) -> str:
        """Get command to delete file"""
        if self.platform.is_windows:
            return f'del "{path}"'
        else:
            return f'rm "{path}"'
    
    def get_create_directory_command(self, path: str) -> str:
        """Get command to create directory"""
        return f'mkdir "{path}"'  # Same on all platforms
    
    def get_python_command(self) -> str:
        """Get the Python executable command"""
        # Try python3 first on Unix, python on Windows
        if self.platform.is_windows:
            return "python"
        else:
            # Check if python3 exists
            try:
                subprocess.run(
                    ["which", "python3"],
                    capture_output=True,
                    check=True
                )
                return "python3"
            except:
                return "python"


# Global instances for easy access
platform_utils = PlatformUtils()
command_mapper = CommandMapper()

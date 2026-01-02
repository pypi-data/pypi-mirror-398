"""
Built-in Command Handlers

This module contains handler implementations for different command categories.
"""

import os
import platform
import socket
import requests
from pathlib import Path
from typing import Dict
from .base_handler import BaseHandler, CommandResult
from .platform_utils import platform_utils, command_mapper


class FileHandler(BaseHandler):
    """Handler for file and directory operations"""
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "file_operation"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute file operations"""
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        # Additional validation for file operations
        if "path" in parameters:
            path = parameters["path"]
            if not self.validate_path(path):
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Operation not allowed on path: {path}",
                    exit_code=1,
                    command=command
                )
        
        return self.run_command(command)


class NetworkHandler(BaseHandler):
    """Handler for network operations"""
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "network"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute network operations"""
        action = parameters.get("action", "")
        
        # Handle special cases with Python instead of shell commands
        if action in ["get_ip", "get_ip_address"]:
            return self._get_ip_address(dry_run)
        elif action in ["check_port", "port_check"]:
            return self._check_port(parameters, dry_run)
        elif action in ["http_request", "make_request"]:
            return self._http_request(parameters, dry_run)
        
        # Default to shell command
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        return self.run_command(command)
    
    def _get_ip_address(self, dry_run: bool) -> CommandResult:
        """Get IP addresses"""
        if dry_run:
            return CommandResult(
                success=True,
                output="[DRY RUN] Would fetch IP addresses"
            )
        
        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Get public IP
            try:
                public_ip = requests.get("https://api.ipify.org", timeout=5).text
            except:
                public_ip = "Unable to fetch"
            
            output = f"Local IP: {local_ip}\nPublic IP: {public_ip}"
            
            return CommandResult(success=True, output=output)
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to get IP: {str(e)}"
            )
    
    def _check_port(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Check if a port is open"""
        host = parameters.get("host", "localhost")
        port = parameters.get("port")
        
        if not port:
            return CommandResult(
                success=False,
                output="",
                error="Port number required"
            )
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would check if port {port} is open on {host}"
            )
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            
            if result == 0:
                output = f"Port {port} is OPEN on {host}"
            else:
                output = f"Port {port} is CLOSED on {host}"
            
            return CommandResult(success=True, output=output)
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to check port: {str(e)}"
            )
    
    def _http_request(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Make HTTP request"""
        url = parameters.get("url")
        method = parameters.get("method", "GET").upper()
        
        if not url:
            return CommandResult(
                success=False,
                output="",
                error="URL required"
            )
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would make {method} request to {url}"
            )
        
        try:
            response = requests.request(method, url, timeout=10)
            output = f"Status: {response.status_code}\n"
            output += f"Response Length: {len(response.content)} bytes"
            
            return CommandResult(success=True, output=output)
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"HTTP request failed: {str(e)}"
            )


class SystemInfoHandler(BaseHandler):
    """Handler for system information queries"""
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "system_info"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute system info commands"""
        action = parameters.get("action", "").lower().replace(" ", "_")
        
        # Handle special cases
        if action in ["disk_usage", "get_disk_usage", "show_disk_usage"]:
            return self._get_disk_usage(parameters, dry_run)
        elif action in ["memory", "get_memory", "get_memory_usage", "memory_info"]:
            return self._get_memory_info(dry_run)
        elif action in ["cpu", "get_cpu", "get_cpu_usage", "cpu_usage"]:
            return self._get_cpu_usage(dry_run)
        elif action in ["uptime", "get_uptime", "get_system_uptime", "system_uptime"]:
            return self._get_uptime(dry_run)
        
        # Default to shell command
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        return self.run_command(command)
    
    def _get_disk_usage(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Get disk usage information"""
        if dry_run:
            return CommandResult(
                success=True,
                output="[DRY RUN] Would show disk usage"
            )
        
        path = parameters.get("path", ".")
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            
            output = f"Disk Usage for {path}:\n"
            output += f"Total: {self._format_bytes(total)}\n"
            output += f"Used: {self._format_bytes(used)}\n"
            output += f"Free: {self._format_bytes(free)}\n"
            output += f"Usage: {used/total*100:.1f}%"
            
            return CommandResult(success=True, output=output)
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to get disk usage: {str(e)}"
            )
    
    def _get_memory_info(self, dry_run: bool) -> CommandResult:
        """Get memory information"""
        if dry_run:
            return CommandResult(
                success=True,
                output="[DRY RUN] Would show memory info"
            )
        
        try:
            # Try to use psutil if available
            import psutil
            mem = psutil.virtual_memory()
            
            output = "Memory Information:\n"
            output += f"Total: {self._format_bytes(mem.total)}\n"
            output += f"Available: {self._format_bytes(mem.available)}\n"
            output += f"Used: {self._format_bytes(mem.used)}\n"
            output += f"Usage: {mem.percent}%"
            
            return CommandResult(success=True, output=output)
        except ImportError:
            # Fall back to command-line tools
            command = command_mapper.get_memory_command()
            return self.run_command(command)
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to get memory info: {str(e)}"
            )
    
    def _get_cpu_usage(self, dry_run: bool) -> CommandResult:
        """Get CPU usage information"""
        if dry_run:
            return CommandResult(
                success=True,
                output="[DRY RUN] Would show CPU usage"
            )
        
        try:
            # Try to use psutil if available
            import psutil
            import time
            
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            output = "CPU Information:\n"
            output += f"Usage: {cpu_percent}%\n"
            output += f"Cores: {cpu_count}\n"
            if cpu_freq:
                output += f"Current Speed: {cpu_freq.current:.0f} MHz\n"
                if cpu_freq.max > 0:
                    output += f"Max Speed: {cpu_freq.max:.0f} MHz"
            
            return CommandResult(success=True, output=output)
        except ImportError:
            return CommandResult(
                success=False,
                output="",
                error="psutil not installed. Install with: pip install psutil"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to get CPU usage: {str(e)}"
            )
    
    def _get_uptime(self, dry_run: bool) -> CommandResult:
        """Get system uptime"""
        if dry_run:
            return CommandResult(
                success=True,
                output="[DRY RUN] Would show system uptime"
            )
        
        try:
            import psutil
            from datetime import datetime, timedelta
            
            # Get boot time
            boot_timestamp = psutil.boot_time()
            boot_time = datetime.fromtimestamp(boot_timestamp)
            
            # Calculate uptime
            uptime = datetime.now() - boot_time
            
            # Format uptime
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            output = "System Uptime:\n"
            output += f"Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"Uptime: {days} days, {hours} hours, {minutes} minutes\n"
            
            # Add friendly message
            if days == 0:
                output += "Computer was rebooted today"
            elif days == 1:
                output += "Computer has been running for 1 day"
            else:
                output += f"Computer has been running for {days} days"
            
            return CommandResult(success=True, output=output)
        except ImportError:
            return CommandResult(
                success=False,
                output="",
                error="psutil not installed. Install with: pip install psutil"
            )
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Failed to get uptime: {str(e)}"
            )
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


class ProcessHandler(BaseHandler):
    """Handler for process management"""
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "process_mgmt"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute process management commands"""
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        # Process commands are sensitive, always require confirmation
        return self.run_command(command)


class DevelopmentHandler(BaseHandler):
    """Handler for development tools (git, docker, package managers, etc.)"""
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "development"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute development tool commands"""
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        return self.run_command(command, timeout=120)  # Longer timeout for dev tools
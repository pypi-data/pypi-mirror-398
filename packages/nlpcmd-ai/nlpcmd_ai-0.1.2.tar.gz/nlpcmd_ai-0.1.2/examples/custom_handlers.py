"""
Example Custom Handler

This is an example of how to create custom command handlers.
Place this file in your custom handlers directory (e.g., ~/.nlpcmd_ai/handlers/)
"""

from nlpcmd_ai.base_handler import BaseHandler, CommandResult
from typing import Dict


class DockerHandler(BaseHandler):
    """
    Custom handler for Docker operations
    
    This handler demonstrates how to extend nlpcmd-ai with
    domain-specific command handling.
    """
    
    def can_handle(self, category: str, action: str) -> bool:
        """Check if this is a Docker-related command"""
        return category == "development" and action.startswith("docker_")
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute Docker commands"""
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        # Check if Docker is installed
        check_result = self.run_command("docker --version", timeout=5)
        if not check_result.success:
            return CommandResult(
                success=False,
                output="",
                error="Docker is not installed or not in PATH",
                exit_code=1
            )
        
        # Execute the Docker command
        return self.run_command(command, timeout=300)  # 5 min timeout for Docker


class GitAdvancedHandler(BaseHandler):
    """
    Advanced Git operations handler
    
    Handles complex Git workflows that require multiple commands
    """
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "development" and action.startswith("git_advanced_")
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute advanced Git operations"""
        
        action = parameters.get("git_action", "")
        
        if action == "squash_commits":
            return self._squash_commits(parameters, dry_run)
        elif action == "interactive_rebase":
            return self._interactive_rebase(parameters, dry_run)
        
        # Default execution
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        return self.run_command(command)
    
    def _squash_commits(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Squash recent commits"""
        num_commits = parameters.get("num_commits", 2)
        
        command = f"git reset --soft HEAD~{num_commits} && git commit"
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would squash last {num_commits} commits",
                command=command
            )
        
        return self.run_command(command)
    
    def _interactive_rebase(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Start interactive rebase"""
        num_commits = parameters.get("num_commits", 5)
        
        command = f"git rebase -i HEAD~{num_commits}"
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would start interactive rebase for last {num_commits} commits",
                command=command
            )
        
        return self.run_command(command, timeout=600)


class DataProcessingHandler(BaseHandler):
    """
    Handler for data processing tasks (CSV, JSON, etc.)
    """
    
    def can_handle(self, category: str, action: str) -> bool:
        return category == "data_processing"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        """Execute data processing operations"""
        
        action = parameters.get("action", "")
        
        if action == "csv_to_json":
            return self._csv_to_json(parameters, dry_run)
        elif action == "json_to_csv":
            return self._json_to_csv(parameters, dry_run)
        elif action == "filter_csv":
            return self._filter_csv(parameters, dry_run)
        
        # Default to shell command
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        return self.run_command(command)
    
    def _csv_to_json(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Convert CSV to JSON"""
        input_file = parameters.get("input_file")
        output_file = parameters.get("output_file", "output.json")
        
        if not input_file:
            return CommandResult(
                success=False,
                output="",
                error="Input file required",
                exit_code=1
            )
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would convert {input_file} to {output_file}",
            )
        
        try:
            import csv
            import json
            
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return CommandResult(
                success=True,
                output=f"Converted {len(data)} rows from {input_file} to {output_file}",
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Conversion failed: {str(e)}",
                exit_code=1
            )
    
    def _json_to_csv(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Convert JSON to CSV"""
        input_file = parameters.get("input_file")
        output_file = parameters.get("output_file", "output.csv")
        
        if not input_file:
            return CommandResult(
                success=False,
                output="",
                error="Input file required",
                exit_code=1
            )
        
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would convert {input_file} to {output_file}",
            )
        
        try:
            import csv
            import json
            
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            if not data:
                return CommandResult(
                    success=False,
                    output="",
                    error="Empty JSON data",
                    exit_code=1
                )
            
            # Get field names from first item
            fieldnames = list(data[0].keys())
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            return CommandResult(
                success=True,
                output=f"Converted {len(data)} records from {input_file} to {output_file}",
            )
            
        except Exception as e:
            return CommandResult(
                success=False,
                output="",
                error=f"Conversion failed: {str(e)}",
                exit_code=1
            )
    
    def _filter_csv(self, parameters: Dict, dry_run: bool) -> CommandResult:
        """Filter CSV based on criteria"""
        # Implementation for CSV filtering
        # This would use pandas or csv module to filter rows
        pass

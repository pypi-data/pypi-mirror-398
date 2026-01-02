"""
Command Line Interface for nlpcmd-ai

Main entry point for the CLI application with interactive and one-off modes.
"""

import os
import sys
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint
from dotenv import load_dotenv

from .engine import AIEngine, CommandIntent
from .base_handler import HandlerRegistry, CommandResult
from .config import Config


console = Console()


class NLPCommandCLI:
    """Main CLI application class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.engine = AIEngine(
            provider=config.ai_provider,
            model=config.ai_model
        )
        self.registry = HandlerRegistry()
        
        # Load custom handlers if configured
        if config.custom_handlers_path:
            self.registry.load_custom_handlers(config.custom_handlers_path)
        
        self.command_history = []
    
    def process_command(
        self, 
        query: str,
        dry_run: bool = False,
        auto_confirm: bool = False
    ) -> Optional[CommandResult]:
        """Process a single command"""
        
        # Get context
        context = {
            "cwd": os.getcwd(),
            "user": os.getenv("USER") or os.getenv("USERNAME"),
            "shell": os.getenv("SHELL", "unknown")
        }
        
        # Show processing message
        with console.status("[bold blue]🤔 Understanding your request...", spinner="dots"):
            intent = self.engine.process_query(query, context)
        
        # Check confidence
        if intent.confidence < 0.5:
            console.print(
                f"[yellow]⚠️  Low confidence ({intent.confidence:.0%}) in understanding this request.[/yellow]"
            )
            console.print(f"[yellow]Understanding: {intent.explanation}[/yellow]")
            
            if not Confirm.ask("Would you like me to try executing anyway?"):
                return None
        
        # Display intent
        self._display_intent(intent)
        
        # Check if we have a command to execute
        if not intent.suggested_command:
            console.print(f"[yellow]{intent.explanation}[/yellow]")
            return None
        
        # Get handler
        handler = self.registry.get_handler(intent.category, intent.action)
        if not handler:
            console.print(f"[red]❌ No handler found for category: {intent.category}[/red]")
            return None
        
        # Check if confirmation needed
        needs_confirmation = intent.requires_confirmation or self.config.require_confirmation
        
        if needs_confirmation and not auto_confirm and not dry_run:
            if not self._confirm_execution(intent):
                console.print("[yellow]⏸️  Execution cancelled[/yellow]")
                return None
        
        # Execute command
        result = self._execute_command(handler, intent, dry_run)
        
        # Log if enabled
        if self.config.log_commands and not dry_run:
            self._log_command(intent, result)
        
        return result
    
    def _display_intent(self, intent: CommandIntent):
        """Display the understood intent"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column()
        
        table.add_row("📋 Category:", intent.category)
        table.add_row("⚡ Action:", intent.action)
        table.add_row("💭 Understanding:", intent.explanation or "N/A")
        table.add_row("🎯 Confidence:", f"{intent.confidence:.0%}")
        
        if intent.suggested_command:
            table.add_row("💻 Command:", intent.suggested_command)
        
        console.print(table)
        console.print()
    
    def _confirm_execution(self, intent: CommandIntent) -> bool:
        """Ask user to confirm execution"""
        panel = Panel(
            f"[bold yellow]{intent.suggested_command}[/bold yellow]",
            title="[red]⚠️  Confirm Execution[/red]",
            border_style="red"
        )
        console.print(panel)
        
        return Confirm.ask("Execute this command?", default=False)
    
    def _execute_command(
        self,
        handler,
        intent: CommandIntent,
        dry_run: bool
    ) -> CommandResult:
        """Execute the command using the appropriate handler"""
        
        if dry_run:
            console.print("[blue]🔍 DRY RUN MODE - Not executing[/blue]")
        else:
            console.print("[green]⚙️  Executing...[/green]")
        
        # Add action to parameters for handlers that need it
        params = intent.parameters.copy()
        params['action'] = intent.action
        
        result = handler.execute(
            intent.suggested_command,
            params,
            dry_run=dry_run
        )
        
        # Display result
        self._display_result(result)
        
        return result
    
    def _display_result(self, result: CommandResult):
        """Display command execution result"""
        if result.success:
            if result.output:
                console.print(Panel(
                    result.output,
                    title="[green]✅ Success[/green]",
                    border_style="green"
                ))
            else:
                console.print("[green]✅ Command executed successfully[/green]")
        else:
            error_msg = result.error or "Unknown error"
            console.print(Panel(
                f"[red]{error_msg}[/red]",
                title="[red]❌ Error[/red]",
                border_style="red"
            ))
            if result.output:
                console.print(f"[dim]Output: {result.output}[/dim]")
    
    def _log_command(self, intent: CommandIntent, result: CommandResult):
        """Log executed command to file"""
        from datetime import datetime
        
        log_file = Path.home() / ".nlpcmd_ai" / "history.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if result.success else "FAILED"
        
        log_entry = (
            f"{timestamp} | {status} | "
            f'Query: "{intent.original_query}" | '
            f'Command: "{intent.suggested_command}"\n'
        )
        
        with open(log_file, "a") as f:
            f.write(log_entry)
    
    def interactive_mode(self):
        """Run in interactive mode"""
        console.print(Panel(
            "[bold blue]🤖 NLP Command Assistant[/bold blue]\n"
            "Type your commands in natural language\n"
            "Type 'exit', 'quit', or 'q' to exit\n"
            "Type 'clear' to clear conversation history\n"
            "Type 'help' for more information",
            border_style="blue"
        ))
        
        while True:
            try:
                # Get user input
                query = console.input("\n[bold green]>[/bold green] ").strip()
                
                if not query:
                    continue
                
                # Handle special commands
                if query.lower() in ['exit', 'quit', 'q']:
                    console.print("[blue]👋 Goodbye![/blue]")
                    break
                
                if query.lower() == 'clear':
                    self.engine.clear_history()
                    console.print("[blue]🧹 Conversation history cleared[/blue]")
                    continue
                
                if query.lower() == 'help':
                    self._show_help()
                    continue
                
                # Process the command
                self.process_command(query)
                
            except KeyboardInterrupt:
                console.print("\n[yellow]⏸️  Interrupted[/yellow]")
                if Confirm.ask("Exit?"):
                    break
            except Exception as e:
                console.print(f"[red]❌ Error: {str(e)}[/red]")
    
    def _show_help(self):
        """Show help information"""
        help_text = """
[bold]Available Commands:[/bold]

[cyan]System Information:[/cyan]
  - "what is my ip address"
  - "show disk usage"
  - "show memory usage"
  - "list running processes"

[cyan]File Operations:[/cyan]
  - "list all python files"
  - "find files larger than 10MB"
  - "create a folder called myproject"
  - "delete all .pyc files"

[cyan]Network:[/cyan]
  - "ping google.com"
  - "check if port 8080 is open"
  - "what's my public IP"

[cyan]Development:[/cyan]
  - "create a git branch called feature-x"
  - "install requests package"
  - "run pytest"

[cyan]Special Commands:[/cyan]
  - exit/quit/q: Exit the program
  - clear: Clear conversation history
  - help: Show this help
"""
        console.print(Panel(help_text, title="Help", border_style="cyan"))


@click.command()
@click.argument('query', nargs=-1)
@click.option('--interactive', '-i', is_flag=True, help='Start interactive mode')
@click.option('--dry-run', is_flag=True, help='Show what would be executed without running')
@click.option('--provider', type=click.Choice(['openai', 'anthropic', 'ollama']), 
              help='AI provider to use')
@click.option('--model', help='Specific model to use')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm all actions')
@click.option('--config', type=click.Path(), help='Path to config file')
def main(query, interactive, dry_run, provider, model, yes, config):
    """
    NLP-powered command line assistant
    
    Examples:
        nlpai "what is my ip address"
        nlpai --dry-run "delete all log files"
        nlpai -i  # Start interactive mode
    """
    
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    cfg = Config.load(config)
    
    # Override with CLI options
    if provider:
        cfg.ai_provider = provider
    if model:
        cfg.ai_model = model
    if dry_run:
        cfg.dry_run_mode = True
    
    # Create CLI instance
    cli = NLPCommandCLI(cfg)
    
    # Determine mode
    if interactive or not query:
        cli.interactive_mode()
    else:
        # One-off command
        query_str = ' '.join(query)
        cli.process_command(query_str, dry_run=dry_run, auto_confirm=yes)


if __name__ == '__main__':
    main()
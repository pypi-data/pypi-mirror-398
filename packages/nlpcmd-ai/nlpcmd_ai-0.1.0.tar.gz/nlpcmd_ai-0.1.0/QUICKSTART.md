# Quick Start Guide for nlpcmd-ai

## Installation

### 1. Install the package

```bash
# From PyPI (when published)
pip install nlpcmd-ai

# Or from source
git clone <repository-url>
cd nlpcmd_ai
pip install -e .
```

### 2. Set up your environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key
nano .env
```

Add your API key:
```
NLP_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Test the installation

```bash
# Try a simple command
nlpai "what is my ip address"

# Start interactive mode
nlpai -i
```

## Usage Examples

### One-off Commands

```bash
# System information
nlpai "show disk usage"
nlpai "what processes are using most CPU"
nlpai "show me system information"

# File operations
nlpai "list all python files in this directory"
nlpai "find files larger than 10MB"
nlpai "create a folder called test_project"

# Network
nlpai "what is my public IP"
nlpai "ping google.com"
nlpai "check if port 8080 is open"

# Development
nlpai "create a git branch called feature/auth"
nlpai "show git status"
nlpai "install the requests package"
```

### Interactive Mode

```bash
nlpai -i
```

Then type commands:
```
> show current directory
> list all files
> show me the largest file
> exit
```

### Dry Run Mode

Test commands without executing:

```bash
nlpai --dry-run "delete all .log files"
```

### Auto-confirm Mode

Skip confirmation prompts (use with caution):

```bash
nlpai --yes "create backup of all python files"
```

## Configuration

### Using Different AI Providers

#### OpenAI (default)
```bash
export NLP_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

#### Anthropic Claude
```bash
export NLP_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

#### Local LLM with Ollama
```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3.2

# Install local support
pip install nlpcmd-ai[local]

# Configure
export NLP_PROVIDER=ollama
export OLLAMA_MODEL=llama3.2
```

### Configuration File

Create `~/.nlpcmd_ai/config.yaml`:

```yaml
ai:
  provider: openai
  model: gpt-4-turbo-preview
  temperature: 0.3

safety:
  require_confirmation: true
  dangerous_patterns:
    - "rm -rf"
    - "dd if="
  allowed_directories:
    - "/home/user/projects"
    - "/tmp"

logging:
  enabled: true
  level: INFO
  file: ~/.nlpcmd_ai/nlpcmd.log
```

## Custom Handlers

Create custom command handlers for your specific needs:

1. Create handlers directory:
```bash
mkdir -p ~/.nlpcmd_ai/handlers
```

2. Create a handler file (e.g., `~/.nlpcmd_ai/handlers/my_handler.py`):

```python
from nlpcmd_ai.base_handler import BaseHandler, CommandResult
from typing import Dict

class MyCustomHandler(BaseHandler):
    def can_handle(self, category: str, action: str) -> bool:
        return category == "custom" and action == "my_action"
    
    def execute(self, command: str, parameters: Dict, dry_run: bool = False) -> CommandResult:
        # Your custom logic here
        return CommandResult(
            success=True,
            output="Custom handler executed!"
        )
```

3. Configure in `config.yaml`:
```yaml
handlers:
  custom_path: ~/.nlpcmd_ai/handlers
```

## Safety Features

### Confirmation Prompts

By default, dangerous operations require confirmation:

```bash
$ nlpai "delete all files in /tmp"
⚠️  WARNING: This will delete files
Command: rm -rf /tmp/*
Execute? [y/N]:
```

### Command Logging

All executed commands are logged to `~/.nlpcmd_ai/history.log`:

```
2025-01-15 10:23:45 | SUCCESS | Query: "show my ip" | Command: "ip addr show"
2025-01-15 10:24:12 | FAILED | Query: "invalid" | Command: "..."
```

## Troubleshooting

### "Command not found: nlpai"

Make sure Python's scripts directory is in your PATH:

```bash
# On Linux/Mac
export PATH="$HOME/.local/bin:$PATH"

# On Windows
# Add %APPDATA%\Python\Scripts to your PATH
```

### "API key not set"

Make sure you've set up your `.env` file or environment variables:

```bash
# Check if key is set
echo $OPENAI_API_KEY

# If not, add it
export OPENAI_API_KEY=sk-your-key
```

### "Low confidence" warnings

If the AI is uncertain about your command, try:
- Being more specific
- Using simpler language
- Breaking complex tasks into steps

### Ollama not working

Make sure Ollama is running:

```bash
# Start Ollama server
ollama serve

# In another terminal, pull the model
ollama pull llama3.2

# Test it
ollama run llama3.2 "Hello"
```

## Advanced Usage

### Using with Scripts

```bash
#!/bin/bash
# Backup script using nlpcmd-ai

nlpai --yes "create backup of all python files in current directory"
nlpai --yes "compress the backup folder"
nlpai "send me a notification that backup is complete"
```

### Piping Output

```bash
nlpai "list all python files" | grep "test"
```

### Combining Commands

```bash
nlpai "show disk usage" && nlpai "show memory usage"
```

## Best Practices

1. **Start with dry-run mode** when testing new commands
2. **Enable command logging** to track what gets executed
3. **Use specific language** for better results
4. **Review commands** before confirming dangerous operations
5. **Create custom handlers** for frequently used workflows
6. **Keep conversation context** in interactive mode for related tasks

## Examples by Category

### File Management
```bash
nlpai "find all files modified in the last 7 days"
nlpai "rename all .jpeg files to .jpg"
nlpai "compress all log files from last month"
nlpai "move all PDF files to Documents folder"
```

### Development Workflow
```bash
nlpai "create a new git branch for the authentication feature"
nlpai "run all my unit tests"
nlpai "format all python files with black"
nlpai "commit my changes with message 'fixed bug'"
```

### System Administration
```bash
nlpai "show all listening ports"
nlpai "find processes using port 8080"
nlpai "check disk usage by directory"
nlpai "show system resource usage"
```

### Data Processing
```bash
nlpai "convert this CSV to JSON"
nlpai "extract all email addresses from this file"
nlpai "sort this file by the second column"
nlpai "merge all CSV files in this directory"
```

## Getting Help

- GitHub Issues: <repository-url>/issues
- Documentation: <documentation-url>
- Discord/Slack: <community-link>

## Next Steps

- Read the full documentation
- Explore example custom handlers
- Join the community
- Contribute handlers for your use cases

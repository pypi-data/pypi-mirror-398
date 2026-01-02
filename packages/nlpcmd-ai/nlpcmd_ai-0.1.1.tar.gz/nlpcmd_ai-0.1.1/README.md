# 🤖 nlpcmd-ai

[![PyPI version](https://img.shields.io/pypi/v/nlpcmd-ai.svg)](https://pypi.org/project/nlpcmd-ai/)
[![Python versions](https://img.shields.io/pypi/pyversions/nlpcmd-ai.svg)](https://pypi.org/project/nlpcmd-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg)](https://pypi.org/project/nlpcmd-ai/)
[![GitHub](https://img.shields.io/badge/GitHub-nlp__terminal__cmd-blue?logo=github)](https://github.com/Avikg/nlp_terminal_cmd)

> **Transform natural language into system commands with AI** 🚀

A **truly AI-powered** command-line assistant for **Windows, Linux, and macOS** that understands natural language and executes system commands intelligently. No more memorizing complex command syntax - just ask in plain English!

Unlike traditional CLI tools with pattern matching, nlpcmd-ai uses **AI/LLM** (OpenAI, Anthropic Claude, or local Ollama) to understand complex, ambiguous commands and translate them into executable system operations - **automatically adapting commands to your operating system**.

## 📚 Links

- **📦 PyPI Package:** [https://pypi.org/project/nlpcmd-ai/](https://pypi.org/project/nlpcmd-ai/)
- **💻 GitHub Repository:** [https://github.com/Avikg/nlp_terminal_cmd](https://github.com/Avikg/nlp_terminal_cmd)
- **📖 Documentation:** [Full Documentation](https://github.com/Avikg/nlp_terminal_cmd#readme)
- **🐛 Issues:** [Report Issues](https://github.com/Avikg/nlp_terminal_cmd/issues)

## ✨ Features

- 🧠 **True Natural Language Understanding** - Uses AI models (OpenAI GPT-4, Anthropic Claude, or local Ollama)
- 🔒 **Safe Execution** - Confirms dangerous operations before execution
- 📝 **Context Awareness** - Remembers conversation history for follow-up commands
- 🎯 **Intent Detection** - Automatically determines what you want to do
- 🔧 **Extensible** - Easy to add custom command handlers
- 🌐 **Cross-platform** - Works seamlessly on Windows, Linux, and macOS
- 💬 **Interactive Mode** - Chat-like interface for complex workflows
- 🆓 **100% Free Option** - Use with local Ollama (no API costs)
- ⚡ **Fast & Efficient** - Powered by optimized AI models

## 🎬 Quick Start

### Try it in 3 commands:

```bash
# 1. Install
pip install nlpcmd-ai

# 2. Setup (choose one - Ollama is free!)
ollama pull llama3.2  # Free option
# OR get OpenAI API key from https://platform.openai.com/api-keys

# 3. Use it!
python -m nlpcmd_ai.cli "what is my ip"
```

## 🚀 Installation

### Prerequisites

- **Python 3.8+** - [Download Python](https://python.org)
- **pip** (comes with Python)

### Step 1: Install the Package

```bash
pip install nlpcmd-ai
```

### Step 2: Choose Your AI Provider

You have **3 options** for the AI backend:

#### **Option A: Ollama (Recommended - 100% Free & Private)**

Run AI models **locally** on your computer - completely free, no API keys needed!

1. **Install Ollama:**
   - Windows/Mac: Download from [https://ollama.ai](https://ollama.ai)
   - Linux: `curl https://ollama.ai/install.sh | sh`

2. **Download AI model:**
   ```bash
   ollama pull llama3.2
   ```

3. **Create configuration file:**
   
   **Windows:**
   ```cmd
   echo NLP_PROVIDER=ollama > .env
   echo OLLAMA_MODEL=llama3.2 >> .env
   echo REQUIRE_CONFIRMATION=false >> .env
   ```
   
   **Linux/macOS:**
   ```bash
   cat > .env << EOF
   NLP_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   REQUIRE_CONFIRMATION=false
   EOF
   ```

#### **Option B: OpenAI (Paid - Most Accurate)**

1. **Get API Key:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

2. **Create .env file:**
   ```bash
   # Windows
   echo NLP_PROVIDER=openai > .env
   echo OPENAI_API_KEY=your-api-key-here >> .env
   
   # Linux/macOS
   cat > .env << EOF
   NLP_PROVIDER=openai
   OPENAI_API_KEY=your-api-key-here
   EOF
   ```

#### **Option C: Anthropic Claude (Paid - Most Intelligent)**

1. **Get API Key:** [https://console.anthropic.com/](https://console.anthropic.com/)

2. **Create .env file:**
   ```bash
   NLP_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your-api-key-here
   ```

### Step 3: Verify Installation

```bash
python -m nlpcmd_ai.cli "what is my ip"
```

If it shows your IP address, you're all set! 🎉

## 💡 Usage

### Basic Commands

Just ask naturally - the AI will understand!

```bash
# System Information
python -m nlpcmd_ai.cli "what is my ip"
python -m nlpcmd_ai.cli "how much memory do I have"
python -m nlpcmd_ai.cli "show disk usage"
python -m nlpcmd_ai.cli "what's my CPU usage"
python -m nlpcmd_ai.cli "how long has my computer been running"
python -m nlpcmd_ai.cli "who am I"

# File Operations
python -m nlpcmd_ai.cli "list all python files"
python -m nlpcmd_ai.cli "find files larger than 10MB"
python -m nlpcmd_ai.cli "show directory structure"

# Network
python -m nlpcmd_ai.cli "is port 8080 open"
python -m nlpcmd_ai.cli "ping google.com"

# Development
python -m nlpcmd_ai.cli "show git status"
python -m nlpcmd_ai.cli "list docker containers"
```

### Interactive Mode (Recommended!)

Have a conversation with your terminal:

```bash
python -m nlpcmd_ai.cli -i
```

Then chat naturally:
```
> what is my ip
> show disk usage
> list python files in current directory
> find files modified today
> exit
```

### Advanced Usage

```bash
# Auto-confirm (skip confirmation prompts)
python -m nlpcmd_ai.cli --yes "show disk usage"

# Dry run (see what would execute without running)
python -m nlpcmd_ai.cli --dry-run "delete all .log files"

# Help
python -m nlpcmd_ai.cli --help
```

### Create a Shortcut (Optional but Convenient)

**Windows:**
Create `nlpai.bat` in your PATH:
```batch
@echo off
python -m nlpcmd_ai.cli %*
```

Then use:
```cmd
nlpai "what is my ip"
nlpai -i
```

**Linux/macOS:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
alias nlpai='python -m nlpcmd_ai.cli'
```

Then:
```bash
nlpai "what is my ip"
nlpai -i
```

## 📋 Supported Commands

### System Information
- CPU usage, memory info, disk space
- System uptime, user info, hostname
- Operating system details

### Network Operations
- IP address lookup (local & public)
- Port checking and scanning
- Network interface information
- Ping and connectivity tests

### File & Directory Operations
- List, find, search files
- Directory navigation
- File information and statistics

### Process Management
- List running processes
- Find processes by name
- Monitor system resources

### Development Tools
- Git operations
- Docker commands
- Package management (pip, npm)

**See [SUPPORTED_COMMANDS.txt](SUPPORTED_COMMANDS.txt) for complete list**

## 🔧 Configuration

### Environment Variables (.env file)

```bash
# AI Provider (required)
NLP_PROVIDER=ollama  # or "openai" or "anthropic"

# Provider-specific settings
OLLAMA_MODEL=llama3.2
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key

# Safety
REQUIRE_CONFIRMATION=false  # Set to true for dangerous operations

# Logging
LOG_COMMANDS=true
LOG_FILE=~/.nlpcmd_ai/history.log
```

## 🛡️ Safety Features

- ✅ Dangerous operations require confirmation (unless disabled)
- ✅ Dry-run mode to preview commands
- ✅ Command logging for audit trail
- ✅ Path validation for file operations
- ✅ Protection against system directory access

## 🎯 Examples

### Example 1: System Monitoring
```bash
$ python -m nlpcmd_ai.cli -i

> what's my CPU usage
CPU Information:
Usage: 23.5%
Cores: 8
Current Speed: 2400 MHz

> how much memory do I have
Memory Information:
Total: 16.00 GB
Available: 8.50 GB
Used: 7.50 GB
Usage: 46.9%

> show disk usage
Disk Usage for C:\:
Total: 476.94 GB
Used: 250.30 GB
Free: 226.64 GB
Usage: 52.5%
```

### Example 2: File Management
```bash
$ python -m nlpcmd_ai.cli "find all python files larger than 1MB"

 📋 Category: file_operation
 ⚡ Action: find_files
 💻 Command: find . -name "*.py" -size +1M

Found 3 files:
./nlpcmd_ai/engine.py
./tests/test_suite.py
./examples/custom_handlers.py
```

### Example 3: Network Troubleshooting
```bash
$ python -m nlpcmd_ai.cli "what is my ip"

Local IP: 192.168.1.100
Public IP: 203.0.113.45

$ python -m nlpcmd_ai.cli "is port 8080 open"

Port 8080 on localhost: CLOSED
```

## 🔌 Extending nlpcmd-ai

Create custom handlers for your specific needs:

```python
# custom_handler.py
from nlpcmd_ai.base_handler import BaseHandler, CommandResult

class MyCustomHandler(BaseHandler):
    def can_handle(self, category: str, action: str) -> bool:
        return category == "my_custom_category"
    
    def execute(self, command: str, parameters: dict, dry_run: bool = False) -> CommandResult:
        # Your custom logic here
        return CommandResult(success=True, output="Custom output")
```

See [examples/custom_handlers.py](examples/custom_handlers.py) for more examples.

## 📊 Comparison with Alternatives

| Feature | nlpcmd-ai | Traditional CLI | Shell Scripts |
|---------|-----------|----------------|---------------|
| Natural Language | ✅ Yes | ❌ No | ❌ No |
| Cross-Platform | ✅ Auto-adapts | ⚠️ Manual | ⚠️ Manual |
| Learning Curve | ✅ None | ❌ High | ❌ High |
| AI-Powered | ✅ Yes | ❌ No | ❌ No |
| Interactive | ✅ Yes | ⚠️ Limited | ❌ No |
| Extensible | ✅ Yes | ⚠️ Limited | ✅ Yes |

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/Avikg/nlp_terminal_cmd.git
cd nlp_terminal_cmd

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenAI GPT](https://openai.com/), [Anthropic Claude](https://anthropic.com/), and [Ollama](https://ollama.ai/)
- Uses [psutil](https://github.com/giampaolo/psutil) for system information
- UI powered by [Rich](https://github.com/Textualize/rich)

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Avikg/nlp_terminal_cmd/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Avikg/nlp_terminal_cmd/discussions)
- **PyPI:** [https://pypi.org/project/nlpcmd-ai/](https://pypi.org/project/nlpcmd-ai/)

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on [GitHub](https://github.com/Avikg/nlp_terminal_cmd)!

---

**Made with ❤️ by [Avikg](https://github.com/Avikg)**

**Try it now:** `pip install nlpcmd-ai`

#### Linux

**Option 1: Using pip (Recommended)**
```bash
pip3 install nlpcmd-ai
```

**Option 2: Using installation script**
```bash
curl -O https://raw.githubusercontent.com/yourusername/nlpcmd-ai/main/install.sh
bash install.sh
```

If `nlpai` not found, add to PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

#### macOS

**Option 1: Using pip (Recommended)**
```bash
pip3 install nlpcmd-ai
```

**Option 2: Using installation script**
```bash
curl -O https://raw.githubusercontent.com/yourusername/nlpcmd-ai/main/install.sh
bash install.sh
```

### Advanced Installation

#### With Local LLM Support (Ollama)

```bash
pip install nlpcmd-ai[local]
```

#### From Source (Developers)

```bash
git clone https://github.com/yourusername/nlpcmd-ai.git
cd nlpcmd-ai
pip install -e .
```

#### All Optional Dependencies

```bash
pip install nlpcmd-ai[all]
```

## ⚙️ Configuration

Create a `.env` file or set environment variables:

```bash
# Choose your AI provider (openai, anthropic, or ollama)
NLP_PROVIDER=openai

# API Keys (if using cloud providers)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Ollama settings (if using local)
OLLAMA_MODEL=llama3.2
OLLAMA_HOST=http://localhost:11434

# Safety settings
REQUIRE_CONFIRMATION=true
DRY_RUN_MODE=false
LOG_COMMANDS=true
```

## 📖 Usage Examples

### One-off Commands

```bash
# Simple commands
nlpai "what is my ip address"
nlpai "show me disk usage"
nlpai "find all python files in this directory"

# Complex operations
nlpai "find all python files larger than 1MB modified in the last week"
nlpai "compress all log files from last month and move them to archive folder"
nlpai "show me the top 5 processes using most CPU"

# Development tasks
nlpai "create a git branch called feature/user-auth"
nlpai "install the requests library and add it to requirements.txt"
nlpai "run my tests and show me only the failures"

# File operations
nlpai "rename all .jpeg files to .jpg in the current folder"
nlpai "create a backup of all my python files"
nlpai "delete all cache folders recursively"

# Network operations
nlpai "check if port 8080 is open"
nlpai "download the file from this url and save it as data.json"
nlpai "what's the response time for google.com"
```

### Interactive Mode

```bash
nlpai

> show me the current directory
📁 Current directory: /home/user/projects

> list all python files
📄 Found 15 Python files:
  - main.py
  - utils.py
  ...

> show me the size of the largest one
📊 main.py: 15.3 KB

> open it in vim
✅ Opening main.py in vim...

> exit
👋 Goodbye!
```

### Conversation History

The AI remembers context within a session:

```bash
nlpai "create a folder called my_project"
nlpai "go into it"  # Remembers "my_project" from previous command
nlpai "create a python file named main.py"
nlpai "add a hello world function to it"  # Knows which file you're referring to
```

## 🎯 Supported Command Categories

### System Operations
- File and directory management
- Process management
- System information
- User management
- Environment variables

### Network Operations
- IP address information
- Port scanning
- Network connectivity tests
- DNS lookups
- HTTP requests

### Development Tools
- Git operations
- Package management (pip, npm, etc.)
- Docker commands
- Code formatting/linting
- Test execution

### Data Processing
- CSV/JSON manipulation
- Text file operations
- Data transformation
- Batch file operations

### Custom Extensions
- Plugin system for custom handlers
- Easy to add domain-specific commands

## 🔒 Safety Features

### Confirmation Prompts
Dangerous operations require confirmation:

```bash
nlpai "delete all files in /tmp"

⚠️  WARNING: This will delete files
Command: rm -rf /tmp/*
Execute? [y/N]:
```

### Dry Run Mode
Test commands without executing:

```bash
nlpai --dry-run "remove all .pyc files"

🔍 DRY RUN MODE
Would execute: find . -name "*.pyc" -delete
Affected files: 23 files
```

### Command Logging
All executed commands are logged:

```bash
cat ~/.nlpcmd_ai/history.log

2025-01-15 10:23:45 | User: "show my ip" | Executed: ip addr show
2025-01-15 10:24:12 | User: "delete old logs" | Executed: rm logs/*.log.old
```

## 🛠️ Advanced Usage

### Custom Handlers

Add your own command handlers:

```python
# ~/.nlpcmd_ai/handlers/custom.py

from nlpcmd_ai.handlers.base import BaseHandler

class MyCustomHandler(BaseHandler):
    def can_handle(self, intent: str, params: dict) -> bool:
        return intent == "deploy_app"
    
    def execute(self, params: dict) -> str:
        # Your custom deployment logic
        return "Deployment successful!"
```

### Configuration File

Advanced settings in `~/.nlpcmd_ai/config.yaml`:

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
    - "mkfs"
  allowed_directories:
    - "/home/user"
    - "/tmp"
    
logging:
  level: INFO
  file: ~/.nlpcmd_ai/nlpcmd.log
  
handlers:
  custom_path: ~/.nlpcmd_ai/handlers
```

## 🔄 How It Works

1. **Natural Language Input** → User types command in plain English
2. **AI Processing** → LLM analyzes intent and extracts parameters
3. **Intent Classification** → Determines command category
4. **Handler Selection** → Routes to appropriate handler
5. **Command Generation** → Creates safe, executable command
6. **Safety Check** → Validates and optionally asks for confirmation
7. **Execution** → Runs command and captures output
8. **Response** → Formats and displays result to user

## 📊 Comparison with Traditional CLI Tools

| Feature | Traditional CLI | nlpcmd-ai |
|---------|----------------|-----------|
| Input Style | Exact syntax required | Natural language |
| Learning Curve | Steep | Minimal |
| Flexibility | Limited to defined patterns | Understands variations |
| Context Awareness | None | Full conversation history |
| Error Handling | Cryptic errors | Helpful explanations |
| Discovery | Man pages/help flags | Just ask what you want |

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/Avikg/nlp_terminal_cmd.git
cd nlp_terminal_cmd

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenAI GPT](https://openai.com/), [Anthropic Claude](https://anthropic.com/), and [Ollama](https://ollama.ai/)
- Uses [psutil](https://github.com/giampaolo/psutil) for system information
- UI powered by [Rich](https://github.com/Textualize/rich)

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Avikg/nlp_terminal_cmd/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Avikg/nlp_terminal_cmd/discussions)
- **PyPI:** [https://pypi.org/project/nlpcmd-ai/](https://pypi.org/project/nlpcmd-ai/)

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on [GitHub](https://github.com/Avikg/nlp_terminal_cmd)!

---

**Made with ❤️ by [Avikg](https://github.com/Avikg)**

**Try it now:** `pip install nlpcmd-ai`

---

**⚠️ Note:** This tool executes system commands based on AI interpretation. Always review commands before execution and use safety features appropriately.
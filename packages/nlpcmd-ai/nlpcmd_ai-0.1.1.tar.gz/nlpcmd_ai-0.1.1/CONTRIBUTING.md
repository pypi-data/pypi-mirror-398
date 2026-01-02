# Contributing to nlpcmd-ai

Thank you for your interest in contributing to nlpcmd-ai! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Creating Custom Handlers](#creating-custom-handlers)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/nlpcmd-ai.git`
3. Add upstream remote: `git remote add upstream https://github.com/original/nlpcmd-ai.git`

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- Git

### Setup Steps

```bash
# Clone and enter directory
git clone https://github.com/yourusername/nlpcmd-ai.git
cd nlpcmd-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
make install-dev

# Or manually:
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env and add your API keys

# Run tests to verify
make test
```

## How to Contribute

### Reporting Bugs

Before creating a bug report:
- Check existing issues to avoid duplicates
- Collect relevant information (OS, Python version, error messages)

Bug report should include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces
- Environment details

### Suggesting Features

Feature requests should include:
- Clear use case and motivation
- Proposed API or interface
- Example usage
- Potential implementation approach (optional)

### Code Contributions

Good first contributions:
- Documentation improvements
- Bug fixes
- New command handlers
- Test coverage improvements
- Example scripts

## Creating Custom Handlers

Custom handlers are a great way to contribute! Here's how:

### Handler Template

```python
from nlpcmd_ai.base_handler import BaseHandler, CommandResult
from typing import Dict

class MyHandler(BaseHandler):
    """
    Brief description of what this handler does
    """
    
    def can_handle(self, category: str, action: str) -> bool:
        """
        Determine if this handler can process the command
        
        Args:
            category: Command category
            action: Specific action
            
        Returns:
            True if this handler should process the command
        """
        return category == "my_category"
    
    def execute(
        self, 
        command: str, 
        parameters: Dict, 
        dry_run: bool = False
    ) -> CommandResult:
        """
        Execute the command
        
        Args:
            command: System command to execute
            parameters: Additional parameters
            dry_run: If True, don't actually execute
            
        Returns:
            CommandResult with execution details
        """
        if dry_run:
            return CommandResult(
                success=True,
                output=f"[DRY RUN] Would execute: {command}",
                command=command
            )
        
        # Your implementation here
        return self.run_command(command)
```

### Handler Guidelines

1. **Single Responsibility**: Each handler should focus on one category
2. **Error Handling**: Always handle exceptions gracefully
3. **Dry Run Support**: Implement dry-run mode
4. **Documentation**: Include docstrings and examples
5. **Safety**: Validate inputs and paths
6. **Cross-platform**: Consider Windows, Linux, and macOS

### Contributing Handlers

1. Create handler in `nlpcmd_ai/handlers/`
2. Add tests in `tests/test_handlers.py`
3. Update documentation
4. Add usage examples
5. Submit PR with description

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_nlpcmd.py -v

# Run specific test
pytest tests/test_nlpcmd.py::TestHandlers::test_file_handler_can_handle -v

# Run with coverage
pytest --cov=nlpcmd_ai tests/
```

### Writing Tests

All new features should include tests:

```python
def test_my_feature():
    """Test description"""
    # Arrange
    handler = MyHandler()
    
    # Act
    result = handler.execute("command", {}, dry_run=True)
    
    # Assert
    assert result.success == True
    assert "expected" in result.output
```

Test categories:
- Unit tests: Test individual functions/methods
- Integration tests: Test components working together
- Handler tests: Test command handlers
- Config tests: Test configuration loading

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

```bash
# Format code
make format

# Check linting
make lint
```

Key points:
- Line length: 100 characters
- Use type hints
- Docstrings for all public functions/classes
- Descriptive variable names

### Docstring Format

```python
def function_name(arg1: str, arg2: int) -> bool:
    """
    Brief one-line description
    
    Longer description if needed, explaining what the function does,
    any important details, edge cases, etc.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When validation fails
    """
    pass
```

## Pull Request Process

### Before Submitting

1. ✅ Tests pass: `make test`
2. ✅ Code formatted: `make format`
3. ✅ Linting passes: `make lint`
4. ✅ Documentation updated
5. ✅ Changelog entry added (if applicable)

### PR Guidelines

1. **Branch naming**: 
   - Feature: `feature/description`
   - Bug fix: `fix/description`
   - Documentation: `docs/description`

2. **Commit messages**:
   - Use clear, descriptive messages
   - Format: `type: description`
   - Types: feat, fix, docs, test, refactor, chore

   ```
   feat: add support for Docker commands
   fix: handle timeout in network operations
   docs: update installation instructions
   ```

3. **PR description**:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Any breaking changes
   - Related issues

4. **Size**:
   - Keep PRs focused and manageable
   - Break large changes into smaller PRs
   - One feature/fix per PR

### Review Process

1. Automated checks must pass
2. At least one maintainer review required
3. Address review feedback
4. Squash commits if requested
5. Maintainer will merge when ready

## Development Workflow

### Typical Workflow

```bash
# Update your fork
git checkout main
git fetch upstream
git merge upstream/main

# Create feature branch
git checkout -b feature/my-feature

# Make changes
# ... edit files ...

# Test changes
make test
make format
make lint

# Commit changes
git add .
git commit -m "feat: add my feature"

# Push to your fork
git push origin feature/my-feature

# Create PR on GitHub
```

### Staying Updated

```bash
# Regularly sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Areas for Contribution

### High Priority

- [ ] Additional command handlers (database, cloud, etc.)
- [ ] Windows-specific command improvements
- [ ] Test coverage expansion
- [ ] Documentation improvements
- [ ] Performance optimizations

### Medium Priority

- [ ] Configuration UI/wizard
- [ ] Command history search
- [ ] Command aliases/shortcuts
- [ ] Output formatters
- [ ] Plugin system enhancements

### Ideas Welcome

- [ ] Your ideas here!

## Questions?

- Open an issue for questions
- Join our Discord/Slack (if available)
- Check existing documentation
- Ask in PR/issue comments

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Given credit in documentation

Thank you for contributing to nlpcmd-ai! 🎉

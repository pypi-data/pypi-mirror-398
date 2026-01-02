"""
Test Suite for nlpcmd-ai

Run with: pytest tests/test_nlpcmd.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from nlpcmd_ai.engine import AIEngine, CommandIntent, AIProvider
from nlpcmd_ai.base_handler import BaseHandler, CommandResult, HandlerRegistry
from nlpcmd_ai.handlers import FileHandler, NetworkHandler, SystemInfoHandler
from nlpcmd_ai.config import Config


class TestAIEngine:
    """Test AI Engine functionality"""
    
    def test_engine_initialization_openai(self):
        """Test OpenAI engine initialization"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            engine = AIEngine(provider="openai")
            assert engine.provider == AIProvider.OPENAI
            assert engine.model == "gpt-4-turbo-preview"
    
    def test_engine_initialization_anthropic(self):
        """Test Anthropic engine initialization"""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            engine = AIEngine(provider="anthropic")
            assert engine.provider == AIProvider.ANTHROPIC
            assert engine.model == "claude-3-5-sonnet-20241022"
    
    def test_parse_json_response(self):
        """Test parsing valid JSON response"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            engine = AIEngine(provider="openai")
            
            json_response = '''
            {
                "category": "file_operation",
                "action": "list",
                "parameters": {"path": "."},
                "command": "ls -la",
                "explanation": "List all files",
                "requires_confirmation": false,
                "confidence": 0.95
            }
            '''
            
            intent = engine._parse_response(json_response, "list all files")
            
            assert intent.category == "file_operation"
            assert intent.action == "list"
            assert intent.confidence == 0.95
            assert intent.suggested_command == "ls -la"
    
    def test_conversation_history(self):
        """Test conversation history tracking"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            engine = AIEngine(provider="openai")
            
            assert len(engine.conversation_history) == 0
            
            # Simulate adding to history
            intent = CommandIntent(
                category="test",
                action="test",
                parameters={},
                confidence=0.9,
                original_query="test query"
            )
            engine.conversation_history.append({"query": "test", "intent": intent})
            
            assert len(engine.conversation_history) == 1
            
            engine.clear_history()
            assert len(engine.conversation_history) == 0


class TestHandlers:
    """Test command handlers"""
    
    def test_file_handler_can_handle(self):
        """Test FileHandler category detection"""
        handler = FileHandler()
        
        assert handler.can_handle("file_operation", "list") == True
        assert handler.can_handle("network", "ping") == False
    
    def test_network_handler_can_handle(self):
        """Test NetworkHandler category detection"""
        handler = NetworkHandler()
        
        assert handler.can_handle("network", "get_ip") == True
        assert handler.can_handle("file_operation", "delete") == False
    
    def test_run_command_success(self):
        """Test successful command execution"""
        handler = FileHandler()
        
        # Run a simple command that should succeed
        result = handler.run_command("echo 'test'")
        
        assert result.success == True
        assert "test" in result.output
        assert result.exit_code == 0
    
    def test_run_command_failure(self):
        """Test failed command execution"""
        handler = FileHandler()
        
        # Run a command that should fail
        result = handler.run_command("nonexistent_command_12345")
        
        assert result.success == False
        assert result.exit_code != 0
    
    def test_validate_path_safe(self):
        """Test path validation for safe paths"""
        handler = FileHandler()
        
        assert handler.validate_path("/home/user/test") == True
        assert handler.validate_path("/tmp/test") == True
    
    def test_validate_path_dangerous(self):
        """Test path validation for dangerous paths"""
        handler = FileHandler()
        
        assert handler.validate_path("/") == False
        assert handler.validate_path("/bin") == False
        assert handler.validate_path("/etc") == False
        assert handler.validate_path("C:\\Windows") == False


class TestHandlerRegistry:
    """Test handler registry"""
    
    def test_registry_initialization(self):
        """Test registry loads default handlers"""
        registry = HandlerRegistry()
        
        assert len(registry.handlers) > 0
    
    def test_get_handler_file_operation(self):
        """Test getting file operation handler"""
        registry = HandlerRegistry()
        
        handler = registry.get_handler("file_operation", "list")
        
        assert handler is not None
        assert isinstance(handler, FileHandler)
    
    def test_get_handler_network(self):
        """Test getting network handler"""
        registry = HandlerRegistry()
        
        handler = registry.get_handler("network", "ping")
        
        assert handler is not None
        assert isinstance(handler, NetworkHandler)
    
    def test_get_handler_not_found(self):
        """Test handler not found"""
        registry = HandlerRegistry()
        
        handler = registry.get_handler("nonexistent", "action")
        
        assert handler is None


class TestConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.ai_provider == "openai"
        assert config.require_confirmation == True
        assert config.log_commands == True
    
    def test_config_from_env(self):
        """Test loading config from environment"""
        with patch.dict('os.environ', {
            'NLP_PROVIDER': 'anthropic',
            'REQUIRE_CONFIRMATION': 'false',
            'LOG_COMMANDS': 'false'
        }):
            config = Config.load()
            
            assert config.ai_provider == "anthropic"
            assert config.require_confirmation == False
            assert config.log_commands == False
    
    def test_dangerous_command_detection(self):
        """Test dangerous command pattern detection"""
        config = Config()
        
        assert config.is_dangerous_command("rm -rf /") == True
        assert config.is_dangerous_command("ls -la") == False
        assert config.is_dangerous_command("dd if=/dev/zero") == True


class TestCommandResult:
    """Test CommandResult dataclass"""
    
    def test_command_result_success(self):
        """Test successful command result"""
        result = CommandResult(
            success=True,
            output="Command executed",
            command="echo 'test'"
        )
        
        assert result.success == True
        assert result.output == "Command executed"
        assert result.error is None
        assert result.exit_code == 0
    
    def test_command_result_failure(self):
        """Test failed command result"""
        result = CommandResult(
            success=False,
            output="",
            error="Command failed",
            exit_code=1,
            command="bad_command"
        )
        
        assert result.success == False
        assert result.error == "Command failed"
        assert result.exit_code == 1


class TestCommandIntent:
    """Test CommandIntent dataclass"""
    
    def test_command_intent_creation(self):
        """Test creating CommandIntent"""
        intent = CommandIntent(
            category="file_operation",
            action="list",
            parameters={"path": "/tmp"},
            confidence=0.95,
            original_query="list files in /tmp",
            suggested_command="ls /tmp",
            explanation="List files in directory",
            requires_confirmation=False
        )
        
        assert intent.category == "file_operation"
        assert intent.action == "list"
        assert intent.confidence == 0.95
        assert intent.requires_confirmation == False


# Integration Tests

class TestIntegration:
    """Integration tests for end-to-end workflows"""
    
    @pytest.mark.integration
    def test_full_workflow_dry_run(self):
        """Test complete workflow in dry-run mode"""
        # This would test the full flow from query to execution
        # Would require mocking the AI API calls
        pass
    
    @pytest.mark.integration 
    def test_interactive_mode(self):
        """Test interactive mode workflow"""
        # This would test the interactive CLI
        # Would require mocking user input
        pass


# Fixture for common test data

@pytest.fixture
def sample_intent():
    """Sample CommandIntent for testing"""
    return CommandIntent(
        category="file_operation",
        action="list",
        parameters={"path": "."},
        confidence=0.9,
        original_query="list all files",
        suggested_command="ls -la",
        explanation="List all files in current directory",
        requires_confirmation=False
    )


@pytest.fixture
def sample_config():
    """Sample Config for testing"""
    return Config(
        ai_provider="openai",
        ai_model="gpt-4-turbo-preview",
        require_confirmation=True,
        log_commands=True
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

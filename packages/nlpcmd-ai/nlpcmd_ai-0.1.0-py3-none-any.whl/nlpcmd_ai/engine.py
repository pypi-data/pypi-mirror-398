"""
AI Engine for NLP Command Processing

This module handles the core AI processing: understanding natural language,
determining intent, extracting parameters, and generating executable commands.
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


@dataclass
class CommandIntent:
    """Represents the understood intent from natural language"""
    category: str  # e.g., "file_operation", "network", "system_info"
    action: str  # e.g., "list", "delete", "create"
    parameters: Dict  # extracted parameters
    confidence: float  # 0.0 to 1.0
    original_query: str
    suggested_command: Optional[str] = None
    explanation: Optional[str] = None
    requires_confirmation: bool = False


class AIEngine:
    """Main AI engine for processing natural language commands"""
    
    SYSTEM_PROMPT = """You are an expert system administrator and command-line interface assistant.
Your role is to understand natural language requests and translate them into safe, executable system commands.

**CRITICAL: Cross-Platform Awareness**
ALWAYS generate commands appropriate for the user's operating system:
- Windows: Use PowerShell or cmd.exe commands (Get-*, where.exe, dir, etc.)
- Linux/macOS: Use bash/zsh commands (find, grep, ls, etc.)
- Prefer cross-platform tools when available (Python, Node.js)

**Guidelines:**
1. Understand the user's intent from natural language
2. Generate OS-appropriate commands based on context provided
3. Provide a clear explanation of what the command does
4. Flag dangerous operations that need confirmation
5. Consider the user's operating system and shell
6. If the request is ambiguous, ask for clarification

**Response Format (JSON):**
{
    "category": "category_name",
    "action": "action_name",
    "parameters": {},
    "command": "executable_command",
    "explanation": "what this command does",
    "requires_confirmation": true/false,
    "confidence": 0.0-1.0,
    "clarification_needed": "optional question if unclear",
    "os_specific": true/false
}

**Categories:**
- file_operation: create, delete, move, copy, rename, find files/directories
- network: IP info, connectivity, DNS, HTTP requests, port scanning
- system_info: disk usage, memory, CPU, processes, users
- process_mgmt: start, stop, kill processes
- development: git, docker, package managers, code tools
- data_processing: CSV, JSON, text manipulation
- custom: user-defined handlers

**Safety:**
Flag requires_confirmation=true for:
- Deleting files/directories (especially recursive)
- Modifying system files
- Stopping critical processes
- Network operations that send data
- Anything with sudo/admin privileges
"""

    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = AIProvider(provider.lower())
        self.model = model or self._get_default_model()
        self.conversation_history: List[Dict] = []
        self._init_client()
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            AIProvider.OPENAI: "gpt-4o-mini",
            AIProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
            AIProvider.OLLAMA: "llama3.2"
        }
        return defaults[self.provider]
    
    def _init_client(self):
        """Initialize the AI client"""
        if self.provider == AIProvider.OPENAI:
            import openai
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = openai.OpenAI(api_key=api_key)
            
        elif self.provider == AIProvider.ANTHROPIC:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=api_key)
            
        elif self.provider == AIProvider.OLLAMA:
            try:
                import ollama
                self.client = ollama.Client(
                    host=os.getenv("OLLAMA_HOST", "http://localhost:11434")
                )
            except ImportError:
                raise ImportError(
                    "Ollama support requires 'ollama' package. "
                    "Install with: pip install nlpcmd-ai[local]"
                )
    
    def process_query(
        self, 
        query: str, 
        context: Optional[Dict] = None
    ) -> CommandIntent:
        """
        Process a natural language query and return structured intent
        
        Args:
            query: Natural language command from user
            context: Optional context (OS, current directory, etc.)
            
        Returns:
            CommandIntent object with parsed information
        """
        # Build context information
        system_context = self._build_context(context)
        
        # Get AI response
        response = self._call_ai(query, system_context)
        
        # Parse and structure the response
        intent = self._parse_response(response, query)
        
        # Add to conversation history
        self.conversation_history.append({
            "query": query,
            "intent": intent
        })
        
        return intent
    
    def _build_context(self, context: Optional[Dict]) -> str:
        """Build context string for AI"""
        import platform
        
        ctx_parts = [
            f"Operating System: {platform.system()}",
            f"Platform: {platform.platform()}",
        ]
        
        if context:
            if "cwd" in context:
                ctx_parts.append(f"Current Directory: {context['cwd']}")
            if "user" in context:
                ctx_parts.append(f"User: {context['user']}")
            if "shell" in context:
                ctx_parts.append(f"Shell: {context['shell']}")
        
        # Add recent conversation context
        if self.conversation_history:
            recent = self.conversation_history[-3:]  # Last 3 exchanges
            ctx_parts.append("\nRecent Conversation:")
            for i, item in enumerate(recent, 1):
                ctx_parts.append(f"{i}. User: {item['query']}")
                if item['intent'].suggested_command:
                    ctx_parts.append(f"   Executed: {item['intent'].suggested_command}")
        
        return "\n".join(ctx_parts)
    
    def _call_ai(self, query: str, context: str) -> str:
        """Call the AI provider"""
        if self.provider == AIProvider.OPENAI:
            return self._call_openai(query, context)
        elif self.provider == AIProvider.ANTHROPIC:
            return self._call_anthropic(query, context)
        elif self.provider == AIProvider.OLLAMA:
            return self._call_ollama(query, context)
    
    def _call_openai(self, query: str, context: str) -> str:
        """Call OpenAI API"""
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT + "\n\n" + context},
            {"role": "user", "content": query}
        ]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    def _call_anthropic(self, query: str, context: str) -> str:
        """Call Anthropic Claude API"""
        system_msg = self.SYSTEM_PROMPT + "\n\n" + context
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0.3,
            system=system_msg,
            messages=[
                {"role": "user", "content": query}
            ]
        )
        
        return message.content[0].text
    
    def _call_ollama(self, query: str, context: str) -> str:
        """Call Ollama local LLM"""
        system_msg = self.SYSTEM_PROMPT + "\n\n" + context
        system_msg += "\n\nIMPORTANT: Respond ONLY with valid JSON, no other text."
        
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": query}
            ],
            options={"temperature": 0.3}
        )
        
        return response['message']['content']
    
    def _parse_response(self, response: str, original_query: str) -> CommandIntent:
        """Parse AI response into CommandIntent"""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            return CommandIntent(
                category=data.get("category", "unknown"),
                action=data.get("action", "unknown"),
                parameters=data.get("parameters", {}),
                confidence=data.get("confidence", 0.8),
                original_query=original_query,
                suggested_command=data.get("command"),
                explanation=data.get("explanation"),
                requires_confirmation=data.get("requires_confirmation", False)
            )
            
        except json.JSONDecodeError:
            # Fallback: try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    return CommandIntent(
                        category=data.get("category", "unknown"),
                        action=data.get("action", "unknown"),
                        parameters=data.get("parameters", {}),
                        confidence=data.get("confidence", 0.8),
                        original_query=original_query,
                        suggested_command=data.get("command"),
                        explanation=data.get("explanation"),
                        requires_confirmation=data.get("requires_confirmation", False)
                    )
                except json.JSONDecodeError:
                    pass
            
            # Fallback: return low-confidence intent
            return CommandIntent(
                category="error",
                action="parse_failed",
                parameters={"raw_response": response},
                confidence=0.1,
                original_query=original_query,
                explanation="Failed to parse AI response. Please try rephrasing your query.",
                requires_confirmation=True
            )
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
"""
Mock ADK (Agent Development Kit) module for development and testing.

This module provides mock implementations of the Google ADK classes
to allow development and testing of the trip planner application
when the actual ADK is not available.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import uuid
import asyncio


class Session:
    """Mock ADK Session class."""
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        self.id = session_id or str(uuid.uuid4())
        self.user_id = user_id or f"user-{uuid.uuid4()}"
        self.data = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get session data."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set session data."""
        self.data[key] = value


class Tool(ABC):
    """Mock ADK Tool base class."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool."""
        pass


class Agent(ABC):
    """Mock ADK Agent base class."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def process(self, input_data: Any, session: Session) -> Any:
        """Process input data."""
        pass


class LlmAgent(Agent):
    """Mock ADK LlmAgent class for AI-powered agents."""
    
    def __init__(self, name: str, description: str = ""):
        super().__init__(name, description)
    
    async def process(self, input_data: Any, session: Session) -> Any:
        """Process input with LLM capabilities."""
        # Mock implementation
        return {"status": "processed", "agent": self.name, "input": input_data}


class AdkApp:
    """Mock ADK Application class."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools: Dict[str, Tool] = {}
        self.agents: Dict[str, Agent] = {}
        self.sessions: Dict[str, Session] = {}
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the application."""
        self.tools[tool.name] = tool
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the application."""
        self.agents[agent.name] = agent
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self.agents.get(name)
    
    def create_session(self, user_id: Optional[str] = None) -> Session:
        """Create a new session."""
        session = Session(user_id=user_id)
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    async def process_message(self, message: str, session: Session) -> str:
        """Process a user message through the application."""
        # Mock implementation - would normally route through agents
        return f"Processed message: {message} in session {session.id}"
    
    def run(self, host: str = "localhost", port: int = 8080, debug: bool = False) -> None:
        """Run the application (mock implementation)."""
        print(f"Mock ADK App '{self.name}' running on {host}:{port}")
        print(f"Tools: {list(self.tools.keys())}")
        print(f"Agents: {list(self.agents.keys())}")
        
        if debug:
            print("Debug mode enabled")


# Mock configuration classes
class Config:
    """Mock ADK Config class."""
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.data = config_dict or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.data[key] = value


class SessionManager:
    """Mock ADK SessionManager class."""
    
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout
        self.sessions: Dict[str, Session] = {}
    
    def create_session(self, user_id: Optional[str] = None) -> Session:
        """Create a new session."""
        session = Session(user_id=user_id)
        self.sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get an existing session."""
        return self.sessions.get(session_id)
    
    def cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        # Mock implementation
        pass


# Export all classes for compatibility
__all__ = [
    "AdkApp", "Agent", "LlmAgent", "Tool", "Session", 
    "Config", "SessionManager"
]
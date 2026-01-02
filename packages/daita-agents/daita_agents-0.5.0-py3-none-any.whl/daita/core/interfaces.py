"""
Core interfaces for Daita Agents.

Defines the essential contracts that components must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import pandas as pd

class Agent(ABC):
    """Base interface for all agents."""

    @abstractmethod
    async def _process(
        self,
        task: str,
        data: Any = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """INTERNAL: Process a task with data and context."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the agent."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the agent."""
        pass

class LLMProvider(ABC):
    """Interface for language model providers."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @property
    @abstractmethod
    def info(self) -> Dict[str, Any]:
        """Get information about the LLM provider."""
        pass

class DatabaseBackend(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute database query."""
        pass

class DataProcessor(ABC):
    """Interface for data processing operations."""
    
    @abstractmethod
    async def process(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]], str, bytes],
        focus: Optional[Union[List[str], str, Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]]:
        """Process data with optional focus parameter."""
        pass
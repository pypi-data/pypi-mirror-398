"""
Agent implementations for Daita Agents.

This module provides the core agent implementations:
- BaseAgent: Foundation class with retry logic and error handling
- SubstrateAgent: Flexible agent that can be customized with handlers and presets

The agent system is designed around the SubstrateAgent as the primary interface,
with preset configurations for common patterns like analysis and transformation.

Usage:
    ```python
    from daita.agents import SubstrateAgent
    
    # Direct instantiation (recommended)
    agent = SubstrateAgent(name="My Agent", llm_provider="openai", model="gpt-4")
    
    # Or with configuration object (backward compatibility)
    from daita.config.base import AgentConfig
    config = AgentConfig(name="My Agent")
    agent = SubstrateAgent(config=config)
    ```
"""

# Core agent classes
from .base import BaseAgent
from .substrate import SubstrateAgent

# Export all agent functionality
__all__ = [
    "BaseAgent",
    "SubstrateAgent", 
]
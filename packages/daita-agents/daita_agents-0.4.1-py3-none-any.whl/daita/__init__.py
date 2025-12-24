"""
Daita Agents - A flexible framework for AI agent creation and orchestration.

This module provides the main entry point for the Daita framework with
automatic tracing and observability built-in.

Key Components:
- Agent framework with BaseAgent and SubstrateAgent
- LLM provider abstractions for OpenAI, Anthropic, Grok, and Gemini
- Plugin system for database and API integrations
- Workflow orchestration for multi-agent systems
- Unified tracing system for automatic observability
- Decision tracing for agent reasoning capture
- Plugin execution monitoring
"""

# Version info
__version__ = "0.1.1"

# PRIMARY INTERFACE - Direct classes
from .agents.substrate import SubstrateAgent
from .agents.base import BaseAgent

# Tool system - For creating custom tools
from .core.tools import tool, AgentTool, ToolRegistry

# Plugin system - Direct imports
from .plugins import postgresql, mysql, mongodb, rest, s3, slack, elasticsearch
from .plugins import PluginAccess

# Configuration classes
from .config.base import AgentConfig, DaitaConfig, AgentType, RetryPolicy, RetryStrategy

# Reliability components - NEW: Production-grade reliability features
from .core.reliability import (
    TaskManager,
    TaskStatus,
    BackpressureController,
    CircuitBreaker,
    CircuitState
)

# Core interfaces - For advanced users who want to implement custom components
from .core.interfaces import (
    Agent,
    LLMProvider,
    DatabaseBackend,
    DataProcessor
)

# Core workflow components - For multi-agent systems
from .core.workflow import Workflow, ReliabilityConfig
from .core.relay import RelayManager

# Scaling components - For horizontal scaling
from .core.scaling import AgentPool, LoadBalancer, PoolStatus, create_agent_pool

# Exception hierarchy - For error handling
from .core.exceptions import (
    DaitaError,
    AgentError,
    LLMError,
    ConfigError,
    PluginError,
    WorkflowError,
    # Retry-specific exceptions
    TransientError,
    RetryableError,
    PermanentError,
    # Specific error types
    RateLimitError,
    TimeoutError,
    AuthenticationError,
    ValidationError,
    # Reliability-specific exceptions
    BackpressureError,
    TaskTimeoutError,
    AcknowledgmentTimeoutError,
    TaskNotFoundError,
    ReliabilityConfigurationError,
    CircuitBreakerOpenError
)

# LLM providers - For direct LLM access
from .llm.factory import create_llm_provider
from .llm.openai import OpenAIProvider
from .llm.anthropic import AnthropicProvider
from .llm.grok import GrokProvider
from .llm.gemini import GeminiProvider
from .llm.mock import MockLLMProvider

# Plugin system - For database and API integrations
from .plugins import PluginAccess
from .plugins.redis_messaging import RedisMessagingPlugin, redis_messaging

# Automatic Tracing System - NEW: Zero-configuration observability
from .core.tracing import (
    get_trace_manager,
    TraceType,
    TraceStatus
)

# Plugin Tracing - NEW: Automatic tool execution monitoring
from .core.plugin_tracing import (
    trace_plugin,
    traced_postgresql,
    traced_mysql,
    traced_mongodb,
    traced_rest
)

# Decision Tracing - NEW: Agent reasoning and confidence capture
from .core.decision_tracing import (
    record_decision_point,
    trace_decision,
    DecisionType
)

# Autonomous Execution - NEW: Programmatic agent execution
from .execution.client import DaitaClient
from .execution.models import ExecutionResult, ScheduledTask, WebhookTrigger
from .execution.exceptions import ExecutionError

# MAIN EXPORTS
__all__ = [
    # PRIMARY INTERFACES - Direct classes (what users need most)
    "SubstrateAgent",
    "BaseAgent",
    "Workflow",
    "DaitaClient",

    # TOOL SYSTEM - For creating custom tools
    "tool",
    "AgentTool",
    "ToolRegistry",

    # PLUGIN FUNCTIONS - Direct imports (new primary way)
    "postgresql", "mysql", "mongodb", "rest", "s3", "slack", "elasticsearch",

    # CORE UTILITIES - Essential framework features
    "RelayManager",
    "create_llm_provider",
    "DaitaError",
    "get_trace_manager",
    
    # CONFIGURATION - Optional advanced usage
    "AgentConfig",
    "DaitaConfig",
    "AgentType",
    "RetryPolicy",
    "RetryStrategy",
    
    # LEGACY COMPONENTS - Advanced/internal usage
    "PluginAccess",
    
    # Advanced workflow components  
    "ReliabilityConfig",
    "AgentPool",
    "LoadBalancer",
    "create_agent_pool",
    
    # Exception hierarchy
    "AgentError",
    "LLMError",
    "ConfigError", 
    "PluginError",
    "WorkflowError",
    
    # LLM providers (optional - auto-created by agents)
    "OpenAIProvider",
    "AnthropicProvider",
    "GrokProvider", 
    "GeminiProvider",
    
    # Advanced interfaces
    "Agent",
    "LLMProvider",
    
    # Tracing (automatic - optional direct access)
    "TraceType",
    "record_decision_point",
    "trace_decision",

    # Autonomous execution models and exceptions
    "ExecutionResult",
    "ScheduledTask",
    "WebhookTrigger",
    "ExecutionError"
]

# Framework metadata
FRAMEWORK_INFO = {
    "name": "Daita Agents",
    "version": __version__,
    "description": "A flexible framework for AI agent creation and orchestration with automatic tracing",
    "features": [
        "Zero-configuration automatic tracing",
        "Production-grade reliability features",
        "Message acknowledgments and task tracking",
        "Backpressure control and circuit breakers", 
        "Agent operation monitoring", 
        "LLM call tracking with costs",
        "Plugin/tool execution tracing",
        "Decision reasoning capture",
        "Workflow communication tracking",
        "Dashboard integration"
    ],
    "tracing_enabled": True
}

def get_framework_info() -> dict:
    """Get framework information and metadata."""
    return FRAMEWORK_INFO.copy()

# Add to exports
__all__.append("get_framework_info")
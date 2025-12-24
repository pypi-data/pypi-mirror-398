"""
Autonomous Execution Package for Daita Agents.

This package provides programmatic execution capabilities for deployed agents
and workflows, enabling users to build autonomous systems that can trigger
agent execution from external code.

Main Components:
- DaitaClient: Primary interface for programmatic agent execution
- ExecutionResult: Response model for execution results
- ScheduledTask: Model for scheduled execution configuration
- WebhookTrigger: Model for webhook-triggered execution configuration

Clean API Design:
- Sync methods are primary interface (no ugly _sync suffixes)
- Async methods available with _async suffix for advanced users
- Clear, descriptive method names that state what they do

Example Usage:
    from daita import DaitaClient

    # Initialize with user's existing API key
    client = DaitaClient(api_key="your_api_key")

    # Execute agent and wait for completion (sync)
    result = client.execute_agent("my_agent", data={"input": "data"}, wait=True)

    # Check execution status
    status = client.get_execution(result.execution_id)

    # Get latest execution for an agent
    latest = client.get_latest_execution(agent_name="my_agent")

Async Usage (Advanced):
    async with DaitaClient(api_key="your_api_key") as client:
        result = await client.execute_agent_async("my_agent", data={"input": "data"})
        status = await client.get_execution_async(result.execution_id)
"""

from .client import DaitaClient
from .models import ExecutionResult, ScheduledTask, WebhookTrigger
from .exceptions import (
    ExecutionError,
    AuthenticationError,
    NotFoundError,
    ValidationError
)

__all__ = [
    "DaitaClient",
    "ExecutionResult",
    "ScheduledTask",
    "WebhookTrigger",
    "ExecutionError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError"
]
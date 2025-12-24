"""
Data models for the autonomous execution system.

These models provide structured representations of execution results,
scheduled tasks, and webhook triggers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
import json


@dataclass
class ExecutionResult:
    """
    Represents the result of an autonomous agent or workflow execution.

    This class provides a structured way to access execution results
    and metadata from programmatic agent executions.
    """

    execution_id: str
    status: str  # queued, running, completed, failed, cancelled
    target_type: str  # agent or workflow
    target_name: str

    # Result data
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Timing information
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Resource usage
    memory_used_mb: Optional[float] = None
    cost_estimate: Optional[float] = None

    # Monitoring and debugging
    trace_id: Optional[str] = None
    dashboard_url: Optional[str] = None

    # Execution metadata
    execution_source: str = "autonomous_sdk"
    source_metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete (success or failure)."""
        return self.status in ['completed', 'success', 'failed', 'cancelled']

    @property
    def is_success(self) -> bool:
        """Check if execution completed successfully."""
        return self.status in ['completed', 'success']

    @property
    def is_running(self) -> bool:
        """Check if execution is currently running."""
        return self.status in ['queued', 'running']

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get duration in seconds."""
        return self.duration_ms / 1000 if self.duration_ms else None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        """Create ExecutionResult from API response data."""

        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        started_at = None
        if data.get('started_at'):
            started_at = datetime.fromisoformat(data['started_at'].replace('Z', '+00:00'))

        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00'))

        # Parse result field - handle both string and dict formats
        result = data.get('result')
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, keep as string or convert to dict with raw content
                result = {"raw_output": result} if result else None

        return cls(
            execution_id=data['execution_id'],
            status=data['status'],
            target_type=data['target_type'],
            target_name=data['target_name'],
            result=result,
            error=data.get('error'),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=data.get('duration_ms'),
            memory_used_mb=data.get('memory_used_mb'),
            cost_estimate=data.get('cost_estimate'),
            trace_id=data.get('trace_id'),
            dashboard_url=data.get('dashboard_url'),
            execution_source=data.get('execution_source', 'autonomous_sdk'),
            source_metadata=data.get('source_metadata', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'execution_id': self.execution_id,
            'status': self.status,
            'target_type': self.target_type,
            'target_name': self.target_name,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_ms': self.duration_ms,
            'memory_used_mb': self.memory_used_mb,
            'cost_estimate': self.cost_estimate,
            'trace_id': self.trace_id,
            'dashboard_url': self.dashboard_url,
            'execution_source': self.execution_source,
            'source_metadata': self.source_metadata
        }

    def __repr__(self) -> str:
        return f"ExecutionResult(id={self.execution_id[:8]}..., status={self.status}, target={self.target_name})"


@dataclass
class ScheduledTask:
    """
    Represents a scheduled agent or workflow execution.

    This class provides information about scheduled tasks configured
    through the YAML-based scheduling system.
    """

    # Required fields (no defaults)
    task_id: str
    organization_id: int
    schedule: str  # cron expression

    # Optional fields (with defaults)
    deployment_id: Optional[str] = None
    agent_name: Optional[str] = None
    workflow_name: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timezone: str = "UTC"
    enabled: bool = True

    # Timing information
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # AWS EventBridge information
    eventbridge_rule_arn: Optional[str] = None

    @property
    def target_name(self) -> str:
        """Get the target name (agent or workflow)."""
        return self.agent_name or self.workflow_name or "unknown"

    @property
    def target_type(self) -> str:
        """Get the target type (agent or workflow)."""
        return "agent" if self.agent_name else "workflow"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScheduledTask":
        """Create ScheduledTask from API response data."""

        # Parse datetime fields
        next_run = None
        if data.get('next_run'):
            next_run = datetime.fromisoformat(data['next_run'].replace('Z', '+00:00'))

        last_run = None
        if data.get('last_run'):
            last_run = datetime.fromisoformat(data['last_run'].replace('Z', '+00:00'))

        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))

        # Handle schedule_config if it's a nested object
        schedule_config = data.get('schedule_config', {})
        if isinstance(schedule_config, str):
            schedule_config = json.loads(schedule_config)

        return cls(
            task_id=data['id'],
            organization_id=data['organization_id'],
            deployment_id=data.get('deployment_id'),
            agent_name=data.get('agent_name'),
            workflow_name=data.get('workflow_name'),
            schedule=schedule_config.get('cron', data.get('schedule', '')),
            data=schedule_config.get('data', {}),
            timezone=schedule_config.get('timezone', 'UTC'),
            enabled=data.get('enabled', True),
            next_run=next_run,
            last_run=last_run,
            created_at=created_at,
            updated_at=updated_at,
            eventbridge_rule_arn=data.get('eventbridge_rule_arn')
        )

    def __repr__(self) -> str:
        return f"ScheduledTask(id={self.task_id[:8]}..., target={self.target_name}, schedule={self.schedule})"


@dataclass
class WebhookTrigger:
    """
    Represents a webhook trigger for agent or workflow execution.

    This class provides information about webhook configurations that
    can trigger agent executions based on external events.
    """

    webhook_id: str
    webhook_url: str
    organization_id: int
    deployment_id: Optional[str] = None

    # Target information
    agent_name: Optional[str] = None
    workflow_name: Optional[str] = None

    # Webhook configuration
    data_template: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    # Timing information
    created_at: Optional[datetime] = None

    # Statistics
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None

    @property
    def target_name(self) -> str:
        """Get the target name (agent or workflow)."""
        return self.agent_name or self.workflow_name or "unknown"

    @property
    def target_type(self) -> str:
        """Get the target type (agent or workflow)."""
        return "agent" if self.agent_name else "workflow"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookTrigger":
        """Create WebhookTrigger from API response data."""

        # Parse datetime fields
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

        last_triggered = None
        if data.get('last_triggered'):
            last_triggered = datetime.fromisoformat(data['last_triggered'].replace('Z', '+00:00'))

        # Handle data_template if it's a string
        data_template = data.get('data_template', {})
        if isinstance(data_template, str):
            data_template = json.loads(data_template)

        return cls(
            webhook_id=data['webhook_id'],
            webhook_url=data['webhook_url'],
            organization_id=data['organization_id'],
            deployment_id=data.get('deployment_id'),
            agent_name=data.get('agent_name'),
            workflow_name=data.get('workflow_name'),
            data_template=data_template,
            enabled=data.get('enabled', True),
            created_at=created_at,
            trigger_count=data.get('trigger_count', 0),
            last_triggered=last_triggered
        )

    def __repr__(self) -> str:
        return f"WebhookTrigger(id={self.webhook_id[:8]}..., target={self.target_name}, enabled={self.enabled})"


# Utility functions for working with models

def parse_execution_response(response_data: Dict[str, Any]) -> ExecutionResult:
    """Parse API response into ExecutionResult."""
    return ExecutionResult.from_dict(response_data)


def parse_schedule_list(response_data: list) -> list[ScheduledTask]:
    """Parse API response list into ScheduledTask objects."""
    return [ScheduledTask.from_dict(item) for item in response_data]


def parse_webhook_list(response_data: list) -> list[WebhookTrigger]:
    """Parse API response list into WebhookTrigger objects."""
    return [WebhookTrigger.from_dict(item) for item in response_data]
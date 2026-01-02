"""
DaitaClient - Primary interface for autonomous agent execution.

This client provides a clean, developer-friendly API for programmatically
executing deployed agents and workflows. It handles authentication, retry
logic, and error handling automatically.

Sync-First Design:
    All primary methods are synchronous by default. Async methods available
    with _async suffix for advanced users who need async/await patterns.

Example Usage:
    from daita import DaitaClient

    # Initialize with user's existing API key
    client = DaitaClient(api_key="your_api_key")

    # Execute agent and wait for completion
    result = client.execute_agent("my_agent", data={"input": "data"}, wait=True)

    # Check execution status
    status = client.get_execution(result.execution_id)

    # Wait for completion if needed
    final_result = client.wait_for_execution(result.execution_id)

    # List recent executions
    executions = client.list_executions(limit=10)

    # Get latest result for specific agent
    latest = client.get_latest_execution(agent_name="my_agent")

Async Usage (Advanced):
    async with DaitaClient(api_key="your_api_key") as client:
        result = await client.execute_agent_async("my_agent")
        status = await client.get_execution_async(result.execution_id)
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone

import aiohttp

from .models import ExecutionResult, ScheduledTask, WebhookTrigger
from .exceptions import (
    ExecutionError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    TimeoutError,
    ServerError
)


class DaitaClient:
    """
    Primary client for autonomous agent and workflow execution.

    This client provides programmatic access to deployed agents and workflows,
    enabling users to build autonomous systems that can trigger executions
    from external code.

    Features:
    - Clean, intuitive API with sync methods as primary interface
    - Async methods available with _async suffix for advanced users
    - Automatic retry logic with exponential backoff
    - Comprehensive error handling and tracing
    - Built on existing DAITA infrastructure

    Primary Methods (Sync):
    - execute_agent() / execute_workflow() - Run agents/workflows
    - get_execution() - Get current status
    - wait_for_execution() - Wait for completion
    - list_executions() - List recent executions
    - get_latest_execution() - Get most recent execution
    - cancel_execution() - Cancel running execution

    Advanced Methods (Async):
    - All methods available with _async suffix for async usage
    """

    def __init__(
        self,
        api_key: str,
        api_base: Optional[str] = None,
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the DaitaClient.

        Args:
            api_key: User's DAITA API key (same key used for CLI)
            api_base: API base URL (defaults to production API)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds
        """
        self.api_key = api_key
        self.api_base = api_base or os.getenv('DAITA_API_ENDPOINT', 'https://api.daita-tech.io')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # HTTP session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None

    async def _ensure_session(self):
        """Ensure HTTP session is created."""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Daita-Autonomous-Client/1.0.0'
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )

    # Core execution methods

    async def run(
        self,
        agent_name: Optional[str] = None,
        workflow_name: Optional[str] = None,
        data: Dict[str, Any] = None,
        task: str = "process",
        context: Dict[str, Any] = None,
        environment: str = "production",
        wait_for_completion: bool = False,
        poll_interval: float = 2.0
    ) -> ExecutionResult:
        """
        Execute an agent or workflow programmatically.

        Args:
            agent_name: Name of the agent to execute (mutually exclusive with workflow_name)
            workflow_name: Name of the workflow to execute (mutually exclusive with agent_name)
            data: Input data for the execution
            task: Task to execute (for agents only)
            context: Additional execution context
            environment: Environment to execute in (default: production)
            wait_for_completion: If True, wait for execution to complete
            poll_interval: How often to poll for completion (seconds)

        Returns:
            ExecutionResult containing execution details and results

        Raises:
            ValidationError: If both or neither agent_name/workflow_name are provided
            AuthenticationError: If API key is invalid
            NotFoundError: If agent/workflow is not found
            ExecutionError: If execution fails
        """
        # Validation
        if not agent_name and not workflow_name:
            raise ValidationError("Either agent_name or workflow_name must be specified")
        if agent_name and workflow_name:
            raise ValidationError("Cannot specify both agent_name and workflow_name")

        # Prepare request
        request_data = {
            "data": data or {},
            "task": task,
            "context": context or {},
            "environment": environment,
            "execution_source": "autonomous_sdk",
            "source_metadata": {
                "client_version": "1.0.0",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

        if agent_name:
            request_data["agent_name"] = agent_name
        else:
            request_data["workflow_name"] = workflow_name

        # Execute request
        response_data = await self._make_request("POST", "/autonomous/execute", request_data)
        result = ExecutionResult.from_dict(response_data)

        # Wait for completion if requested
        if wait_for_completion:
            result = await self._wait_for_completion(result.execution_id, poll_interval)

        return result

    async def status(self, execution_id: str) -> ExecutionResult:
        """
        Get the current status of an execution.

        Args:
            execution_id: ID of the execution to check

        Returns:
            ExecutionResult with current status and results

        Raises:
            NotFoundError: If execution is not found
            ExecutionError: If status check fails
        """
        response_data = await self._make_request("GET", f"/autonomous/executions/{execution_id}")
        return ExecutionResult.from_dict(response_data)

    async def cancel(self, execution_id: str) -> bool:
        """
        Cancel a running execution.

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if cancellation was successful

        Raises:
            NotFoundError: If execution is not found
            ExecutionError: If cancellation fails
        """
        try:
            await self._make_request("DELETE", f"/autonomous/executions/{execution_id}")
            return True
        except Exception as e:
            raise ExecutionError(f"Failed to cancel execution: {e}", execution_id=execution_id)

    async def list_executions(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        target_type: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[ExecutionResult]:
        """
        List recent autonomous executions.

        Args:
            limit: Maximum number of executions to return
            offset: Number of executions to skip
            status: Filter by status (queued, running, completed, failed, cancelled)
            target_type: Filter by target type (agent, workflow)
            environment: Filter by environment (production, staging)

        Returns:
            List of ExecutionResult objects

        Raises:
            ExecutionError: If listing fails
        """
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        if target_type:
            params['target_type'] = target_type
        if environment:
            params['environment'] = environment

        response_data = await self._make_request("GET", "/autonomous/executions", params=params)

        # Handle both list response and paginated response
        if isinstance(response_data, list):
            executions = response_data
        else:
            executions = response_data.get('executions', response_data.get('items', []))

        return [ExecutionResult.from_dict(item) for item in executions]



    # Internal helper methods

    async def _wait_for_completion(
        self,
        execution_id: str,
        poll_interval: float = 2.0,
        max_wait_time: int = 3600  # 1 hour max
    ) -> ExecutionResult:
        """Wait for execution to complete by polling status."""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            result = await self.status(execution_id)

            if result.is_complete:
                return result

            await asyncio.sleep(poll_interval)

        raise TimeoutError(
            f"Execution {execution_id} did not complete within {max_wait_time} seconds",
            timeout_seconds=max_wait_time
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling."""
        await self._ensure_session()

        url = f"{self.api_base}/api/v1{endpoint}"

        for attempt in range(self.max_retries):
            try:
                async with self._session.request(
                    method=method,
                    url=url,
                    json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                    params=params,
                ) as response:

                    # Handle different response status codes
                    if response.status == 200:
                        return await response.json()

                    elif response.status == 401:
                        raise AuthenticationError("Invalid API key or insufficient permissions")

                    elif response.status == 404:
                        error_data = await self._safe_json(response)
                        detail = error_data.get('detail', 'Resource not found')
                        raise NotFoundError(detail)

                    elif response.status == 400:
                        error_data = await self._safe_json(response)
                        detail = error_data.get('detail', 'Bad request')
                        raise ValidationError(detail)

                    elif response.status == 429:
                        # Rate limited - check for retry-after header
                        retry_after = response.headers.get('retry-after')
                        if retry_after:
                            await asyncio.sleep(int(retry_after))
                        else:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue

                    elif response.status >= 500:
                        error_data = await self._safe_json(response)
                        detail = error_data.get('detail', f'Server error (status: {response.status})')

                        # Retry on server errors
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        else:
                            raise ServerError(detail)

                    else:
                        # Other client errors - don't retry
                        error_data = await self._safe_json(response)
                        detail = error_data.get('detail', f'HTTP {response.status}')
                        raise ExecutionError(detail, status_code=response.status)

            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    raise ExecutionError(f"Network error: {e}")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise TimeoutError("Request timeout")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except (AuthenticationError, NotFoundError, ValidationError):
                # Don't retry authentication, not found, or validation errors
                raise

        raise ExecutionError("Max retries exceeded")

    async def _safe_json(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """Safely parse JSON response, returning empty dict if parsing fails."""
        try:
            return await response.json()
        except Exception:
            return {}

    # ===========================================
    # PRIMARY SYNC INTERFACE (Main Methods)
    # ===========================================

    def execute_agent(self, agent_name: str, data: Dict[str, Any] = None,
                     task: str = "process", context: Dict[str, Any] = None,
                     environment: str = "production", wait: bool = False) -> ExecutionResult:
        """
        Execute an agent synchronously.

        Args:
            agent_name: Name of the agent to execute
            data: Input data for the agent (default: {})
            task: Task for the agent to perform (default: "process")
            context: Additional execution context (default: {})
            environment: Environment to execute in (default: "production")
            wait: If True, wait for completion before returning (default: False)

        Returns:
            ExecutionResult containing execution details and agent output

        Raises:
            ValidationError: If agent_name is invalid
            ExecutionError: If execution fails
            TimeoutError: If wait=True and execution times out

        Example:
            # Simple execution
            result = client.execute_agent("my_agent")

            # Execute with data and wait for completion
            result = client.execute_agent(
                "data_processor",
                data={"csv_file": "data.csv"},
                wait=True
            )

            # Check result
            if result.is_success:
                print(f"Agent output: {result.result}")
        """
        return asyncio.run(self.execute_agent_async(
            agent_name=agent_name,
            data=data,
            task=task,
            context=context,
            environment=environment,
            wait=wait
        ))

    def execute_workflow(self, workflow_name: str, data: Dict[str, Any] = None,
                        context: Dict[str, Any] = None, environment: str = "production",
                        wait: bool = False) -> ExecutionResult:
        """
        Execute a workflow synchronously.

        Args:
            workflow_name: Name of the workflow to execute
            data: Input data for the workflow (default: {})
            context: Additional execution context (default: {})
            environment: Environment to execute in (default: "production")
            wait: If True, wait for completion before returning (default: False)

        Returns:
            ExecutionResult containing execution details and workflow output

        Example:
            result = client.execute_workflow("data_pipeline", data={"source": "s3"})
        """
        return asyncio.run(self.execute_workflow_async(
            workflow_name=workflow_name,
            data=data,
            context=context,
            environment=environment,
            wait=wait
        ))

    def execute_and_wait(self, agent_name: str = None, workflow_name: str = None,
                        data: Dict[str, Any] = None, timeout: int = 300, **kwargs) -> ExecutionResult:
        """
        Execute and wait for completion synchronously.

        Args:
            agent_name: Name of the agent to execute (mutually exclusive with workflow_name)
            workflow_name: Name of the workflow to execute (mutually exclusive with agent_name)
            data: Input data for execution
            timeout: Maximum time to wait in seconds (default: 300)
            **kwargs: Additional arguments passed to execution

        Returns:
            ExecutionResult with completed execution results

        Example:
            result = client.execute_and_wait("my_agent", data={"input": "test"})
        """
        return asyncio.run(self.execute_and_wait_async(
            agent_name=agent_name,
            workflow_name=workflow_name,
            data=data,
            timeout=timeout,
            **kwargs
        ))

    def get_execution(self, execution_id: str) -> ExecutionResult:
        """
        Get current execution status and results.

        Args:
            execution_id: ID of the execution to check

        Returns:
            ExecutionResult with current status and results

        Example:
            result = client.get_execution("exec_123")
            print(f"Status: {result.status}")
        """
        return asyncio.run(self.get_execution_async(execution_id))

    def wait_for_execution(self, execution_id: str, timeout: int = 300,
                          poll_interval: float = 2.0) -> ExecutionResult:
        """
        Wait for execution to complete.

        Args:
            execution_id: ID of the execution to wait for
            timeout: Maximum time to wait in seconds (default: 300)
            poll_interval: How often to poll for completion in seconds (default: 2.0)

        Returns:
            ExecutionResult with completed execution results

        Example:
            result = client.wait_for_execution("exec_123", timeout=60)
        """
        return asyncio.run(self.wait_for_execution_async(
            execution_id=execution_id,
            timeout=timeout,
            poll_interval=poll_interval
        ))

    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a running execution.

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if cancellation was successful

        Example:
            success = client.cancel_execution("exec_123")
        """
        return asyncio.run(self.cancel_execution_async(execution_id))

    def list_executions(self, limit: int = 50, offset: int = 0,
                       status: str = None, target_type: str = None,
                       environment: str = None) -> List[ExecutionResult]:
        """
        List recent executions with filtering.

        Args:
            limit: Maximum number of executions to return (default: 50)
            offset: Number of executions to skip (default: 0)
            status: Filter by status (queued, running, completed, failed, cancelled)
            target_type: Filter by target type (agent, workflow)
            environment: Filter by environment (production, staging)

        Returns:
            List of ExecutionResult objects

        Example:
            executions = client.list_executions(limit=10, status="completed")
        """
        # Call the original async method directly
        async def _list():
            params = {'limit': limit, 'offset': offset}
            if status:
                params['status'] = status
            if target_type:
                params['target_type'] = target_type
            if environment:
                params['environment'] = environment

            response_data = await self._make_request("GET", "/autonomous/executions", params=params)

            # Handle both list response and paginated response
            if isinstance(response_data, list):
                executions = response_data
            else:
                executions = response_data.get('executions', response_data.get('items', []))

            return [ExecutionResult.from_dict(item) for item in executions]

        return asyncio.run(_list())

    def get_latest_execution(self, agent_name: str = None, workflow_name: str = None,
                           environment: str = "production") -> Optional[ExecutionResult]:
        """
        Get the most recent execution for an agent or workflow.

        Args:
            agent_name: Name of the agent (mutually exclusive with workflow_name)
            workflow_name: Name of the workflow (mutually exclusive with agent_name)
            environment: Environment to filter by (default: "production")

        Returns:
            ExecutionResult with the latest execution, or None if no executions found

        Example:
            latest = client.get_latest_execution(agent_name="my_agent")
            if latest:
                print(f"Latest result: {latest.result}")
        """
        # Call the original async method directly
        async def _get_latest():
            # Validation
            if not agent_name and not workflow_name:
                raise ValidationError("Either agent_name or workflow_name must be specified")
            if agent_name and workflow_name:
                raise ValidationError("Cannot specify both agent_name and workflow_name")

            # Get recent executions for the target
            target_type = "agent" if agent_name else "workflow"

            # Use the original async list_executions method
            params = {'limit': 10, 'target_type': target_type, 'environment': environment}
            response_data = await self._make_request("GET", "/autonomous/executions", params=params)

            # Handle both list response and paginated response
            if isinstance(response_data, list):
                executions_data = response_data
            else:
                executions_data = response_data.get('executions', response_data.get('items', []))

            executions = [ExecutionResult.from_dict(item) for item in executions_data]

            # Filter by specific agent/workflow name if needed
            target_name = agent_name or workflow_name
            for execution in executions:
                if execution.target_name == target_name:
                    return execution

            return None

        return asyncio.run(_get_latest())

    # ===========================================
    # ASYNC VERSIONS (For Advanced Users)
    # ===========================================

    async def execute_agent_async(self, agent_name: str, data: Dict[str, Any] = None,
                                 task: str = "process", context: Dict[str, Any] = None,
                                 environment: str = "production", wait: bool = False) -> ExecutionResult:
        """Execute an agent asynchronously."""
        return await self.run(
            agent_name=agent_name,
            data=data,
            task=task,
            context=context,
            environment=environment,
            wait_for_completion=wait
        )

    async def execute_workflow_async(self, workflow_name: str, data: Dict[str, Any] = None,
                                    context: Dict[str, Any] = None, environment: str = "production",
                                    wait: bool = False) -> ExecutionResult:
        """Execute a workflow asynchronously."""
        return await self.run(
            workflow_name=workflow_name,
            data=data,
            context=context,
            environment=environment,
            wait_for_completion=wait
        )

    async def execute_and_wait_async(self, agent_name: str = None, workflow_name: str = None,
                                    data: Dict[str, Any] = None, timeout: int = 300, **kwargs) -> ExecutionResult:
        """Execute and wait for completion asynchronously."""
        return await self.run(
            agent_name=agent_name,
            workflow_name=workflow_name,
            data=data,
            wait_for_completion=True,
            **kwargs
        )

    async def get_execution_async(self, execution_id: str) -> ExecutionResult:
        """Get execution status asynchronously."""
        return await self.status(execution_id)

    async def wait_for_execution_async(self, execution_id: str, timeout: int = 300,
                                      poll_interval: float = 2.0) -> ExecutionResult:
        """Wait for execution completion asynchronously."""
        return await self._wait_for_completion(execution_id, poll_interval, timeout)

    async def cancel_execution_async(self, execution_id: str) -> bool:
        """Cancel execution asynchronously."""
        return await self.cancel(execution_id)

    async def list_executions_async(self, limit: int = 50, offset: int = 0,
                                   status: str = None, target_type: str = None,
                                   environment: str = None) -> List[ExecutionResult]:
        """List executions asynchronously."""
        # Use the original async method
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        if target_type:
            params['target_type'] = target_type
        if environment:
            params['environment'] = environment

        response_data = await self._make_request("GET", "/autonomous/executions", params=params)

        # Handle both list response and paginated response
        if isinstance(response_data, list):
            executions = response_data
        else:
            executions = response_data.get('executions', response_data.get('items', []))

        return [ExecutionResult.from_dict(item) for item in executions]

    async def get_latest_execution_async(self, agent_name: str = None, workflow_name: str = None,
                                        environment: str = "production") -> Optional[ExecutionResult]:
        """Get latest execution asynchronously."""
        # Validation
        if not agent_name and not workflow_name:
            raise ValidationError("Either agent_name or workflow_name must be specified")
        if agent_name and workflow_name:
            raise ValidationError("Cannot specify both agent_name and workflow_name")

        # Get recent executions for the target
        target_type = "agent" if agent_name else "workflow"
        executions = await self.list_executions_async(
            limit=10,  # Get more to filter by name
            target_type=target_type,
            environment=environment
        )

        # Filter by specific agent/workflow name if needed
        target_name = agent_name or workflow_name
        for execution in executions:
            if execution.target_name == target_name:
                return execution

        return None

    # Cleanup
    def close(self):
        """Close the HTTP session (for sync usage)."""
        if self._session and not self._session.closed:
            asyncio.run(self._session.close())

    def __del__(self):
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass  # Ignore cleanup errors


# ===========================================
# CONVENIENCE FUNCTIONS (One-off executions)
# ===========================================

async def execute_agent(
    api_key: str,
    agent_name: str,
    data: Dict[str, Any] = None,
    **kwargs
) -> ExecutionResult:
    """
    Execute an agent with a one-off client (async).

    Args:
        api_key: DAITA API key
        agent_name: Name of the agent to execute
        data: Input data for the execution
        **kwargs: Additional arguments passed to execute_agent_async()

    Returns:
        ExecutionResult containing execution details
    """
    async with DaitaClient(api_key) as client:
        return await client.execute_agent_async(agent_name, data, **kwargs)


async def execute_workflow(
    api_key: str,
    workflow_name: str,
    data: Dict[str, Any] = None,
    **kwargs
) -> ExecutionResult:
    """
    Execute a workflow with a one-off client (async).

    Args:
        api_key: DAITA API key
        workflow_name: Name of the workflow to execute
        data: Input data for the execution
        **kwargs: Additional arguments passed to execute_workflow_async()

    Returns:
        ExecutionResult containing execution details
    """
    async with DaitaClient(api_key) as client:
        return await client.execute_workflow_async(workflow_name, data, **kwargs)


# Synchronous convenience functions (primary interface)

def execute_agent_standalone(
    api_key: str,
    agent_name: str,
    data: Dict[str, Any] = None,
    **kwargs
) -> ExecutionResult:
    """
    Execute an agent with a one-off client.

    Args:
        api_key: DAITA API key
        agent_name: Name of the agent to execute
        data: Input data for the execution
        **kwargs: Additional arguments

    Returns:
        ExecutionResult containing execution details

    Example:
        result = execute_agent_standalone("sk-123", "my_agent", data={"input": "test"})
    """
    return asyncio.run(execute_agent(api_key, agent_name, data, **kwargs))


def execute_workflow_standalone(
    api_key: str,
    workflow_name: str,
    data: Dict[str, Any] = None,
    **kwargs
) -> ExecutionResult:
    """
    Execute a workflow with a one-off client.

    Args:
        api_key: DAITA API key
        workflow_name: Name of the workflow to execute
        data: Input data for the execution
        **kwargs: Additional arguments

    Returns:
        ExecutionResult containing execution details

    Example:
        result = execute_workflow_standalone("sk-123", "data_pipeline", data={"source": "s3"})
    """
    return asyncio.run(execute_workflow(api_key, workflow_name, data, **kwargs))
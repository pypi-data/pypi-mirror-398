"""
Remote execution command for running agents and workflows in the cloud.

This allows users to execute their deployed agents/workflows remotely
from the command line, with real-time status updates and result streaming.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import aiohttp
import click
import yaml
from ..utils import find_project_root

async def run_remote_execution(
    target_name: str,
    target_type: str = "agent",
    environment: str = "production",
    data_file: Optional[str] = None,
    data_json: Optional[str] = None,
    task: str = "process",
    follow: bool = False,
    timeout: int = 300,
    verbose: bool = False
):
    """
    Execute an agent or workflow remotely in the cloud.
    
    Args:
        target_name: Name of the agent or workflow to execute
        target_type: "agent" or "workflow"
        environment: Environment to execute in (production, staging)
        data_file: Path to JSON file containing input data
        data_json: JSON string containing input data
        task: Task to execute (for agents only)
        follow: Whether to follow execution progress
        timeout: Execution timeout in seconds
        verbose: Enable verbose output
    """

    # Load environment variables from .env file if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional

    # Get API credentials
    api_key = os.getenv('DAITA_API_KEY')
    api_base = os.getenv('DAITA_API_BASE') or os.getenv('DAITA_API_ENDPOINT') or 'https://ondk4sdyv0.execute-api.us-east-1.amazonaws.com'

    if not api_key:
        click.echo(" DAITA_API_KEY not found", err=True)
        click.echo("   Get your API key from daita-tech.io", err=True)
        click.echo("   Set it with: export DAITA_API_KEY='your-key-here'", err=True)
        click.echo("   Or add it to your project's .env file", err=True)
        return False
    
    # Prepare input data
    input_data = {}
    if data_file:
        try:
            with open(data_file, 'r') as f:
                input_data = json.load(f)
            if verbose:
                click.echo(f" Loaded data from {data_file}")
        except Exception as e:
            click.echo(f" Failed to load data file: {e}", err=True)
            return False
    elif data_json:
        try:
            input_data = json.loads(data_json)
        except Exception as e:
            click.echo(f" Invalid JSON data: {e}", err=True)
            return False
    
    # Prepare execution request
    request_data = {
        "data": input_data,
        "environment": environment,
        "timeout_seconds": timeout,
        "execution_source": "cli",
        "source_metadata": {
            "cli_version": "1.0.0",
            "command": f"daita run {target_name}",
            "working_directory": str(Path.cwd())
        }
    }
    
    # Validate agent exists and get file name for execution
    if verbose:
        click.echo(f" Looking up agent '{target_name}'...")
    
    agent_info = validate_agent_exists(target_name, target_type)
    if not agent_info:
        return False
    
    file_name = agent_info['file_name']
    display_name = agent_info.get('display_name', file_name)
    
    if verbose:
        click.echo(f" Found agent: {file_name} → '{display_name}'")
        click.echo(f" Executing with file name: '{file_name}'")
    
    # Add target-specific fields using file name (API/Lambda expects this)
    if target_type == "agent":
        request_data["agent_name"] = file_name
        request_data["task"] = task
    else:
        request_data["workflow_name"] = file_name
    
    if verbose:
        click.echo(f" Executing {target_type} '{target_name}' in {environment}")
        if input_data:
            click.echo(f" Input data: {len(str(input_data))} characters")
    
    # Execute the request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Daita-CLI/1.0.0'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Submit execution request
            async with session.post(
                f"{api_base}/api/v1/executions/execute",
                headers=headers,
                json=request_data
            ) as response:
                
                if response.status != 200:
                    error_data = await response.json()
                    error_detail = error_data.get('detail', 'Unknown error')
                    click.echo(f" Execution failed: {error_detail}", err=True)
                    
                    # Provide helpful guidance based on error type
                    if response.status == 404 and "No deployment found" in error_detail:
                        click.echo(f" Possible causes:", err=True)
                        click.echo(f"   • Agent not deployed: daita push {environment}", err=True)
                        click.echo(f"   • Wrong agent name (using: '{file_name}')", err=True)
                        click.echo(f"   • Check deployed agents: daita status", err=True)
                    
                    return False
                
                result = await response.json()
                execution_id = result['execution_id']
                
                if verbose:
                    click.echo(f" Execution ID: {execution_id}")
                
                # All executions are now asynchronous
                if follow:
                    # Show progress while following
                    return await _follow_execution(session, api_base, headers, execution_id, verbose)
                else:
                    # Poll once for immediate result, then return
                    return await _poll_for_result(session, api_base, headers, execution_id, verbose)
                
    except aiohttp.ClientError as e:
        click.echo(f" Network error: {e}", err=True)
        return False
    except Exception as e:
        click.echo(f" Unexpected error: {e}", err=True)
        return False

async def _follow_execution(
    session: aiohttp.ClientSession,
    api_base: str,
    headers: Dict[str, str],
    execution_id: str,
    verbose: bool
) -> bool:
    """Follow an asynchronous execution until completion."""
    
    click.echo(" Following execution progress...")
    
    last_status = None
    start_time = time.time()
    
    try:
        while True:
            # Check execution status
            async with session.get(
                f"{api_base}/api/v1/executions/{execution_id}",
                headers=headers
            ) as response:
                
                if response.status != 200:
                    click.echo(" Failed to get execution status", err=True)
                    return False
                
                result = await response.json()
                status = result['status']
                
                # Display status changes
                if status != last_status:
                    elapsed = int(time.time() - start_time)
                    
                    if status == 'running':
                        click.echo(f" Execution started (after {elapsed}s)")
                    elif status in ['completed', 'success']:  # Handle both status values
                        click.echo(f" Execution completed (after {elapsed}s)")
                        _display_result(result, verbose)
                        return True
                    elif status in ['failed', 'error']:  # Handle both status values
                        click.echo(f" Execution failed (after {elapsed}s)")
                        if result.get('error'):
                            click.echo(f"   Error: {result['error']}")
                        return False
                    elif status == 'cancelled':
                        click.echo(f" Execution cancelled (after {elapsed}s)")
                        return False
                    
                    last_status = status
                
                # Break if execution is complete
                if status in ['completed', 'success', 'failed', 'error', 'cancelled']:
                    break
                
                # Wait before next check
                await asyncio.sleep(2)
                
    except KeyboardInterrupt:
        click.echo("\n Stopped following execution (execution continues in background)")
        click.echo(f"   Check status with: daita logs --execution-id {execution_id}")
        return False

async def _poll_for_result(
    session: aiohttp.ClientSession,
    api_base: str,
    headers: Dict[str, str],
    execution_id: str,
    verbose: bool
) -> bool:
    """Poll for execution result without showing progress (for non-follow mode)."""

    max_polls = 360  # 3 minutes max wait (0.5s intervals)
    polls = 0

    while polls < max_polls:
        try:
            # Check execution status
            async with session.get(
                f"{api_base}/api/v1/executions/{execution_id}",
                headers=headers
            ) as response:

                if response.status != 200:
                    click.echo(" Failed to get execution status", err=True)
                    return False

                result = await response.json()
                status = result['status']

                # Return result if complete
                if status in ['completed', 'success']:  # Handle both status values
                    click.echo("\n" + "=" * 60)
                    click.echo(" EXECUTION COMPLETED")
                    click.echo("=" * 60)
                    _display_result(result, verbose)
                    return True
                elif status in ['failed', 'error']:  # Handle both status values
                    click.echo("\n" + "=" * 60)
                    click.echo(" EXECUTION FAILED")
                    click.echo("=" * 60)
                    if result.get('error'):
                        click.echo(f"\nError: {result['error']}")
                    return False
                elif status == 'cancelled':
                    click.echo(" Execution cancelled")
                    return False

                # Continue polling
                await asyncio.sleep(0.5)
                polls += 1

        except Exception as e:
            click.echo(f" Error polling execution: {e}", err=True)
            return False

    # Timeout reached
    click.echo(" Execution still running (timeout reached)")
    click.echo(f"   Check status with: daita execution-logs {execution_id}")
    click.echo(f"   Follow progress with: daita execution-logs {execution_id} --follow")
    return False

def _display_result(result: Dict[str, Any], verbose: bool):
    """Display execution results in a formatted way."""

    # Display execution metadata
    click.echo("\nExecution Metadata:")
    click.echo("-" * 60)

    if result.get('duration_ms'):
        duration = float(result['duration_ms'])  # Convert string to number
        if duration < 1000:
            click.echo(f"  Duration:    {duration:.0f}ms")
        elif duration < 60000:
            click.echo(f"  Duration:    {duration/1000:.1f}s")
        else:
            click.echo(f"  Duration:    {duration/60000:.1f}m")

    if result.get('memory_used_mb'):
        click.echo(f"  Memory:      {result['memory_used_mb']:.1f}MB")

    # Display result data
    if result.get('result'):
        click.echo("\n" + "-" * 60)
        click.echo("Result:")
        click.echo("-" * 60)

        if verbose:
            # Pretty print full result with indentation
            result_json = json.dumps(result['result'], indent=2)
            for line in result_json.split('\n'):
                click.echo(f"  {line}")
        else:
            # Display summary
            result_data = result['result']

            if isinstance(result_data, dict):
                # Show key fields if present
                if 'status' in result_data:
                    click.echo(f"  Status:      {result_data['status']}")
                if 'message' in result_data:
                    # Word wrap long messages
                    message = result_data['message']
                    if len(message) > 70:
                        click.echo(f"  Message:     {message[:70]}...")
                    else:
                        click.echo(f"  Message:     {message}")

                # Show presence of complex data types
                data_types = []
                if 'insights' in result_data:
                    data_types.append('insights')
                if 'recommendations' in result_data:
                    data_types.append('recommendations')
                if 'data' in result_data:
                    data_types.append('data')
                if 'results' in result_data:
                    data_types.append('results')

                if data_types:
                    click.echo(f"  Contains:    {', '.join(data_types)}")

                # Show all keys for reference
                all_keys = list(result_data.keys())
                if len(all_keys) > 0:
                    keys_display = ', '.join(all_keys[:8])
                    if len(all_keys) > 8:
                        keys_display += f" (+{len(all_keys) - 8} more)"
                    click.echo(f"  Keys:        {keys_display}")

                click.echo("\n  Tip: Use --verbose or -v flag to see full result")

            elif isinstance(result_data, str):
                # String result - show first part
                if len(result_data) > 200:
                    click.echo(f"  {result_data[:200]}...")
                    click.echo(f"\n  (Result truncated - use -v for full output)")
                else:
                    click.echo(f"  {result_data}")
            else:
                # Other types
                click.echo(f"  {result_data}")

    click.echo("=" * 60 + "\n")

async def list_remote_executions(
    limit: int = 10,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
    environment: Optional[str] = None,
    verbose: bool = False
):
    """List recent executions with filtering."""
    
    api_key = os.getenv('DAITA_API_KEY')
    api_base = os.getenv('DAITA_API_BASE') or os.getenv('DAITA_API_ENDPOINT') or 'https://ondk4sdyv0.execute-api.us-east-1.amazonaws.com'
    
    if not api_key:
        click.echo(" DAITA_API_KEY not found", err=True)
        return False
    
    # Build query parameters
    params = {'limit': limit}
    if status:
        params['status'] = status
    if target_type:
        params['target_type'] = target_type
    if environment:
        params['environment'] = environment
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Daita-CLI/1.0.0'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{api_base}/api/v1/executions",
                headers=headers,
                params=params
            ) as response:
                
                if response.status != 200:
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get('detail', 'Unknown error')
                    except:
                        error_msg = await response.text()
                    click.echo(f" Failed to list executions: {error_msg}", err=True)
                    if verbose:
                        click.echo(f"   Status code: {response.status}", err=True)
                    return False
                
                executions = await response.json()
                
                if not executions:
                    click.echo(" No executions found")
                    return True

                # Display executions header
                click.echo(f"\n Recent Executions ({len(executions)})")
                click.echo(" " + "=" * 70)
                click.echo(f" {'Status':<10} {'Agent/Workflow':<25} {'Time & Duration'}")
                click.echo(" " + "-" * 70)

                for execution in executions:
                    # Map status to friendly text labels
                    status_label = {
                        'completed': 'success',
                        'success': 'success',
                        'failed': 'error',
                        'error': 'error',
                        'running': 'running',
                        'queued': 'queued',
                        'cancelled': 'cancelled',
                        'started': 'running'
                    }.get(execution['status'], execution['status'])

                    # Format time
                    created_at = execution['created_at']
                    if 'T' in created_at:
                        time_str = created_at.split('T')[1].split('.')[0]
                    else:
                        time_str = created_at

                    # Format duration
                    duration_str = "N/A"
                    if execution.get('duration_ms'):
                        ms = execution['duration_ms']
                        if ms < 1000:
                            duration_str = f"{ms}ms"
                        elif ms < 60000:
                            duration_str = f"{ms/1000:.1f}s"
                        else:
                            duration_str = f"{ms/60000:.1f}m"

                    # Format agent/workflow name with type
                    target_info = f"{execution['target_name']} ({execution['target_type']})"

                    # Format time and duration info
                    time_duration = f"{time_str} ({duration_str})"

                    # Display execution line
                    click.echo(f" {status_label:<10} {target_info:<25} {time_duration}")

                    # Show full execution ID on next line (indented)
                    click.echo(f" {'':>10} ID: {execution['execution_id']}")

                    if verbose and execution.get('error'):
                        click.echo(f" {'':>10} Error: {execution['error']}")

                    click.echo()  # Blank line between executions
                
                return True

    except Exception as e:
        click.echo(f" Failed to list executions: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        return False

async def get_execution_logs(
    execution_id: str,
    follow: bool = False,
    verbose: bool = False
):
    """Get logs for a specific execution."""
    
    api_key = os.getenv('DAITA_API_KEY')
    api_base = os.getenv('DAITA_API_BASE') or os.getenv('DAITA_API_ENDPOINT') or 'https://ondk4sdyv0.execute-api.us-east-1.amazonaws.com'
    
    if not api_key:
        click.echo(" DAITA_API_KEY not found", err=True)
        return False
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Daita-CLI/1.0.0'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            if follow:
                # Follow mode - continuously check status
                await _follow_execution(session, api_base, headers, execution_id, verbose)
            else:
                # One-time status check
                async with session.get(
                    f"{api_base}/api/v1/executions/{execution_id}",
                    headers=headers
                ) as response:
                    
                    if response.status == 404:
                        click.echo(" Execution not found", err=True)
                        return False
                    elif response.status != 200:
                        error_data = await response.json()
                        click.echo(f" Failed to get execution: {error_data.get('detail', 'Unknown error')}", err=True)
                        return False
                    
                    result = await response.json()
                    
                    # Display execution info
                    click.echo(f" Execution: {result['execution_id']}")
                    click.echo(f" Target: {result['target_name']} ({result['target_type']})")
                    click.echo(f" Environment: {result['environment']}")
                    click.echo(f" Status: {result['status']}")
                    
                    if result.get('created_at'):
                        click.echo(f" Created: {result['created_at']}")
                    
                    _display_result(result, verbose)
                    
                    return True
                    
    except Exception as e:
        click.echo(f" Error: {e}", err=True)
        return False


async def _resolve_agent_id(agent_name: str, environment: str, api_key: str, api_base: str) -> Optional[str]:
    """
    Resolve agent name to deployed agent ID.
    
    This function queries the deployments API to find the actual agent ID
    that corresponds to the simple agent name provided by the user.
    
    Args:
        agent_name: Simple agent name (e.g., "sentiment_analyzer")
        environment: Target environment (e.g., "staging", "production")
        api_key: DAITA API key for authentication
        api_base: API base URL
        
    Returns:
        Agent ID if found, None otherwise
    """
    try:
        # Get current project name to filter deployments
        project_root = find_project_root()
        project_name = None
        if project_root:
            try:
                import yaml
                config_file = project_root / 'daita-project.yaml'
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        project_name = config.get('name')
            except:
                pass
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Daita-CLI/1.0.0'
        }
        
        async with aiohttp.ClientSession() as session:
            # Query deployments API to find matching agent
            url = f"{api_base}/api/v1/deployments"
            params = {
                'environment': environment,
                'status': 'active'
            }
            
            # Add project filter if available
            if project_name:
                params['project_name'] = project_name
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    deployments = await response.json()
                    
                    # Debug logging
                    click.echo(f" DEBUG: Found {len(deployments)} deployments for project '{project_name}' in {environment}", err=True)
                    
                    # Search through deployments for matching agent
                    for deployment in deployments:
                        agents_config = deployment.get('agents_config', [])
                        for agent_config in agents_config:
                            # Extract agent file name from agent_id 
                            # Format: {org_id}_{project_name}_{agent_file_name}
                            agent_id = agent_config.get('agent_id', '')
                            agent_file_name = ''
                            
                            if agent_id and project_name:
                                # Try to extract agent name by removing org_id and project_name prefix
                                # Expected format: "1_{project_name}_{agent_name}" where project_name may contain hyphens
                                # Strategy: look for pattern that starts with "1_{project_name}_"
                                prefix = f"1_{project_name}_"
                                if agent_id.startswith(prefix):
                                    # Extract everything after the prefix
                                    agent_file_name = agent_id[len(prefix):]
                            
                            # Match by multiple criteria:
                            display_name = agent_config.get('agent_name', '')
                            
                            if (agent_name == agent_file_name or
                                agent_name == display_name or
                                agent_name.replace('_', ' ').title() == display_name or
                                agent_name.replace('_', '').lower() == display_name.replace(' ', '').lower()):
                                return agent_config.get('agent_id')
                    
                    return None
                else:
                    # If API call fails, return None to let execution try with original name
                    click.echo(f" DEBUG: Deployments API returned status {response.status}", err=True)
                    return None
                    
    except Exception:
        # If resolution fails, return None to let execution try with original name
        return None


def validate_agent_exists(target_name: str, target_type: str = "agent") -> Optional[dict]:
    """
    Validate agent exists and return file name and display name.
    
    Args:
        target_name: Name of the agent/workflow (file name or display name)
        target_type: "agent" or "workflow"
        
    Returns:
        Dict with 'file_name' and 'display_name' if found, None otherwise
    """
    project_root = find_project_root()
    if not project_root:
        click.echo(" No daita-project.yaml found")
        click.echo(" Run 'daita init' to create a project")
        return None
    
    config_file = project_root / 'daita-project.yaml'
    if not config_file.exists():
        click.echo(" No daita-project.yaml found")
        click.echo(" Run 'daita init' to create a project")
        return None
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        click.echo(f" Failed to read daita-project.yaml: {e}")
        return None
    
    if not config:
        click.echo(" Invalid daita-project.yaml file")
        return None
    
    # Get the appropriate component list
    component_key = 'agents' if target_type == 'agent' else 'workflows'
    components = config.get(component_key, [])
    
    # Find the component by name OR display_name
    component = next((c for c in components if c.get('name') == target_name), None)
    
    # If not found by name, try finding by display_name
    if not component:
        component = next((c for c in components if c.get('display_name') == target_name), None)
    
    if not component:
        available_names = [c.get('name', 'unknown') for c in components]
        click.echo(f" {target_type.title()} '{target_name}' not found in project")
        if available_names:
            click.echo(f" Available {component_key} (use file names): {', '.join(available_names)}")
        else:
            click.echo(f" No {component_key} found. Create one with: daita create {target_type}")
        click.echo(" Use file names for execution (e.g., 'my_agent' not 'My Agent')")
        return None
    
    file_name = component.get('name')
    display_name = component.get('display_name')
    
    if not file_name:
        click.echo(f" {target_type.title()} missing name in config")
        return None
    
    return {
        'file_name': file_name,
        'display_name': display_name or file_name
    }
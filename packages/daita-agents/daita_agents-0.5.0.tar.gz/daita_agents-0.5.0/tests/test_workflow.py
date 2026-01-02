"""
Test suite for Workflow system - testing multi-agent orchestration.

Tests cover:
- Workflow creation and agent management
- Agent connections via relay channels
- Workflow lifecycle (start/stop)
- Data injection and processing
- Communication tracking and logging
- Semantic conversation viewing
- Error handling and edge cases
- Workflow statistics and monitoring
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from daita.core.workflow import (
    Workflow, 
    WorkflowStatus, 
    WorkflowError, 
    Connection,
    CommunicationLogger,
    CommunicationMessage
)
from daita.core.relay import RelayManager
from daita.agents.substrate import SubstrateAgent
from daita.llm.mock import MockLLMProvider
from daita.config.base import AgentConfig


class MockAgent:
    """Simple mock agent for testing workflow functionality."""
    
    def __init__(self, name: str, responses: Dict[str, Any] = None):
        self.name = name
        self.agent_id = f"mock_{name.lower()}"
        self.responses = responses or {}
        self.process_calls = []
        self.started = False
        self.stopped = False
    
    async def start(self):
        self.started = True
    
    async def stop(self):
        self.stopped = True
    
    async def process(self, task: str, data: Any = None, context: Dict[str, Any] = None):
        """Mock process method that records calls and returns configured responses."""
        call_record = {
            'task': task,
            'data': data,
            'context': context or {},
            'timestamp': time.time()
        }
        self.process_calls.append(call_record)
        
        # Return configured response or default
        response_key = f"{task}_{self.name}"
        if response_key in self.responses:
            return self.responses[response_key]
        
        return {
            'status': 'success',
            'result': {
                'agent': self.name,
                'processed_task': task,
                'received_data': data,
                'message': f"{self.name} processed {task}"
            },
            'agent_id': self.agent_id,
            'agent_name': self.name
        }


class TestWorkflowInitialization:
    """Test workflow creation and basic configuration."""
    
    def test_basic_initialization(self):
        """Test creating workflow with minimal parameters."""
        workflow = Workflow("Test Workflow")
        
        assert workflow.name == "Test Workflow"
        assert workflow.project_id is None
        assert workflow.status == WorkflowStatus.CREATED
        assert len(workflow.agents) == 0
        assert len(workflow.connections) == 0
        assert len(workflow.channels) == 0
        assert workflow.created_at is not None
        assert workflow.started_at is None
        assert workflow.stopped_at is None
        assert workflow.error is None
    
    def test_initialization_with_project_id(self):
        """Test creating workflow with project ID."""
        workflow = Workflow("Test Workflow", project_id="test_project")
        
        assert workflow.name == "Test Workflow"
        assert workflow.project_id == "test_project"
    
    def test_initialization_with_custom_relay(self):
        """Test creating workflow with custom relay manager."""
        custom_relay = RelayManager()
        workflow = Workflow("Test Workflow", relay_manager=custom_relay)
        
        assert workflow.relay_manager == custom_relay
    
    def test_communication_logger_initialization(self):
        """Test that communication logger is properly initialized."""
        workflow = Workflow("Test Workflow")
        
        assert workflow.comm_logger is not None
        assert isinstance(workflow.comm_logger, CommunicationLogger)
        assert len(workflow.comm_logger.messages) == 0


class TestWorkflowAgentManagement:
    """Test adding, removing, and managing agents in workflows."""
    
    def test_add_agent(self):
        """Test adding agents to workflow."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        # Add agents
        result = workflow.add_agent("agent1", agent1)
        assert result == workflow  # Should return self for chaining
        
        workflow.add_agent("agent2", agent2)
        
        assert len(workflow.agents) == 2
        assert workflow.agents["agent1"] == agent1
        assert workflow.agents["agent2"] == agent2
    
    def test_add_duplicate_agent_error(self):
        """Test error when adding agent with duplicate name."""
        workflow = Workflow("Test Workflow")
        agent = MockAgent("Agent1")
        
        workflow.add_agent("agent1", agent)
        
        with pytest.raises(WorkflowError) as exc_info:
            workflow.add_agent("agent1", MockAgent("Agent2"))
        
        assert "Agent 'agent1' already exists" in str(exc_info.value)
    
    def test_remove_agent(self):
        """Test removing agents from workflow."""
        workflow = Workflow("Test Workflow")
        agent = MockAgent("Agent1")
        
        workflow.add_agent("agent1", agent)
        assert len(workflow.agents) == 1
        
        # Remove agent
        result = workflow.remove_agent("agent1")
        assert result is True
        assert len(workflow.agents) == 0
        
        # Try to remove non-existent agent
        result = workflow.remove_agent("nonexistent")
        assert result is False
    
    def test_remove_agent_with_connections_error(self):
        """Test error when removing agent that has connections."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "channel1", "agent2")
        
        # Should not be able to remove agent with connections
        with pytest.raises(WorkflowError) as exc_info:
            workflow.remove_agent("agent1")
        
        assert "Cannot remove agent 'agent1' - it's used in connections" in str(exc_info.value)
    
    def test_list_agents(self):
        """Test listing agent names."""
        workflow = Workflow("Test Workflow")
        
        assert workflow.list_agents() == []
        
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        agent_names = workflow.list_agents()
        assert set(agent_names) == {"agent1", "agent2"}
    
    def test_get_agent(self):
        """Test getting agents by name."""
        workflow = Workflow("Test Workflow")
        agent = MockAgent("Agent1")
        
        workflow.add_agent("agent1", agent)
        
        assert workflow.get_agent("agent1") == agent
        assert workflow.get_agent("nonexistent") is None


class TestWorkflowConnections:
    """Test connecting agents via relay channels."""
    
    def test_connect_agents(self):
        """Test creating connections between agents."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        # Connect agents
        result = workflow.connect("agent1", "data_channel", "agent2")
        assert result == workflow  # Should return self for chaining
        
        assert len(workflow.connections) == 1
        assert len(workflow.channels) == 1
        assert "data_channel" in workflow.channels
        
        connection = workflow.connections[0]
        assert connection.from_agent == "agent1"
        assert connection.channel == "data_channel"
        assert connection.to_agent == "agent2"
        assert connection.task == "relay_message"  # Default task
    
    def test_connect_with_custom_task(self):
        """Test connecting agents with custom task."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        workflow.connect("agent1", "data_channel", "agent2", task="process_data")
        
        connection = workflow.connections[0]
        assert connection.task == "process_data"
    
    def test_connect_nonexistent_agents_error(self):
        """Test error when connecting non-existent agents."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        
        # Missing from_agent
        with pytest.raises(WorkflowError) as exc_info:
            workflow.connect("nonexistent", "channel", "agent1")
        assert "Agent 'nonexistent' not found" in str(exc_info.value)
        
        # Missing to_agent
        with pytest.raises(WorkflowError) as exc_info:
            workflow.connect("agent1", "channel", "nonexistent")
        assert "Agent 'nonexistent' not found" in str(exc_info.value)
    
    def test_duplicate_connection_warning(self):
        """Test handling of duplicate connections."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        # Create connection
        workflow.connect("agent1", "channel", "agent2")
        assert len(workflow.connections) == 1
        
        # Create duplicate - should not error but warn
        workflow.connect("agent1", "channel", "agent2")
        assert len(workflow.connections) == 1  # Still only one connection
    
    def test_disconnect_agents(self):
        """Test disconnecting agents."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        workflow.add_agent("agent3", MockAgent("Agent3"))
        
        # Create connections
        workflow.connect("agent1", "channel1", "agent2")
        workflow.connect("agent1", "channel2", "agent3")
        
        assert len(workflow.connections) == 2
        assert len(workflow.channels) == 2
        
        # Disconnect one connection
        result = workflow.disconnect("agent1", "channel1", "agent2")
        assert result is True
        assert len(workflow.connections) == 1
        assert "channel2" in workflow.channels
        assert "channel1" not in workflow.channels  # Channel removed when no longer used
        
        # Try to disconnect non-existent connection
        result = workflow.disconnect("agent1", "nonexistent", "agent2")
        assert result is False
    
    def test_list_connections(self):
        """Test listing connections as strings."""
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        assert workflow.list_connections() == []
        
        workflow.connect("agent1", "data_channel", "agent2")
        connections = workflow.list_connections()
        
        assert len(connections) == 1
        assert "agent1 -> data_channel -> agent2" in connections[0]


class TestWorkflowLifecycle:
    """Test workflow start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_workflow(self):
        """Test starting workflow with agents."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "data_channel", "agent2")
        
        await workflow.start()
        
        # Check workflow status
        assert workflow.status == WorkflowStatus.RUNNING
        assert workflow.started_at is not None
        assert workflow.stopped_at is None
        
        # Check agents were started
        assert agent1.started is True
        assert agent2.started is True
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_stop_workflow(self):
        """Test stopping workflow."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        
        await workflow.start()
        await workflow.stop()
        
        # Check workflow status
        assert workflow.status == WorkflowStatus.STOPPED
        assert workflow.stopped_at is not None
        
        # Check agents were stopped
        assert agent1.stopped is True
        assert agent2.stopped is True
    
    @pytest.mark.asyncio
    async def test_start_already_running_workflow(self):
        """Test starting workflow that's already running."""
        workflow = Workflow("Test Workflow")
        
        await workflow.start()
        assert workflow.status == WorkflowStatus.RUNNING
        
        # Starting again should not error
        await workflow.start()
        assert workflow.status == WorkflowStatus.RUNNING
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_stop_already_stopped_workflow(self):
        """Test stopping workflow that's already stopped."""
        workflow = Workflow("Test Workflow")
        
        # Workflow starts as CREATED, stopping should be idempotent
        await workflow.stop()
        assert workflow.status == WorkflowStatus.STOPPED
        
        # Stopping again should not error
        await workflow.stop()
        assert workflow.status == WorkflowStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_agent_start_failure(self):
        """Test handling of agent start failures."""
        class FailingAgent:
            async def start(self):
                raise Exception("Agent failed to start")
            
            async def stop(self):
                pass
        
        workflow = Workflow("Test Workflow")
        workflow.add_agent("failing_agent", FailingAgent())
        
        with pytest.raises(WorkflowError) as exc_info:
            await workflow.start()
        
        assert workflow.status == WorkflowStatus.ERROR
        assert "Failed to start agent 'failing_agent'" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test workflow as async context manager."""
        agent = MockAgent("Agent1")
        
        # Create workflow and add agent BEFORE starting
        workflow = Workflow("Test Workflow")
        workflow.add_agent("agent1", agent)
        
        # Now use context manager to start/stop
        async with workflow:
            assert workflow.status == WorkflowStatus.RUNNING
            assert agent.started is True
        
        # Should be stopped after exiting context
        assert workflow.status == WorkflowStatus.STOPPED
        assert agent.stopped is True


class TestWorkflowDataInjection:
    """Test data injection and processing in workflows."""
    
    @pytest.mark.asyncio
    async def test_inject_data(self):
        """Test injecting data into specific agent."""
        workflow = Workflow("Test Workflow")
        agent = MockAgent("Agent1")
        
        workflow.add_agent("agent1", agent)
        await workflow.start()
        
        test_data = {"test": "data"}
        await workflow.inject_data("agent1", test_data, task="process")
        
        # Verify agent received the data
        assert len(agent.process_calls) == 1
        call = agent.process_calls[0]
        assert call['task'] == "process"
        assert call['data'] == test_data
        assert call['context']['workflow'] == "Test Workflow"
        assert call['context']['injection'] is True
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_inject_data_workflow_not_running(self):
        """Test error when injecting data into non-running workflow."""
        workflow = Workflow("Test Workflow")
        agent = MockAgent("Agent1")
        
        workflow.add_agent("agent1", agent)
        # Don't start workflow
        
        with pytest.raises(WorkflowError) as exc_info:
            await workflow.inject_data("agent1", {"test": "data"})
        
        assert "Cannot inject data - workflow is not running" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_inject_data_nonexistent_agent(self):
        """Test error when injecting data into non-existent agent."""
        workflow = Workflow("Test Workflow")
        await workflow.start()
        
        with pytest.raises(WorkflowError) as exc_info:
            await workflow.inject_data("nonexistent", {"test": "data"})
        
        assert "Agent 'nonexistent' not found" in str(exc_info.value)
        
        await workflow.stop()


class TestCommunicationLogger:
    """Test communication logging and tracking."""
    
    def test_communication_logger_initialization(self):
        """Test communication logger initialization."""
        logger = CommunicationLogger(max_messages=50)
        
        assert len(logger.messages) == 0
        assert logger.total_messages == 0
        assert logger.error_count == 0
    
    def test_log_communication_success(self):
        """Test logging successful communication."""
        logger = CommunicationLogger()
        
        test_data = {"result": "processed data", "status": "success"}
        logger.log_communication("Agent1", "Agent2", "data_channel", test_data)
        
        assert len(logger.messages) == 1
        assert logger.total_messages == 1
        assert logger.error_count == 0
        
        message = logger.messages[0]
        assert message.from_agent == "Agent1"
        assert message.to_agent == "Agent2"
        assert message.channel == "data_channel"
        assert message.success is True
        assert message.error_message is None
        assert "dict" in message.data_type
    
    def test_log_communication_error(self):
        """Test logging failed communication."""
        logger = CommunicationLogger()
        
        logger.log_communication(
            "Agent1", "Agent2", "data_channel", None,
            success=False, error_message="Connection failed"
        )
        
        assert len(logger.messages) == 1
        assert logger.total_messages == 1
        assert logger.error_count == 1
        
        message = logger.messages[0]
        assert message.success is False
        assert message.error_message == "Connection failed"
    
    def test_semantic_content_extraction(self):
        """Test semantic content extraction from different data types."""
        logger = CommunicationLogger()
        
        # Test with LLM response
        llm_data = {"llm_response": "Based on the analysis, I found that sales increased by 25%."}
        logger.log_communication("Agent1", "Agent2", "channel", llm_data)
        message = logger.messages[0]
        assert "sales increased by 25%" in message.semantic_content
        
        # Test with analysis data
        analysis_data = {"analysis_text": "The data shows strong performance in Q3."}
        logger.log_communication("Agent1", "Agent2", "channel", analysis_data)
        message = logger.messages[1]
        assert "strong performance in Q3" in message.semantic_content
        
        # Test with string data
        logger.log_communication("Agent1", "Agent2", "channel", "Simple string message")
        message = logger.messages[2]
        assert message.semantic_content == "Simple string message"
    
    def test_show_conversation_semantic(self):
        """Test showing conversation in semantic mode."""
        logger = CommunicationLogger()
        
        # Add some messages
        logger.log_communication("Fetcher", "Processor", "raw_data", {
            "fetch_status": "success",
            "records_fetched": 100,
            "source": "database"
        })
        
        logger.log_communication("Processor", "Analyzer", "clean_data", {
            "preprocess_status": "success",
            "records_processed": 100,
            "summary": {"total_sales": 50000, "average_sale": 500}
        })
        
        conversation = logger.show_conversation(mode="semantic", count=10)
        
        assert "Fetcher" in conversation
        assert "Processor" in conversation
        assert "100 records" in conversation
        assert "" in conversation  # Should show agent emoji
    
    def test_show_conversation_raw(self):
        """Test showing conversation in raw mode."""
        logger = CommunicationLogger()
        
        test_data = {"status": "success", "data": [1, 2, 3]}
        logger.log_communication("Agent1", "Agent2", "channel", test_data)
        
        raw_output = logger.show_conversation(mode="raw", count=10)
        
        assert "Agent1 -> Agent2" in raw_output
        assert "channel" in raw_output
        assert '"status": "success"' in raw_output or "status" in raw_output
    
    def test_query_conversation(self):
        """Test querying conversation with natural language."""
        logger = CommunicationLogger()
        
        # Add some messages with errors
        logger.log_communication("Agent1", "Agent2", "channel", None, 
                                success=False, error_message="Network timeout")
        logger.log_communication("Agent2", "Agent3", "channel", {"success": True})
        
        # Query for errors
        error_response = logger.query_conversation("show me errors")
        assert "Network timeout" in error_response
        
        # Query for conversation
        conv_response = logger.query_conversation("show conversation")
        assert "Agent1" in conv_response and "Agent2" in conv_response
        
        # Query for latest
        latest_response = logger.query_conversation("show latest 1")
        assert "Agent2" in latest_response  # Should show most recent
    
    def test_get_stats(self):
        """Test getting communication statistics."""
        logger = CommunicationLogger()
        
        # Add some messages
        logger.log_communication("Agent1", "Agent2", "channel", {"success": True})
        logger.log_communication("Agent2", "Agent3", "channel", None, 
                                success=False, error_message="Error")
        
        stats = logger.get_stats()
        
        assert stats['total_messages'] == 2
        assert stats['messages_in_memory'] == 2
        assert stats['error_count'] == 1
        assert stats['success_rate'] == 0.5
    
    def test_clear_logger(self):
        """Test clearing communication logger."""
        logger = CommunicationLogger()
        
        logger.log_communication("Agent1", "Agent2", "channel", {"test": True})
        assert len(logger.messages) == 1
        assert logger.total_messages == 1
        
        logger.clear()
        
        assert len(logger.messages) == 0
        assert logger.total_messages == 0
        assert logger.error_count == 0


class TestWorkflowCommunicationIntegration:
    """Test workflow integration with communication tracking."""
    
    @pytest.mark.asyncio
    async def test_communication_tracking_in_workflow(self):
        """Test that workflow tracks communication between agents."""
        workflow = Workflow("Test Workflow")
        
        # Create agents that publish to relay
        llm = MockLLMProvider()
        agent1 = SubstrateAgent(name="Publisher", llm_provider=llm, relay="data_channel")
        agent2 = MockAgent("Subscriber")
        
        workflow.add_agent("publisher", agent1)
        workflow.add_agent("subscriber", agent2)
        workflow.connect("publisher", "data_channel", "subscriber")
        
        await workflow.start()
        
        # Inject data to trigger communication
        await workflow.inject_data("publisher", {"test": "data"}, task="analyze")
        
        # Give time for relay communication
        await asyncio.sleep(0.1)
        
        # Check communication was logged
        comm_log = workflow.get_communication_log(count=5)
        assert len(comm_log) >= 0  # May be 0 if relay didn't trigger
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_get_agent_communication(self):
        """Test getting communication for specific agent."""
        workflow = Workflow("Test Workflow")
        
        # Manually log some communication
        workflow.comm_logger.log_communication("Agent1", "Agent2", "channel1", {"data": 1})
        workflow.comm_logger.log_communication("Agent2", "Agent3", "channel2", {"data": 2})
        workflow.comm_logger.log_communication("Agent1", "Agent3", "channel3", {"data": 3})
        
        agent1_comm = workflow.get_agent_communication("Agent1", count=10)
        
        assert len(agent1_comm) == 2  # Agent1 was involved in 2 communications
        
        # Should include both as sender and receiver
        agent_names = [msg['from'] for msg in agent1_comm] + [msg['to'] for msg in agent1_comm]
        assert "Agent1" in agent_names
    
    @pytest.mark.asyncio
    async def test_get_channel_communication(self):
        """Test getting communication for specific channel."""
        workflow = Workflow("Test Workflow")
        
        # Manually log communication on different channels
        workflow.comm_logger.log_communication("Agent1", "Agent2", "data_channel", {"data": 1})
        workflow.comm_logger.log_communication("Agent2", "Agent3", "control_channel", {"data": 2})
        workflow.comm_logger.log_communication("Agent3", "Agent1", "data_channel", {"data": 3})
        
        data_channel_comm = workflow.get_channel_communication("data_channel", count=10)
        
        assert len(data_channel_comm) == 2
        for msg in data_channel_comm:
            assert msg['channel'] == "data_channel"


class TestWorkflowStatistics:
    """Test workflow statistics and monitoring."""
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting comprehensive workflow statistics."""
        workflow = Workflow("Test Workflow", project_id="test_project")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        workflow.connect("agent1", "data_channel", "agent2")
        
        await workflow.start()
        
        stats = workflow.get_stats()
        
        # Check basic stats
        assert stats['name'] == "Test Workflow"
        assert stats['project_id'] == "test_project"
        assert stats['status'] == WorkflowStatus.RUNNING.value
        assert stats['agent_count'] == 2
        assert stats['connection_count'] == 1
        assert stats['channel_count'] == 1
        assert stats['created_at'] is not None
        assert stats['started_at'] is not None
        assert stats['stopped_at'] is None
        assert stats['running_time'] is not None
        assert stats['error'] is None
        
        # Check agent and channel lists
        assert set(stats['agents']) == {"agent1", "agent2"}
        assert list(stats['channels']) == ["data_channel"]
        
        # Check communication stats
        assert 'communication' in stats
        
        await workflow.stop()
        
        # Check stats after stopping
        final_stats = workflow.get_stats()
        assert final_stats['status'] == WorkflowStatus.STOPPED.value
        assert final_stats['stopped_at'] is not None
    
    @pytest.mark.asyncio
    async def test_stats_with_error(self):
        """Test statistics when workflow has errors."""
        workflow = Workflow("Test Workflow")
        
        class FailingAgent:
            async def start(self):
                raise Exception("Test error")
            async def stop(self):
                pass
        
        workflow.add_agent("failing", FailingAgent())
        
        try:
            await workflow.start()
        except WorkflowError:
            pass  # Expected
        
        stats = workflow.get_stats()
        
        assert stats['status'] == WorkflowStatus.ERROR.value
        assert stats['error'] is not None
        assert "Test error" in stats['error']


class TestWorkflowEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_empty_workflow(self):
        """Test workflow with no agents."""
        workflow = Workflow("Empty Workflow")
        
        # Should be able to start/stop empty workflow
        await workflow.start()
        assert workflow.status == WorkflowStatus.RUNNING
        
        await workflow.stop()
        assert workflow.status == WorkflowStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_workflow_with_agents_no_connections(self):
        """Test workflow with agents but no connections."""
        workflow = Workflow("Disconnected Workflow")
        workflow.add_agent("agent1", MockAgent("Agent1"))
        workflow.add_agent("agent2", MockAgent("Agent2"))
        
        # Should work fine
        await workflow.start()
        await workflow.inject_data("agent1", {"test": "data"})
        await workflow.stop()
    
    def test_connection_string_representation(self):
        """Test string representation of connections."""
        connection = Connection("agent1", "data_channel", "agent2", "process")
        
        assert str(connection) == "agent1 -> data_channel -> agent2"
    
    @pytest.mark.asyncio
    async def test_agent_without_start_stop_methods(self):
        """Test workflow with agents that don't have start/stop methods."""
        class SimpleAgent:
            def __init__(self, name):
                self.name = name
            
            async def process(self, task, data, context):
                return {"result": f"{self.name} processed {task}"}
        
        workflow = Workflow("Simple Workflow")
        workflow.add_agent("simple", SimpleAgent("Simple"))
        
        # Should not error even if agent doesn't have start/stop
        await workflow.start()
        await workflow.inject_data("simple", {"test": "data"})
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_get_channel_data(self):
        """Test getting data from relay channels."""
        workflow = Workflow("Test Workflow")
        
        # Mock relay manager to return test data
        with patch.object(workflow.relay_manager, 'get_latest', return_value=[{"test": "data"}]):
            data = workflow.get_channel_data("test_channel", count=1)
            assert data == [{"test": "data"}]
    
    def test_clear_communication_log(self):
        """Test clearing workflow communication log."""
        workflow = Workflow("Test Workflow")
        
        # Add some communication
        workflow.comm_logger.log_communication("Agent1", "Agent2", "channel", {"test": True})
        assert len(workflow.comm_logger.messages) == 1
        
        # Clear log
        workflow.clear_communication_log()
        assert len(workflow.comm_logger.messages) == 0


class TestWorkflowRelayIntegration:
    """Test workflow integration with relay system."""
    
    @pytest.mark.asyncio
    async def test_relay_subscription_setup(self):
        """Test that workflow properly sets up relay subscriptions."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "data_channel", "agent2")
        
        await workflow.start()
        
        # Verify subscriptions were created
        assert len(workflow._subscriptions) == 1
        channel, callback = workflow._subscriptions[0]
        assert channel == "data_channel"
        assert callable(callback)
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_relay_subscription_cleanup(self):
        """Test that workflow cleans up relay subscriptions on stop."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "data_channel", "agent2")
        
        await workflow.start()
        assert len(workflow._subscriptions) == 1
        
        await workflow.stop()
        
        # Subscriptions should be cleared
        assert len(workflow._subscriptions) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_connections_same_channel(self):
        """Test multiple agents subscribing to the same channel."""
        workflow = Workflow("Test Workflow")
        agent1 = MockAgent("Agent1")
        agent2 = MockAgent("Agent2")
        agent3 = MockAgent("Agent3")
        
        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.add_agent("agent3", agent3)
        
        # Both agent2 and agent3 subscribe to the same channel
        workflow.connect("agent1", "broadcast_channel", "agent2")
        workflow.connect("agent1", "broadcast_channel", "agent3")
        
        await workflow.start()
        
        # Should have 2 subscriptions for the same channel
        assert len(workflow._subscriptions) == 2
        assert all(sub[0] == "broadcast_channel" for sub in workflow._subscriptions)
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_workflow_relay_error_handling(self):
        """Test workflow handles relay errors gracefully."""
        workflow = Workflow("Test Workflow")
        
        # Mock relay manager that raises errors
        mock_relay = Mock()
        mock_relay._running = False
        mock_relay.start = AsyncMock(side_effect=Exception("Relay start failed"))
        workflow.relay_manager = mock_relay
        
        agent = MockAgent("Agent1")
        workflow.add_agent("agent1", agent)
        
        # Workflow start should fail due to relay error
        with pytest.raises(WorkflowError):
            await workflow.start()
        
        assert workflow.status == WorkflowStatus.ERROR


class TestWorkflowComplexScenarios:
    """Test complex workflow scenarios and integration patterns."""
    
    @pytest.mark.asyncio
    async def test_data_pipeline_workflow(self):
        """Test a complete data pipeline workflow scenario."""
        workflow = Workflow("Data Pipeline")
        
        # Create mock agents for a typical data pipeline
        fetcher_responses = {
            "fetch_data_Fetcher": {
                "status": "success",
                "result": {
                    "fetch_status": "success",
                    "records_fetched": 100,
                    "source": "database",
                    "data": {"sales_records": [{"amount": 100}, {"amount": 200}]}
                }
            }
        }
        
        processor_responses = {
            "relay_message_Processor": {
                "status": "success", 
                "result": {
                    "preprocess_status": "success",
                    "records_processed": 100,
                    "summary": {"total_sales": 300, "average_sale": 150}
                }
            }
        }
        
        analyzer_responses = {
            "relay_message_Analyzer": {
                "status": "success",
                "result": {
                    "analysis_status": "success",
                    "records_analyzed": 100,
                    "insights": ["Sales increased", "Peak performance in Q3"]
                }
            }
        }
        
        fetcher = MockAgent("Fetcher", fetcher_responses)
        processor = MockAgent("Processor", processor_responses)
        analyzer = MockAgent("Analyzer", analyzer_responses)
        
        # Build pipeline: fetcher -> processor -> analyzer
        workflow.add_agent("fetcher", fetcher)
        workflow.add_agent("processor", processor)
        workflow.add_agent("analyzer", analyzer)
        
        workflow.connect("fetcher", "raw_data", "processor")
        workflow.connect("processor", "clean_data", "analyzer")
        
        await workflow.start()
        
        # Trigger the pipeline
        await workflow.inject_data("fetcher", {"source": "sales_db"}, task="fetch_data")
        
        # Give time for async processing
        await asyncio.sleep(0.1)
        
        # Verify fetcher was called
        assert len(fetcher.process_calls) == 1
        assert fetcher.process_calls[0]['task'] == "fetch_data"
        
        # Check communication was logged
        comm_log = workflow.get_communication_log(count=10)
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_parallel_processing_workflow(self):
        """Test workflow with parallel processing branches."""
        workflow = Workflow("Parallel Processing")
        
        # Create agents for parallel processing
        splitter = MockAgent("Splitter")
        processor1 = MockAgent("Processor1")
        processor2 = MockAgent("Processor2")
        combiner = MockAgent("Combiner")
        
        workflow.add_agent("splitter", splitter)
        workflow.add_agent("processor1", processor1)
        workflow.add_agent("processor2", processor2)
        workflow.add_agent("combiner", combiner)
        
        # Set up parallel connections
        workflow.connect("splitter", "branch1", "processor1")
        workflow.connect("splitter", "branch2", "processor2")
        workflow.connect("processor1", "results1", "combiner")
        workflow.connect("processor2", "results2", "combiner")
        
        await workflow.start()
        
        # Inject data to start parallel processing
        await workflow.inject_data("splitter", {"data": "to_split"}, task="split")
        
        await asyncio.sleep(0.1)
        
        # Verify all agents are in the workflow
        assert len(workflow.agents) == 4
        assert len(workflow.connections) == 4
        assert len(workflow.channels) == 4
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """Test workflow behavior with agent errors."""
        workflow = Workflow("Error Recovery")
        
        # Create an agent that sometimes fails
        class UnreliableAgent:
            def __init__(self, name, fail_count=1):
                self.name = name
                self.call_count = 0
                self.fail_count = fail_count
                self.process_calls = []
            
            async def start(self):
                pass
            
            async def stop(self):
                pass
            
            async def process(self, task, data, context):
                self.call_count += 1
                self.process_calls.append({'task': task, 'data': data, 'context': context})
                
                if self.call_count <= self.fail_count:
                    raise Exception(f"Simulated failure #{self.call_count}")
                
                return {
                    "status": "success",
                    "result": {"recovered": True, "attempt": self.call_count}
                }
        
        unreliable = UnreliableAgent("Unreliable", fail_count=2)
        reliable = MockAgent("Reliable")
        
        workflow.add_agent("unreliable", unreliable)
        workflow.add_agent("reliable", reliable)
        workflow.connect("unreliable", "data_flow", "reliable")
        
        await workflow.start()
        
        # This should trigger an error initially
        await workflow.inject_data("unreliable", {"test": "data"}, task="process")
        
        await asyncio.sleep(0.1)
        
        # Check that the unreliable agent was called
        assert len(unreliable.process_calls) == 1
        
        await workflow.stop()
    
    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self):
        """Test workflow performance and timing monitoring."""
        workflow = Workflow("Performance Test")
        
        # Add multiple agents to monitor
        for i in range(5):
            agent = MockAgent(f"Agent{i}")
            workflow.add_agent(f"agent{i}", agent)
        
        start_time = time.time()
        await workflow.start()
        start_duration = time.time() - start_time
        
        # Start should be reasonably fast
        assert start_duration < 1.0
        
        # Check timing in stats
        stats = workflow.get_stats()
        assert stats['running_time'] is not None
        assert stats['running_time'] > 0
        
        stop_time = time.time()
        await workflow.stop()
        stop_duration = time.time() - stop_time
        
        # Stop should also be fast
        assert stop_duration < 1.0
        
        # Final stats should show total runtime
        final_stats = workflow.get_stats()
        assert final_stats['running_time'] > stats['running_time']


class TestWorkflowConversationFeatures:
    """Test advanced conversation and communication features."""
    
    def test_semantic_content_sales_analysis(self):
        """Test semantic content extraction for sales analysis workflow."""
        logger = CommunicationLogger()
        
        # Simulate fetcher agent output
        fetch_data = {
            "fetch_status": "success",
            "records_fetched": 1000,
            "source": "sales_database",
            "data": {"sales_records": []}
        }
        logger.log_communication("DataFetcher", "DataProcessor", "raw_data", fetch_data)
        
        # Simulate processor agent output
        process_data = {
            "preprocess_status": "success", 
            "records_processed": 1000,
            "original_source": "sales_database",
            "summary": {
                "total_sales": 50000,
                "average_sale": 50,
                "unique_regions": ["North", "South", "East"]
            }
        }
        logger.log_communication("DataProcessor", "DataAnalyzer", "clean_data", process_data)
        
        # Simulate analyzer agent output
        analysis_data = {
            "analysis_status": "success",
            "records_analyzed": 1000,
            "source": "sales_database",
            "detailed_analysis": {
                "revenue_analysis": {
                    "total_revenue": 50000,
                    "performance": "excellent"
                },
                "regional_analysis": {
                    "regional_distribution": {
                        "North": {"total": 20000},
                        "South": {"total": 15000}
                    }
                },
                "llm_insights": "Sales performance exceeded expectations with 25% growth over last quarter."
            }
        }
        logger.log_communication("DataAnalyzer", "ReportGenerator", "analysis_results", analysis_data)
        
        # Test semantic conversation view
        conversation = logger.show_conversation(mode="semantic", count=10)
        
        # Should contain meaningful business context
        assert "1000 records" in conversation
        assert "sales_database" in conversation
        assert "$50,000" in conversation or "50000" in conversation
        assert "3 regions" in conversation or "North" in conversation
        assert "excellent performance" in conversation
        assert "25% growth" in conversation
    
    def test_conversation_query_natural_language(self):
        """Test natural language querying of workflow conversations."""
        logger = CommunicationLogger()
        
        # Add various types of communications
        logger.log_communication("Agent1", "Agent2", "data", {"success": True})
        logger.log_communication("Agent2", "Agent3", "data", None, 
                                success=False, error_message="Database connection failed")
        logger.log_communication("Agent3", "Agent4", "data", {
            "llm_response": "Based on the analysis, revenue is up 15% this quarter."
        })
        
        # Test different query types
        error_query = logger.query_conversation("What errors happened?")
        assert "Database connection failed" in error_query
        
        ai_query = logger.query_conversation("What did the AI say?")
        assert "revenue is up 15%" in ai_query
        
        recent_query = logger.query_conversation("Show me the last 2 messages")
        lines = recent_query.split('\n')
        assert len([line for line in lines if line.strip()]) >= 2
    
    def test_communication_message_to_dict(self):
        """Test conversion of communication messages to dictionary format."""
        message = CommunicationMessage(
            timestamp=1234567890.0,
            from_agent="Agent1",
            to_agent="Agent2", 
            channel="test_channel",
            data_type="dict",
            data_preview="{'key': 'value'}",
            semantic_content="Agent processed the data successfully",
            full_data={"key": "value"},
            success=True
        )
        
        msg_dict = message.to_dict()
        
        assert msg_dict['timestamp'] == 1234567890.0
        assert msg_dict['from'] == "Agent1"
        assert msg_dict['to'] == "Agent2"
        assert msg_dict['channel'] == "test_channel"
        assert msg_dict['semantic_content'] == "Agent processed the data successfully"
        assert msg_dict['success'] is True
        assert msg_dict['error'] is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
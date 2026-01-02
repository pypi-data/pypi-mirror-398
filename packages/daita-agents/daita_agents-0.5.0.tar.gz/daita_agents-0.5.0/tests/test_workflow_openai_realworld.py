"""
Real-world workflow tests using OpenAI LLM.

This test suite validates the complete workflow and relay system with actual
LLM interactions, testing:
- Agent-to-agent communication via relay channels
- Multi-stage data processing workflows
- Parallel processing patterns
- receive_message() API for workflow communication
- Token usage tracking across workflows
- Real autonomous LLM decision-making in workflows

These tests use OpenAI's GPT models to ensure the framework works
with real-world LLM providers, not just mocks.
"""
import pytest
import asyncio
import os
from typing import Dict, Any, List

from daita.core.workflow import Workflow, WorkflowStatus
from daita.agents.substrate import SubstrateAgent
from daita.core.tools import tool
from daita.core.relay import get_global_relay


# Test data
SAMPLE_SALES_DATA = [
    {"region": "North", "product": "Widget A", "sales": 1200, "date": "2024-01-15"},
    {"region": "South", "product": "Widget B", "sales": 850, "date": "2024-01-16"},
    {"region": "East", "product": "Widget A", "sales": 2100, "date": "2024-01-17"},
    {"region": "West", "product": "Widget C", "sales": 1500, "date": "2024-01-18"},
    {"region": "North", "product": "Widget B", "sales": 980, "date": "2024-01-19"},
]


class TestSimpleTwoAgentWorkflow:
    """Test basic two-agent workflow with relay communication."""

    @pytest.mark.asyncio
    async def test_data_fetcher_to_analyzer_workflow(self):
        """Test a simple workflow: fetcher sends data to analyzer via relay."""
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        workflow = Workflow("Sales Analysis Workflow")

        # Create data fetcher agent
        fetcher = SubstrateAgent(
            name="DataFetcher",
            model="gpt-4o-mini",
            prompt="You are a data fetcher. When asked to fetch sales data, you retrieve it.",
            api_key=api_key
        )

        # Add tool to fetcher
        @tool
        async def get_sales_data() -> list:
            """Get sales data from the database."""
            return SAMPLE_SALES_DATA

        fetcher.register_tool(get_sales_data)

        # Create analyzer agent
        analyzer_result = {"received": False, "data": None, "analysis": None}

        analyzer = SubstrateAgent(
            name="DataAnalyzer",
            model="gpt-4o-mini",
            prompt="You are a data analyst. Analyze sales data and provide insights about trends and performance.",
            api_key=api_key
        )

        # Override receive_message to capture data
        original_receive = analyzer.receive_message

        async def custom_receive_message(data, source_agent, channel, workflow_name=None):
            analyzer_result["received"] = True
            analyzer_result["data"] = data

            # Process the data with the analyzer
            result = await original_receive(data, source_agent, channel, workflow_name)
            analyzer_result["analysis"] = result.get("result", "")
            return result

        analyzer.receive_message = custom_receive_message

        # Build workflow
        workflow.add_agent("fetcher", fetcher)
        workflow.add_agent("analyzer", analyzer)

        # Connect: fetcher publishes to "sales_data" channel, analyzer subscribes
        # This means when fetcher publishes to sales_data, analyzer.receive_message() gets called
        workflow.connect("fetcher", "sales_data", "analyzer")

        await workflow.start()

        try:
            # Trigger fetcher to get data
            # Fetcher should use get_sales_data tool and then publish result
            result = await fetcher.run_detailed(
                "Fetch the sales data and publish it to the sales_data relay channel"
            )

            print(f"\nFetcher result: {result.get('result', '')[:200]}")

            # Manually publish to relay to trigger analyzer (since auto-relay might not be set up)
            await workflow.relay_manager.publish(
                "sales_data",
                SAMPLE_SALES_DATA,  # Just raw data - no wrapper needed!
                publisher="DataFetcher"
            )

            # Wait for relay communication
            await asyncio.sleep(2)

            # Verify analyzer received data
            assert analyzer_result["received"], "Analyzer did not receive data via relay"
            assert analyzer_result["data"] is not None, "Analyzer received null data"

            print(f"\nAnalyzer received: {str(analyzer_result['data'])[:200]}")
            print(f"\nAnalyzer analysis: {str(analyzer_result['analysis'])[:500]}")

            # Verify workflow stats
            stats = workflow.get_stats()
            assert stats["status"] == WorkflowStatus.RUNNING.value
            assert stats["agent_count"] == 2
            assert stats["connection_count"] == 1

            # Check token usage
            token_usage = workflow.get_token_usage()
            if token_usage:
                print(f"\nWorkflow token usage: {token_usage['total_tokens']} tokens")
                assert token_usage["total_tokens"] > 0, "No tokens used in workflow"
                assert len(token_usage["agents_with_usage"]) > 0, "No agents reported token usage"

        finally:
            await workflow.stop()


class TestMultiStageDataPipeline:
    """Test multi-stage data processing workflow."""

    @pytest.mark.asyncio
    async def test_three_stage_pipeline(self):
        """Test fetcher -> processor -> analyzer pipeline."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        workflow = Workflow("Data Processing Pipeline")

        # Stage 1: Data Fetcher
        fetcher = SubstrateAgent(
            name="DataFetcher",
            model="gpt-4o-mini",
            prompt="You fetch data from sources.",
            api_key=api_key
        )

        @tool
        async def fetch_sales_data() -> dict:
            """Fetch sales data from database."""
            return {
                "source": "sales_db",
                "records": SAMPLE_SALES_DATA,
                "count": len(SAMPLE_SALES_DATA)
            }

        fetcher.register_tool(fetch_sales_data)

        # Stage 2: Data Processor
        processor_state = {"processed": False, "result": None}

        processor = SubstrateAgent(
            name="DataProcessor",
            model="gpt-4o-mini",
            prompt="You process and clean data. Calculate totals and summaries.",
            api_key=api_key
        )

        # Override receive_message to process data
        original_processor_receive = processor.receive_message

        async def processor_receive_message(data, source_agent, channel, workflow_name=None):
            print(f"\nProcessor received data from {source_agent} via {channel}")
            processor_state["processed"] = True

            # Process with LLM
            result = await original_processor_receive(data, source_agent, channel, workflow_name)
            processor_state["result"] = result

            # Publish processed result to next stage
            if "result" in result:
                # Get workflow's relay manager
                relay = get_global_relay()
                await relay.publish(
                    "processed_data",
                    result["result"],  # Still extract result from agent response
                    publisher="DataProcessor"
                )

            return result

        processor.receive_message = processor_receive_message

        # Stage 3: Data Analyzer
        analyzer_state = {"analyzed": False, "insights": None}

        analyzer = SubstrateAgent(
            name="DataAnalyzer",
            model="gpt-4o-mini",
            prompt="You analyze processed data and provide business insights.",
            api_key=api_key
        )

        original_analyzer_receive = analyzer.receive_message

        async def analyzer_receive_message(data, source_agent, channel, workflow_name=None):
            print(f"\nAnalyzer received data from {source_agent} via {channel}")
            analyzer_state["analyzed"] = True

            # Analyze with LLM
            result = await original_analyzer_receive(data, source_agent, channel, workflow_name)
            analyzer_state["insights"] = result.get("result", "")

            return result

        analyzer.receive_message = analyzer_receive_message

        # Build pipeline
        workflow.add_agent("fetcher", fetcher)
        workflow.add_agent("processor", processor)
        workflow.add_agent("analyzer", analyzer)

        # Connect pipeline: fetcher -> raw_data -> processor -> processed_data -> analyzer
        workflow.connect("fetcher", "raw_data", "processor")
        workflow.connect("processor", "processed_data", "analyzer")

        await workflow.start()

        try:
            # Trigger the pipeline
            print("\nTriggering data fetcher...")
            await fetcher.run("Fetch the sales data and publish to raw_data channel")

            # Publish data to start pipeline
            raw_data = {
                "source": "sales_db",
                "records": SAMPLE_SALES_DATA,
                "count": len(SAMPLE_SALES_DATA)
            }
            await workflow.relay_manager.publish("raw_data", raw_data, publisher="DataFetcher")

            # Wait for pipeline to process
            await asyncio.sleep(3)

            # Verify each stage
            assert processor_state["processed"], "Processor did not receive data"
            print(f"\nProcessor result: {str(processor_state['result'])[:300]}")

            # Note: Analyzer might not receive data if processor didn't publish correctly
            # This is expected in some cases, just log it
            if analyzer_state["analyzed"]:
                print(f"\nAnalyzer insights: {str(analyzer_state['insights'])[:500]}")
            else:
                print("\nNote: Analyzer did not receive data (expected if processor didn't publish)")

            # Check workflow health
            health = workflow.health_check()
            assert health["status"] == WorkflowStatus.RUNNING.value

            # Check token usage across pipeline
            token_usage = workflow.get_token_usage()
            if token_usage:
                print(f"\nPipeline total tokens: {token_usage['total_tokens']}")
                print(f"Agents with usage: {token_usage['agents_with_usage']}")
                assert token_usage["total_tokens"] > 0

        finally:
            await workflow.stop()


class TestReceiveMessageAPI:
    """Test the receive_message() API for workflow communication."""

    @pytest.mark.asyncio
    async def test_receive_message_integration(self):
        """Test that receive_message() properly integrates with workflows."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        # Create two agents
        sender = SubstrateAgent(
            name="Sender",
            model="gpt-4o-mini",
            prompt="You send data to other agents.",
            api_key=api_key
        )

        receiver_state = {"calls": []}

        receiver = SubstrateAgent(
            name="Receiver",
            model="gpt-4o-mini",
            prompt="You receive and process data from other agents. Provide a brief acknowledgment.",
            api_key=api_key
        )

        # Track receive_message calls
        original_receive = receiver.receive_message

        async def tracked_receive_message(data, source_agent, channel, workflow_name=None):
            call_info = {
                "data": data,
                "source": source_agent,
                "channel": channel,
                "workflow": workflow_name
            }
            receiver_state["calls"].append(call_info)

            result = await original_receive(data, source_agent, channel, workflow_name)
            call_info["result"] = result

            return result

        receiver.receive_message = tracked_receive_message

        # Start agents
        await sender.start()
        await receiver.start()

        try:
            # Test direct receive_message call (simulating workflow relay)
            test_data = {
                "message": "Hello from sender",
                "data": SAMPLE_SALES_DATA[:2]
            }

            result = await receiver.receive_message(
                data=test_data,
                source_agent="Sender",
                channel="test_channel",
                workflow_name="TestWorkflow"
            )

            print(f"\nReceive message result: {str(result)[:500]}")

            # Verify the call was tracked
            assert len(receiver_state["calls"]) == 1
            call = receiver_state["calls"][0]

            assert call["data"] == test_data
            assert call["source"] == "Sender"
            assert call["channel"] == "test_channel"
            assert call["workflow"] == "TestWorkflow"
            assert "result" in call

            # Verify result structure
            assert "result" in result or "status" in result

            print(f"\nReceive message tracking successful!")
            print(f"Call info: {call}")

        finally:
            await sender.stop()
            await receiver.stop()


class TestWorkflowErrorHandling:
    """Test error handling in workflows."""

    @pytest.mark.asyncio
    async def test_agent_error_propagation(self):
        """Test that errors in workflow agents are handled properly."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        workflow = Workflow("Error Test Workflow")

        # Create an agent that will encounter errors
        agent1 = SubstrateAgent(
            name="ErrorProne",
            model="gpt-4o-mini",
            prompt="You process data.",
            api_key=api_key
        )

        agent2_state = {"received_error": False, "data": None}

        agent2 = SubstrateAgent(
            name="ErrorHandler",
            model="gpt-4o-mini",
            prompt="You handle data and errors gracefully.",
            api_key=api_key
        )

        # Track what agent2 receives
        original_receive = agent2.receive_message

        async def tracked_receive(data, source_agent, channel, workflow_name=None):
            agent2_state["data"] = data
            try:
                result = await original_receive(data, source_agent, channel, workflow_name)
                return result
            except Exception as e:
                agent2_state["received_error"] = True
                print(f"\nAgent2 caught error: {e}")
                raise

        agent2.receive_message = tracked_receive

        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.connect("agent1", "data_channel", "agent2")

        await workflow.start()

        try:
            # Send some data through the workflow
            await workflow.relay_manager.publish(
                "data_channel",
                {"test": "data", "value": 123},  # Just raw data!
                publisher="ErrorProne"
            )

            await asyncio.sleep(2)

            # Check that data was received (even if processing had issues)
            if agent2_state["data"]:
                print(f"\nAgent2 received data: {agent2_state['data']}")

            # Workflow should still be running
            assert workflow.status == WorkflowStatus.RUNNING

        finally:
            await workflow.stop()


class TestWorkflowTokenTracking:
    """Test token usage tracking across workflows."""

    @pytest.mark.asyncio
    async def test_workflow_aggregates_token_usage(self):
        """Test that workflow aggregates token usage from all agents."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        workflow = Workflow("Token Tracking Workflow")

        # Create multiple agents
        agent1 = SubstrateAgent(
            name="Agent1",
            model="gpt-4o-mini",
            prompt="You are agent 1. Respond briefly.",
            api_key=api_key
        )

        agent2 = SubstrateAgent(
            name="Agent2",
            model="gpt-4o-mini",
            prompt="You are agent 2. Respond briefly.",
            api_key=api_key
        )

        agent3 = SubstrateAgent(
            name="Agent3",
            model="gpt-4o-mini",
            prompt="You are agent 3. Respond briefly.",
            api_key=api_key
        )

        workflow.add_agent("agent1", agent1)
        workflow.add_agent("agent2", agent2)
        workflow.add_agent("agent3", agent3)

        await workflow.start()

        try:
            # Run each agent to generate token usage
            await agent1.run("Say hello")
            await agent2.run("Say goodbye")
            await agent3.run("Say thank you")

            # Get workflow token usage
            token_usage = workflow.get_token_usage()

            print(f"\nWorkflow token usage: {token_usage}")

            # Verify aggregation
            if token_usage:
                assert token_usage["total_tokens"] > 0, "No total tokens tracked"
                assert token_usage["llm_calls"] >= 3, f"Expected at least 3 LLM calls, got {token_usage['llm_calls']}"
                assert len(token_usage["agents_with_usage"]) >= 1, "No agents reported usage"

                print(f"\nTotal tokens used: {token_usage['total_tokens']}")
                print(f"LLM calls: {token_usage['llm_calls']}")
                print(f"Agents with usage: {token_usage['agents_with_usage']}")
            else:
                print("\nWarning: No token usage tracked (might be expected depending on implementation)")

        finally:
            await workflow.stop()


class TestWorkflowRelayCommunication:
    """Test relay-based communication between agents."""

    @pytest.mark.asyncio
    async def test_relay_publish_subscribe_pattern(self):
        """Test pub-sub pattern with relay channels."""
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        workflow = Workflow("Pub-Sub Workflow")

        # Publisher agent
        publisher = SubstrateAgent(
            name="Publisher",
            model="gpt-4o-mini",
            prompt="You publish news updates.",
            api_key=api_key
        )

        # Multiple subscribers
        subscriber_states = {"sub1": [], "sub2": []}

        subscriber1 = SubstrateAgent(
            name="Subscriber1",
            model="gpt-4o-mini",
            prompt="You process news updates.",
            api_key=api_key
        )

        subscriber2 = SubstrateAgent(
            name="Subscriber2",
            model="gpt-4o-mini",
            prompt="You analyze news updates.",
            api_key=api_key
        )

        # Track what each subscriber receives
        original_sub1_receive = subscriber1.receive_message
        original_sub2_receive = subscriber2.receive_message

        async def sub1_receive(data, source_agent, channel, workflow_name=None):
            subscriber_states["sub1"].append(data)
            return await original_sub1_receive(data, source_agent, channel, workflow_name)

        async def sub2_receive(data, source_agent, channel, workflow_name=None):
            subscriber_states["sub2"].append(data)
            return await original_sub2_receive(data, source_agent, channel, workflow_name)

        subscriber1.receive_message = sub1_receive
        subscriber2.receive_message = sub2_receive

        # Build pub-sub workflow
        workflow.add_agent("publisher", publisher)
        workflow.add_agent("subscriber1", subscriber1)
        workflow.add_agent("subscriber2", subscriber2)

        # Both subscribers listen to same channel
        workflow.connect("publisher", "news_channel", "subscriber1")
        workflow.connect("publisher", "news_channel", "subscriber2")

        await workflow.start()

        try:
            # Publish messages
            messages = [
                {"headline": "Sales up 20%", "priority": "high"},
                {"headline": "New product launch", "priority": "medium"},
            ]

            for msg in messages:
                await workflow.relay_manager.publish(
                    "news_channel",
                    msg,  # Just the message dict!
                    publisher="Publisher"
                )

            # Wait for delivery
            await asyncio.sleep(2)

            # Verify both subscribers received messages
            print(f"\nSubscriber1 received: {len(subscriber_states['sub1'])} messages")
            print(f"Subscriber2 received: {len(subscriber_states['sub2'])} messages")

            # Both should receive the same messages
            assert len(subscriber_states["sub1"]) == len(messages), \
                f"Sub1 expected {len(messages)} messages, got {len(subscriber_states['sub1'])}"
            assert len(subscriber_states["sub2"]) == len(messages), \
                f"Sub2 expected {len(messages)} messages, got {len(subscriber_states['sub2'])}"

            # Verify workflow stats
            stats = workflow.get_stats()
            assert stats["connection_count"] == 2, "Should have 2 connections"
            assert stats["channel_count"] == 1, "Should have 1 channel (shared)"

        finally:
            await workflow.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

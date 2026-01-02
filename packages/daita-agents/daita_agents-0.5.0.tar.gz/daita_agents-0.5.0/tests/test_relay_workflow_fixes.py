"""
Test suite for Phase 1 Relay & Workflow Bug Fixes.

Tests verify the following fixes:
1. Dead Letter Queue removal (no memory leaks)
2. Retry thundering herd prevention (jitter in delays)
3. Publish-subscribe race condition fix (atomic operations)
4. Subscriber error tracking (not swallowed)
5. Unbounded subscription list fix (duplicate prevention)
6. Circuit breaker removal (clean configuration)
"""
import pytest
import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import AsyncMock

from daita.core.relay import RelayManager, ReliableMessage, MessageStatus
from daita.core.workflow import Workflow, WorkflowError, ReliabilityConfig
from daita.config.base import RetryPolicy


class TestDeadLetterQueueRemoval:
    """Test that DLQ has been completely removed."""

    def test_no_dlq_attribute(self):
        """Test that dead_letter_queue attribute doesn't exist."""
        relay = RelayManager(enable_reliability=True)
        assert not hasattr(relay, 'dead_letter_queue')

    def test_no_dlq_methods(self):
        """Test that DLQ methods don't exist."""
        relay = RelayManager(enable_reliability=True)
        assert not hasattr(relay, 'get_dead_letter_queue')
        assert not hasattr(relay, 'clear_dead_letter_queue')
        assert not hasattr(relay, 'retry_from_dead_letter_queue')
        assert not hasattr(relay, '_move_to_dead_letter_queue')

    def test_no_dlq_in_stats(self):
        """Test that DLQ doesn't appear in stats."""
        relay = RelayManager(enable_reliability=True)
        stats = relay.get_stats()
        assert 'dead_letter_queue_size' not in stats

    def test_no_dlq_in_reliability_config(self):
        """Test that DLQ not in ReliabilityConfig."""
        config = ReliabilityConfig()
        assert not hasattr(config, 'dead_letter_queue')

    @pytest.mark.asyncio
    async def test_failed_message_cleanup(self):
        """Test that failed messages are properly cleaned up without DLQ."""
        relay = RelayManager(enable_reliability=True)
        await relay.start()

        # Create a message that will fail
        message_id = await relay.publish(
            "test_channel",
            {"result": "test"},
            publisher="test",
            require_ack=True
        )

        # NACK the message multiple times to exceed retry limit
        for _ in range(3):
            await relay.nack_message(message_id, "Test error")
            await asyncio.sleep(0.1)

        # Message should be removed from pending, not moved to DLQ
        pending = relay.get_pending_messages()
        assert all(msg['id'] != message_id for msg in pending)

        await relay.stop()


class TestRetryThunderingHerd:
    """Test that retry jitter prevents thundering herd."""

    def test_calculate_retry_delay_has_jitter(self):
        """Test that retry delay calculation includes jitter."""
        relay = RelayManager(enable_reliability=True)

        # Calculate multiple delays for same attempt
        delays = [relay._calculate_retry_delay(attempt=1) for _ in range(100)]

        # All delays should be unique (with very high probability)
        unique_delays = len(set(delays))
        assert unique_delays > 90  # At least 90% should be unique

        # Delays should be within expected range with jitter
        # For attempt 1: base_delay * 2^1 = 2s, with ±50% jitter = 1s to 3s
        assert all(1.0 <= d <= 3.0 for d in delays), f"Delays out of range: {min(delays)}-{max(delays)}"

    def test_retry_delay_cap(self):
        """Test that retry delay is capped at 60 seconds."""
        relay = RelayManager(enable_reliability=True)

        # Very high attempt should still cap at 60s
        delay = relay._calculate_retry_delay(attempt=100)
        assert delay <= 60.0 * 1.5  # Max 60s * 1.5 (jitter factor)

    def test_retry_delay_increases_exponentially(self):
        """Test that retry delay increases exponentially with attempts."""
        relay = RelayManager(enable_reliability=True)

        # Get average delays for different attempts
        attempt_0_avg = sum(relay._calculate_retry_delay(0) for _ in range(50)) / 50
        attempt_1_avg = sum(relay._calculate_retry_delay(1) for _ in range(50)) / 50
        attempt_2_avg = sum(relay._calculate_retry_delay(2) for _ in range(50)) / 50

        # Should roughly double each time (accounting for jitter)
        assert attempt_1_avg > attempt_0_avg
        assert attempt_2_avg > attempt_1_avg


class TestPublishSubscribeRaceCondition:
    """Test that publish-subscribe operations are atomic."""

    @pytest.mark.asyncio
    async def test_concurrent_publish_subscribe(self):
        """Test that concurrent publish and subscribe don't race."""
        relay = RelayManager()
        await relay.start()

        received_messages = []

        async def subscriber(data):
            received_messages.append(data)

        async def publisher():
            for i in range(50):
                await relay.publish("test_channel", {"result": i})
                await asyncio.sleep(0.001)

        async def late_subscriber():
            await asyncio.sleep(0.01)  # Subscribe slightly late
            await relay.subscribe("test_channel", subscriber)
            await asyncio.sleep(0.1)  # Wait for messages

        # Run publisher and late subscriber concurrently
        await asyncio.gather(publisher(), late_subscriber())

        # With the fix, late subscriber should still receive some messages
        # because publish is atomic with notify
        assert len(received_messages) > 0

        await relay.stop()

    @pytest.mark.asyncio
    async def test_channel_locks_exist(self):
        """Test that per-channel locks are created."""
        relay = RelayManager()
        await relay.start()

        # Publish to create channel
        await relay.publish("test_channel", {"result": "test"})

        # Check that lock exists for the channel
        assert "test_channel" in relay._channel_locks
        assert hasattr(relay._channel_locks["test_channel"], 'acquire')

        await relay.stop()

    @pytest.mark.asyncio
    async def test_atomic_publish_operations(self):
        """Test that all publish operations happen atomically."""
        relay = RelayManager()
        await relay.start()

        received_count = 0

        async def counting_subscriber(data):
            nonlocal received_count
            received_count += 1

        await relay.subscribe("test_channel", counting_subscriber)

        # Publish multiple messages concurrently
        await asyncio.gather(*[
            relay.publish("test_channel", {"result": i})
            for i in range(20)
        ])

        await asyncio.sleep(0.1)

        # All messages should be received
        assert received_count == 20

        # Channel should have messages (may be truncated to maxlen)
        assert len(relay.channels["test_channel"]) <= 20

        await relay.stop()


class TestSubscriberErrorTracking:
    """Test that subscriber errors are tracked, not swallowed."""

    @pytest.mark.asyncio
    async def test_subscriber_errors_tracked(self):
        """Test that subscriber errors are tracked."""
        relay = RelayManager()
        await relay.start()

        async def failing_subscriber(data):
            raise ValueError("Test subscriber error")

        await relay.subscribe("test_channel", failing_subscriber)
        await relay.publish("test_channel", {"result": "test"})

        await asyncio.sleep(0.1)

        # Check that error was tracked
        errors = relay.get_subscriber_errors()
        assert len(errors) == 1
        assert errors[0]['error_type'] == 'ValueError'
        assert 'Test subscriber error' in errors[0]['error']

        await relay.stop()

    @pytest.mark.asyncio
    async def test_error_tracking_has_details(self):
        """Test that error tracking includes useful details."""
        relay = RelayManager()
        await relay.start()

        async def failing_subscriber(data):
            raise RuntimeError("Detailed error message")

        await relay.subscribe("test_channel", failing_subscriber)
        await relay.publish("test_channel", {"result": {"data": "test"}})

        await asyncio.sleep(0.1)

        errors = relay.get_subscriber_errors()
        assert len(errors) == 1

        error = errors[0]
        assert 'callback' in error
        assert 'error' in error
        assert 'error_type' in error
        assert 'timestamp' in error
        assert 'data_preview' in error

        assert error['error_type'] == 'RuntimeError'
        assert 'Detailed error message' in error['error']

        await relay.stop()

    @pytest.mark.asyncio
    async def test_other_subscribers_continue_on_error(self):
        """Test that one subscriber error doesn't affect others."""
        relay = RelayManager()
        await relay.start()

        successful_calls = []

        async def failing_subscriber(data):
            raise ValueError("I fail")

        async def successful_subscriber(data):
            successful_calls.append(data)

        await relay.subscribe("test_channel", failing_subscriber)
        await relay.subscribe("test_channel", successful_subscriber)

        await relay.publish("test_channel", {"result": "test"})

        await asyncio.sleep(0.1)

        # Successful subscriber should still receive message
        assert len(successful_calls) == 1

        # Error should be tracked
        errors = relay.get_subscriber_errors()
        assert len(errors) == 1

        await relay.stop()

    def test_get_subscriber_errors_limit(self):
        """Test that get_subscriber_errors respects limit."""
        relay = RelayManager()

        # Manually add errors
        for i in range(20):
            relay.subscriber_errors.append({
                'error': f'Error {i}',
                'timestamp': time.time()
            })

        # Get limited errors
        errors = relay.get_subscriber_errors(limit=5)
        assert len(errors) == 5

        # Should be most recent
        assert 'Error 19' in errors[-1]['error']


class TestUnboundedSubscriptionList:
    """Test that subscription lists don't grow unbounded."""

    def test_duplicate_connections_prevented(self):
        """Test that duplicate connections are prevented."""
        workflow = Workflow("Test Workflow")

        # Create mock agents
        class MockAgent:
            async def start(self): pass
            async def stop(self): pass
            async def process(self, task, data, context): pass

        workflow.add_agent("agent1", MockAgent())
        workflow.add_agent("agent2", MockAgent())

        # Connect agents
        workflow.connect("agent1", "channel", "agent2")
        assert len(workflow.connections) == 1

        # Try to create duplicate connection
        workflow.connect("agent1", "channel", "agent2")

        # Should still only have one connection
        assert len(workflow.connections) == 1

    def test_remove_agent_cleans_connections(self):
        """Test that removing agent cleans up connections."""
        workflow = Workflow("Test Workflow")

        class MockAgent:
            async def start(self): pass
            async def stop(self): pass
            async def process(self, task, data, context): pass

        workflow.add_agent("agent1", MockAgent())
        workflow.add_agent("agent2", MockAgent())
        workflow.add_agent("agent3", MockAgent())

        # Create connections
        workflow.connect("agent1", "channel1", "agent2")
        workflow.connect("agent2", "channel2", "agent3")

        assert len(workflow.connections) == 2

        # Remove agent2
        result = workflow.remove_agent("agent2")

        assert result is True
        assert len(workflow.connections) == 0  # Both connections removed

    @pytest.mark.asyncio
    async def test_subscriptions_cleaned_on_stop(self):
        """Test that subscriptions are cleaned up when workflow stops."""
        workflow = Workflow("Test Workflow")

        class MockAgent:
            async def start(self): pass
            async def stop(self): pass
            async def process(self, task, data, context): pass

        workflow.add_agent("agent1", MockAgent())
        workflow.add_agent("agent2", MockAgent())
        workflow.connect("agent1", "channel", "agent2")

        await workflow.start()

        # Subscriptions should exist
        assert len(workflow._subscriptions) == 1

        await workflow.stop()

        # Subscriptions should be cleaned up
        assert len(workflow._subscriptions) == 0


class TestCircuitBreakerRemoval:
    """Test that circuit breaker has been removed from configuration."""

    def test_no_circuit_breaker_in_reliability_config(self):
        """Test that circuit_breaker not in ReliabilityConfig."""
        config = ReliabilityConfig()
        assert not hasattr(config, 'circuit_breaker')

    def test_configure_reliability_no_circuit_breaker_param(self):
        """Test that configure_reliability doesn't accept circuit_breaker."""
        workflow = Workflow("Test")

        # Should work without circuit_breaker parameter
        workflow.configure_reliability(
            acknowledgments=True,
            task_tracking=True,
            backpressure_control=True
        )

        assert workflow.reliability_config is not None

    def test_presets_work_without_circuit_breaker(self):
        """Test that reliability presets work without circuit_breaker."""
        workflow = Workflow("Test")

        # Test all presets
        for preset in ["basic", "production", "enterprise"]:
            workflow.configure_reliability(preset=preset)
            assert workflow.reliability_config is not None
            assert not hasattr(workflow.reliability_config, 'circuit_breaker')

    def test_no_circuit_breaker_in_stats(self):
        """Test that circuit_breaker doesn't appear in stats."""
        workflow = Workflow("Test")
        workflow.configure_reliability(preset="production")

        stats = workflow.get_stats()

        if 'reliability_config' in stats:
            assert 'circuit_breaker' not in stats['reliability_config']


class TestIntegrationScenarios:
    """Integration tests for all fixes together."""

    @pytest.mark.asyncio
    async def test_complete_reliable_workflow(self):
        """Test a complete workflow with reliability features."""
        workflow = Workflow("Test Workflow")

        processed_data = []

        class MockAgent:
            def __init__(self, name):
                self.name = name

            async def start(self):
                pass

            async def stop(self):
                pass

            async def process(self, task, data, context):
                processed_data.append({
                    'agent': self.name,
                    'task': task,
                    'data': data
                })
                return {
                    'status': 'success',
                    'result': f'{self.name} processed {task}',
                    'agent_id': self.name
                }

        workflow.add_agent("agent1", MockAgent("agent1"))
        workflow.add_agent("agent2", MockAgent("agent2"))
        workflow.connect("agent1", "channel", "agent2")

        # Configure reliability without deprecated features
        workflow.configure_reliability(
            acknowledgments=True,
            task_tracking=True,
            backpressure_control=True
        )

        await workflow.start()

        # Inject data
        await workflow.inject_data("agent1", {"test": "data"}, task="process")

        await asyncio.sleep(0.2)

        # Verify processing happened
        assert len(processed_data) >= 1

        # Check stats don't include removed features
        stats = workflow.get_stats()
        if 'reliability_config' in stats:
            assert 'dead_letter_queue' not in stats['reliability_config']
            assert 'circuit_breaker' not in stats['reliability_config']

        await workflow.stop()

    @pytest.mark.asyncio
    async def test_error_handling_without_dlq(self):
        """Test that errors are handled properly without DLQ."""
        relay = RelayManager(enable_reliability=False)  # Use non-reliable for error tracking test
        await relay.start()

        error_count = 0

        async def failing_handler(data):
            nonlocal error_count
            error_count += 1
            raise ValueError(f"Error {error_count}")

        await relay.subscribe("test_channel", failing_handler)

        await relay.publish(
            "test_channel",
            {"result": "test"}
        )

        await asyncio.sleep(0.1)

        # Error should be tracked in subscriber_errors
        errors = relay.get_subscriber_errors()
        assert len(errors) > 0
        assert 'ValueError' in str(errors[0]['error_type'])

        # Message should not be in DLQ (doesn't exist)
        assert not hasattr(relay, 'dead_letter_queue')

        await relay.stop()

    @pytest.mark.asyncio
    async def test_concurrent_operations_with_fixes(self):
        """Test concurrent operations with all fixes in place."""
        relay = RelayManager(enable_reliability=True)
        await relay.start()

        received_messages = []

        async def subscriber(data, message_id=None):
            received_messages.append(data)
            if message_id:
                await relay.ack_message(message_id)

        await relay.subscribe("test_channel", subscriber)

        # Publish many messages concurrently
        message_ids = await asyncio.gather(*[
            relay.publish("test_channel", {"result": i}, require_ack=True)
            for i in range(50)
        ])

        await asyncio.sleep(0.2)

        # Check that messages were received
        assert len(received_messages) > 0

        # Check that retry jitter is working (delays should vary)
        if hasattr(relay, '_calculate_retry_delay'):
            delays = [relay._calculate_retry_delay(1) for _ in range(10)]
            assert len(set(delays)) > 5  # Should have variety

        await relay.stop()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])

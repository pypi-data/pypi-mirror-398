"""
Test relay API simplification - both old and new APIs should work.

Verifies:
1. New API: relay.publish(channel, raw_data) works
2. Old API: relay.publish(channel, {"result": data}) still works (backward compat)
3. Both produce the same result
"""
import pytest
import asyncio
from daita.core.relay import RelayManager


class TestRelayAPISimplification:
    """Test that relay.publish() accepts both raw data and agent response dicts."""

    @pytest.mark.asyncio
    async def test_new_api_raw_data_list(self):
        """Test publishing raw list data (new API)."""
        relay = RelayManager()
        await relay.start()

        received = []

        async def subscriber(data, metadata=None):
            received.append(data)

        await relay.subscribe("test_channel", subscriber)

        # NEW API: Just publish the list directly!
        raw_data = [1, 2, 3, 4, 5]
        await relay.publish("test_channel", raw_data, publisher="TestPublisher")

        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0] == [1, 2, 3, 4, 5]

        await relay.stop()

    @pytest.mark.asyncio
    async def test_new_api_raw_data_dict(self):
        """Test publishing raw dict data without 'result' field (new API)."""
        relay = RelayManager()
        await relay.start()

        received = []

        async def subscriber(data, metadata=None):
            received.append(data)

        await relay.subscribe("test_channel", subscriber)

        # NEW API: Publish a dict that doesn't have 'result' field
        raw_data = {"name": "Alice", "age": 30, "city": "NYC"}
        await relay.publish("test_channel", raw_data, publisher="TestPublisher")

        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0] == {"name": "Alice", "age": 30, "city": "NYC"}

        await relay.stop()

    @pytest.mark.asyncio
    async def test_new_api_raw_data_string(self):
        """Test publishing raw string data (new API)."""
        relay = RelayManager()
        await relay.start()

        received = []

        async def subscriber(data, metadata=None):
            received.append(data)

        await relay.subscribe("test_channel", subscriber)

        # NEW API: Publish a string directly!
        await relay.publish("test_channel", "Hello, World!", publisher="TestPublisher")

        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0] == "Hello, World!"

        await relay.stop()

    @pytest.mark.asyncio
    async def test_old_api_agent_response_dict(self):
        """Test publishing agent response dict with 'result' field (old API - backward compat)."""
        relay = RelayManager()
        await relay.start()

        received = []

        async def subscriber(data, metadata=None):
            received.append(data)

        await relay.subscribe("test_channel", subscriber)

        # OLD API: Publish agent response with 'result' field
        agent_response = {
            "result": {"sales": 1000, "region": "North"},
            "status": "success",
            "agent_id": "test_agent",
            "processing_time_ms": 123.45
        }
        await relay.publish("test_channel", agent_response, publisher="TestAgent")

        await asyncio.sleep(0.1)

        # Should extract just the 'result' field
        assert len(received) == 1
        assert received[0] == {"sales": 1000, "region": "North"}

        await relay.stop()

    @pytest.mark.asyncio
    async def test_backward_compatibility_both_apis_work(self):
        """Test that both old and new APIs work side by side."""
        relay = RelayManager()
        await relay.start()

        received = []

        async def subscriber(data, metadata=None):
            received.append(data)

        await relay.subscribe("test_channel", subscriber)

        # NEW API: Raw data
        await relay.publish("test_channel", [1, 2, 3], publisher="NewAPI")

        # OLD API: Agent response dict
        await relay.publish("test_channel", {"result": [4, 5, 6]}, publisher="OldAPI")

        # NEW API: Raw dict without 'result'
        await relay.publish("test_channel", {"value": 100}, publisher="NewAPI2")

        await asyncio.sleep(0.1)

        # All three should be received
        assert len(received) == 3
        assert received[0] == [1, 2, 3]
        assert received[1] == [4, 5, 6]  # Extracted from 'result'
        assert received[2] == {"value": 100}

        await relay.stop()

    @pytest.mark.asyncio
    async def test_metadata_propagation_with_old_api(self):
        """Test that metadata is properly extracted from agent response (old API)."""
        relay = RelayManager()
        await relay.start()

        received_metadata = []

        async def subscriber(data, metadata=None):
            received_metadata.append(metadata)

        await relay.subscribe("test_channel", subscriber)

        # OLD API with metadata
        agent_response = {
            "result": {"data": "test"},
            "status": "success",
            "agent_id": "test_agent_123",
            "agent_name": "TestAgent",
            "tool_calls": ["tool1", "tool2"],
            "correlation_id": "corr-123"
        }
        await relay.publish("test_channel", agent_response, publisher="TestAgent")

        await asyncio.sleep(0.1)

        assert len(received_metadata) == 1
        metadata = received_metadata[0]

        # Should have extracted metadata from agent response
        assert metadata["upstream_agent_id"] == "test_agent_123"
        assert metadata["upstream_agent"] == "TestAgent"
        assert metadata["status"] == "success"
        assert metadata["correlation_id"] == "corr-123"

        await relay.stop()

    @pytest.mark.asyncio
    async def test_metadata_creation_with_new_api(self):
        """Test that minimal metadata is created for raw data (new API)."""
        relay = RelayManager()
        await relay.start()

        received_metadata = []

        async def subscriber(data, metadata=None):
            received_metadata.append(metadata)

        await relay.subscribe("test_channel", subscriber)

        # NEW API - raw data
        await relay.publish("test_channel", [1, 2, 3], publisher="TestPublisher")

        await asyncio.sleep(0.1)

        assert len(received_metadata) == 1
        metadata = received_metadata[0]

        # Should have minimal metadata
        assert metadata["publisher"] == "TestPublisher"
        assert "timestamp" in metadata
        assert "correlation_id" in metadata
        assert metadata["status"] == "success"

        await relay.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

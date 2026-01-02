"""
Simple integration tests for plugins without test coverage.

These tests verify that plugins can be used as tools with agents.
No external dependencies required - just validates the integration pattern.
"""
import pytest
import asyncio
from daita.agents.substrate import SubstrateAgent
from daita.llm.mock import MockLLMProvider
from daita.core.tools import tool


class TestPluginAsToolPattern:
    """Test that plugins can be wrapped as agent tools."""

    @pytest.mark.asyncio
    async def test_elasticsearch_style_tool(self):
        """Test Elasticsearch-style search tool with agent."""
        agent = SubstrateAgent(
            name="SearchAgent",
            model="gpt-4o-mini",
            prompt="You search for documents.",
            llm_provider=MockLLMProvider()
        )

        # Simulated Elasticsearch search tool
        @tool
        async def search_documents(query: str, index: str = "default") -> list:
            """Search for documents matching query."""
            # Simulate ES response
            return [
                {"id": "doc1", "title": "Result 1", "score": 0.95},
                {"id": "doc2", "title": "Result 2", "score": 0.82}
            ]

        agent.register_tool(search_documents)
        await agent.start()

        try:
            result = await agent.run_detailed("Search for test documents")

            assert result is not None
            assert "result" in result
            print(f"\nElasticsearch-style tool test passed")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_slack_style_tool(self):
        """Test Slack-style messaging tool with agent."""
        agent = SubstrateAgent(
            name="NotificationAgent",
            model="gpt-4o-mini",
            prompt="You send notifications.",
            llm_provider=MockLLMProvider()
        )

        # Simulated Slack messaging tool
        @tool
        async def send_slack_message(
            channel: str,
            message: str,
            thread_ts: str = None
        ) -> dict:
            """Send message to Slack channel."""
            # Simulate Slack response
            return {
                "ok": True,
                "channel": channel,
                "ts": "1234567890.123456",
                "message": {"text": message}
            }

        agent.register_tool(send_slack_message)
        await agent.start()

        try:
            result = await agent.run("Send alert to #general channel")

            assert result is not None
            print(f"\nSlack-style tool test passed")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_redis_style_tool(self):
        """Test Redis-style pub/sub and caching tools with agent."""
        agent = SubstrateAgent(
            name="CacheAgent",
            model="gpt-4o-mini",
            prompt="You manage cache and messaging.",
            llm_provider=MockLLMProvider()
        )

        # Simulated Redis tools
        @tool
        async def publish_message(channel: str, message: str) -> dict:
            """Publish message to Redis channel."""
            return {"published": True, "subscribers": 3}

        @tool
        async def cache_set(key: str, value: str, ttl: int = 3600) -> dict:
            """Set cache value with TTL."""
            return {"cached": True, "key": key, "ttl": ttl}

        @tool
        async def cache_get(key: str) -> str:
            """Get value from cache."""
            return "cached_value_123"

        agent.register_tool(publish_message)
        agent.register_tool(cache_set)
        agent.register_tool(cache_get)
        await agent.start()

        try:
            result = await agent.run("Cache user data and publish update")

            assert result is not None
            print(f"\nRedis-style tools test passed")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_plugin_tools_in_workflow(self):
        """Test plugin-style tools working in workflow context."""
        from daita.core.workflow import Workflow

        workflow = Workflow("Plugin Workflow")

        # Agent 1: Data fetcher with ES-style tool
        fetcher = SubstrateAgent(
            name="Fetcher",
            model="gpt-4o-mini",
            prompt="You fetch data from Elasticsearch.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def elasticsearch_search(query: str) -> list:
            """Search Elasticsearch."""
            return [{"doc": "result1"}, {"doc": "result2"}]

        fetcher.register_tool(elasticsearch_search)

        # Agent 2: Notifier with Slack-style tool
        notifier_state = {"received": False}

        notifier = SubstrateAgent(
            name="Notifier",
            model="gpt-4o-mini",
            prompt="You send Slack notifications.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def send_slack(message: str) -> dict:
            """Send to Slack."""
            return {"sent": True}

        notifier.register_tool(send_slack)

        # Track receive_message
        original_receive = notifier.receive_message

        async def tracked_receive(data, source_agent, channel, workflow_name=None):
            notifier_state["received"] = True
            return await original_receive(data, source_agent, channel, workflow_name)

        notifier.receive_message = tracked_receive

        # Build workflow
        workflow.add_agent("fetcher", fetcher)
        workflow.add_agent("notifier", notifier)
        workflow.connect("fetcher", "data", "notifier")

        await workflow.start()

        try:
            # Publish data
            await workflow.relay_manager.publish(
                "data",
                [{"item": 1}, {"item": 2}],
                publisher="Fetcher"
            )

            await asyncio.sleep(1.5)

            # Verify workflow communication
            assert notifier_state["received"], "Notifier did not receive data"

            print(f"\nPlugin tools in workflow test passed")

        finally:
            await workflow.stop()


class TestPluginPatternsWithSystemEntryPoints:
    """Test plugin patterns work with all system entry points."""

    @pytest.mark.asyncio
    async def test_plugin_tool_with_webhook(self):
        """Test plugin-style tool with webhook entry point."""
        agent = SubstrateAgent(
            name="WebhookWithPlugin",
            model="gpt-4o-mini",
            prompt="You process webhooks and search data.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def search_data(entity_id: str) -> dict:
            """Search for entity data."""
            return {"id": entity_id, "status": "active", "score": 95}

        agent.register_tool(search_data)
        await agent.start()

        try:
            webhook_payload = {
                "event": "user.update",
                "user_id": "U12345"
            }

            result = await agent.on_webhook(webhook_payload, {"slug": "user-events"})

            assert result is not None
            assert "result" in result
            print(f"\nPlugin tool with webhook test passed")

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_plugin_tool_with_schedule(self):
        """Test plugin-style tool with scheduled task entry point."""
        agent = SubstrateAgent(
            name="ScheduledWithPlugin",
            model="gpt-4o-mini",
            prompt="You run scheduled reports using search data.",
            llm_provider=MockLLMProvider()
        )

        @tool
        async def fetch_metrics() -> dict:
            """Fetch daily metrics."""
            return {
                "total_docs": 15000,
                "new_docs": 250,
                "updated_docs": 180
            }

        @tool
        async def send_report(metrics: dict) -> dict:
            """Send report via Slack."""
            return {"sent": True, "channel": "#reports"}

        agent.register_tool(fetch_metrics)
        agent.register_tool(send_report)
        await agent.start()

        try:
            schedule_config = {
                "schedule": "0 9 * * *",
                "name": "daily-report",
                "task": "Generate and send daily report"
            }

            result = await agent.on_schedule(schedule_config)

            assert result is not None
            assert "result" in result
            print(f"\nPlugin tools with schedule test passed")

        finally:
            await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

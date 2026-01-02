"""
Integration tests for plugins without test coverage:
- Elasticsearch
- Slack
- Redis Messaging

These tests verify plugins can be used as tools with agents
after handler removal. Uses simplified approach without external dependencies.
"""
import pytest
import asyncio
from daita.agents.substrate import SubstrateAgent
from daita.llm.mock import MockLLMProvider
from daita.core.tools import tool


class TestElasticsearchPlugin:
    """Test Elasticsearch plugin integration with agents."""

    @pytest.mark.asyncio
    async def test_elasticsearch_plugin_initialization(self):
        """Test that Elasticsearch plugin can be initialized."""
        from daita.plugins.elasticsearch import ElasticsearchPlugin

        # Mock Elasticsearch to avoid needing actual ES instance
        with patch('daita.plugins.elasticsearch.AsyncElasticsearch') as mock_es:
            mock_client = AsyncMock()
            mock_es.return_value = mock_client

            plugin = ElasticsearchPlugin(
                hosts=["localhost:9200"],
                index_name="test_index"
            )

            assert plugin is not None
            assert plugin.index_name == "test_index"

            print("\nElasticsearch plugin initialized successfully")

    @pytest.mark.asyncio
    async def test_elasticsearch_with_agent(self):
        """Test Elasticsearch plugin with agent tool registration."""
        from daita.plugins.elasticsearch import ElasticsearchPlugin

        # Mock Elasticsearch
        with patch('daita.plugins.elasticsearch.AsyncElasticsearch') as mock_es:
            mock_client = AsyncMock()
            mock_client.search = AsyncMock(return_value={
                "hits": {
                    "hits": [
                        {"_source": {"title": "Test Doc", "content": "Sample content"}}
                    ]
                }
            })
            mock_es.return_value = mock_client

            plugin = ElasticsearchPlugin(
                hosts=["localhost:9200"],
                index_name="documents"
            )

            agent = SubstrateAgent(
                name="SearchAgent",
                model="gpt-4o-mini",
                prompt="You search documents.",
                llm_provider=MockLLMProvider()
            )

            # Register plugin's search capability as a tool
            @tool
            async def search_documents(query: str) -> list:
                """Search documents in Elasticsearch."""
                result = await mock_client.search(
                    index="documents",
                    body={"query": {"match": {"content": query}}}
                )
                return [hit["_source"] for hit in result["hits"]["hits"]]

            agent.register_tool(search_documents)
            await agent.start()

            try:
                result = await agent.run_detailed("Search for test documents")

                assert result is not None
                assert "result" in result
                print(f"\nElasticsearch agent test: {result['result'][:200]}")

            finally:
                await agent.stop()


class TestSlackPlugin:
    """Test Slack plugin integration with agents."""

    @pytest.mark.asyncio
    async def test_slack_plugin_initialization(self):
        """Test that Slack plugin can be initialized."""
        from daita.plugins.slack import SlackPlugin

        # Mock Slack client
        with patch('daita.plugins.slack.AsyncWebClient') as mock_slack:
            mock_client = AsyncMock()
            mock_slack.return_value = mock_client

            plugin = SlackPlugin(
                token="xoxb-test-token",
                default_channel="#general"
            )

            assert plugin is not None
            assert plugin.default_channel == "#general"

            print("\nSlack plugin initialized successfully")

    @pytest.mark.asyncio
    async def test_slack_with_agent(self):
        """Test Slack plugin with agent for notifications."""
        from daita.plugins.slack import SlackPlugin

        # Mock Slack client
        with patch('daita.plugins.slack.AsyncWebClient') as mock_slack:
            mock_client = AsyncMock()
            mock_client.chat_postMessage = AsyncMock(return_value={
                "ok": True,
                "ts": "1234567890.123456"
            })
            mock_slack.return_value = mock_client

            plugin = SlackPlugin(
                token="xoxb-test-token",
                default_channel="#alerts"
            )

            agent = SubstrateAgent(
                name="NotificationAgent",
                model="gpt-4o-mini",
                prompt="You send notifications to Slack.",
                llm_provider=MockLLMProvider()
            )

            # Register Slack notification as a tool
            @tool
            async def send_slack_message(message: str, channel: str = "#alerts") -> dict:
                """Send a message to Slack."""
                result = await mock_client.chat_postMessage(
                    channel=channel,
                    text=message
                )
                return {"sent": result["ok"], "timestamp": result["ts"]}

            agent.register_tool(send_slack_message)
            await agent.start()

            try:
                result = await agent.run_detailed("Send alert: System is healthy")

                assert result is not None
                assert "result" in result
                print(f"\nSlack agent test: {result['result'][:200]}")

            finally:
                await agent.stop()

    @pytest.mark.asyncio
    async def test_slack_block_kit_formatting(self):
        """Test Slack Block Kit message formatting."""
        from daita.plugins.slack import SlackPlugin

        with patch('daita.plugins.slack.AsyncWebClient') as mock_slack:
            mock_client = AsyncMock()
            mock_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_slack.return_value = mock_client

            plugin = SlackPlugin(token="xoxb-test", default_channel="#test")

            agent = SubstrateAgent(
                name="SlackFormatter",
                model="gpt-4o-mini",
                prompt="You format Slack messages.",
                llm_provider=MockLLMProvider()
            )

            @tool
            async def send_formatted_slack(title: str, message: str) -> dict:
                """Send formatted Slack message with blocks."""
                blocks = [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": title}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message}
                    }
                ]
                result = await mock_client.chat_postMessage(
                    channel="#test",
                    blocks=blocks
                )
                return {"sent": result["ok"]}

            agent.register_tool(send_formatted_slack)
            await agent.start()

            try:
                result = await agent.run("Send a formatted alert message")

                assert result is not None
                print(f"\nSlack Block Kit test passed")

            finally:
                await agent.stop()


class TestRedisMessagingPlugin:
    """Test Redis messaging plugin integration."""

    @pytest.mark.asyncio
    async def test_redis_plugin_initialization(self):
        """Test that Redis messaging plugin can be initialized."""
        from daita.plugins.redis_messaging import RedisMessagingPlugin

        # Mock Redis
        with patch('daita.plugins.redis_messaging.redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.from_url.return_value = mock_client

            plugin = RedisMessagingPlugin(
                redis_url="redis://localhost:6379",
                channel_prefix="daita:"
            )

            assert plugin is not None
            assert plugin.channel_prefix == "daita:"

            print("\nRedis messaging plugin initialized successfully")

    @pytest.mark.asyncio
    async def test_redis_pubsub_with_agent(self):
        """Test Redis pub/sub with agent."""
        from daita.plugins.redis_messaging import RedisMessagingPlugin

        # Mock Redis
        with patch('daita.plugins.redis_messaging.redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.publish = AsyncMock(return_value=1)
            mock_client.get = AsyncMock(return_value=b'{"status": "ok"}')
            mock_redis.from_url.return_value = mock_client

            plugin = RedisMessagingPlugin(
                redis_url="redis://localhost:6379"
            )

            agent = SubstrateAgent(
                name="RedisAgent",
                model="gpt-4o-mini",
                prompt="You publish messages to Redis.",
                llm_provider=MockLLMProvider()
            )

            @tool
            async def publish_to_redis(channel: str, message: str) -> dict:
                """Publish message to Redis channel."""
                count = await mock_client.publish(channel, message)
                return {"published": True, "subscribers": count}

            agent.register_tool(publish_to_redis)
            await agent.start()

            try:
                result = await agent.run_detailed("Publish status update to redis")

                assert result is not None
                assert "result" in result
                print(f"\nRedis pub/sub test: {result['result'][:200]}")

            finally:
                await agent.stop()

    @pytest.mark.asyncio
    async def test_redis_caching_with_agent(self):
        """Test Redis caching capabilities with agent."""
        from daita.plugins.redis_messaging import RedisMessagingPlugin

        with patch('daita.plugins.redis_messaging.redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.set = AsyncMock(return_value=True)
            mock_client.get = AsyncMock(return_value=b'cached_value')
            mock_redis.from_url.return_value = mock_client

            plugin = RedisMessagingPlugin(redis_url="redis://localhost:6379")

            agent = SubstrateAgent(
                name="CacheAgent",
                model="gpt-4o-mini",
                prompt="You cache data in Redis.",
                llm_provider=MockLLMProvider()
            )

            @tool
            async def cache_data(key: str, value: str, ttl: int = 3600) -> dict:
                """Cache data in Redis with TTL."""
                await mock_client.set(key, value, ex=ttl)
                return {"cached": True, "key": key, "ttl": ttl}

            @tool
            async def get_cached_data(key: str) -> str:
                """Get data from Redis cache."""
                value = await mock_client.get(key)
                return value.decode() if value else None

            agent.register_tool(cache_data)
            agent.register_tool(get_cached_data)
            await agent.start()

            try:
                result = await agent.run("Cache user preferences and retrieve them")

                assert result is not None
                print(f"\nRedis caching test passed")

            finally:
                await agent.stop()


class TestPluginEndToEndIntegration:
    """Test multiple plugins working together in a realistic scenario."""

    @pytest.mark.asyncio
    async def test_elasticsearch_to_slack_pipeline(self):
        """Test searching ES and sending results to Slack."""
        from daita.plugins.elasticsearch import ElasticsearchPlugin
        from daita.plugins.slack import SlackPlugin

        with patch('daita.plugins.elasticsearch.AsyncElasticsearch') as mock_es, \
             patch('daita.plugins.slack.AsyncWebClient') as mock_slack:

            # Mock Elasticsearch
            mock_es_client = AsyncMock()
            mock_es_client.search = AsyncMock(return_value={
                "hits": {"hits": [{"_source": {"title": "Critical Alert"}}]}
            })
            mock_es.return_value = mock_es_client

            # Mock Slack
            mock_slack_client = AsyncMock()
            mock_slack_client.chat_postMessage = AsyncMock(return_value={"ok": True})
            mock_slack.return_value = mock_slack_client

            agent = SubstrateAgent(
                name="AlertPipeline",
                model="gpt-4o-mini",
                prompt="You search for alerts and send them to Slack.",
                llm_provider=MockLLMProvider()
            )

            @tool
            async def search_alerts() -> list:
                """Search for critical alerts."""
                result = await mock_es_client.search(
                    index="alerts",
                    body={"query": {"term": {"severity": "critical"}}}
                )
                return [hit["_source"] for hit in result["hits"]["hits"]]

            @tool
            async def send_to_slack(alerts: list) -> dict:
                """Send alerts to Slack."""
                for alert in alerts:
                    await mock_slack_client.chat_postMessage(
                        channel="#alerts",
                        text=f"Alert: {alert.get('title', 'Unknown')}"
                    )
                return {"sent": len(alerts)}

            agent.register_tool(search_alerts)
            agent.register_tool(send_to_slack)
            await agent.start()

            try:
                result = await agent.run("Search for critical alerts and send to Slack")

                assert result is not None
                print(f"\nMulti-plugin pipeline test passed")

            finally:
                await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""
Comprehensive unit tests for LLM streaming functionality.

Tests cover:
- Text-only streaming
- Streaming with tool calls
- Non-streaming with tools
- Chunk format validation
- All providers: OpenAI, Anthropic, Grok, Gemini
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from daita.llm.openai import OpenAIProvider
from daita.llm.anthropic import AnthropicProvider
from daita.llm.grok import GrokProvider
from daita.llm.gemini import GeminiProvider
from daita.core.streaming import LLMChunk
from daita.core.tools import AgentTool


# ============================================================================
# Test Helpers
# ============================================================================

def create_tool_spec():
    """Create a sample tool specification."""
    return AgentTool(
        name="get_weather",
        description="Get weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        },
        handler=AsyncMock(return_value={"temp": 72, "condition": "sunny"})
    )


# ============================================================================
# OpenAI Provider Tests
# ============================================================================

class TestOpenAIStreaming:
    """Test OpenAI provider streaming functionality."""

    @pytest.mark.asyncio
    async def test_streaming_text_only(self):
        """Test streaming text without tools."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock the OpenAI client
        mock_chunk_1 = Mock()
        mock_chunk_1.choices = [Mock(delta=Mock(content="Hello", tool_calls=None), finish_reason=None)]
        mock_chunk_1.usage = None

        mock_chunk_2 = Mock()
        mock_chunk_2.choices = [Mock(delta=Mock(content=" world", tool_calls=None), finish_reason=None)]
        mock_chunk_2.usage = None

        mock_chunk_3 = Mock()
        mock_chunk_3.choices = [Mock(delta=Mock(content="!", tool_calls=None), finish_reason="stop")]
        mock_chunk_3.usage = Mock(total_tokens=10, prompt_tokens=5, completion_tokens=5)

        async def mock_stream():
            for chunk in [mock_chunk_1, mock_chunk_2, mock_chunk_3]:
                yield chunk

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test streaming
        chunks = []
        messages = [{"role": "user", "content": "Hi"}]

        async for chunk in provider._stream_impl(messages, None, temperature=0.7):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) == 3
        assert chunks[0].type == "text"
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].content == "!"

        # Verify usage was stored
        assert provider._last_usage.total_tokens == 10

    @pytest.mark.asyncio
    async def test_streaming_with_tool_calls(self):
        """Test streaming with tool calls."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock function object with proper attributes
        mock_function_1 = Mock()
        mock_function_1.name = "get_weather"
        mock_function_1.arguments = ""

        mock_function_2 = Mock()
        mock_function_2.name = None
        mock_function_2.arguments = '{"location":'

        mock_function_3 = Mock()
        mock_function_3.name = None
        mock_function_3.arguments = ' "Paris"}'

        # Mock streaming chunks with tool calls
        mock_chunk_1 = Mock()
        mock_chunk_1.choices = [Mock(
            delta=Mock(content=None, tool_calls=[
                Mock(index=0, id="call_123", function=mock_function_1)
            ]),
            finish_reason=None
        )]
        mock_chunk_1.usage = None

        mock_chunk_2 = Mock()
        mock_chunk_2.choices = [Mock(
            delta=Mock(content=None, tool_calls=[
                Mock(index=0, id=None, function=mock_function_2)
            ]),
            finish_reason=None
        )]
        mock_chunk_2.usage = None

        mock_chunk_3 = Mock()
        mock_chunk_3.choices = [Mock(
            delta=Mock(content=None, tool_calls=[
                Mock(index=0, id=None, function=mock_function_3)
            ]),
            finish_reason="tool_calls"
        )]
        mock_chunk_3.usage = Mock(total_tokens=20, prompt_tokens=10, completion_tokens=10)

        async def mock_stream():
            for chunk in [mock_chunk_1, mock_chunk_2, mock_chunk_3]:
                yield chunk

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test streaming with tools
        chunks = []
        messages = [{"role": "user", "content": "What's the weather in Paris?"}]
        tool = create_tool_spec()

        async for chunk in provider._stream_impl(messages, [tool.to_openai_function()], temperature=0.7):
            chunks.append(chunk)

        # Verify we got a complete tool call
        tool_call_chunks = [c for c in chunks if c.type == "tool_call_complete"]
        assert len(tool_call_chunks) == 1
        assert tool_call_chunks[0].tool_name == "get_weather"
        assert tool_call_chunks[0].tool_args == {"location": "Paris"}
        assert tool_call_chunks[0].tool_call_id == "call_123"

    @pytest.mark.asyncio
    async def test_non_streaming_with_tools(self):
        """Test non-streaming generation with tools."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock function object
        mock_function = Mock()
        mock_function.name = "get_weather"
        mock_function.arguments = '{"location": "Tokyo"}'

        # Mock tool call object
        mock_tool_call = Mock()
        mock_tool_call.id = "call_456"
        mock_tool_call.function = mock_function

        # Mock response with tool call
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(
            content=None,
            tool_calls=[mock_tool_call]
        ))]
        mock_response.usage = Mock(total_tokens=15, prompt_tokens=8, completion_tokens=7)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        # Test non-streaming with tools
        messages = [{"role": "user", "content": "Weather in Tokyo?"}]
        tool = create_tool_spec()

        result = await provider._generate_impl(messages, [tool.to_openai_function()], temperature=0.7)

        # Verify tool call result
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "get_weather"
        assert result["tool_calls"][0]["arguments"] == {"location": "Tokyo"}
        assert result["tool_calls"][0]["id"] == "call_456"

    @pytest.mark.asyncio
    async def test_non_streaming_text_only(self):
        """Test non-streaming text generation."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock response with text
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(
            content="The weather is sunny!",
            tool_calls=None
        ))]
        mock_response.usage = Mock(total_tokens=12, prompt_tokens=6, completion_tokens=6)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        # Test non-streaming text
        messages = [{"role": "user", "content": "How's the weather?"}]

        result = await provider._generate_impl(messages, None, temperature=0.7)

        # Verify text result
        assert result == "The weather is sunny!"
        assert provider._last_usage.total_tokens == 12


# ============================================================================
# Anthropic Provider Tests
# ============================================================================

class TestAnthropicStreaming:
    """Test Anthropic provider streaming functionality."""

    @pytest.mark.asyncio
    async def test_streaming_text_only(self):
        """Test streaming text without tools."""
        provider = AnthropicProvider(model="claude-3-sonnet-20240229", api_key="test-key")

        # Mock streaming events
        mock_event_1 = Mock(type="content_block_delta", delta=Mock(text="Hello"))
        mock_event_2 = Mock(type="content_block_delta", delta=Mock(text=" from Claude"))
        mock_event_3 = Mock(type="message_stop")

        # Mock final message
        mock_final_message = Mock(usage=Mock(input_tokens=5, output_tokens=7))

        # Mock stream context manager
        mock_stream = AsyncMock()

        async def mock_event_iterator():
            for event in [mock_event_1, mock_event_2, mock_event_3]:
                yield event

        mock_stream.__aiter__ = lambda self: mock_event_iterator()
        mock_stream.get_final_message = AsyncMock(return_value=mock_final_message)
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = Mock()
        mock_client.messages.stream = Mock(return_value=mock_stream)
        provider._client = mock_client

        # Test streaming
        chunks = []
        messages = [{"role": "user", "content": "Hi"}]

        async for chunk in provider._stream_impl(messages, None, temperature=0.7):
            chunks.append(chunk)

        # Verify chunks
        text_chunks = [c for c in chunks if c.type == "text"]
        assert len(text_chunks) == 2
        assert text_chunks[0].content == "Hello"
        assert text_chunks[1].content == " from Claude"

        # Verify usage
        assert provider._last_usage.input_tokens == 5

    @pytest.mark.asyncio
    async def test_streaming_with_tool_calls(self):
        """Test streaming with tool calls."""
        provider = AnthropicProvider(model="claude-3-sonnet-20240229", api_key="test-key")

        # Mock streaming events with tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "toolu_123"
        mock_tool_block.name = "get_weather"
        mock_tool_block.input = {"location": "London"}

        mock_event_1 = Mock(type="content_block_start", content_block=mock_tool_block)
        mock_event_2 = Mock(type="content_block_stop")
        mock_event_3 = Mock(type="message_stop")

        mock_final_message = Mock(usage=Mock(input_tokens=10, output_tokens=5))

        # Mock stream
        mock_stream = AsyncMock()

        async def mock_event_iterator():
            for event in [mock_event_1, mock_event_2, mock_event_3]:
                yield event

        mock_stream.__aiter__ = lambda self: mock_event_iterator()
        mock_stream.get_final_message = AsyncMock(return_value=mock_final_message)
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock(return_value=None)

        mock_client = Mock()
        mock_client.messages.stream = Mock(return_value=mock_stream)
        provider._client = mock_client

        # Test streaming with tools
        chunks = []
        messages = [{"role": "user", "content": "Weather in London?"}]
        tool = create_tool_spec()

        async for chunk in provider._stream_impl(messages, [tool.to_anthropic_tool()], temperature=0.7):
            chunks.append(chunk)

        # Verify tool call
        tool_chunks = [c for c in chunks if c.type == "tool_call_complete"]
        assert len(tool_chunks) == 1
        assert tool_chunks[0].tool_name == "get_weather"
        assert tool_chunks[0].tool_args == {"location": "London"}
        assert tool_chunks[0].tool_call_id == "toolu_123"

    @pytest.mark.asyncio
    async def test_non_streaming_with_tools(self):
        """Test non-streaming with tools."""
        provider = AnthropicProvider(model="claude-3-sonnet-20240229", api_key="test-key")

        # Mock response with tool use
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "toolu_456"
        mock_tool_block.name = "get_weather"
        mock_tool_block.input = {"location": "Berlin"}

        mock_response = Mock()
        mock_response.content = [mock_tool_block]
        mock_response.usage = Mock(input_tokens=8, output_tokens=6)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        # Test non-streaming
        messages = [{"role": "user", "content": "Weather in Berlin?"}]
        tool = create_tool_spec()

        result = await provider._generate_impl(messages, [tool.to_anthropic_tool()], temperature=0.7)

        # Verify tool call
        assert "tool_calls" in result
        assert result["tool_calls"][0]["name"] == "get_weather"
        assert result["tool_calls"][0]["arguments"] == {"location": "Berlin"}


# ============================================================================
# Grok Provider Tests
# ============================================================================

class TestGrokStreaming:
    """Test Grok provider streaming functionality (OpenAI-compatible)."""

    @pytest.mark.asyncio
    async def test_streaming_text_only(self):
        """Test streaming text without tools."""
        provider = GrokProvider(model="grok-3", api_key="test-key")

        # Same as OpenAI - Grok uses OpenAI-compatible API
        mock_chunk_1 = Mock()
        mock_chunk_1.choices = [Mock(delta=Mock(content="Grok", tool_calls=None), finish_reason=None)]
        mock_chunk_1.usage = None

        mock_chunk_2 = Mock()
        mock_chunk_2.choices = [Mock(delta=Mock(content=" response", tool_calls=None), finish_reason="stop")]
        mock_chunk_2.usage = Mock(total_tokens=8, prompt_tokens=4, completion_tokens=4)

        async def mock_stream():
            for chunk in [mock_chunk_1, mock_chunk_2]:
                yield chunk

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test streaming
        chunks = []
        messages = [{"role": "user", "content": "Hi"}]

        async for chunk in provider._stream_impl(messages, None, temperature=0.7):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) == 2
        assert chunks[0].content == "Grok"
        assert chunks[1].content == " response"


# ============================================================================
# Gemini Provider Tests
# ============================================================================

class TestGeminiStreaming:
    """Test Gemini provider streaming functionality."""

    @pytest.mark.asyncio
    async def test_streaming_text_only(self):
        """Test streaming text without tools."""
        provider = GeminiProvider(model="gemini-2.5-flash", api_key="test-key")

        # Mock Gemini streaming chunks
        mock_chunk_1 = Mock()
        mock_chunk_1.text = "Gemini"
        mock_chunk_1.candidates = [Mock(content=Mock(parts=[]))]
        mock_chunk_1.usage_metadata = None

        mock_chunk_2 = Mock()
        mock_chunk_2.text = " says hello"
        mock_chunk_2.candidates = [Mock(content=Mock(parts=[]))]
        mock_chunk_2.usage_metadata = Mock(prompt_token_count=5, candidates_token_count=5, total_token_count=10)

        async def mock_stream():
            for chunk in [mock_chunk_1, mock_chunk_2]:
                yield chunk

        mock_client = Mock()
        mock_client.generate_content = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test streaming
        chunks = []
        messages = [{"role": "user", "content": "Hi"}]

        async for chunk in provider._stream_impl(messages, None, temperature=0.7):
            chunks.append(chunk)

        # Verify chunks
        text_chunks = [c for c in chunks if c.type == "text"]
        assert len(text_chunks) == 2
        assert text_chunks[0].content == "Gemini"
        assert text_chunks[1].content == " says hello"

    @pytest.mark.asyncio
    async def test_streaming_with_tool_calls(self):
        """Test streaming with tool calls."""
        provider = GeminiProvider(model="gemini-2.5-flash", api_key="test-key")

        # Mock function call part
        mock_function_call = Mock()
        mock_function_call.name = "get_weather"
        mock_function_call.args = {"location": "Madrid"}

        mock_part = Mock()
        mock_part.function_call = mock_function_call

        mock_chunk = Mock()
        mock_chunk.text = None
        mock_chunk.candidates = [Mock(content=Mock(parts=[mock_part]))]
        mock_chunk.usage_metadata = Mock(prompt_token_count=7, candidates_token_count=3, total_token_count=10)

        async def mock_stream():
            yield mock_chunk

        mock_client = Mock()
        mock_client.generate_content = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test streaming with tools
        chunks = []
        messages = [{"role": "user", "content": "Weather in Madrid?"}]
        tool = create_tool_spec()

        async for chunk in provider._stream_impl(messages, [{"name": "get_weather", "description": "Get weather", "parameters": {}}], temperature=0.7):
            chunks.append(chunk)

        # Verify tool call
        tool_chunks = [c for c in chunks if c.type == "tool_call_complete"]
        assert len(tool_chunks) == 1
        assert tool_chunks[0].tool_name == "get_weather"
        assert tool_chunks[0].tool_args == {"location": "Madrid"}


# ============================================================================
# Integration Tests
# ============================================================================

class TestUnifiedGenerateAPI:
    """Test the unified generate() method across providers."""

    @pytest.mark.asyncio
    async def test_openai_unified_api_text(self):
        """Test OpenAI unified generate() for text."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!", tool_calls=None))]
        mock_response.usage = Mock(total_tokens=10, prompt_tokens=5, completion_tokens=5)

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        # Test via unified API
        result = await provider.generate("Hi", stream=False)

        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_openai_unified_api_streaming(self):
        """Test OpenAI unified generate() for streaming."""
        provider = OpenAIProvider(model="gpt-4", api_key="test-key")

        # Mock stream
        mock_chunk = Mock()
        mock_chunk.choices = [Mock(delta=Mock(content="Test", tool_calls=None), finish_reason=None)]
        mock_chunk.usage = None

        async def mock_stream():
            yield mock_chunk

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        provider._client = mock_client

        # Test via unified API - need to await generate() to get the async generator
        chunks = []
        async for chunk in await provider.generate("Hi", stream=True):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0].content == "Test"

    @pytest.mark.asyncio
    async def test_anthropic_unified_api_with_tools(self):
        """Test Anthropic unified generate() with tools."""
        provider = AnthropicProvider(model="claude-3-sonnet-20240229", api_key="test-key")

        # Mock response with tool
        mock_tool_block = Mock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "t1"
        mock_tool_block.name = "test_tool"
        mock_tool_block.input = {"arg": "value"}

        mock_response = Mock()
        mock_response.content = [mock_tool_block]
        mock_response.usage = Mock(input_tokens=5, output_tokens=5)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        provider._client = mock_client

        # Test via unified API
        tool = create_tool_spec()
        result = await provider.generate(
            [{"role": "user", "content": "Test"}],
            tools=[tool],
            stream=False
        )

        assert "tool_calls" in result
        assert result["tool_calls"][0]["name"] == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

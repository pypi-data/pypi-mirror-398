"""
Unit tests for unified execution path consolidation.

Tests verify that the consolidated _execute_autonomous() method correctly
handles both streaming and non-streaming execution modes, with proper
tool execution and focus system integration.
"""
import pytest
import json
from typing import Dict, Any, List
from daita import SubstrateAgent
from daita.core.tools import tool, AgentTool
from daita.llm.mock import MockLLMProvider
from daita.core.streaming import EventType, LLMChunk


class ToolCallingMockProvider(MockLLMProvider):
    """
    Enhanced mock provider that simulates tool calling behavior.

    This provider can be configured to return tool calls on first invocation,
    then return final answer after tool results are provided.
    """

    def __init__(self, tool_calls_to_make: List[Dict] = None, **kwargs):
        super().__init__(**kwargs)
        self.tool_calls_to_make = tool_calls_to_make or []
        self.turn_count = 0

    async def _generate_impl(self, messages, tools=None, **kwargs):
        """
        Mock implementation that simulates tool calling.

        - First turn: Returns tool calls
        - Subsequent turns: Returns final answer
        """
        self.turn_count += 1

        # Extract last user message
        if isinstance(messages, list):
            prompt = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    prompt = msg.get("content", "")
                    break
        else:
            prompt = str(messages)

        # Record call
        self.call_history.append({
            'turn': self.turn_count,
            'messages': messages if isinstance(messages, list) else None,
            'tools': tools,
            'params': kwargs
        })

        # First turn with tools: Return tool calls
        if self.turn_count == 1 and tools and self.tool_calls_to_make:
            return {
                "content": "",
                "tool_calls": self.tool_calls_to_make
            }

        # Subsequent turns or no tools: Return final answer
        # Check if we have tool results in conversation
        has_tool_results = False
        if isinstance(messages, list):
            for msg in messages:
                if msg.get("role") == "tool":
                    has_tool_results = True
                    break

        if has_tool_results:
            return {
                "content": "I executed the tool and got the result: 42",
                "tool_calls": None
            }

        return {
            "content": f"Mock response for: {prompt[:50]}",
            "tool_calls": None
        }

    async def _stream_impl(self, messages, tools=None, **kwargs):
        """Mock streaming implementation with tool call support."""
        self.turn_count += 1

        # Extract last user message
        if isinstance(messages, list):
            prompt = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    prompt = msg.get("content", "")
                    break
        else:
            prompt = str(messages)

        # Record call
        self.call_history.append({
            'turn': self.turn_count,
            'messages': messages if isinstance(messages, list) else None,
            'tools': tools,
            'params': kwargs
        })

        # First turn with tools: Return tool calls
        if self.turn_count == 1 and tools and self.tool_calls_to_make:
            # Emit tool call chunks
            for tc in self.tool_calls_to_make:
                yield LLMChunk(
                    type="tool_call_complete",
                    tool_call_id=tc["id"],
                    tool_name=tc["name"],
                    tool_args=tc["arguments"]
                )
            return

        # Check if we have tool results
        has_tool_results = False
        if isinstance(messages, list):
            for msg in messages:
                if msg.get("role") == "tool":
                    has_tool_results = True
                    break

        # Generate response text
        if has_tool_results:
            response = "I executed the tool and got the result: 42"
        else:
            response = f"Mock response for: {prompt[:50]}"

        # Stream the response
        for char in response:
            yield LLMChunk(type="text", content=char)


class TestUnifiedExecution:
    """Test suite for unified execution path."""

    @pytest.mark.asyncio
    async def test_non_streaming_executes_tools(self):
        """
        CRITICAL TEST: Verify tools execute in non-streaming mode.

        This was the broken behavior that the consolidation fixes.
        The non-streaming path previously returned tool call JSON
        without actually executing tools.
        """
        # Create agent with tool-calling mock provider
        llm = ToolCallingMockProvider(
            tool_calls_to_make=[{
                "id": "call_1",
                "name": "get_value",
                "arguments": {}
            }],
            delay=0
        )

        agent = SubstrateAgent(
            name="test",
            model="mock",
            llm_provider=llm
        )

        @tool
        async def get_value() -> int:
            """Get a test value."""
            return 42

        agent.register_tool(get_value)
        await agent.start()

        try:
            # Call WITHOUT on_event - uses non-streaming path
            result = await agent.run_detailed("Use get_value and return the number")

            # Verify tool was executed
            assert "result" in result, "Result dict missing 'result' key"
            assert "tool_calls" in result, "Result dict missing 'tool_calls' key"
            assert len(result["tool_calls"]) == 1, f"Expected 1 tool call, got {len(result['tool_calls'])}"
            assert result["tool_calls"][0]["tool"] == "get_value", "Wrong tool name"
            assert result["tool_calls"][0]["result"] == 42, "Tool result not captured"

            # Verify we got a final answer, not tool call JSON
            assert isinstance(result["result"], str), "Result should be string (final answer)"
            assert "42" in result["result"] or "tool" in result["result"].lower(), \
                "Final answer should reference tool execution"

            # Verify multiple LLM turns happened
            assert llm.turn_count >= 2, f"Expected 2+ turns, got {llm.turn_count}"

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_streaming_still_works(self):
        """
        Verify streaming path continues working (no regression).

        The streaming path was working before consolidation and
        should continue to work identically.
        """
        # Create agent with tool-calling mock provider
        llm = ToolCallingMockProvider(
            tool_calls_to_make=[{
                "id": "call_1",
                "name": "get_value",
                "arguments": {}
            }],
            delay=0
        )

        agent = SubstrateAgent(
            name="test",
            model="mock",
            llm_provider=llm
        )

        @tool
        async def get_value() -> int:
            """Get a test value."""
            return 42

        agent.register_tool(get_value)
        await agent.start()

        try:
            # Call WITH on_event - uses streaming path
            events = []
            result = await agent.run_detailed(
                "Use get_value and return the number",
                on_event=lambda e: events.append(e)
            )

            # Verify events were emitted
            assert len(events) > 0, "No events emitted"

            # Check for expected event types
            event_types = [e.type for e in events]
            assert EventType.ITERATION in event_types, "Missing ITERATION event"
            assert EventType.TOOL_CALL in event_types, "Missing TOOL_CALL event"
            assert EventType.TOOL_RESULT in event_types, "Missing TOOL_RESULT event"
            assert EventType.COMPLETE in event_types, "Missing COMPLETE event"

            # Verify tool was executed
            assert len(result["tool_calls"]) == 1, f"Expected 1 tool call, got {len(result['tool_calls'])}"
            assert result["tool_calls"][0]["tool"] == "get_value"
            assert result["tool_calls"][0]["result"] == 42

        finally:
            await agent.stop()

    # Note: Focus system tests are comprehensive in test_focus_system.py
    # These tests verify the unified execution path works correctly
    # Focus filtering functionality is already validated elsewhere

    @pytest.mark.asyncio
    async def test_multi_turn_tool_calling(self):
        """
        Verify multiple tool calls in sequence work correctly.

        The execution loop should handle multiple iterations where
        the LLM calls tools, receives results, and calls more tools.
        """
        # Create provider that makes two tool calls in sequence
        llm = ToolCallingMockProvider(delay=0)

        # Override to simulate multi-turn behavior
        original_generate = llm._generate_impl
        turn_count = [0]

        async def multi_turn_generate(messages, tools=None, **kwargs):
            turn_count[0] += 1

            if turn_count[0] == 1 and tools:
                # First turn: Call get_number
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_1",
                        "name": "get_number",
                        "arguments": {}
                    }]
                }
            elif turn_count[0] == 2 and tools:
                # Second turn: Call multiply after getting number
                return {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_2",
                        "name": "multiply",
                        "arguments": {"x": 10, "factor": 5}
                    }]
                }
            else:
                # Final turn: Return answer
                return {
                    "content": "The result is 50",
                    "tool_calls": None
                }

        llm._generate_impl = multi_turn_generate

        agent = SubstrateAgent(
            name="test",
            model="mock",
            llm_provider=llm
        )

        @tool
        async def get_number() -> int:
            """Get a number."""
            return 10

        @tool
        async def multiply(x: int, factor: int) -> int:
            """Multiply x by factor."""
            return x * factor

        agent.register_tool(get_number)
        agent.register_tool(multiply)
        await agent.start()

        try:
            result = await agent.run_detailed(
                "Get a number, then multiply it by 5",
                max_iterations=10
            )

            # Verify both tools were called
            assert len(result["tool_calls"]) == 2, f"Expected 2 tool calls, got {len(result['tool_calls'])}"
            assert result["tool_calls"][0]["tool"] == "get_number"
            assert result["tool_calls"][1]["tool"] == "multiply"

            # Verify correct results
            assert result["tool_calls"][0]["result"] == 10
            assert result["tool_calls"][1]["result"] == 50

            # Verify iterations
            assert result["iterations"] >= 3, f"Expected 3+ iterations, got {result['iterations']}"

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_no_tools_needed(self):
        """
        Verify execution works when LLM doesn't call any tools.

        If the LLM can answer directly without tools, it should
        return immediately without entering the tool calling loop.
        """
        llm = MockLLMProvider(delay=0)

        agent = SubstrateAgent(
            name="test",
            model="mock",
            llm_provider=llm
        )

        @tool
        async def get_value() -> int:
            """Get a value (won't be called)."""
            return 42

        agent.register_tool(get_value)
        await agent.start()

        try:
            result = await agent.run_detailed("What is 2+2?")

            # Verify no tools were called
            assert len(result["tool_calls"]) == 0, "No tools should be called"

            # Verify we got a direct answer
            assert "result" in result
            assert isinstance(result["result"], str)

            # Should be single iteration
            assert result["iterations"] == 1

        finally:
            await agent.stop()

    @pytest.mark.asyncio
    async def test_both_paths_produce_same_structure(self):
        """
        Verify streaming and non-streaming produce identical result structure.

        Both execution paths should return results in the same format
        with the same fields and types.
        """
        # Test with same configuration twice
        for mode in ["non-streaming", "streaming"]:
            llm = ToolCallingMockProvider(
                tool_calls_to_make=[{
                    "id": "call_1",
                    "name": "get_value",
                    "arguments": {}
                }],
                delay=0
            )

            agent = SubstrateAgent(
                name="test",
                model="mock",
                llm_provider=llm
            )

            @tool
            async def get_value() -> int:
                return 42

            agent.register_tool(get_value)
            await agent.start()

            try:
                if mode == "non-streaming":
                    result = await agent.run_detailed("Test")
                else:
                    result = await agent.run_detailed("Test", on_event=lambda e: None)

                # Verify all required fields present
                assert "result" in result, f"{mode}: missing 'result'"
                assert "tool_calls" in result, f"{mode}: missing 'tool_calls'"
                assert "iterations" in result, f"{mode}: missing 'iterations'"
                assert "tokens" in result, f"{mode}: missing 'tokens'"
                assert "cost" in result, f"{mode}: missing 'cost'"

                # Verify types
                assert isinstance(result["result"], str), f"{mode}: result should be string"
                assert isinstance(result["tool_calls"], list), f"{mode}: tool_calls should be list"
                assert isinstance(result["iterations"], int), f"{mode}: iterations should be int"
                assert isinstance(result["tokens"], dict), f"{mode}: tokens should be dict"
                assert isinstance(result["cost"], (int, float)), f"{mode}: cost should be numeric"

            finally:
                await agent.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

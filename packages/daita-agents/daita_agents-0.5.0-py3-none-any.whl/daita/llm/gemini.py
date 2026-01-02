"""
Google Gemini LLM provider implementation with integrated tracing.
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List

from ..core.exceptions import LLMError
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation with automatic call tracing."""
    
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Gemini provider.

        Args:
            model: Gemini model name (e.g., "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash")
            api_key: Google AI API key
            **kwargs: Additional Gemini-specific parameters
        """
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        super().__init__(model=model, api_key=api_key, **kwargs)
        
        # Gemini-specific default parameters
        self.default_params.update({
            'timeout': kwargs.get('timeout', 60),
            'safety_settings': kwargs.get('safety_settings', None),
            'generation_config': kwargs.get('generation_config', None)
        })
        
        # Lazy-load Gemini client
        self._client = None
    
    @property
    def client(self):
        """Lazy-load Google Generative AI client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                self._validate_api_key()
                
                # Configure the API key
                genai.configure(api_key=self.api_key)
                
                # Create the generative model
                self._client = genai.GenerativeModel(self.model)
                logger.debug("Gemini client initialized")
            except ImportError:
                raise LLMError(
                    "Google Generative AI package not installed. Install with: pip install google-generativeai"
                )
        return self._client
    
    async def _generate_impl(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs
    ):
        """
        Gemini non-streaming with optional tools.

        Args:
            messages: Conversation history in standardized format
            tools: Tool specifications in Gemini format (or None)
            **kwargs: Optional parameters

        Returns:
            - If no tools or LLM returns text: str
            - If LLM wants to call tools: {"tool_calls": [...]}
        """
        try:
            # Convert to Gemini format
            gemini_messages = self._convert_messages_to_gemini(messages)

            generation_config = {
                'max_output_tokens': kwargs.get('max_tokens', 2048),
                'temperature': kwargs.get('temperature'),
                'top_p': kwargs.get('top_p')
            }

            api_params = {
                "contents": gemini_messages,
                "generation_config": generation_config,
            }

            # Add tools if provided
            if tools:
                from google.generativeai.types import FunctionDeclaration, Tool
                function_declarations = [
                    FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"]
                    )
                    for tool in tools
                ]
                api_params["tools"] = [Tool(function_declarations=function_declarations)]

            # Generate (may be async or sync)
            if asyncio.iscoroutinefunction(self.client.generate_content):
                response = await self.client.generate_content(**api_params)
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: self.client.generate_content(**api_params)
                )

            # Store usage
            if hasattr(response, 'usage_metadata'):
                self._last_usage = response.usage_metadata

            # Check for function calls
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        fc = part.function_call
                        return {
                            "tool_calls": [{
                                "id": str(hash(fc.name)),
                                "name": fc.name,
                                "arguments": dict(fc.args) if fc.args else {}
                            }]
                        }

            return response.text

        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise LLMError(f"Gemini generation failed: {str(e)}")

    async def _stream_impl(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs
    ):
        """
        Gemini streaming with optional tools.

        Args:
            messages: Conversation history in standardized format
            tools: Tool specifications in Gemini format (or None)
            **kwargs: Optional parameters

        Yields:
            LLMChunk objects with type "text" or "tool_call_complete"
        """
        from ..core.streaming import LLMChunk

        try:
            gemini_messages = self._convert_messages_to_gemini(messages)

            generation_config = {
                'max_output_tokens': kwargs.get('max_tokens', 2048),
                'temperature': kwargs.get('temperature'),
            }

            api_params = {
                "contents": gemini_messages,
                "generation_config": generation_config,
                "stream": True,
            }

            if tools:
                from google.generativeai.types import FunctionDeclaration, Tool
                function_declarations = [
                    FunctionDeclaration(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool["parameters"]
                    )
                    for tool in tools
                ]
                api_params["tools"] = [Tool(function_declarations=function_declarations)]

            # Stream
            if asyncio.iscoroutinefunction(self.client.generate_content):
                response_stream = await self.client.generate_content(**api_params)

                async for chunk in response_stream:
                    # Text
                    if chunk.text:
                        yield LLMChunk(type="text", content=chunk.text, model=self.model)

                    # Function calls
                    if chunk.candidates[0].content.parts:
                        for part in chunk.candidates[0].content.parts:
                            if hasattr(part, 'function_call'):
                                fc = part.function_call
                                # Only yield if function call has a valid name
                                if fc.name:
                                    yield LLMChunk(
                                        type="tool_call_complete",
                                        tool_name=fc.name,
                                        tool_args=dict(fc.args),
                                        model=self.model
                                    )

                    # Usage
                    if hasattr(chunk, 'usage_metadata'):
                        self._last_usage = chunk.usage_metadata
            else:
                # Sync streaming
                loop = asyncio.get_event_loop()
                response_stream = await loop.run_in_executor(
                    None, lambda: self.client.generate_content(**api_params)
                )

                for chunk in response_stream:
                    # Check for function calls first
                    has_function_call = False
                    if chunk.candidates[0].content.parts:
                        for part in chunk.candidates[0].content.parts:
                            if hasattr(part, 'function_call'):
                                fc = part.function_call
                                # Only yield if function call has a valid name
                                if fc.name:
                                    has_function_call = True
                                    yield LLMChunk(
                                        type="tool_call_complete",
                                        tool_name=fc.name,
                                        tool_args=dict(fc.args) if fc.args else {},
                                        model=self.model
                                    )

                    # Text (only if no function call, since accessing .text raises error when function_call exists)
                    if not has_function_call:
                        try:
                            if chunk.text:
                                yield LLMChunk(type="text", content=chunk.text, model=self.model)
                        except ValueError:
                            # Gemini raises ValueError when trying to access .text on function_call chunks
                            pass

                    # Usage
                    if hasattr(chunk, 'usage_metadata'):
                        self._last_usage = chunk.usage_metadata

        except Exception as e:
            logger.error(f"Gemini streaming failed: {str(e)}")
            raise LLMError(f"Gemini streaming failed: {str(e)}")

    def _get_last_token_usage(self) -> Dict[str, int]:
        """
        Override base class method to handle Gemini's token format.
        
        Gemini uses different token field names in usage_metadata.
        """
        if self._last_usage:
            # Gemini format varies, try to extract what we can
            prompt_tokens = getattr(self._last_usage, 'prompt_token_count', 0)
            completion_tokens = getattr(self._last_usage, 'candidates_token_count', 0)
            total_tokens = getattr(self._last_usage, 'total_token_count', prompt_tokens + completion_tokens)
            
            return {
                'total_tokens': total_tokens,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens
            }
        
        # Fallback to base class estimation
        return super()._get_last_token_usage()

    def _convert_tools_to_format(self, tools: List['AgentTool']) -> List[Dict[str, Any]]:
        """
        Convert AgentTool list to Gemini function declaration format.

        Gemini uses a simpler format than OpenAI.
        """
        gemini_tools = []
        for tool in tools:
            openai_format = tool.to_openai_function()

            # Convert OpenAI format to Gemini format
            gemini_tools.append({
                "name": openai_format["function"]["name"],
                "description": openai_format["function"]["description"],
                "parameters": openai_format["function"]["parameters"]
            })

        return gemini_tools

    def _convert_messages_to_gemini(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert universal flat format to Gemini's format.

        Gemini uses "user" and "model" roles (not "assistant").
        Uses plain dict format for function calls and responses.
        """
        gemini_messages = []

        for msg in messages:
            if msg["role"] == "user":
                gemini_messages.append({
                    "role": "user",
                    "parts": [msg["content"]]
                })
            elif msg["role"] == "assistant":
                if msg.get("tool_calls"):
                    # Assistant with tool calls - use dict format
                    parts = []
                    for tc in msg["tool_calls"]:
                        parts.append({
                            'function_call': {
                                'name': tc["name"],
                                'args': tc["arguments"]
                            }
                        })
                    gemini_messages.append({
                        "role": "model",
                        "parts": parts
                    })
                else:
                    # Regular assistant message
                    gemini_messages.append({
                        "role": "model",
                        "parts": [msg.get("content", "")]
                    })
            elif msg["role"] == "tool":
                # Tool result - use dict format
                gemini_messages.append({
                    "role": "function",
                    "parts": [{
                        'function_response': {
                            'name': msg.get("name", ""),
                            'response': {'result': msg["content"]}
                        }
                    }]
                })

        return gemini_messages


    @property
    def info(self) -> Dict[str, Any]:
        """Get information about the Gemini provider."""
        base_info = super().info
        base_info.update({
            'provider_name': 'Google Gemini',
            'api_compatible': 'Google AI'
        })
        return base_info
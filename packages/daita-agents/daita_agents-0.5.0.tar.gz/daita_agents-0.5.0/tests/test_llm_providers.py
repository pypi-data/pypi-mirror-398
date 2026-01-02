"""
Test suite for LLM Providers - testing all provider implementations.

Tests cover:
- Provider factory and registration
- Mock provider for testing
- OpenAI provider integration
- Anthropic provider integration
- Grok provider integration
- Gemini provider integration
- Error handling and token tracking
- Provider configuration and validation
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from daita.llm.factory import (
    create_llm_provider, 
    register_llm_provider, 
    list_available_providers,
    PROVIDER_REGISTRY
)
from daita.llm.base import BaseLLMProvider
from daita.llm.mock import MockLLMProvider
from daita.llm.openai import OpenAIProvider
from daita.llm.anthropic import AnthropicProvider
from daita.llm.grok import GrokProvider
from daita.llm.gemini import GeminiProvider
from daita.core.exceptions import LLMError


class TestLLMProviderFactory:
    """Test the LLM provider factory and registration system."""
    
    def test_list_available_providers(self):
        """Test listing all available providers."""
        providers = list_available_providers()
        
        expected_providers = ['openai', 'anthropic', 'grok', 'gemini', 'mock']
        for provider in expected_providers:
            assert provider in providers
    
    def test_create_mock_provider(self):
        """Test creating mock provider through factory."""
        provider = create_llm_provider("mock", "test-model", agent_id="test_agent")
        
        assert isinstance(provider, MockLLMProvider)
        assert provider.model == "test-model"
        assert provider.agent_id == "test_agent"
    
    def test_create_openai_provider(self):
        """Test creating OpenAI provider through factory."""
        provider = create_llm_provider("openai", "gpt-4", api_key="test-key", agent_id="test_agent")
        
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4"
        assert provider.api_key == "test-key"
        assert provider.agent_id == "test_agent"
    
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider through factory."""
        provider = create_llm_provider("anthropic", "claude-3-sonnet-20240229", api_key="test-key")
        
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-3-sonnet-20240229"
        assert provider.api_key == "test-key"
    
    def test_create_grok_provider(self):
        """Test creating Grok provider through factory."""
        provider = create_llm_provider("grok", "grok-beta", api_key="test-key")
        
        assert isinstance(provider, GrokProvider)
        assert provider.model == "grok-beta"
        assert provider.api_key == "test-key"
    
    def test_create_gemini_provider(self):
        """Test creating Gemini provider through factory."""
        provider = create_llm_provider("gemini", "gemini-1.5-pro", api_key="test-key")
        
        assert isinstance(provider, GeminiProvider)
        assert provider.model == "gemini-1.5-pro"
        assert provider.api_key == "test-key"
    
    def test_unsupported_provider_error(self):
        """Test error when requesting unsupported provider."""
        with pytest.raises(LLMError) as exc_info:
            create_llm_provider("unsupported", "model")
        
        assert "Unsupported LLM provider: unsupported" in str(exc_info.value)
        assert "Available providers:" in str(exc_info.value)
    
    def test_register_custom_provider(self):
        """Test registering a custom provider."""
        class CustomProvider(BaseLLMProvider):
            async def generate(self, prompt: str, **kwargs) -> str:
                return "custom response"
        
        # Register custom provider
        register_llm_provider("custom", CustomProvider)
        
        # Should appear in available providers
        providers = list_available_providers()
        assert "custom" in providers
        
        # Should be creatable through factory
        provider = create_llm_provider("custom", "custom-model", api_key="test")
        assert isinstance(provider, CustomProvider)
        
        # Cleanup
        del PROVIDER_REGISTRY["custom"]
    
    def test_factory_error_handling(self):
        """Test factory error handling for provider creation failures."""
        class FailingProvider(BaseLLMProvider):
            def __init__(self, *args, **kwargs):
                raise ValueError("Provider initialization failed")
            
            async def generate(self, prompt: str, **kwargs) -> str:
                return "never reached"
        
        # Register failing provider
        register_llm_provider("failing", FailingProvider)
        
        # Should raise LLMError with context
        with pytest.raises(LLMError) as exc_info:
            create_llm_provider("failing", "model")
        
        assert "Failed to create failing provider" in str(exc_info.value)
        
        # Cleanup
        del PROVIDER_REGISTRY["failing"]


class TestMockLLMProvider:
    """Test the mock LLM provider used for testing."""
    
    def test_initialization_defaults(self):
        """Test mock provider initialization with defaults."""
        provider = MockLLMProvider()
        
        assert provider.model == "mock-model"
        assert provider.api_key == "mock-key"
        assert provider.delay == 0.1
        assert len(provider.call_history) == 0
    
    def test_initialization_custom(self):
        """Test mock provider with custom configuration."""
        responses = {"test": "custom response"}
        provider = MockLLMProvider(
            model="custom-model",
            responses=responses,
            delay=0.5,
            agent_id="test_agent"
        )
        
        assert provider.model == "custom-model"
        assert provider.responses == responses
        assert provider.delay == 0.5
        assert provider.agent_id == "test_agent"
    
    @pytest.mark.asyncio
    async def test_generate_default_response(self):
        """Test generating default response."""
        provider = MockLLMProvider(delay=0.01)  # Fast for testing
        
        response = await provider.generate("any prompt")
        
        assert "Mock response for: any prompt" in response
        assert len(provider.call_history) == 1
    
    @pytest.mark.asyncio
    async def test_generate_custom_response(self):
        """Test generating with custom response mapping."""
        provider = MockLLMProvider(
            responses={"specific prompt": "specific response"},
            delay=0.01
        )
        
        response = await provider.generate("specific prompt")
        
        assert response == "specific response"
        assert len(provider.call_history) == 1
    
    @pytest.mark.asyncio
    async def test_generate_keyword_response(self):
        """Test generating with keyword-based responses."""
        provider = MockLLMProvider(delay=0.01)
        
        # Test analyze keyword
        response = await provider.generate("Please analyze this data")
        assert "mock analysis" in response.lower()
        
        # Test summarize keyword
        response = await provider.generate("Summarize the following")
        assert "mock summary" in response.lower()
        
        # Test error keyword
        response = await provider.generate("This should error")
        assert "error response" in response.lower()
    
    def test_set_response(self):
        """Test setting specific responses."""
        provider = MockLLMProvider()
        
        provider.set_response("test prompt", "test response")
        
        assert provider.responses["test prompt"] == "test response"
    
    def test_call_history_tracking(self):
        """Test call history tracking."""
        provider = MockLLMProvider(delay=0.01)
        
        asyncio.run(provider.generate("test1"))
        asyncio.run(provider.generate("test2", temperature=0.5))
        
        assert len(provider.call_history) == 2
        
        # Check first call
        call1 = provider.call_history[0]
        assert call1['prompt'] == "test1"
        assert call1['params'] == {}
        
        # Check second call
        call2 = provider.call_history[1]
        assert call2['prompt'] == "test2"
        assert call2['params'] == {'temperature': 0.5}
    
    def test_utility_methods(self):
        """Test utility methods."""
        provider = MockLLMProvider()
        
        # Add some history
        asyncio.run(provider.generate("test"))
        
        # Test get_last_call
        last_call = provider.get_last_call()
        assert last_call['prompt'] == "test"
        
        # Test clear_history
        provider.clear_history()
        assert len(provider.call_history) == 0
        assert provider.get_last_call() is None


class TestBaseLLMProvider:
    """Test the base LLM provider functionality."""
    
    def test_initialization(self):
        """Test base provider initialization."""
        provider = MockLLMProvider(
            model="test-model",
            api_key="test-key",
            temperature=0.8,
            max_tokens=2000,
            agent_id="test_agent"
        )
        
        assert provider.model == "test-model"
        assert provider.api_key == "test-key"
        assert provider.agent_id == "test_agent"
        assert provider.default_params['temperature'] == 0.8
        assert provider.default_params['max_tokens'] == 2000
    
    def test_merge_params(self):
        """Test parameter merging."""
        provider = MockLLMProvider(temperature=0.7, max_tokens=1000)
        
        # Test merging with overrides
        merged = provider._merge_params({'temperature': 0.9, 'top_p': 0.95})
        
        assert merged['temperature'] == 0.9  # Overridden
        assert merged['max_tokens'] == 1000  # From defaults
        assert merged['top_p'] == 0.95  # New parameter
    
    def test_info_property(self):
        """Test provider info property."""
        provider = MockLLMProvider(
            model="test-model",
            agent_id="test_agent",
            custom_param="custom_value"
        )
        
        info = provider.info
        
        assert info['provider'] == 'MockLLMProvider'
        assert info['model'] == 'test-model'
        assert 'config' in info
        assert 'token_usage' in info
    
    def test_token_usage_without_agent_id(self):
        """Test token usage when no agent ID is set."""
        provider = MockLLMProvider()
        
        usage = provider.get_token_usage()
        
        # Should return zero usage
        assert usage['total_tokens'] == 0
        assert usage['prompt_tokens'] == 0
        assert usage['completion_tokens'] == 0
        assert usage['requests'] == 0
    
    def test_set_agent_id(self):
        """Test setting agent ID after initialization."""
        provider = MockLLMProvider()
        
        provider.set_agent_id("new_agent_id")
        
        assert provider.agent_id == "new_agent_id"


class TestProviderEnvironmentIntegration:
    """Test provider integration with environment variables."""
    
    def test_openai_env_key(self):
        """Test OpenAI provider uses environment API key."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            provider = OpenAIProvider()
            assert provider.api_key == 'env-key'
    
    def test_anthropic_env_key(self):
        """Test Anthropic provider uses environment API key."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env-key'}):
            provider = AnthropicProvider()
            assert provider.api_key == 'env-key'
    
    def test_grok_env_key(self):
        """Test Grok provider uses environment API key."""
        with patch.dict(os.environ, {'XAI_API_KEY': 'env-key'}):
            provider = GrokProvider()
            assert provider.api_key == 'env-key'
        
        # Test alternative env var
        with patch.dict(os.environ, {'GROK_API_KEY': 'env-key2'}, clear=True):
            provider = GrokProvider()
            assert provider.api_key == 'env-key2'
    
    def test_gemini_env_key(self):
        """Test Gemini provider uses environment API key."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'env-key'}):
            provider = GeminiProvider()
            assert provider.api_key == 'env-key'
        
        # Test alternative env var
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'env-key2'}, clear=True):
            provider = GeminiProvider()
            assert provider.api_key == 'env-key2'
    
    def test_parameter_overrides_env(self):
        """Test that explicit parameters override environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'env-key'}):
            provider = OpenAIProvider(api_key='explicit-key')
            assert provider.api_key == 'explicit-key'


class TestProviderConfiguration:
    """Test provider-specific configuration options."""
    
    def test_openai_configuration(self):
        """Test OpenAI provider configuration."""
        provider = OpenAIProvider(
            model="gpt-3.5-turbo",
            api_key="test-key",
            temperature=0.8,
            frequency_penalty=0.5,
            timeout=120
        )
        
        assert provider.model == "gpt-3.5-turbo"
        assert provider.default_params['temperature'] == 0.8
        assert provider.default_params['frequency_penalty'] == 0.5
        assert provider.default_params['timeout'] == 120
    
    def test_anthropic_configuration(self):
        """Test Anthropic provider configuration."""
        provider = AnthropicProvider(
            model="claude-3-haiku-20240307",
            api_key="test-key",
            temperature=0.3,
            timeout=90
        )
        
        assert provider.model == "claude-3-haiku-20240307"
        assert provider.default_params['temperature'] == 0.3
        assert provider.default_params['timeout'] == 90
    
    def test_grok_configuration(self):
        """Test Grok provider configuration."""
        provider = GrokProvider(
            model="grok-vision-beta",
            api_key="test-key",
            base_url="https://custom.api.url",
            stream=True
        )
        
        assert provider.model == "grok-vision-beta"
        assert provider.base_url == "https://custom.api.url"
        assert provider.default_params['stream'] is True
    
    def test_gemini_configuration(self):
        """Test Gemini provider configuration."""
        provider = GeminiProvider(
            model="gemini-1.0-pro",
            api_key="test-key",
            timeout=60,
            safety_settings={"harassment": "block_none"}
        )
        
        assert provider.model == "gemini-1.0-pro"
        assert provider.default_params['timeout'] == 60
        assert provider.default_params['safety_settings'] == {"harassment": "block_none"}


class TestProviderErrorHandling:
    """Test error handling across all providers."""
    
    def test_missing_api_key_validation(self):
        """Test API key validation."""
        provider = OpenAIProvider(api_key=None)
        
        with pytest.raises(ValueError) as exc_info:
            provider._validate_api_key()
        
        assert "API key required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_mock_provider_no_errors(self):
        """Test that mock provider doesn't raise unexpected errors."""
        provider = MockLLMProvider(delay=0.01)
        
        # Should handle any prompt without errors
        response = await provider.generate("")
        assert isinstance(response, str)
        
        response = await provider.generate("x" * 10000)  # Very long prompt
        assert isinstance(response, str)
        
        response = await provider.generate("Special chars: !@#$%^&*()")
        assert isinstance(response, str)


class TestTokenTracking:
    """Test token tracking integration across providers."""
    
    def setup_method(self):
        """Clear token tracking before each test."""
        from daita.utils.token_tracking import clear_tokens
        clear_tokens()
    
    @pytest.mark.asyncio
    async def test_mock_provider_token_tracking(self):
        """Test token tracking with mock provider."""
        provider = MockLLMProvider(agent_id="test_agent", delay=0.01)
        
        # Mock provider doesn't track real tokens, but should not error
        await provider.generate("test prompt")
        
        usage = provider.get_token_usage()
        assert isinstance(usage, dict)
        assert 'total_tokens' in usage
    
    def test_provider_agent_id_setting(self):
        """Test setting agent ID for token tracking."""
        provider = MockLLMProvider()
        
        provider.set_agent_id("new_agent_123")
        
        assert provider.agent_id == "new_agent_123"
        
        # Usage should reflect the agent ID
        usage = provider.get_token_usage()
        assert isinstance(usage, dict)


class TestProviderIntegrationMocking:
    """Test provider integration with mocked external APIs."""
    
    @pytest.mark.asyncio
    async def test_openai_generate_mock(self):
        """Test OpenAI provider with mocked API calls."""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            # Mock the client instance and response
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Mocked OpenAI response"
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 100
            mock_response.usage.prompt_tokens = 80
            mock_response.usage.completion_tokens = 20
            
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            provider = OpenAIProvider(api_key="test-key", agent_id="test_agent")
            response = await provider.generate("Test prompt")
            
            assert response == "Mocked OpenAI response"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_anthropic_generate_mock(self):
        """Test Anthropic provider with mocked API calls."""
        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            # Mock the client instance and response
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = "Mocked Anthropic response"
            mock_response.usage = Mock()
            mock_response.usage.input_tokens = 75
            mock_response.usage.output_tokens = 25
            
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            
            provider = AnthropicProvider(api_key="test-key", agent_id="test_agent")
            response = await provider.generate("Test prompt")
            
            assert response == "Mocked Anthropic response"
            mock_client.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_provider_error_handling_mock(self):
        """Test provider error handling with mocked failures."""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock API failure
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API rate limit exceeded")
            )
            
            provider = OpenAIProvider(api_key="test-key")
            
            with pytest.raises(LLMError) as exc_info:
                await provider.generate("Test prompt")
            
            assert "OpenAI generation failed" in str(exc_info.value)
            assert "API rate limit exceeded" in str(exc_info.value)


class TestProviderCompatibility:
    """Test provider compatibility and interface consistency."""
    
    def test_all_providers_implement_interface(self):
        """Test that all providers implement the required interface."""
        providers = [
            MockLLMProvider(),
            OpenAIProvider(api_key="test"),
            AnthropicProvider(api_key="test"),
            GrokProvider(api_key="test"),
            GeminiProvider(api_key="test")
        ]
        
        for provider in providers:
            # Should have required methods
            assert hasattr(provider, 'generate')
            assert callable(provider.generate)
            
            # Should have info property
            assert hasattr(provider, 'info')
            info = provider.info
            assert isinstance(info, dict)
            assert 'provider' in info
            assert 'model' in info
            
            # Should have token tracking
            assert hasattr(provider, 'get_token_usage')
            usage = provider.get_token_usage()
            assert isinstance(usage, dict)
    
    def test_provider_parameter_consistency(self):
        """Test that all providers handle common parameters consistently."""
        providers = [
            ("mock", MockLLMProvider(model="test", temperature=0.5, max_tokens=500)),
            ("openai", OpenAIProvider(api_key="test", model="gpt-4", temperature=0.5, max_tokens=500)),
            ("anthropic", AnthropicProvider(api_key="test", model="claude-3-sonnet-20240229", temperature=0.5, max_tokens=500)),
            ("grok", GrokProvider(api_key="test", model="grok-beta", temperature=0.5, max_tokens=500)),
            ("gemini", GeminiProvider(api_key="test", model="gemini-1.5-pro", temperature=0.5, max_tokens=500))
        ]
        
        for name, provider in providers:
            assert provider.model is not None
            assert provider.default_params['temperature'] == 0.5
            assert provider.default_params['max_tokens'] == 500


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
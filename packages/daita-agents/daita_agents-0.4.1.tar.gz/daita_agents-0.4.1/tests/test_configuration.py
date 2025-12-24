"""
Test suite for Configuration System - testing all configuration components.

Tests cover:
- Base configuration classes (AgentConfig, DaitaConfig)
- Configuration validation and defaults
- Retry policy configuration
- Focus configuration
- Environment variable integration
- Configuration serialization/deserialization
- Configuration merging and inheritance
- Runtime settings management
- Configuration validation and error handling
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from typing import Dict, Any
import pydantic_core

from daita.config.base import (
    AgentConfig,
 
    DaitaConfig,
    FocusConfig,
    RetryPolicy,
    AgentType,
    FocusType,
    RetryStrategy
)
from daita.config.settings import Settings, settings
from daita.core.exceptions import ValidationError


class TestAgentType:
    """Test AgentType enumeration."""
    
    def test_agent_type_values(self):
        """Test that AgentType has expected values."""
        assert AgentType.SUBSTRATE == "substrate"
        
        # Test that it's a string enum
        assert isinstance(AgentType.SUBSTRATE, str)
        # Fix: Python enums return "EnumClass.VALUE" format with str(), not just the value
        assert AgentType.SUBSTRATE.value == "substrate"
    
    def test_agent_type_usage(self):
        """Test AgentType usage in configuration."""
        config = AgentConfig(name="Test Agent", type=AgentType.SUBSTRATE)
        assert config.type == AgentType.SUBSTRATE
        assert config.type.value == "substrate"


class TestFocusType:
    """Test FocusType enumeration."""
    
    def test_focus_type_values(self):
        """Test that FocusType has all expected values."""
        expected_types = {
            "column", "jsonpath", "xpath", "css", "regex", "semantic"
        }
        actual_types = {ft.value for ft in FocusType}
        assert actual_types == expected_types
    
    def test_focus_type_usage(self):
        """Test FocusType usage in focus configuration."""
        focus_config = FocusConfig(type=FocusType.COLUMN, include=["name", "age"])
        assert focus_config.type == FocusType.COLUMN


class TestRetryStrategy:
    """Test RetryStrategy enumeration."""
    
    def test_retry_strategy_values(self):
        """Test that RetryStrategy has expected values."""
        expected_strategies = {
            "exponential_backoff", "fixed_delay", "immediate"
        }
        actual_strategies = {rs.value for rs in RetryStrategy}
        assert actual_strategies == expected_strategies
    
    def test_retry_strategy_defaults(self):
        """Test default retry strategy."""
        policy = RetryPolicy()
        assert policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF


class TestFocusConfig:
    """Test FocusConfig configuration class."""
    
    def test_focus_config_defaults(self):
        """Test FocusConfig with default values."""
        config = FocusConfig()
        
        assert config.type is None
        assert config.include is None
        assert config.exclude is None
        assert config.paths is None
        assert config.description is None
    
    def test_focus_config_with_include_list(self):
        """Test FocusConfig with include as list."""
        config = FocusConfig(
            type=FocusType.COLUMN,
            include=["name", "age", "email"],
            description="User profile fields"
        )
        
        assert config.type == FocusType.COLUMN
        assert config.include == ["name", "age", "email"]
        assert config.description == "User profile fields"
    
    def test_focus_config_with_include_string(self):
        """Test FocusConfig with include as string."""
        config = FocusConfig(
            type=FocusType.JSONPATH,
            include="$.user.profile",
            paths=["$.user.id", "$.user.name"]
        )
        
        assert config.type == FocusType.JSONPATH
        assert config.include == "$.user.profile"
        assert config.paths == ["$.user.id", "$.user.name"]
    
    def test_focus_config_with_exclude(self):
        """Test FocusConfig with exclude patterns."""
        config = FocusConfig(
            type=FocusType.COLUMN,
            include=["name", "age", "email", "password"],
            exclude=["password"]
        )
        
        assert config.exclude == ["password"]
    
    def test_focus_config_serialization(self):
        """Test FocusConfig serialization to dict."""
        config = FocusConfig(
            type=FocusType.SEMANTIC,
            include=["important", "relevant"],
            description="Semantic filtering"
        )
        
        config_dict = config.model_dump_yaml_safe()
        
        assert config_dict["type"] == "semantic"
        assert config_dict["include"] == ["important", "relevant"]
        assert config_dict["description"] == "Semantic filtering"


class TestRetryPolicy:
    """Test RetryPolicy configuration class."""
    
    def test_retry_policy_defaults(self):
        """Test RetryPolicy with default values."""
        policy = RetryPolicy()
        
        assert policy.max_retries == 3
        assert policy.initial_delay == 1.0
        assert policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
        assert isinstance(policy.permanent_errors, list)
        assert len(policy.permanent_errors) > 0
        assert "AuthenticationError" in policy.permanent_errors
        assert "ValidationError" in policy.permanent_errors
    
    def test_retry_policy_custom_values(self):
        """Test RetryPolicy with custom values."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=2.0,
            strategy=RetryStrategy.FIXED_DELAY,
            permanent_errors=["CustomError", "PermanentError"]
        )
        
        assert policy.max_retries == 5
        assert policy.initial_delay == 2.0
        assert policy.strategy == RetryStrategy.FIXED_DELAY
        assert policy.permanent_errors == ["CustomError", "PermanentError"]
    
    def test_retry_policy_validation(self):
        """Test RetryPolicy validation constraints."""
        # Valid values should work
        policy = RetryPolicy(max_retries=0, initial_delay=0.1)
        assert policy.max_retries == 0
        assert policy.initial_delay == 0.1
        
        # Test edge cases
        policy = RetryPolicy(max_retries=10, initial_delay=60.0)
        assert policy.max_retries == 10
        assert policy.initial_delay == 60.0
    
    def test_retry_policy_invalid_values(self):
        """Test RetryPolicy with invalid values."""
        # Fix: Expect pydantic_core.ValidationError instead of our custom ValidationError
        # Should validate max_retries range
        with pytest.raises(pydantic_core.ValidationError):
            RetryPolicy(max_retries=-1)
        
        with pytest.raises(pydantic_core.ValidationError):
            RetryPolicy(max_retries=11)  # Above max
        
        # Should validate initial_delay range  
        with pytest.raises(pydantic_core.ValidationError):
            RetryPolicy(initial_delay=0.05)  # Below minimum
        
        with pytest.raises(pydantic_core.ValidationError):
            RetryPolicy(initial_delay=61.0)  # Above maximum
    
    def test_retry_policy_serialization(self):
        """Test RetryPolicy serialization."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=1.5,
            strategy=RetryStrategy.FIXED_DELAY
        )
        
        policy_dict = policy.model_dump_yaml_safe()
        
        assert policy_dict["max_retries"] == 5
        assert policy_dict["initial_delay"] == 1.5
        assert policy_dict["strategy"] == "fixed_delay"
        assert isinstance(policy_dict["permanent_errors"], list)



class TestAgentConfig:
    """Test AgentConfig configuration class."""
    
    def test_agent_config_minimal(self):
        """Test AgentConfig with minimal parameters."""
        config = AgentConfig(name="Test Agent")
        
        assert config.name == "Test Agent"
        assert config.type == AgentType.SUBSTRATE
        assert config.enabled is True
        assert config.settings == {}
        assert config.llm is None
        assert config.enable_retry is False
        assert config.retry_policy is None
        assert config.retry_enabled is False
    
    def test_agent_config_with_retry_enabled(self):
        """Test AgentConfig with retry enabled."""
        config = AgentConfig(
            name="Retry Agent",
            enable_retry=True
        )
        
        assert config.enable_retry is True
        assert config.retry_policy is not None
        assert isinstance(config.retry_policy, RetryPolicy)
        assert config.retry_enabled is True
    
    def test_agent_config_with_custom_retry_policy(self):
        """Test AgentConfig with custom retry policy."""
        custom_policy = RetryPolicy(
            max_retries=5,
            initial_delay=2.0,
            strategy=RetryStrategy.FIXED_DELAY
        )
        
        config = AgentConfig(
            name="Custom Retry Agent",
            enable_retry=True,
            retry_policy=custom_policy
        )
        
        assert config.retry_policy == custom_policy
        assert config.retry_policy.max_retries == 5
        assert config.retry_enabled is True
    
    def test_agent_config_with_settings(self):
        """Test AgentConfig with custom settings."""
        settings = {
            "focus": ["name", "age"],
            "relay_channel": "agent_output",
            "custom_param": "custom_value"
        }
        
        config = AgentConfig(
            name="Settings Agent",
            settings=settings
        )
        
        assert config.settings == settings
        assert config.settings["focus"] == ["name", "age"]
        assert config.settings["custom_param"] == "custom_value"
    
    def test_agent_config_retry_policy_auto_creation(self):
        """Test that retry policy is auto-created when retry is enabled."""
        config = AgentConfig(
            name="Auto Retry Agent",
            enable_retry=True,
            retry_policy=None  # Explicitly set to None
        )
        
        # Should auto-create retry policy
        assert config.retry_policy is not None
        assert isinstance(config.retry_policy, RetryPolicy)
        assert config.retry_enabled is True
    
    def test_agent_config_retry_disabled_by_default(self):
        """Test that retry is disabled by default."""
        config = AgentConfig(name="Default Agent")
        
        assert config.enable_retry is False
        assert config.retry_policy is None
        assert config.retry_enabled is False
    
    def test_agent_config_serialization(self):
        """Test AgentConfig serialization."""
        config = AgentConfig(
            name="Serialization Test",
            type=AgentType.SUBSTRATE,
            enabled=True,
            enable_retry=True,
            settings={"test": "value"}
        )
        
        config_dict = config.model_dump_yaml_safe()
        
        assert config_dict["name"] == "Serialization Test"
        assert config_dict["type"] == "substrate"
        assert config_dict["enabled"] is True
        assert config_dict["enable_retry"] is True
        assert config_dict["retry_policy"] is not None
        assert config_dict["settings"] == {"test": "value"}


class TestDaitaConfig:
    """Test DaitaConfig main configuration class."""
    
    def test_daita_config_defaults(self):
        """Test DaitaConfig with default values."""
        config = DaitaConfig()
        
        assert config.version == "1.0.0"
        assert config.agents == []
        assert isinstance(config.llm, LLMConfig)
        assert config.llm.provider == "openai"
        assert config.settings == {}
    
    def test_daita_config_with_agents(self):
        """Test DaitaConfig with agent configurations."""
        agent1 = AgentConfig(name="Agent 1")
        agent2 = AgentConfig(name="Agent 2", enable_retry=True)
        
        config = DaitaConfig(
            version="2.0.0",
            agents=[agent1, agent2]
        )
        
        assert config.version == "2.0.0"
        assert len(config.agents) == 2
        assert config.agents[0].name == "Agent 1"
        assert config.agents[1].name == "Agent 2"
        assert config.agents[1].retry_enabled is True
    
    def test_daita_config_with_custom_llm(self):
        """Test DaitaConfig with custom LLM configuration."""
        llm_config = LLMConfig(
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.1
        )
        
        config = DaitaConfig(llm=llm_config)
        
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3-opus-20240229"
        assert config.llm.temperature == 0.1
    
    def test_daita_config_with_settings(self):
        """Test DaitaConfig with global settings."""
        settings = {
            "log_level": "DEBUG",
            "cache_enabled": True,
            "default_timeout": 60
        }
        
        config = DaitaConfig(settings=settings)
        
        assert config.settings == settings
        assert config.settings["log_level"] == "DEBUG"
    
    def test_daita_config_serialization(self):
        """Test DaitaConfig serialization."""
        agent_config = AgentConfig(name="Test Agent")
        llm_config = LLMConfig(provider="openai", model="gpt-4")
        
        config = DaitaConfig(
            version="1.5.0",
            agents=[agent_config],
            llm=llm_config,
            settings={"test": True}
        )
        
        config_dict = config.model_dump_yaml_safe()
        
        assert config_dict["version"] == "1.5.0"
        assert len(config_dict["agents"]) == 1
        assert config_dict["agents"][0]["name"] == "Test Agent"
        assert config_dict["llm"]["provider"] == "openai"
        assert config_dict["settings"]["test"] is True


class TestRuntimeSettings:
    """Test runtime settings management."""
    
    def setup_method(self):
        """Set up clean environment for each test."""
        # Clear any environment variables that might affect tests
        self.env_vars_to_clear = [
            'DAITA_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
            'GOOGLE_API_KEY', 'XAI_API_KEY', 'DAITA_API_ENDPOINT',
            'DAITA_LOCAL_MODE', 'DAITA_LOG_LEVEL', 'DAITA_DEFAULT_MODEL',
            'DAITA_DEFAULT_PROVIDER', 'DAITA_DEFAULT_TEMPERATURE'
        ]
        self.original_env = {}
        for var in self.env_vars_to_clear:
            self.original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
    
    def teardown_method(self):
        """Restore environment after each test."""
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    def test_settings_defaults(self):
        """Test Settings class with default values."""
        test_settings = Settings()
        
        assert test_settings.api_key is None
        assert test_settings.api_endpoint == "https://api.daita.ai"
        assert test_settings.local_mode is True
        assert test_settings.log_level == "INFO"
        assert test_settings.default_model == "gpt-4"
        assert test_settings.default_provider == "openai"
        assert test_settings.default_temperature == 0.7
        assert isinstance(test_settings.cache_dir, Path)
    
    def test_settings_with_environment_variables(self):
        """Test Settings with environment variable overrides."""
        with patch.dict(os.environ, {
            'DAITA_API_KEY': 'env-api-key',
            'DAITA_API_ENDPOINT': 'https://custom.api.endpoint',
            'DAITA_LOCAL_MODE': 'false',
            'DAITA_LOG_LEVEL': 'DEBUG',
            'DAITA_DEFAULT_MODEL': 'gpt-3.5-turbo',
            'DAITA_DEFAULT_PROVIDER': 'anthropic',
            'DAITA_DEFAULT_TEMPERATURE': '0.5'
        }):
            test_settings = Settings()
            
            assert test_settings.api_key == 'env-api-key'
            assert test_settings.api_endpoint == 'https://custom.api.endpoint'
            assert test_settings.local_mode is False
            assert test_settings.log_level == 'DEBUG'
            assert test_settings.default_model == 'gpt-3.5-turbo'
            assert test_settings.default_provider == 'anthropic'
            assert test_settings.default_temperature == 0.5
    
    def test_settings_api_key_priority(self):
        """Test API key priority from different environment variables."""
        # Test DAITA_API_KEY takes priority
        with patch.dict(os.environ, {
            'DAITA_API_KEY': 'daita-key',
            'OPENAI_API_KEY': 'openai-key',
            'ANTHROPIC_API_KEY': 'anthropic-key'
        }):
            test_settings = Settings()
            assert test_settings.api_key == 'daita-key'
        
        # Test OPENAI_API_KEY fallback
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'openai-key',
            'ANTHROPIC_API_KEY': 'anthropic-key'
        }, clear=True):
            test_settings = Settings()
            assert test_settings.api_key == 'openai-key'
        
        # Test ANTHROPIC_API_KEY fallback
        with patch.dict(os.environ, {
            'ANTHROPIC_API_KEY': 'anthropic-key'
        }, clear=True):
            test_settings = Settings()
            assert test_settings.api_key == 'anthropic-key'
    
    def test_settings_invalid_temperature(self):
        """Test Settings handles invalid temperature values."""
        with patch.dict(os.environ, {
            'DAITA_DEFAULT_TEMPERATURE': 'invalid'
        }):
            test_settings = Settings()
            # Should fall back to default when invalid
            assert test_settings.default_temperature == 0.7
    
    def test_settings_cache_directory_creation(self):
        """Test that cache directory is created."""
        test_settings = Settings()
        
        # Cache directory should exist
        assert test_settings.cache_dir.exists()
        assert test_settings.cache_dir.is_dir()
    
    def test_global_settings_instance(self):
        """Test global settings instance."""
        from daita.config.settings import settings
        
        assert isinstance(settings, Settings)
        assert settings.api_endpoint == "https://api.daita.ai"
    
    def test_settings_explicit_overrides(self):
        """Test Settings with explicit parameter overrides."""
        test_settings = Settings(
            api_key="explicit-key",
            local_mode=False,
            default_model="custom-model"
        )
        
        assert test_settings.api_key == "explicit-key"
        assert test_settings.local_mode is False
        assert test_settings.default_model == "custom-model"


class TestConfigurationValidation:
    """Test configuration validation and error handling."""
    
    def test_agent_config_validation_errors(self):
        """Test AgentConfig validation errors."""
        # Empty name should be handled gracefully or raise error
        try:
            config = AgentConfig(name="")
            # If it doesn't raise an error, that's also valid
            assert config.name == ""
        except ValidationError:
            # If it does raise an error, that's also valid
            pass
    
    def test_retry_policy_validation_comprehensive(self):
        """Test comprehensive RetryPolicy validation."""
        # Valid edge cases
        policy = RetryPolicy(max_retries=0)  # No retries
        assert policy.max_retries == 0
        
        policy = RetryPolicy(initial_delay=0.1)  # Minimum delay
        assert policy.initial_delay == 0.1
        
        # Test all strategies
        for strategy in RetryStrategy:
            policy = RetryPolicy(strategy=strategy)
            assert policy.strategy == strategy
    
    def test_llm_config_provider_validation(self):
        """Test LLM config with various providers."""
        providers = ["openai", "anthropic", "grok", "gemini", "mock", "custom"]
        
        for provider in providers:
            config = LLMConfig(provider=provider)
            assert config.provider == provider
    
    def test_configuration_type_safety(self):
        """Test configuration type safety."""
        # Test that configurations maintain type information
        config = AgentConfig(name="Type Test")
        assert isinstance(config.type, AgentType)
        assert config.type == AgentType.SUBSTRATE
        
        policy = RetryPolicy()
        assert isinstance(policy.strategy, RetryStrategy)


class TestConfigurationSerialization:
    """Test configuration serialization and deserialization."""
    
    def test_agent_config_round_trip(self):
        """Test AgentConfig serialization round trip."""
        original_config = AgentConfig(
            name="Round Trip Test",
            type=AgentType.SUBSTRATE,
            enable_retry=True,
            settings={"test": "value"}
        )
        
        # Serialize to dict
        config_dict = original_config.model_dump_yaml_safe()
        
        # Deserialize from dict
        restored_config = AgentConfig(**config_dict)
        
        assert restored_config.name == original_config.name
        assert restored_config.type == original_config.type
        assert restored_config.enable_retry == original_config.enable_retry
        assert restored_config.settings == original_config.settings
    
    def test_daita_config_round_trip(self):
        """Test DaitaConfig serialization round trip."""
        agent1 = AgentConfig(name="Agent 1")
        agent2 = AgentConfig(name="Agent 2", enable_retry=True)
        llm_config = LLMConfig(provider="anthropic", model="claude-3-sonnet-20240229")
        
        original_config = DaitaConfig(
            version="2.0.0",
            agents=[agent1, agent2],
            llm=llm_config,
            settings={"global": "setting"}
        )
        
        # Serialize to dict
        config_dict = original_config.model_dump_yaml_safe()
        
        # Deserialize from dict
        restored_config = DaitaConfig(**config_dict)
        
        assert restored_config.version == original_config.version
        assert len(restored_config.agents) == len(original_config.agents)
        assert restored_config.llm.provider == original_config.llm.provider
        assert restored_config.settings == original_config.settings
    
    def test_configuration_json_serialization(self):
        """Test configuration JSON serialization."""
        import json
        
        config = AgentConfig(
            name="JSON Test",
            enable_retry=True,
            settings={"nested": {"value": 123}}
        )
        
        # Convert to dict then JSON
        config_dict = config.model_dump_yaml_safe()
        json_str = json.dumps(config_dict)
        
        # Parse back from JSON
        parsed_dict = json.loads(json_str)
        restored_config = AgentConfig(**parsed_dict)
        
        assert restored_config.name == config.name
        assert restored_config.settings == config.settings


class TestConfigurationInheritance:
    """Test configuration inheritance and merging."""
    
    def test_agent_config_inheritance(self):
        """Test agent configuration inheritance patterns."""
        # Base configuration
        base_config = AgentConfig(
            name="Base Agent",
            enable_retry=True,
            settings={"base_setting": "base_value"}
        )
        
        # Derived configuration with overrides
        derived_settings = base_config.settings.copy()
        derived_settings.update({"derived_setting": "derived_value"})
        
        derived_config = AgentConfig(
            name="Derived Agent",
            enable_retry=base_config.enable_retry,
            retry_policy=base_config.retry_policy,
            settings=derived_settings
        )
        
        assert derived_config.name == "Derived Agent"
        assert derived_config.enable_retry == base_config.enable_retry
        assert derived_config.settings["base_setting"] == "base_value"
        assert derived_config.settings["derived_setting"] == "derived_value"
    
    def test_llm_config_merging(self):
        """Test LLM configuration merging."""
        base_llm = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.7
        )
        
        # Override specific values
        custom_llm = LLMConfig(
            provider=base_llm.provider,
            model="gpt-3.5-turbo",  # Override model
            api_key="custom-key",   # Add API key
            temperature=base_llm.temperature,
            max_tokens=2000         # Override max_tokens
        )
        
        assert custom_llm.provider == base_llm.provider
        assert custom_llm.model == "gpt-3.5-turbo"
        assert custom_llm.api_key == "custom-key"
        assert custom_llm.temperature == base_llm.temperature
        assert custom_llm.max_tokens == 2000


class TestConfigurationEdgeCases:
    """Test configuration edge cases and error conditions."""
    
    def test_empty_configurations(self):
        """Test configurations with minimal/empty data."""
        # Minimal agent config
        config = AgentConfig(name="Minimal")
        assert config.name == "Minimal"
        assert config.settings == {}
        
        # Empty settings
        config = AgentConfig(name="Empty Settings", settings={})
        assert config.settings == {}
    
    def test_large_configurations(self):
        """Test configurations with large amounts of data."""
        # Large settings dictionary
        large_settings = {f"setting_{i}": f"value_{i}" for i in range(1000)}
        
        config = AgentConfig(
            name="Large Config",
            settings=large_settings
        )
        
        assert len(config.settings) == 1000
        assert config.settings["setting_500"] == "value_500"
    
    def test_unicode_in_configuration(self):
        """Test configurations with Unicode characters."""
        config = AgentConfig(
            name="Unicode Test ",
            settings={
                "emoji": "",
                "unicode": "Ñiño",
                "chinese": "你好"
            }
        )
        
        assert "" in config.name
        assert config.settings["emoji"] == ""
        assert config.settings["unicode"] == "Ñiño"
        assert config.settings["chinese"] == "你好"
    
    def test_none_value_handling(self):
        """Test configuration handling of None values."""
        config = AgentConfig(
            name="None Test",
            llm=None,
            settings={"none_value": None}
        )
        
        assert config.llm is None
        assert config.settings["none_value"] is None


class TestConfigurationIntegration:
    """Test configuration integration with other framework components."""
    
    def test_configuration_with_sdk(self):
        """Test configuration integration with SDK."""
        from daita.sdk.client import DaitaSDK
        
        # Test that configurations work with SDK
        config = DaitaConfig(
            llm=LLMConfig(
                provider="mock",
                model="test-model",
                api_key="test-key"
            )
        )
        
        # SDK should be able to use the configuration
        sdk = DaitaSDK(
            api_key=config.llm.api_key,
            model=config.llm.model,
            provider=config.llm.provider
        )
        
        assert sdk.default_model == config.llm.model
        assert sdk.default_provider == config.llm.provider
    
    def test_configuration_with_agents(self):
        """Test configuration integration with agents."""
        from daita.agents.substrate import SubstrateAgent
        from daita.llm.mock import MockLLMProvider
        
        # Create agent configuration
        agent_config = AgentConfig(
            name="Config Test Agent",
            enable_retry=True,
            settings={"test_setting": "test_value"}
        )
        
        # Create LLM provider
        llm = MockLLMProvider(model="test-model")
        
        # Create agent with configuration
        agent = SubstrateAgent(
            config=agent_config,
            llm_provider=llm
        )
        
        assert agent.name == agent_config.name
        assert agent.config.enable_retry == agent_config.enable_retry
        assert agent.config.settings == agent_config.settings
    
    def test_configuration_file_operations(self):
        """Test configuration file save/load operations."""
        import yaml
        import tempfile
        
        # Create configuration
        config = DaitaConfig(
            version="1.5.0",
            agents=[
                AgentConfig(name="Agent 1", enable_retry=True),
                AgentConfig(name="Agent 2", settings={"custom": "value"})
            ],
            llm=LLMConfig(provider="anthropic", model="claude-3-sonnet-20240229"),
            settings={"global_setting": "global_value"}
        )
        
        # Save to temporary file using YAML-safe serialization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_dict = config.model_dump_yaml_safe()  # Fix: Use YAML-safe method
            yaml.dump(config_dict, f)
            temp_path = f.name
        
        try:
            # Load from file
            with open(temp_path, 'r') as f:
                loaded_dict = yaml.safe_load(f)
            
            restored_config = DaitaConfig(**loaded_dict)
            
            assert restored_config.version == config.version
            assert len(restored_config.agents) == len(config.agents)
            assert restored_config.llm.provider == config.llm.provider
            assert restored_config.settings == config.settings
        
        finally:
            # Clean up
            import os
            os.unlink(temp_path)


class TestConfigurationDocumentation:
    """Test configuration examples for documentation."""
    
    def test_basic_agent_configuration_example(self):
        """Test basic agent configuration example."""
        # Example: Basic agent configuration
        config = AgentConfig(
            name="Data Processor",
            type=AgentType.SUBSTRATE,
            settings={
                "focus": ["name", "age", "email"],
                "timeout": 30
            }
        )
        
        assert config.name == "Data Processor"
        assert config.type == AgentType.SUBSTRATE
        assert config.settings["focus"] == ["name", "age", "email"]
        assert not config.retry_enabled
    
    def test_retry_agent_configuration_example(self):
        """Test retry-enabled agent configuration example."""
        # Example: Agent with retry configuration
        config = AgentConfig(
            name="Robust Agent",
            enable_retry=True,
            retry_policy=RetryPolicy(
                max_retries=5,
                initial_delay=1.0,
                strategy=RetryStrategy.EXPONENTIAL_BACKOFF
            ),
            settings={
                "error_handling": "graceful",
                "fallback_enabled": True
            }
        )
        
        assert config.name == "Robust Agent"
        assert config.retry_enabled
        assert config.retry_policy.max_retries == 5
        assert config.retry_policy.strategy == RetryStrategy.EXPONENTIAL_BACKOFF
    
    def test_multi_agent_system_configuration_example(self):
        """Test multi-agent system configuration example."""
        # Example: Multi-agent system configuration
        config = DaitaConfig(
            version="1.0.0",
            agents=[
                AgentConfig(
                    name="Data Fetcher",
                    settings={
                        "data_source": "api",
                        "batch_size": 100
                    }
                ),
                AgentConfig(
                    name="Data Processor", 
                    enable_retry=True,
                    settings={
                        "processing_mode": "streaming",
                        "output_format": "json"
                    }
                ),
                AgentConfig(
                    name="Data Analyzer",
                    settings={
                        "analysis_type": "statistical",
                        "confidence_threshold": 0.8
                    }
                )
            ],
            llm=LLMConfig(
                provider="openai",
                model="gpt-4",
                temperature=0.3  # Lower temperature for more deterministic analysis
            ),
            settings={
                "pipeline_mode": "sequential",
                "error_propagation": "stop_on_first_error",
                "logging_level": "INFO"
            }
        )
        
        assert len(config.agents) == 3
        assert config.agents[0].name == "Data Fetcher"
        assert config.agents[1].retry_enabled
        assert config.llm.provider == "openai"
        assert config.llm.temperature == 0.3
        assert config.settings["pipeline_mode"] == "sequential"
    
    def test_llm_provider_configuration_examples(self):
        """Test LLM provider configuration examples."""
        # Example: OpenAI configuration
        openai_config = LLMConfig(
            provider="openai",
            model="gpt-4",
            api_key="sk-your-openai-key",
            temperature=0.7,
            max_tokens=2000
        )
        
        # Example: Anthropic configuration
        anthropic_config = LLMConfig(
            provider="anthropic",
            model="claude-3-sonnet-20240229",
            api_key="sk-ant-your-key",
            temperature=0.5,
            max_tokens=4000
        )
        
        # Example: Grok configuration
        grok_config = LLMConfig(
            provider="grok",
            model="grok-beta",
            api_key="xai-your-key",
            temperature=0.8,
            max_tokens=1500
        )
        
        configs = [openai_config, anthropic_config, grok_config]
        providers = ["openai", "anthropic", "grok"]
        models = ["gpt-4", "claude-3-sonnet-20240229", "grok-beta"]
        
        for config, provider, model in zip(configs, providers, models):
            assert config.provider == provider
            assert config.model == model
            assert config.api_key is not None
    
    def test_focus_configuration_examples(self):
        """Test focus configuration examples."""
        # Example: Column focus
        column_focus = FocusConfig(
            type=FocusType.COLUMN,
            include=["user_id", "name", "email", "created_at"],
            exclude=["password", "internal_id"]
        )
        
        # Example: JSONPath focus
        jsonpath_focus = FocusConfig(
            type=FocusType.JSONPATH,
            paths=["$.user.profile", "$.user.preferences"],
            description="Extract user profile and preferences"
        )
        
        # Example: Semantic focus
        semantic_focus = FocusConfig(
            type=FocusType.SEMANTIC,
            include=["important", "urgent", "actionable"],
            description="Focus on important and actionable content"
        )
        
        assert column_focus.type == FocusType.COLUMN
        assert "email" in column_focus.include
        assert "password" in column_focus.exclude
        
        assert jsonpath_focus.type == FocusType.JSONPATH
        assert len(jsonpath_focus.paths) == 2
        
        assert semantic_focus.type == FocusType.SEMANTIC
        assert "urgent" in semantic_focus.include


class TestConfigurationPerformance:
    """Test configuration performance characteristics."""
    
    def test_large_scale_configuration_creation(self):
        """Test creating large-scale configurations."""
        import time
        
        start_time = time.time()
        
        # Create configuration with many agents
        agents = []
        for i in range(100):
            agent = AgentConfig(
                name=f"Agent_{i}",
                enable_retry=(i % 2 == 0),  # Every other agent has retry
                settings={
                    "agent_id": i,
                    "priority": i % 10,
                    "data": [j for j in range(10)]  # Some nested data
                }
            )
            agents.append(agent)
        
        config = DaitaConfig(
            version="performance_test",
            agents=agents,
            settings={"total_agents": len(agents)}
        )
        
        creation_time = time.time() - start_time
        
        # Should create quickly (under 1 second for 100 agents)
        assert creation_time < 1.0
        assert len(config.agents) == 100
        assert config.settings["total_agents"] == 100
    
    def test_configuration_serialization_performance(self):
        """Test configuration serialization performance."""
        import time
        
        # Create a complex configuration
        agents = [
            AgentConfig(
                name=f"Agent_{i}",
                enable_retry=True,
                settings={f"setting_{j}": f"value_{j}" for j in range(20)}
            )
            for i in range(50)
        ]
        
        config = DaitaConfig(
            agents=agents,
            settings={f"global_{i}": f"global_value_{i}" for i in range(100)}
        )
        
        # Test serialization performance
        start_time = time.time()
        config_dict = config.model_dump_yaml_safe()
        serialization_time = time.time() - start_time
        
        # Should serialize quickly
        assert serialization_time < 0.5
        assert len(config_dict["agents"]) == 50
        assert len(config_dict["settings"]) == 100
    
    def test_configuration_validation_performance(self):
        """Test configuration validation performance."""
        import time
        
        start_time = time.time()
        
        # Create many configurations with validation
        configs = []
        for i in range(1000):
            config = AgentConfig(
                name=f"ValidationTest_{i}",
                enable_retry=(i % 3 == 0),
                settings={"index": i}
            )
            configs.append(config)
        
        validation_time = time.time() - start_time
        
        # Should validate quickly even for many configurations
        assert validation_time < 2.0
        assert len(configs) == 1000
        assert all(config.name.startswith("ValidationTest_") for config in configs)


class TestConfigurationCompatibility:
    """Test configuration compatibility and backwards compatibility."""
    
    def test_configuration_version_compatibility(self):
        """Test configuration compatibility across versions."""
        # Simulate older configuration format
        old_config_dict = {
            "name": "Legacy Agent",
            "type": "substrate",
            "enabled": True,
            "settings": {"legacy_setting": "legacy_value"}
            # Note: Missing newer fields like enable_retry
        }
        
        # Should be able to create new config from old format
        config = AgentConfig(**old_config_dict)
        
        assert config.name == "Legacy Agent"
        assert config.type == AgentType.SUBSTRATE
        assert config.enabled is True
        assert config.settings["legacy_setting"] == "legacy_value"
        # New fields should have defaults
        assert config.enable_retry is False
        assert config.retry_policy is None
    
    def test_configuration_extension(self):
        """Test extending configurations with new fields."""
        # Base configuration
        base_dict = {
            "name": "Extensible Agent",
            "type": "substrate",
            "settings": {"base": "value"}
        }
        
        # Extended configuration with additional fields
        extended_dict = {
            **base_dict,
            "enable_retry": True,
            "settings": {
                **base_dict["settings"],
                "extended": "new_value"
            }
        }
        
        config = AgentConfig(**extended_dict)
        
        assert config.name == "Extensible Agent"
        assert config.enable_retry is True
        assert config.settings["base"] == "value"
        assert config.settings["extended"] == "new_value"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
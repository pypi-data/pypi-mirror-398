"""
Centralized test configuration for the Daita framework testing suite.

Provides configuration, utilities, and setup for all test levels.
"""

import os
import sys
import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add daita to path for all tests
DAITA_ROOT = Path(__file__).parent.parent / "daita"
if str(DAITA_ROOT) not in sys.path:
    sys.path.insert(0, str(DAITA_ROOT))

class TestConfig:
    """Central configuration for all tests."""
    
    # Test environment settings
    TEST_TIMEOUT = 30  # Default test timeout in seconds
    PERFORMANCE_TEST_TIMEOUT = 120  # Performance tests need more time
    
    # API availability flags
    OPENAI_AVAILABLE = bool(os.getenv("OPENAI_API_KEY"))
    ANTHROPIC_AVAILABLE = bool(os.getenv("ANTHROPIC_API_KEY"))
    LLM_AVAILABLE = OPENAI_AVAILABLE or ANTHROPIC_AVAILABLE
    
    # Database test settings
    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    
    # Performance test thresholds
    PERFORMANCE_THRESHOLDS = {
        "max_agent_creation_time": 0.1,  # seconds
        "max_processing_latency": 0.05,  # seconds
        "min_throughput": 100,  # operations per second
        "max_memory_per_agent": 10,  # MB
        "max_concurrent_workflows": 50
    }
    
    # Test data sizes
    SMALL_DATASET_SIZE = 10
    MEDIUM_DATASET_SIZE = 100
    LARGE_DATASET_SIZE = 1000
    STRESS_DATASET_SIZE = 5000
    
    @classmethod
    def get_test_markers(cls) -> Dict[str, str]:
        """Get pytest markers for test categorization."""
        return {
            "unit": "Unit tests - fast, isolated tests",
            "integration": "Integration tests - test component interactions", 
            "performance": "Performance tests - measure speed and resource usage",
            "slow": "Slow tests - may take several seconds",
            "requires_llm": "Tests that require LLM API keys",
            "requires_db": "Tests that require database setup",
            "stress": "Stress tests - high load scenarios"
        }
    
    @classmethod
    def should_skip_llm_tests(cls) -> bool:
        """Check if LLM tests should be skipped."""
        return not cls.LLM_AVAILABLE
    
    @classmethod
    def get_skip_reason(cls, test_type: str) -> str:
        """Get skip reason for different test types."""
        reasons = {
            "llm": "No LLM API keys available (set OPENAI_API_KEY or ANTHROPIC_API_KEY)",
            "openai": "OpenAI API key not available (set OPENAI_API_KEY)",
            "anthropic": "Anthropic API key not available (set ANTHROPIC_API_KEY)",
            "database": "Test database not available",
            "performance": "Performance tests disabled in CI"
        }
        return reasons.get(test_type, f"Test type {test_type} requirements not met")

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    # Register custom markers
    markers = TestConfig.get_test_markers()
    for marker, description in markers.items():
        config.addinivalue_line("markers", f"{marker}: {description}")
    
    # Set test timeout
    config.addinivalue_line("timeout", str(TestConfig.TEST_TIMEOUT))
    
    # Configure asyncio mode
    config.addinivalue_line("asyncio_mode", "auto")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers and skip conditions."""
    for item in items:
        # Add markers based on test path
        test_path = str(item.fspath)
        
        if "/integration/" in test_path:
            item.add_marker(pytest.mark.integration)
        
        if "/performance/" in test_path:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        if "test_basic_agents" in test_path:
            item.add_marker(pytest.mark.unit)
        
        # Add skip conditions
        if hasattr(item, 'get_closest_marker'):
            if item.get_closest_marker("requires_llm") and TestConfig.should_skip_llm_tests():
                skip_reason = TestConfig.get_skip_reason("llm")
                item.add_marker(pytest.mark.skip(reason=skip_reason))

# Test utilities and fixtures
@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration to tests."""
    return TestConfig()

@pytest.fixture(scope="session") 
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_environment():
    """Provide clean mock environment for tests."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "DAITA_ENVIRONMENT": "test",
        "DAITA_LOG_LEVEL": "DEBUG",
        "DAITA_LOCAL_MODE": "true"
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory for tests."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create basic project structure
    (project_dir / ".daita").mkdir()
    (project_dir / "agents").mkdir()
    (project_dir / "workflows").mkdir()
    
    # Create basic config file
    config_content = """
project_name: test_project
version: 1.0.0
agents: []
workflows: []
"""
    (project_dir / "daita.yaml").write_text(config_content)
    
    return project_dir

# Performance test utilities
class PerformanceTracker:
    """Track performance metrics during tests."""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, name: str):
        """Start timing an operation."""
        import time
        self.start_times[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timing and return duration."""
        import time
        if name not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[name]
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(duration)
        
        return duration
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        if name not in self.metrics:
            return {}
        
        import statistics
        values = self.metrics[name]
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "total": sum(values)
        }

@pytest.fixture
def performance_tracker():
    """Provide performance tracking for tests."""
    return PerformanceTracker()

# Test data helpers
def create_test_agent_config(name: str = "test_agent", **kwargs) -> Dict[str, Any]:
    """Create test agent configuration."""
    return {
        "name": name,
        "type": "substrate",
        "enable_retry": kwargs.get("enable_retry", False),
        **kwargs
    }

def create_test_workflow_config(name: str = "test_workflow", **kwargs) -> Dict[str, Any]:
    """Create test workflow configuration."""
    return {
        "name": name,
        "agents": kwargs.get("agents", []),
        "connections": kwargs.get("connections", []),
        **kwargs
    }

# Assertion helpers
def assert_response_structure(response: Dict[str, Any], required_fields: List[str]):
    """Assert that response has required structure."""
    assert isinstance(response, dict), f"Expected dict, got {type(response)}"
    
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"

def assert_performance_threshold(actual: float, threshold: float, metric_name: str):
    """Assert that performance meets threshold."""
    assert actual <= threshold, f"{metric_name} threshold exceeded: {actual} > {threshold}"

def assert_agent_health(agent, expected_status: str = "healthy"):
    """Assert agent health status."""
    health = agent.health
    assert isinstance(health, dict), "Health should be a dictionary"
    assert "id" in health, "Health missing agent ID"
    assert "name" in health, "Health missing agent name"

# Custom pytest markers for better test organization
pytest_markers = {
    "basic": pytest.mark.basic,
    "intermediate": pytest.mark.intermediate, 
    "advanced": pytest.mark.advanced,
    "core": pytest.mark.core,
    "load": pytest.mark.load,
    "memory": pytest.mark.memory,
    "latency": pytest.mark.latency
}

# Export test utilities
__all__ = [
    "TestConfig",
    "PerformanceTracker", 
    "create_test_agent_config",
    "create_test_workflow_config",
    "assert_response_structure",
    "assert_performance_threshold", 
    "assert_agent_health",
    "pytest_markers"
]
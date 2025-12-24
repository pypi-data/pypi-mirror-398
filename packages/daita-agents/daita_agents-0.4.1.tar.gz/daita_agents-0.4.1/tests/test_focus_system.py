"""
Test suite for Focus System - testing data filtering and selection capabilities.

Tests cover:
- Focus parameter validation
- Dictionary data focusing
- DataFrame data focusing (with pandas)
- List of dictionaries focusing
- Focus configuration types (list, string, dict)
- Include/exclude patterns
- Primary/secondary focus
- Error handling and edge cases
- Integration with agents
"""
import pytest
import pandas as pd
from typing import Dict, Any, List
from unittest.mock import patch

from daita.core.focus import apply_focus
from daita.core.exceptions import ValidationError, InvalidDataError


class TestFocusParameterValidation:
    """Test validation of focus parameter formats."""
    
    def test_valid_string_focus(self):
        """Test validation of string focus parameters."""
        # Valid string focus should not raise errors
        data = {"name": "John", "age": 30}
        result = apply_focus(data, "name")
        assert result == {"name": "John"}
    
    def test_empty_string_focus_error(self):
        """Test that empty string focus raises validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, "")
        
        assert "Focus string cannot be empty" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, "   ")  # Whitespace only
        
        assert "Focus string cannot be empty" in str(exc_info.value)
    
    def test_valid_list_focus(self):
        """Test validation of list focus parameters."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        result = apply_focus(data, ["name", "age"])
        assert result == {"name": "John", "age": 30}
    
    def test_empty_list_focus_error(self):
        """Test that empty list focus raises validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, [])
        
        assert "Focus list cannot be empty" in str(exc_info.value)
    
    def test_list_with_non_string_items_error(self):
        """Test that list with non-string items raises validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, ["name", 123])
        
        assert "Focus list item 1 must be string" in str(exc_info.value)
    
    def test_list_with_empty_string_items_error(self):
        """Test that list with empty string items raises validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, ["name", ""])
        
        assert "Focus list item 1 cannot be empty" in str(exc_info.value)
    
    def test_valid_dict_focus(self):
        """Test validation of dictionary focus parameters."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer"}
        
        # Test include pattern
        result = apply_focus(data, {"include": ["name", "age"]})
        assert result == {"name": "John", "age": 30}
        
        # Test primary pattern
        result = apply_focus(data, {"primary": ["name", "city"]})
        assert result == {"name": "John", "city": "NYC"}
    
    def test_empty_dict_focus_error(self):
        """Test that empty dictionary focus raises validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {})
        
        assert "Focus dict cannot be empty" in str(exc_info.value)
    
    def test_invalid_dict_keys_error(self):
        """Test that invalid dictionary keys raise validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {"invalid_key": ["name"]})
        
        assert "Invalid focus keys: {'invalid_key'}" in str(exc_info.value)
        assert "Valid keys: {'include', 'exclude', 'primary', 'secondary'}" in str(exc_info.value)
    
    def test_dict_focus_without_required_keys_error(self):
        """Test that dict focus without include or primary raises error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {"exclude": ["age"]})  # Only exclude, no include/primary
        
        assert "Dict focus must contain 'include' or 'primary' key" in str(exc_info.value)
    
    def test_invalid_focus_type_error(self):
        """Test that invalid focus types raise validation error."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, 123)  # Number is not valid
        
        assert "Focus must be string, list, or dict" in str(exc_info.value)
    
    def test_dict_focus_invalid_value_types(self):
        """Test validation of values within dictionary focus."""
        data = {"name": "John", "age": 30}
        
        # Invalid include value type
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {"include": 123})
        
        assert "Focus 'include' must be string or list" in str(exc_info.value)
        
        # Empty include list
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {"include": []})
        
        assert "Focus 'include' list cannot be empty" in str(exc_info.value)
        
        # Empty include string
        with pytest.raises(ValidationError) as exc_info:
            apply_focus(data, {"include": ""})
        
        assert "Focus 'include' string cannot be empty" in str(exc_info.value)


class TestDictionaryFocus:
    """Test focus application on dictionary data."""
    
    def test_string_focus_single_key(self):
        """Test focusing on a single key with string focus."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer"}
        
        result = apply_focus(data, "name")
        
        assert result == {"name": "John"}
        assert len(result) == 1
    
    def test_string_focus_missing_key_error(self):
        """Test error when string focus key doesn't exist."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, "nonexistent")
        
        assert "Key 'nonexistent' not found in dict" in str(exc_info.value)
        assert "Available: ['name', 'age']" in str(exc_info.value)
    
    def test_list_focus_multiple_keys(self):
        """Test focusing on multiple keys with list focus."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer", "salary": 50000}
        
        result = apply_focus(data, ["name", "age", "city"])
        
        expected = {"name": "John", "age": 30, "city": "NYC"}
        assert result == expected
        assert len(result) == 3
    
    def test_list_focus_missing_keys_error(self):
        """Test error when list focus contains missing keys."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, ["name", "nonexistent", "missing"])
        
        assert "Keys not found in dict: ['nonexistent', 'missing']" in str(exc_info.value)
    
    def test_list_focus_partial_missing_keys_error(self):
        """Test error when some keys in list focus are missing."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, ["name", "age", "nonexistent"])
        
        assert "Keys not found in dict: ['nonexistent']" in str(exc_info.value)
    
    def test_dict_focus_include_only(self):
        """Test dictionary focus with include pattern only."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer", "salary": 50000}
        
        result = apply_focus(data, {"include": ["name", "job", "salary"]})
        
        expected = {"name": "John", "job": "Engineer", "salary": 50000}
        assert result == expected
    
    def test_dict_focus_include_string(self):
        """Test dictionary focus with include as string."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        
        result = apply_focus(data, {"include": "name"})
        
        assert result == {"name": "John"}
    
    def test_dict_focus_include_with_exclude(self):
        """Test dictionary focus with both include and exclude."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer", "salary": 50000}
        
        result = apply_focus(data, {
            "include": ["name", "age", "city", "job"],
            "exclude": ["age", "city"]
        })
        
        expected = {"name": "John", "job": "Engineer"}
        assert result == expected
    
    def test_dict_focus_include_exclude_nonexistent(self):
        """Test that excluding non-existent keys doesn't cause errors."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        
        result = apply_focus(data, {
            "include": ["name", "age"],
            "exclude": ["nonexistent", "age"]  # age exists, nonexistent doesn't
        })
        
        assert result == {"name": "John"}
    
    def test_dict_focus_primary_pattern(self):
        """Test dictionary focus with primary pattern."""
        data = {"name": "John", "age": 30, "city": "NYC", "job": "Engineer"}
        
        result = apply_focus(data, {"primary": ["name", "job"]})
        
        expected = {"name": "John", "job": "Engineer"}
        assert result == expected
    
    def test_dict_focus_primary_string(self):
        """Test dictionary focus with primary as string."""
        data = {"name": "John", "age": 30, "city": "NYC"}
        
        result = apply_focus(data, {"primary": "name"})
        
        assert result == {"name": "John"}
    
    def test_dict_focus_primary_missing_keys_error(self):
        """Test error when primary keys are missing."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, {"primary": ["name", "nonexistent"]})
        
        assert "Primary keys not found: ['nonexistent']" in str(exc_info.value)
    
    def test_dict_focus_include_missing_keys_error(self):
        """Test error when include keys are missing."""
        data = {"name": "John", "age": 30}
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, {"include": ["name", "nonexistent"]})
        
        assert "Include keys not found: ['nonexistent']" in str(exc_info.value)


class TestDataFrameFocus:
    """Test focus application on pandas DataFrame data."""
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'name': ['John', 'Jane', 'Bob'],
            'age': [25, 30, 35],
            'city': ['NYC', 'LA', 'Chicago'],
            'job': ['Engineer', 'Designer', 'Manager'],
            'salary': [50000, 60000, 70000]
        })
    
    def test_string_focus_single_column(self, sample_dataframe):
        """Test focusing on a single column with string focus."""
        result = apply_focus(sample_dataframe, "name")
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name"]
        assert len(result) == 3
        assert result["name"].tolist() == ['John', 'Jane', 'Bob']
    
    def test_string_focus_missing_column_error(self, sample_dataframe):
        """Test error when string focus column doesn't exist."""
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(sample_dataframe, "nonexistent")
        
        assert "Column 'nonexistent' not found in DataFrame" in str(exc_info.value)
        assert "Available: ['name', 'age', 'city', 'job', 'salary']" in str(exc_info.value)
    
    def test_list_focus_multiple_columns(self, sample_dataframe):
        """Test focusing on multiple columns with list focus."""
        result = apply_focus(sample_dataframe, ["name", "age", "salary"])
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "age", "salary"]
        assert len(result) == 3
        assert result["name"].tolist() == ['John', 'Jane', 'Bob']
        assert result["age"].tolist() == [25, 30, 35]
        assert result["salary"].tolist() == [50000, 60000, 70000]
    
    def test_list_focus_missing_columns_error(self, sample_dataframe):
        """Test error when list focus contains missing columns."""
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(sample_dataframe, ["name", "nonexistent", "missing"])
        
        assert "Columns not found in DataFrame: ['nonexistent', 'missing']" in str(exc_info.value)
    
    def test_dict_focus_include_only(self, sample_dataframe):
        """Test dictionary focus with include pattern on DataFrame."""
        result = apply_focus(sample_dataframe, {"include": ["name", "job", "salary"]})
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "job", "salary"]
        assert len(result) == 3
    
    def test_dict_focus_include_string(self, sample_dataframe):
        """Test dictionary focus with include as string on DataFrame."""
        result = apply_focus(sample_dataframe, {"include": "name"})
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name"]
    
    def test_dict_focus_include_with_exclude(self, sample_dataframe):
        """Test dictionary focus with both include and exclude on DataFrame."""
        result = apply_focus(sample_dataframe, {
            "include": ["name", "age", "city", "job"],
            "exclude": ["age", "city"]
        })
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "job"]
        assert len(result) == 3
    
    def test_dict_focus_exclude_nonexistent_columns(self, sample_dataframe):
        """Test that excluding non-existent columns doesn't cause errors."""
        result = apply_focus(sample_dataframe, {
            "include": ["name", "age"],
            "exclude": ["nonexistent", "age"]
        })
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name"]
    
    def test_dict_focus_primary_pattern(self, sample_dataframe):
        """Test dictionary focus with primary pattern on DataFrame."""
        result = apply_focus(sample_dataframe, {"primary": ["name", "salary"]})
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["name", "salary"]
        assert len(result) == 3
    
    def test_dict_focus_primary_missing_columns_error(self, sample_dataframe):
        """Test error when primary columns are missing in DataFrame."""
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(sample_dataframe, {"primary": ["name", "nonexistent"]})
        
        assert "Primary columns not found: ['nonexistent']" in str(exc_info.value)
    
    def test_dict_focus_include_missing_columns_error(self, sample_dataframe):
        """Test error when include columns are missing in DataFrame."""
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(sample_dataframe, {"include": ["name", "nonexistent"]})
        
        assert "Include columns not found: ['nonexistent']" in str(exc_info.value)


class TestListOfDictionariesFocus:
    """Test focus application on list of dictionaries."""
    
    @pytest.fixture
    def sample_list_of_dicts(self):
        """Create a sample list of dictionaries for testing."""
        return [
            {"name": "John", "age": 25, "city": "NYC", "job": "Engineer"},
            {"name": "Jane", "age": 30, "city": "LA", "job": "Designer"},
            {"name": "Bob", "age": 35, "city": "Chicago", "job": "Manager"}
        ]
    
    def test_string_focus_single_key(self, sample_list_of_dicts):
        """Test focusing on a single key in list of dictionaries."""
        result = apply_focus(sample_list_of_dicts, "name")
        
        expected = [
            {"name": "John"},
            {"name": "Jane"},
            {"name": "Bob"}
        ]
        assert result == expected
    
    def test_list_focus_multiple_keys(self, sample_list_of_dicts):
        """Test focusing on multiple keys in list of dictionaries."""
        result = apply_focus(sample_list_of_dicts, ["name", "job"])
        
        expected = [
            {"name": "John", "job": "Engineer"},
            {"name": "Jane", "job": "Designer"},
            {"name": "Bob", "job": "Manager"}
        ]
        assert result == expected
    
    def test_dict_focus_include_pattern(self, sample_list_of_dicts):
        """Test dictionary focus with include pattern on list of dictionaries."""
        result = apply_focus(sample_list_of_dicts, {"include": ["name", "age"]})
        
        expected = [
            {"name": "John", "age": 25},
            {"name": "Jane", "age": 30},
            {"name": "Bob", "age": 35}
        ]
        assert result == expected
    
    def test_dict_focus_include_with_exclude(self, sample_list_of_dicts):
        """Test dictionary focus with include and exclude on list of dictionaries."""
        result = apply_focus(sample_list_of_dicts, {
            "include": ["name", "age", "city"],
            "exclude": ["age"]
        })
        
        expected = [
            {"name": "John", "city": "NYC"},
            {"name": "Jane", "city": "LA"},
            {"name": "Bob", "city": "Chicago"}
        ]
        assert result == expected
    
    def test_empty_list_passthrough(self):
        """Test that empty list passes through unchanged."""
        result = apply_focus([], ["name", "age"])
        
        assert result == []
    
    def test_missing_keys_error_in_list(self, sample_list_of_dicts):
        """Test error when keys are missing in list of dictionaries."""
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(sample_list_of_dicts, ["name", "nonexistent"])
        
        assert "Keys not found in dict: ['nonexistent']" in str(exc_info.value)


class TestFocusEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_none_focus_passthrough(self):
        """Test that None focus returns data unchanged."""
        data = {"name": "John", "age": 30}
        
        result = apply_focus(data, None)
        assert result == data
        assert result is data  # Should be same object
    
    def test_none_data_passthrough(self):
        """Test that None data returns None regardless of focus."""
        result = apply_focus(None, ["name", "age"])
        assert result is None
    
    def test_focus_on_unsupported_data_type_with_list_focus(self):
        """Test that structured focus on unsupported data types raises error."""
        data = "simple string"
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, ["name", "age"])
        
        assert "Cannot apply structured focus to str" in str(exc_info.value)
        assert "Focus requires dict, DataFrame, or list of dicts" in str(exc_info.value)
    
    def test_focus_on_unsupported_data_type_with_dict_focus(self):
        """Test that structured focus on unsupported data types raises error."""
        data = 12345
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(data, {"include": ["name"]})
        
        assert "Cannot apply structured focus to int" in str(exc_info.value)
    
    def test_string_focus_on_unsupported_data_type(self):
        """Test that string focus on unsupported data types returns original data."""
        data = "simple string"
        
        # String focus should just return original data with info message
        result = apply_focus(data, "some_field")
        assert result == data
    
    def test_focus_application_error_wrapping(self):
        """Test that unexpected errors are wrapped with context."""
        # Mock a DataFrame that raises unexpected error
        class BadDataFrame:
            @property
            def columns(self):
                raise RuntimeError("Unexpected DataFrame error")
        
        bad_df = BadDataFrame()
        
        with pytest.raises(InvalidDataError) as exc_info:
            apply_focus(bad_df, ["col1"])
        
        assert "Failed to apply focus" in str(exc_info.value)
        assert "Unexpected DataFrame error" in str(exc_info.value)


class TestFocusIntegrationWithAgents:
    """Test focus integration within agent processing."""
    
    def test_focus_with_agent_processing(self):
        """Test that focus works properly within agent context."""
        from daita.agents.substrate import SubstrateAgent
        from daita.llm.mock import MockLLMProvider
        
        # Create agent with focus configuration
        llm = MockLLMProvider()
        agent = SubstrateAgent(
            name="Test Agent",
            llm_provider=llm,
            focus=["name", "age"]  # Default focus
        )
        
        # Test that focus is stored correctly
        assert agent.default_focus == ["name", "age"]
    
    def test_focus_parameter_processing(self):
        """Test focus parameter processing in isolation."""
        # Test complex focus configuration
        data = {
            "personal": {"name": "John", "age": 30},
            "contact": {"email": "john@example.com", "phone": "123-456-7890"},
            "work": {"job": "Engineer", "salary": 50000, "department": "Tech"},
            "metadata": {"created": "2024-01-01", "updated": "2024-01-15"}
        }
        
        # Focus on specific top-level keys
        result = apply_focus(data, ["personal", "work"])
        
        expected = {
            "personal": {"name": "John", "age": 30},
            "work": {"job": "Engineer", "salary": 50000, "department": "Tech"}
        }
        assert result == expected


class TestFocusPerformance:
    """Test focus system performance with larger datasets."""
    
    def test_large_dictionary_focus(self):
        """Test focus performance with large dictionary."""
        # Create large dictionary
        large_dict = {f"field_{i}": f"value_{i}" for i in range(1000)}
        
        # Focus on subset
        focus_keys = [f"field_{i}" for i in range(0, 100, 10)]  # Every 10th field
        result = apply_focus(large_dict, focus_keys)
        
        assert len(result) == 10
        assert all(key in result for key in focus_keys)
    
    def test_large_dataframe_focus(self):
        """Test focus performance with large DataFrame."""
        # Create large DataFrame
        data = {f"col_{i}": range(1000) for i in range(50)}
        large_df = pd.DataFrame(data)
        
        # Focus on subset of columns
        focus_cols = [f"col_{i}" for i in range(0, 10)]
        result = apply_focus(large_df, focus_cols)
        
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == focus_cols
        assert len(result) == 1000
    
    def test_large_list_of_dicts_focus(self):
        """Test focus performance with large list of dictionaries."""
        # Create large list of dictionaries
        large_list = [
            {f"field_{i}": f"value_{j}_{i}" for i in range(20)}
            for j in range(1000)
        ]
        
        # Focus on subset of fields
        focus_fields = ["field_0", "field_5", "field_10"]
        result = apply_focus(large_list, focus_fields)
        
        assert len(result) == 1000
        assert all(len(item) == 3 for item in result)
        assert all(all(key in item for key in focus_fields) for item in result)


class TestFocusWithoutPandas:
    """Test focus system behavior when pandas is not available."""
    
    def test_focus_without_pandas_import(self):
        """Test that focus system works without pandas."""
        # Test with regular dictionary (should work fine)
        data = {"name": "John", "age": 30, "city": "NYC"}
        result = apply_focus(data, ["name", "age"])
        
        expected = {"name": "John", "age": 30}
        assert result == expected
    
    def test_dataframe_like_object_without_pandas(self):
        """Test focus with DataFrame-like object when pandas not available."""
        # Create mock DataFrame-like object
        class MockDataFrame:
            def __init__(self, data):
                self.data = data
                self.columns = list(data.keys())
            
            def __getitem__(self, key):
                if isinstance(key, list):
                    return MockDataFrame({k: self.data[k] for k in key})
                return self.data[key]
        
        mock_df = MockDataFrame({"name": ["John", "Jane"], "age": [25, 30], "city": ["NYC", "LA"]})
        
        # Should be detected as having columns attribute
        result = apply_focus(mock_df, ["name", "age"])
        
        assert hasattr(result, 'columns')
        assert result.columns == ["name", "age"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
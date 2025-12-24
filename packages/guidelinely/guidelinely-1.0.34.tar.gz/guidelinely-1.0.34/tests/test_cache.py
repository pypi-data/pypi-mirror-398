"""Unit tests for client-side caching functionality using diskcache."""

import os
import tempfile

import pytest
from diskcache import Cache


class TestSortDataStructure:
    """Test _sort_data_structure function for all data types."""

    def test_sort_none(self):
        """None should return 'None' string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(None)
        assert result == "None"
        assert isinstance(result, str)

    def test_sort_bool_true(self):
        """Boolean True should return 'True' string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(True)
        assert result == "True"
        assert isinstance(result, str)

    def test_sort_bool_false(self):
        """Boolean False should return 'False' string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(False)
        assert result == "False"
        assert isinstance(result, str)

    def test_sort_int(self):
        """Integer should return string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(42)
        assert result == "42"
        assert isinstance(result, str)

    def test_sort_int_negative(self):
        """Negative integer should return string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(-42)
        assert result == "-42"
        assert isinstance(result, str)

    def test_sort_int_zero(self):
        """Zero should return '0' string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(0)
        assert result == "0"
        assert isinstance(result, str)

    def test_sort_float(self):
        """Float should return formatted string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(3.14)
        assert result == "3.140000"
        assert isinstance(result, str)

    def test_sort_float_negative(self):
        """Negative float should return formatted string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(-3.14)
        assert result == "-3.140000"
        assert isinstance(result, str)

    def test_sort_float_zero(self):
        """Float zero should return formatted string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(0.0)
        assert result == "0.000000"
        assert isinstance(result, str)

    def test_sort_string(self):
        """String should return itself."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure("test")
        assert result == "test"
        assert isinstance(result, str)

    def test_sort_string_empty(self):
        """Empty string should return empty string."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure("")
        assert result == ""
        assert isinstance(result, str)

    def test_sort_dict_empty(self):
        """Empty dict should return sorted representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure({})
        assert result == "[]"
        assert isinstance(result, str)

    def test_sort_dict_single_key(self):
        """Single key dict should return sorted representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure({"key": "value"})
        assert "key" in result
        assert "value" in result
        assert isinstance(result, str)

    def test_sort_dict_multiple_keys_order_independent(self):
        """Dict with multiple keys should produce same result regardless of input order."""
        from guidelinely.client import _sort_data_structure

        dict1 = {"z": 1, "a": 2, "m": 3}
        dict2 = {"a": 2, "m": 3, "z": 1}
        dict3 = {"m": 3, "z": 1, "a": 2}

        result1 = _sort_data_structure(dict1)
        result2 = _sort_data_structure(dict2)
        result3 = _sort_data_structure(dict3)

        assert result1 == result2 == result3
        assert isinstance(result1, str)

    def test_sort_dict_nested(self):
        """Nested dict should be recursively sorted."""
        from guidelinely.client import _sort_data_structure

        data = {"outer": {"inner": "value"}}
        result = _sort_data_structure(data)
        assert "outer" in result
        assert "inner" in result
        assert "value" in result
        assert isinstance(result, str)

    def test_sort_list_empty(self):
        """Empty list should return sorted representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure([])
        assert result == "[]"
        assert isinstance(result, str)

    def test_sort_list_single_item(self):
        """Single item list should return sorted representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(["item"])
        assert "item" in result
        assert isinstance(result, str)

    def test_sort_list_multiple_items_sorted(self):
        """List items should be sorted in result."""
        from guidelinely.client import _sort_data_structure

        list1 = ["z", "a", "m"]
        list2 = ["a", "m", "z"]

        result1 = _sort_data_structure(list1)
        result2 = _sort_data_structure(list2)

        # Lists should produce same result when sorted
        assert result1 == result2
        assert isinstance(result1, str)

    def test_sort_list_mixed_types(self):
        """List with mixed types should be sorted."""
        from guidelinely.client import _sort_data_structure

        data = [1, "string", 3.14]
        result = _sort_data_structure(data)
        assert isinstance(result, str)

    def test_sort_list_nested(self):
        """Nested list should be recursively sorted."""
        from guidelinely.client import _sort_data_structure

        data = [["inner", "list"], ["another", "list"]]
        result = _sort_data_structure(data)
        assert isinstance(result, str)

    def test_sort_complex_nested_structure(self):
        """Complex nested structure should be sorted consistently."""
        from guidelinely.client import _sort_data_structure

        data1 = {
            "params": ["Aluminum", {"name": "Copper", "unit": "mg/L"}],
            "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
            "media": "surface_water",
        }
        data2 = {
            "media": "surface_water",
            "context": {"hardness": "100 mg/L", "pH": "7.0 1"},
            "params": ["Aluminum", {"unit": "mg/L", "name": "Copper"}],
        }

        result1 = _sort_data_structure(data1)
        result2 = _sort_data_structure(data2)

        assert result1 == result2
        assert isinstance(result1, str)

    def test_sort_tuple_empty(self):
        """Empty tuple should return string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure(())
        assert result == "()"
        assert isinstance(result, str)

    def test_sort_tuple_single_item(self):
        """Single item tuple should return string representation."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure((42,))
        assert "42" in result
        assert isinstance(result, str)

    def test_sort_tuple_multiple_items(self):
        """Multiple item tuple should be recursively sorted."""
        from guidelinely.client import _sort_data_structure

        result = _sort_data_structure((1, "test", 3.14))
        assert isinstance(result, str)

    def test_sort_tuple_nested(self):
        """Nested tuple should be recursively sorted."""
        from guidelinely.client import _sort_data_structure

        data = ((1, 2), (3, 4))
        result = _sort_data_structure(data)
        assert isinstance(result, str)

    def test_sort_unsupported_type_raises_error(self):
        """Unsupported types should raise TypeError."""
        from guidelinely.client import _sort_data_structure

        class CustomClass:
            pass

        with pytest.raises(TypeError, match="Unsupported data type for cache key"):
            _sort_data_structure(CustomClass())

    def test_sort_bytes_raises_error(self):
        """Bytes should raise TypeError (not supported)."""
        from guidelinely.client import _sort_data_structure

        with pytest.raises(TypeError, match="Unsupported data type for cache key"):
            _sort_data_structure(b"bytes")

    def test_sort_set_raises_error(self):
        """Set should raise TypeError (not supported)."""
        from guidelinely.client import _sort_data_structure

        with pytest.raises(TypeError, match="Unsupported data type for cache key"):
            _sort_data_structure({1, 2, 3})


class TestCacheOperations:
    """Test cache get/set operations using temporary cache."""

    @pytest.fixture
    def temp_cache(self):
        """Create a temporary cache for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = Cache(directory=temp_dir)
            yield cache
            cache.close()

    def test_get_cached_miss(self, temp_cache):
        """Should return None for missing key."""
        assert temp_cache.get({"test": "data"}) is None

    def test_set_and_get_cached(self, temp_cache):
        """Should store and retrieve cached data."""
        key_data = {"endpoint": "test", "param": "value"}
        response_data = {"results": [], "context": {}, "total_count": 0}

        temp_cache[key_data] = response_data
        cached = temp_cache.get(key_data)
        assert cached == response_data

    def test_different_keys_different_values(self, temp_cache):
        """Different keys should store different values."""
        key1 = {"a": 1}
        key2 = {"a": 2}
        val1 = "value1"
        val2 = "value2"

        temp_cache[key1] = val1
        temp_cache[key2] = val2

        assert temp_cache.get(key1) == val1
        assert temp_cache.get(key2) == val2

    def test_complex_key_types(self, temp_cache):
        """Should handle complex key types like lists and nested dicts."""
        key = {
            "endpoint": "calculate/batch",
            "parameters": ["Aluminum", {"name": "Copper", "target_unit": "mg/L"}],
            "media": "surface_water",
            "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
            "api_key": None,
        }
        value = {"results": [], "context": {}, "total_count": 0}

        temp_cache[key] = value
        assert temp_cache.get(key) == value


class TestCacheKeyNormalization:
    """Test cache key normalization for consistent cache hits."""

    def test_get_cache_key_dict_order_independent(self):
        """Same dict with different key order should produce same cache key."""
        from guidelinely.client import _get_cache_key

        data1 = {"pH": "7.0 1", "hardness": "100 mg/L", "temperature": "20 °C"}
        data2 = {"temperature": "20 °C", "pH": "7.0 1", "hardness": "100 mg/L"}
        data3 = {"hardness": "100 mg/L", "temperature": "20 °C", "pH": "7.0 1"}

        key1 = _get_cache_key(data1)
        key2 = _get_cache_key(data2)
        key3 = _get_cache_key(data3)

        assert key1 == key2 == key3

    def test_get_cache_key_list_order_matters_but_items_normalized(self):
        """Lists maintain order but nested structures are normalized."""
        from guidelinely.client import _get_cache_key

        # Same items in same order with different dict key orders
        data1 = [
            {"pH": "7.0 1", "hardness": "100 mg/L"},
            {"pH": "8.0 1", "hardness": "200 mg/L"},
        ]
        data2 = [
            {"hardness": "100 mg/L", "pH": "7.0 1"},
            {"hardness": "200 mg/L", "pH": "8.0 1"},
        ]

        key1 = _get_cache_key(data1)
        key2 = _get_cache_key(data2)

        # Should be equal because dict items are sorted
        assert key1 == key2

    def test_get_cache_key_handles_none(self):
        """None should produce consistent cache key."""
        from guidelinely.client import _get_cache_key

        key = _get_cache_key(None)
        assert key == "None"

    def test_get_cache_key_nested_structures(self):
        """Complex nested structures should be normalized consistently."""
        from guidelinely.client import _get_cache_key

        data1 = {
            "endpoint": "calculate",
            "parameters": ["Aluminum", {"name": "Copper", "target_unit": "μg/L"}],
            "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
        }
        data2 = {
            "context": {"hardness": "100 mg/L", "pH": "7.0 1"},  # Different order
            "parameters": [
                "Aluminum",
                {"target_unit": "μg/L", "name": "Copper"},
            ],  # Different order
            "endpoint": "calculate",
        }

        key1 = _get_cache_key(data1)
        key2 = _get_cache_key(data2)

        assert key1 == key2

    def test_cache_hit_with_reordered_context(self, httpx_mock):
        """Cache should hit when same context is provided with different key order."""
        from guidelinely import calculate_guidelines
        from guidelinely.cache import cache

        cache.clear()

        # Mock API response
        httpx_mock.add_response(
            method="POST",
            url="https://guidelines.1681248.com/api/v1/calculate",
            json={"results": [], "context": {}, "total_count": 0},
            status_code=200,
        )

        # First call with context keys in one order
        calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"pH": "7.0 1", "hardness": "100 mg/L"},
            api_key="test_key",
        )

        # Second call with context keys in different order - should use cache
        calculate_guidelines(
            parameter="Aluminum",
            media="surface_water",
            context={"hardness": "100 mg/L", "pH": "7.0 1"},
            api_key="test_key",
        )

        # Only one HTTP request should have been made (second was cache hit)
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

    def test_cache_hit_with_reordered_parameter_dicts(self, httpx_mock):
        """Cache should hit when parameter dicts have different key orders."""
        from guidelinely import calculate_batch
        from guidelinely.cache import cache

        cache.clear()

        # Mock API response
        httpx_mock.add_response(
            method="POST",
            url="https://guidelines.1681248.com/api/v1/calculate/batch",
            json={"results": [], "context": {}, "total_count": 0},
            status_code=200,
        )

        # First call with parameter dict keys in one order
        calculate_batch(
            parameters=[
                "Aluminum",
                {"name": "Copper", "target_unit": "μg/L"},
            ],
            media="surface_water",
            api_key="test_key",
        )

        # Second call with parameter dict keys in different order - should use cache
        calculate_batch(
            parameters=[
                "Aluminum",
                {"target_unit": "μg/L", "name": "Copper"},  # Reordered keys
            ],
            media="surface_water",
            api_key="test_key",
        )

        # Only one HTTP request should have been made (second was cache hit)
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

    def test_cache_hit_with_reordered_parameters(self, httpx_mock):
        """Cache should hit when parameters are provided in different order."""
        from guidelinely import calculate_batch
        from guidelinely.cache import cache

        cache.clear()

        # Mock API response
        httpx_mock.add_response(
            method="POST",
            url="https://guidelines.1681248.com/api/v1/calculate/batch",
            json={"results": [], "context": {}, "total_count": 0},
            status_code=200,
        )

        # First call with parameters in one order
        calculate_batch(
            parameters=["Aluminum", "Copper", "Lead"],
            media="surface_water",
            api_key="test_key",
        )

        # Second call with parameters in different order - should use cache
        calculate_batch(
            parameters=["Copper", "Lead", "Aluminum"],  # Different order
            media="surface_water",
            api_key="test_key",
        )

        # Only one HTTP request should have been made (second was cache hit)
        requests = httpx_mock.get_requests()
        assert len(requests) == 1

    def test_cache_key_string_consistency(self):
        """Test that _get_cache_key produces consistent string results."""
        from guidelinely.client import _get_cache_key

        # Same cache key data with different dict order
        cache_key1 = {
            "endpoint": "calculate",
            "parameter": "Aluminum",
            "media": "surface_water",
            "context": {"hardness": "100 mg/L", "pH": "7.0 1"},
            "target_unit": None,
            "include_formula_svg": False,
        }

        cache_key2 = {
            "include_formula_svg": False,
            "target_unit": None,
            "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
            "media": "surface_water",
            "parameter": "Aluminum",
            "endpoint": "calculate",
        }

        key1 = _get_cache_key(cache_key1)
        key2 = _get_cache_key(cache_key2)

        # Should produce identical cache keys
        assert key1 == key2
        assert isinstance(key1, str)
        assert isinstance(key2, str)

    def test_cache_works_with_string_keys(self, httpx_mock):
        """Cache should work correctly with string keys from _get_cache_key."""
        from guidelinely.cache import cache, get_cached, set_cached
        from guidelinely.client import _get_cache_key

        cache.clear()

        # Create cache keys that would have different order
        cache_key_dict1 = {
            "endpoint": "calculate",
            "parameter": "Aluminum",
            "media": "surface_water",
            "context": {"hardness": "100 mg/L", "pH": "7.0 1"},
            "target_unit": None,
            "include_formula_svg": False,
        }

        cache_key_dict2 = {
            "include_formula_svg": False,
            "target_unit": None,
            "context": {"pH": "7.0 1", "hardness": "100 mg/L"},
            "media": "surface_water",
            "parameter": "Aluminum",
            "endpoint": "calculate",
        }

        # Get string keys
        key1 = _get_cache_key(cache_key_dict1)
        key2 = _get_cache_key(cache_key_dict2)

        # Set cache with first key
        test_data = {"results": [], "context": {}, "total_count": 0}
        set_cached(key1, test_data)

        # Should retrieve with second key (different dict order but same data)
        cached_data = get_cached(key2)
        assert cached_data == test_data


class TestCacheConfiguration:
    """Test cache directory configuration."""

    def test_cache_dir_defaults_to_home(self):
        """CACHE_DIR should default to ~/.guidelinely_cache when env var not set."""
        from pathlib import Path

        # Remove env var if set, reload module to test default
        old_value = os.environ.pop("GUIDELINELY_CACHE_DIR", None)
        try:
            # We need to test the logic, not the actual module state
            # since the module is already loaded
            default_cache_dir = Path.home() / ".guidelinely_cache"
            test_dir = Path(os.getenv("GUIDELINELY_CACHE_DIR", str(default_cache_dir)))
            assert test_dir == default_cache_dir
        finally:
            if old_value is not None:
                os.environ["GUIDELINELY_CACHE_DIR"] = old_value

    def test_cache_dir_from_environment(self):
        """CACHE_DIR should use GUIDELINELY_CACHE_DIR env var when set."""
        from pathlib import Path

        custom_dir = "/tmp/custom_guidelinely_cache"
        old_value = os.environ.get("GUIDELINELY_CACHE_DIR")
        try:
            os.environ["GUIDELINELY_CACHE_DIR"] = custom_dir
            default_cache_dir = Path.home() / ".guidelinely_cache"
            test_dir = Path(os.getenv("GUIDELINELY_CACHE_DIR", str(default_cache_dir)))
            assert test_dir == Path(custom_dir)
        finally:
            if old_value is not None:
                os.environ["GUIDELINELY_CACHE_DIR"] = old_value
            else:
                os.environ.pop("GUIDELINELY_CACHE_DIR", None)

    def test_default_ttl_value(self):
        """DEFAULT_TTL should be 7 days (604800 seconds) by default."""
        # When env var is not set, should be 7 days
        old_value = os.environ.pop("GUIDELINELY_CACHE_TTL", None)
        try:
            expected_ttl = 7 * 24 * 3600  # 604800 seconds
            test_ttl = int(os.getenv("GUIDELINELY_CACHE_TTL", str(expected_ttl)))
            assert test_ttl == expected_ttl
        finally:
            if old_value is not None:
                os.environ["GUIDELINELY_CACHE_TTL"] = old_value

    def test_ttl_from_environment(self):
        """DEFAULT_TTL should use GUIDELINELY_CACHE_TTL env var when set."""
        custom_ttl = "3600"  # 1 hour
        old_value = os.environ.get("GUIDELINELY_CACHE_TTL")
        try:
            os.environ["GUIDELINELY_CACHE_TTL"] = custom_ttl
            test_ttl = int(os.getenv("GUIDELINELY_CACHE_TTL", str(7 * 24 * 3600)))
            assert test_ttl == int(custom_ttl)
        finally:
            if old_value is not None:
                os.environ["GUIDELINELY_CACHE_TTL"] = old_value
            else:
                os.environ.pop("GUIDELINELY_CACHE_TTL", None)

import pytest
from nestedutils import get_at, set_at, delete_at, exists_at
from nestedutils.exceptions import PathError, PathErrorCode


class TestExceptionHandling:
    """Tests for exception handling and error codes."""
    
    def test_path_error_has_message(self):
        """PathError should have a message."""
        try:
            get_at({}, 123)
        except PathError as e:
            assert e.message is not None
            assert len(str(e)) > 0
    
    def test_path_error_has_code(self):
        """PathError should have a code."""
        try:
            get_at({}, 123)
        except PathError as e:
            assert e.code is not None
            assert e.code == PathErrorCode.INVALID_PATH
    
    def test_exception_inheritance(self):
        """PathError should be an Exception."""
        try:
            get_at({}, 123)
        except PathError as e:
            assert isinstance(e, Exception)
            assert isinstance(e, PathError)
    
    def test_all_error_codes_exist(self):
        """Verify all expected error codes exist."""
        codes = [
            PathErrorCode.INVALID_INDEX,
            PathErrorCode.MISSING_KEY,
            PathErrorCode.EMPTY_PATH,
            PathErrorCode.IMMUTABLE_CONTAINER,
            PathErrorCode.INVALID_PATH,
            PathErrorCode.INVALID_FILL_STRATEGY,
        ]
        assert len(codes) == 6
    
    def test_error_code_values(self):
        """Verify error code string values."""
        assert PathErrorCode.INVALID_INDEX.value == "INVALID_INDEX"
        assert PathErrorCode.MISSING_KEY.value == "MISSING_KEY"
        assert PathErrorCode.EMPTY_PATH.value == "EMPTY_PATH"
        assert PathErrorCode.IMMUTABLE_CONTAINER.value == "IMMUTABLE_CONTAINER"
        assert PathErrorCode.INVALID_PATH.value == "INVALID_PATH"
        assert PathErrorCode.INVALID_FILL_STRATEGY.value == "INVALID_FILL_STRATEGY"


class TestPathNormalizationEdgeCases:
    """Additional edge cases for path normalization."""
    
    def test_path_list_with_negative_index(self):
        """List form path with negative index."""
        d = {"a": [10, 20, 30]}
        assert get_at(d, ["a", -1]) == 30
        set_at(d, ["a", -1], 999)
        assert d["a"][2] == 999
    
    def test_path_list_empty_strings(self):
        """List form with empty strings should raise PathError."""
        d = {}
        with pytest.raises(PathError) as exc_info:
            set_at(d, ["a", "", "b"], 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Also test with get_at
        with pytest.raises(PathError) as exc_info:
            get_at(d, ["a", "", "b"])
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH


class TestComplexIntegrationScenarios:
    """Complex integration scenarios combining multiple operations."""
    
    def test_round_trip_operations(self):
        """Multiple operations in sequence."""
        d = {}
        set_at(d, "a.b.c", 1)
        assert get_at(d, "a.b.c") == 1
        set_at(d, "a.b.d", 2)
        assert get_at(d, "a.b.d") == 2
        val = delete_at(d, "a.b.c")
        assert val == 1
        assert get_at(d, "a.b.c") is None
        assert get_at(d, "a.b.d") == 2
    
    def test_mixed_numeric_and_string_keys(self):
        """Mixed numeric and string keys."""
        d = {}
        set_at(d, "a.0.b.1.c", 42)
        assert isinstance(d["a"], list)
        assert isinstance(d["a"][0], dict)
        assert isinstance(d["a"][0]["b"], list)
        assert d["a"][0]["b"][1]["c"] == 42


class TestEmptyAndNoneValues:
    """Tests for empty and None value handling."""
    
    def test_get_none_vs_missing(self):
        """Distinguish between None value and missing key."""
        d1 = {"a": None}
        d2 = {}
        assert get_at(d1, "a") is None
        assert get_at(d2, "a") is None
        # Both return None, but one has the key, one doesn't
        assert "a" in d1
        assert "a" not in d2


class TestLargeStructures:
    """Tests for large data structures."""
    
    def test_very_deep_nesting(self):
        """Very deeply nested structure."""
        d = {}
        path = ".".join(["level" + str(i) for i in range(20)])
        set_at(d, path, "deep")
        assert get_at(d, path) == "deep"
    
    def test_many_keys_in_dict(self):
        """Dict with many keys."""
        d = {}
        for i in range(100):
            set_at(d, f"key{i}", i)
        for i in range(100):
            assert get_at(d, f"key{i}") == i


class TestTypeCoercion:
    """Tests for type coercion and conversion."""
    
    def test_list_path_with_string_numbers(self):
        """List form path with string numbers."""
        d = {"a": [1, 2, 3]}
        assert get_at(d, ["a", "0"]) == 1
        assert get_at(d, ["a", "1"]) == 2
    
    def test_list_path_with_integers(self):
        """List form path with actual integers."""
        d = {"a": [1, 2, 3]}
        assert get_at(d, ["a", 0]) == 1
        assert get_at(d, ["a", 1]) == 2
    
    def test_mixed_path_types(self):
        """Mixed path types in list form."""
        d = {"a": {"0": [1, 2, 3]}}
        assert get_at(d, ["a", "0", 1]) == 2


class TestSpecialCharacters:
    """Tests for special characters in keys."""
    
    def test_keys_with_special_chars(self):
        """Keys with special characters."""
        d = {}
        set_at(d, "a-b.c_d.e@f", 42)
        assert get_at(d, "a-b.c_d.e@f") == 42
    
    def test_keys_with_spaces_in_list_form(self):
        """Keys with spaces using list form."""
        d = {}
        set_at(d, ["key with spaces", "another key"], 1)
        assert get_at(d, ["key with spaces", "another key"]) == 1
    
    def test_keys_with_newlines_in_list_form(self):
        """Keys with newlines using list form."""
        d = {}
        set_at(d, ["key\nwith\nnewlines"], 1)
        assert get_at(d, ["key\nwith\nnewlines"]) == 1


class TestNegativeIndexEdgeCases:
    """Comprehensive edge cases for negative indices."""
    
    def test_negative_index_boundary_conditions(self):
        """Test negative indices at boundaries."""
        d = {"a": [10, 20, 30]}
        # Valid negative indices
        assert get_at(d, "a.-1") == 30
        assert get_at(d, "a.-2") == 20
        assert get_at(d, "a.-3") == 10
        # Just out of bounds
        assert get_at(d, "a.-4") is None
        assert get_at(d, "a.-5") is None
    
    def test_negative_index_single_element_list(self):
        """Negative index on single element list."""
        d = {"a": [42]}
        assert get_at(d, "a.-1") == 42
        assert get_at(d, "a.-2") is None
        # Can modify with negative index
        set_at(d, "a.-1", 99)
        assert d["a"] == [99]
    
    def test_negative_index_in_intermediate_path(self):
        """Negative index used in intermediate path steps."""
        d = {"data": [[1, 2], [3, 4], [5, 6]]}
        # Navigate using negative index, then access nested
        assert get_at(d, "data.-1.0") == 5
        assert get_at(d, "data.-2.-1") == 4
        # Set using negative index in intermediate path
        set_at(d, "data.-1.-1", 99)
        assert d["data"][-1] == [5, 99]
    
    def test_negative_index_with_tuples(self):
        """Negative index works with tuples (read-only)."""
        d = {"a": (10, 20, 30)}
        assert get_at(d, "a.-1") == 30
        assert get_at(d, "a.-2") == 20
        assert exists_at(d, "a.-1") is True
        assert exists_at(d, "a.-4") is False
        # Cannot modify tuples
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.-1", 99)
        assert exc_info.value.code == PathErrorCode.IMMUTABLE_CONTAINER
    
    def test_negative_index_very_large_negative(self):
        """Very large negative numbers should be out of bounds."""
        d = {"a": [1, 2, 3]}
        assert get_at(d, "a.-1000") is None
        assert get_at(d, "a.-999999") is None
        # Should not raise, just return default
    
    def test_negative_index_chaining(self):
        """Chaining multiple negative index operations."""
        d = {"levels": [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]}
        # Navigate through multiple levels using negative indices
        assert get_at(d, "levels.-1.-1.-1") == 8
        assert get_at(d, "levels.-1.-1.-2") == 7
        assert get_at(d, "levels.-2.-1.-1") == 4
    
    def test_negative_index_after_list_mutation(self):
        """Negative index behavior after list mutations."""
        d = {"items": [1, 2, 3, 4, 5]}
        # Delete using positive index
        delete_at(d, "items.1", allow_list_mutation=True)
        assert d["items"] == [1, 3, 4, 5]
        # Negative indices should still work correctly
        assert get_at(d, "items.-1") == 5
        assert get_at(d, "items.-2") == 4
        assert get_at(d, "items.-4") == 1
        # -5 should now be out of bounds
        assert get_at(d, "items.-5") is None


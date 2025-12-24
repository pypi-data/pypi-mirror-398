import pytest
from nestedutils import exists_at
from nestedutils.exceptions import PathError, PathErrorCode


class TestExistsBasic:
    """Basic exists_at functionality tests."""
    
    def test_exists_simple(self):
        """Check existence in simple dict."""
        d = {"a": 1}
        assert exists_at(d, "a") is True
        assert exists_at(d, "b") is False
    
    def test_exists_nested_dict(self):
        """Check existence in deeply nested dict."""
        d = {"a": {"b": {"c": 5}}}
        assert exists_at(d, "a.b.c") is True
        assert exists_at(d, "a.b.d") is False
        assert exists_at(d, "a.c") is False
        assert exists_at(d, "x.y.z") is False
    
    def test_exists_list_index(self):
        """Check existence in list using index."""
        d = {"a": [10, 20, 30]}
        assert exists_at(d, "a.0") is True
        assert exists_at(d, "a.1") is True
        assert exists_at(d, "a.2") is True
        assert exists_at(d, "a.3") is False
        assert exists_at(d, "a.5") is False
    
    def test_exists_negative_list_index(self):
        """Check existence using negative list index."""
        d = {"a": [10, 20, 30]}
        assert exists_at(d, "a.-1") is True
        assert exists_at(d, "a.-2") is True
        assert exists_at(d, "a.-3") is True
        assert exists_at(d, "a.-4") is False
        assert exists_at(d, "a.-10") is False
    
    def test_exists_negative_index_nested_structure(self):
        """Check existence using negative index in nested list-dict structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert exists_at(d, "items.-1.name") is True
        assert exists_at(d, "items.-2.name") is True
        assert exists_at(d, "items.-1") is True
        assert exists_at(d, "items.-5.name") is False
        assert exists_at(d, "items.5.name") is False
    
    def test_exists_negative_index_out_of_bounds(self):
        """Check existence with out-of-bounds negative index."""
        d = {"a": [10, 20, 30]}
        assert exists_at(d, "a.-4") is False
        assert exists_at(d, "a.-5") is False
        assert exists_at(d, "a.-100") is False
        # Test both positive and negative out-of-bounds
        assert exists_at(d, "a.10") is False
        assert exists_at(d, "a.-10") is False
    
    def test_exists_nested_list_dict_mix(self):
        """Check existence in mixed nested list and dict."""
        d = {"a": [{"b": 1}, {"b": 2}]}
        assert exists_at(d, "a.0.b") is True
        assert exists_at(d, "a.1.b") is True
        assert exists_at(d, "a.0.c") is False
        assert exists_at(d, "a.2.b") is False
    
    def test_exists_list_index_out_of_bounds(self):
        """Check existence for out-of-bounds list index."""
        d = {"a": [10, 20]}
        assert exists_at(d, "a.5") is False
        assert exists_at(d, "a.-10") is False
    
    def test_exists_list_index_non_integer(self):
        """Check existence with non-integer key on list."""
        d = {"a": [1]}
        assert exists_at(d, "a.x") is False


class TestExistsPathNormalization:
    """Tests for path normalization (list form, unicode, etc.)."""
    
    def test_exists_path_as_list_form(self):
        """Check existence using list form path."""
        d = {"a": {"b": {"c": 1}}}
        assert exists_at(d, ["a", "b", "c"]) is True
        assert exists_at(d, ["a", "b", "d"]) is False
    
    def test_exists_path_list_mixed_int(self):
        """Check existence using list form with integer keys."""
        d = {"a": [{"b": 3}]}
        assert exists_at(d, ["a", 0, "b"]) is True
        assert exists_at(d, ["a", 1, "b"]) is False
    
    def test_exists_path_list_with_negative_index(self):
        """Check existence using list form with negative index."""
        d = {"a": [10, 20, 30]}
        assert exists_at(d, ["a", -1]) is True
        assert exists_at(d, ["a", -2]) is True
        assert exists_at(d, ["a", -3]) is True
        assert exists_at(d, ["a", -4]) is False
    
    def test_exists_path_list_with_negative_index_nested(self):
        """Check existence using list form with negative index in nested structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        assert exists_at(d, ["items", -1, "name"]) is True
        assert exists_at(d, ["items", -2, "name"]) is True
        assert exists_at(d, ["items", -5, "name"]) is False
    
    def test_exists_unicode_keys(self):
        """Check existence with unicode keys."""
        d = {}
        d["你好"] = {"world": {"🌍": 42}}
        assert exists_at(d, "你好.world.🌍") is True
        assert exists_at(d, "你好.world.🌎") is False
        assert exists_at(d, ["你好", "world", "🌍"]) is True
    
    def test_exists_keys_with_dots_in_list_form(self):
        """List form allows keys with dots."""
        d = {"a.b": {"c.d": 10}}
        assert exists_at(d, ["a.b", "c.d"]) is True
        assert exists_at(d, ["a.b", "c.e"]) is False


class TestExistsEdgeCases:
    """Edge cases for exists_at."""
    
    def test_exists_empty_dict(self):
        """Check existence in empty dict."""
        d = {}
        assert exists_at(d, "a") is False
        assert exists_at(d, "a.b.c") is False
    
    def test_exists_empty_list(self):
        """Check existence in empty list."""
        d = {"a": []}
        assert exists_at(d, "a.0") is False
    
    def test_exists_none_value(self):
        """Check existence of None value explicitly stored."""
        d = {"a": None}
        assert exists_at(d, "a") is True
        assert exists_at(d, "a.b") is False
    
    def test_exists_false_value(self):
        """Check existence of False value."""
        d = {"a": False}
        assert exists_at(d, "a") is True
    
    def test_exists_zero_value(self):
        """Check existence of zero value."""
        d = {"a": 0}
        assert exists_at(d, "a") is True
    
    def test_exists_empty_string_value(self):
        """Check existence of empty string value."""
        d = {"a": ""}
        assert exists_at(d, "a") is True
    
    def test_exists_very_deep_nesting(self):
        """Check existence in very deeply nested structure."""
        d = {"a": {"b": {"c": {"d": {"e": {"f": {"g": 42}}}}}}}
        assert exists_at(d, "a.b.c.d.e.f.g") is True
        assert exists_at(d, "a.b.c.d.e.f.h") is False
    
    def test_exists_from_dict_with_numeric_keys(self):
        """Check existence in dict with numeric string keys."""
        d = {"0": {"1": {"2": 5}}}
        assert exists_at(d, "0.1.2") is True
        assert exists_at(d, "0.1.3") is False
    
    def test_exists_mixed_types(self):
        """Check existence in structure with mixed types."""
        d = {
            "a": [1, "two", {"three": 3}],
            "b": {"list": [10, 20], "dict": {"nested": "value"}}
        }
        assert exists_at(d, "a.0") is True
        assert exists_at(d, "a.1") is True
        assert exists_at(d, "a.2.three") is True
        assert exists_at(d, "a.3") is False
        assert exists_at(d, "b.list.1") is True
        assert exists_at(d, "b.list.2") is False
        assert exists_at(d, "b.dict.nested") is True
        assert exists_at(d, "b.dict.missing") is False


class TestExistsInvalidPaths:
    """Tests for invalid path types."""
    
    @pytest.mark.parametrize("invalid_path", [
        123,
        None,
        {},
        tuple(),
        set(),
        3.14,
        True,
        False,
    ])
    def test_exists_at_invalid_path_types(self, invalid_path):
        """exists_at should raise PathError with INVALID_PATH code for invalid path types."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            exists_at(d, invalid_path)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_exists_empty_path(self):
        """Exists with empty path should raise PathError."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            exists_at(d, "")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_exists_empty_key_in_middle(self):
        """Exists with empty key in middle of path should raise PathError."""
        d = {"a": {"": {"b": 1}}}
        with pytest.raises(PathError) as exc_info:
            exists_at(d, "a..b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        with pytest.raises(PathError) as exc_info:
            exists_at(d, ["a", "", "b"])
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_exists_path_validation_edge_cases(self):
        """Test path validation for various edge cases with dots."""
        d = {"a": {"b": 1}}
        
        # Leading dot
        with pytest.raises(PathError) as exc_info:
            exists_at(d, ".a.b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Trailing dot
        with pytest.raises(PathError) as exc_info:
            exists_at(d, "a.b.")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Just dots
        with pytest.raises(PathError) as exc_info:
            exists_at(d, "...")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Multiple consecutive dots
        with pytest.raises(PathError) as exc_info:
            exists_at(d, "a...b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Leading and trailing dots
        with pytest.raises(PathError) as exc_info:
            exists_at(d, ".a.b.")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH


class TestExistsWithTuples:
    """Tests for exists_at with tuples."""
    
    def test_exists_in_tuple(self):
        """Check existence in tuple."""
        d = {"a": (1, 2, 3)}
        assert exists_at(d, "a.0") is True
        assert exists_at(d, "a.1") is True
        assert exists_at(d, "a.2") is True
        assert exists_at(d, "a.3") is False
    
    def test_exists_negative_index_in_tuple(self):
        """Check existence using negative index in tuple."""
        d = {"a": (10, 20, 30)}
        assert exists_at(d, "a.-1") is True
        assert exists_at(d, "a.-2") is True
        assert exists_at(d, "a.-3") is True
        assert exists_at(d, "a.-4") is False


class TestExistsComplexScenarios:
    """Complex scenarios for exists_at."""
    
    def test_exists_partial_path(self):
        """Check existence of partial paths."""
        d = {"a": {"b": {"c": 1}}}
        assert exists_at(d, "a") is True
        assert exists_at(d, "a.b") is True
        assert exists_at(d, "a.b.c") is True
        assert exists_at(d, "a.b.c.d") is False
    
    def test_exists_after_set(self):
        """Check existence after setting a value."""
        from nestedutils import set_at
        d = {}
        assert exists_at(d, "a.b.c") is False
        set_at(d, "a.b.c", 1)
        assert exists_at(d, "a.b.c") is True
    
    def test_exists_after_delete(self):
        """Check existence after deleting a value."""
        from nestedutils import delete_at
        d = {"a": {"b": 1, "c": 2}}
        assert exists_at(d, "a.b") is True
        delete_at(d, "a.b")
        assert exists_at(d, "a.b") is False
        assert exists_at(d, "a.c") is True
    
    def test_exists_with_sparse_list(self):
        """Check existence in sparse list created with fill_strategy."""
        from nestedutils import set_at
        d = {}
        set_at(d, "items.5", "Item 6", fill_strategy="none")
        assert exists_at(d, "items.5") is True
        assert exists_at(d, "items.0") is True  # None values exist
        assert exists_at(d, "items.4") is True  # None values exist
        assert exists_at(d, "items.6") is False
    
    def test_exists_root_level(self):
        """Check existence at root level."""
        d = {"a": 1, "b": 2}
        assert exists_at(d, "a") is True
        assert exists_at(d, "b") is True
        assert exists_at(d, "c") is False
    
    def test_exists_nested_none_replacement(self):
        """Check existence when None is replaced by container."""
        from nestedutils import set_at
        d = {"a": None}
        assert exists_at(d, "a") is True
        assert exists_at(d, "a.b") is False
        set_at(d, "a.b.c", 10)
        assert exists_at(d, "a") is True
        assert exists_at(d, "a.b") is True
        assert exists_at(d, "a.b.c") is True


import pytest
from nestedutils import delete_at
from nestedutils.exceptions import PathError, PathErrorCode


class TestDeleteBasic:
    """Basic delete_at functionality tests."""
    
    def test_delete_from_dict(self):
        """Delete key from dict."""
        d = {"a": {"b": 1}}
        val = delete_at(d, "a.b")
        assert val == 1
        assert d == {"a": {}}
    
    def test_delete_root_key(self):
        """Delete root-level key."""
        d = {"a": 1, "b": 2}
        val = delete_at(d, "a")
        assert val == 1
        assert d == {"b": 2}
    
    def test_delete_missing_key(self):
        """Delete missing key should raise PathError."""
        d = {"a": {}}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.b")
        assert exc_info.value.code == PathErrorCode.MISSING_KEY
    
    def test_delete_from_nested_list_dict(self):
        """Delete from nested list containing dicts."""
        d = {"a": [{"b": 1}, {"b": 2}]}
        val = delete_at(d, "a.0.b")
        assert val == 1
        assert d == {"a": [{}, {"b": 2}]}


class TestDeleteListOperations:
    """Tests for deleting from lists."""
    
    def test_delete_list_index_disallowed(self):
        """Delete list index without allow_list_mutation should fail."""
        d = {"a": [1, 2, 3]}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.1")
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_delete_list_index_allowed(self):
        """Delete list index with allow_list_mutation=True."""
        d = {"a": [1, 2, 3]}
        val = delete_at(d, "a.1", allow_list_mutation=True)
        assert val == 2
        assert d == {"a": [1, 3]}
    
    def test_delete_negative_index(self):
        """Delete using negative index."""
        d = {"a": [10, 20, 30]}
        val = delete_at(d, "a.-1", allow_list_mutation=True)
        assert val == 30
        assert d == {"a": [10, 20]}
    
    def test_delete_negative_index_all_positions(self):
        """Delete using negative index at various positions."""
        d = {"a": [10, 20, 30, 40]}
        # Delete last
        val = delete_at(d, "a.-1", allow_list_mutation=True)
        assert val == 40
        assert d["a"] == [10, 20, 30]
        # Delete last again (was middle)
        val = delete_at(d, "a.-1", allow_list_mutation=True)
        assert val == 30
        assert d["a"] == [10, 20]
        # Delete first using negative
        val = delete_at(d, "a.-2", allow_list_mutation=True)
        assert val == 10
        assert d["a"] == [20]
    
    def test_delete_negative_index_out_of_bounds(self):
        """Delete with out-of-bounds negative index should raise PathError."""
        d = {"items": [1, 2, 3]}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "items.-5", allow_list_mutation=True)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
        # Verify list unchanged
        assert d["items"] == [1, 2, 3]
    
    def test_delete_negative_index_nested_structure(self):
        """Delete using negative index in nested structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}, {"name": "cherry"}]}
        val = delete_at(d, "items.-1.name", allow_list_mutation=False)
        assert val == "cherry"
        assert d["items"][-1] == {}
        # Delete the whole last item
        val = delete_at(d, "items.-1", allow_list_mutation=True)
        assert val == {}
        assert len(d["items"]) == 2
        assert d["items"][-1]["name"] == "banana"
    
    def test_delete_first_item(self):
        """Delete first item from list."""
        d = {"a": [1, 2, 3]}
        val = delete_at(d, "a.0", allow_list_mutation=True)
        assert val == 1
        assert d == {"a": [2, 3]}
    
    def test_delete_all_items(self):
        """Delete all items from list."""
        d = {"a": [1, 2, 3]}
        delete_at(d, "a.0", allow_list_mutation=True)
        delete_at(d, "a.0", allow_list_mutation=True)
        delete_at(d, "a.0", allow_list_mutation=True)
        assert d == {"a": []}
    
    def test_delete_from_empty_list(self):
        """Delete from empty list should fail."""
        d = {"a": []}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.0", allow_list_mutation=True)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_delete_negative_index_from_empty_list(self):
        """Delete with negative index from empty list should fail."""
        d = {"a": []}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.-1", allow_list_mutation=True)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_delete_list_index_out_of_bounds(self):
        """Delete out-of-bounds index should fail."""
        d = {"a": [1, 2]}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.5", allow_list_mutation=True)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX


class TestDeleteErrorCases:
    """Error cases for delete_at."""
    
    def test_delete_non_integer_list_index(self):
        """Delete with non-integer key on list should fail."""
        d = {"a": [1]}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.x", allow_list_mutation=True)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_delete_path_invalid_type(self):
        """Delete from non-container type should fail."""
        d = {"a": 5}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.b")
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_delete_from_none(self):
        """Delete from None should fail."""
        d = {"a": None}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.b")
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_delete_from_tuple(self):
        """Delete from tuple should fail (immutable)."""
        d = {"a": (1, 2, 3)}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.0")
        assert exc_info.value.code == PathErrorCode.IMMUTABLE_CONTAINER
    
    def test_delete_missing_intermediate_key(self):
        """Delete with missing intermediate key should fail."""
        d = {"a": {}}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.b.c")
        assert exc_info.value.code == PathErrorCode.MISSING_KEY
    
    def test_delete_empty_path(self):
        """Delete with empty path should fail."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_delete_empty_key_in_middle(self):
        """Delete with empty key in middle of path should fail."""
        d = {"a": {"": {"b": 1}}}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a..b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        with pytest.raises(PathError) as exc_info:
            delete_at(d, ["a", "", "b"])
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_delete_path_validation_edge_cases(self):
        """Test path validation for various edge cases with dots."""
        d = {"a": {"b": 1}}
        
        # Leading dot
        with pytest.raises(PathError) as exc_info:
            delete_at(d, ".a.b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Trailing dot
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a.b.")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Just dots
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "...")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Multiple consecutive dots
        with pytest.raises(PathError) as exc_info:
            delete_at(d, "a...b")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Leading and trailing dots
        with pytest.raises(PathError) as exc_info:
            delete_at(d, ".a.b.")
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH


class TestDeleteComplex:
    """Complex delete scenarios."""
    
    def test_delete_leaf_inside_nested_mixed(self):
        """Delete leaf value in nested mixed structure."""
        d = {"x": [{"y": {"z": 5}}]}
        val = delete_at(d, "x.0.y.z")
        assert val == 5
        assert d == {"x": [{"y": {}}]}
    
    def test_delete_complex_list_item(self):
        """Delete complex item from list."""
        d = {"a": [{"b": 1}, {"b": 2}, {"b": 3}]}
        delete_at(d, "a.1", allow_list_mutation=True)
        assert d == {"a": [{"b": 1}, {"b": 3}]}
    
    def test_delete_multiple_nested_keys(self):
        """Delete multiple keys from nested structure."""
        d = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
        delete_at(d, "a.b.c")
        delete_at(d, "a.b.d")
        assert d == {"a": {"b": {}, "e": 3}}
    
    def test_delete_from_deeply_nested(self):
        """Delete from very deeply nested structure."""
        d = {"a": {"b": {"c": {"d": {"e": {"f": 42}}}}}}
        val = delete_at(d, "a.b.c.d.e.f")
        assert val == 42
        assert d == {"a": {"b": {"c": {"d": {"e": {}}}}}}
    
    def test_delete_after_set(self):
        """Delete value that was just set."""
        d = {}
        from nestedutils import set_at
        set_at(d, "a.b.c", 1)
        val = delete_at(d, "a.b.c")
        assert val == 1
        assert d == {"a": {"b": {}}}


class TestDeleteInvalidPaths:
    """Tests for invalid path types in delete_at."""
    
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
    def test_delete_at_invalid_path_types(self, invalid_path):
        """delete_at should raise PathError with INVALID_PATH code for invalid path types."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            delete_at(d, invalid_path)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_delete_path_as_list(self):
        """Delete using list form path."""
        d = {"a": {"b": {"c": 1}}}
        val = delete_at(d, ["a", "b", "c"])
        assert val == 1
        assert d == {"a": {"b": {}}}


class TestDeleteReturnValues:
    """Tests for return values from delete_at."""
    
    def test_delete_returns_deleted_value(self):
        """Delete should return the deleted value."""
        d = {"a": 1}
        val = delete_at(d, "a")
        assert val == 1
    
    def test_delete_returns_none_value(self):
        """Delete should return None if that was the value."""
        d = {"a": None}
        val = delete_at(d, "a")
        assert val is None
    
    def test_delete_returns_false_value(self):
        """Delete should return False if that was the value."""
        d = {"a": False}
        val = delete_at(d, "a")
        assert val is False
    
    def test_delete_returns_zero_value(self):
        """Delete should return 0 if that was the value."""
        d = {"a": 0}
        val = delete_at(d, "a")
        assert val == 0
    
    def test_delete_returns_complex_value(self):
        """Delete should return complex nested value."""
        complex_val = {"nested": [1, 2, 3]}
        d = {"a": complex_val}
        val = delete_at(d, "a")
        assert val == complex_val


import pytest
from nestedutils import set_at
from nestedutils.exceptions import PathError, PathErrorCode


class TestSetBasic:
    """Basic set_at functionality tests."""
    
    def test_set_simple(self):
        """Set value in simple dict."""
        d = {}
        set_at(d, "a", 5)
        assert d == {"a": 5}
    
    def test_set_nested_existing(self):
        """Set value in existing nested structure."""
        d = {"a": {"b": {}}}
        set_at(d, "a.b.c", 9)
        assert d == {"a": {"b": {"c": 9}}}
    
    def test_set_auto_create_dicts(self):
        """Auto-create nested dicts when setting."""
        d = {}
        set_at(d, "x.y.z", 10)
        assert d == {"x": {"y": {"z": 10}}}
    
    def test_set_auto_create_lists(self):
        """Auto-create lists when using numeric keys."""
        d = {}
        set_at(d, "a.0.b", 1)
        assert d == {"a": [{"b": 1}]}
    
    def test_set_auto_sparse_list(self):
        """Auto-create sparse list with None fill."""
        d = {"a": []}
        set_at(d, "a.5", 99)
        assert d == {"a": [None, None, None, None, None, 99]}
    
    def test_set_negative_index_write(self):
        """Set value using negative index."""
        d = {"a": [1, 2, 3]}
        set_at(d, "a.-1", 999)
        assert d["a"] == [1, 2, 999]
    
    def test_set_negative_index_modify_existing(self):
        """Modify existing element using negative index (from docstring example)."""
        data = [1, 2, 3]
        set_at(data, "-1", 99)
        assert data == [1, 2, 99]
    
    def test_set_negative_index_out_of_bounds_raises_error(self):
        """Out-of-bounds negative index should raise PathError."""
        data = [1, 2, 3]
        with pytest.raises(PathError) as exc_info:
            set_at(data, "-5", 99)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
        # Verify data unchanged
        assert data == [1, 2, 3]
    
    def test_set_negative_index_nested_structure(self):
        """Set value using negative index in nested structure."""
        d = {"items": [{"name": "apple"}, {"name": "banana"}]}
        set_at(d, "items.-1.name", "cherry")
        assert d["items"][-1]["name"] == "cherry"
        assert d["items"][0]["name"] == "apple"
    
    def test_set_negative_index_intermediate_path(self):
        """Set value where intermediate path uses negative index."""
        d = {"data": [[1, 2], [3, 4], [5, 6]]}
        set_at(d, "data.-1.-1", 99)
        assert d["data"][-1][-1] == 99
        assert d["data"][-1] == [5, 99]
    
    def test_set_negative_index_extends_list(self):
        """Negative index on short list should still work."""
        d = {"a": [1]}
        set_at(d, "a.-1", 99)
        assert d == {"a": [99]}
    
    def test_set_negative_index_all_valid_indices(self):
        """Test all valid negative indices for a list."""
        d = {"a": [10, 20, 30, 40]}
        set_at(d, "a.-1", 1)
        set_at(d, "a.-2", 2)
        set_at(d, "a.-3", 3)
        set_at(d, "a.-4", 4)
        assert d["a"] == [4, 3, 2, 1]
    
    def test_set_inside_list_of_dicts(self):
        """Set value inside list containing dicts."""
        d = {"a": [{}]}
        set_at(d, "a.0.x.y", 5)
        assert d == {"a": [{"x": {"y": 5}}]}


class TestSetFillStrategy:
    """Tests for fill_strategy parameter."""
    
    def test_set_fill_strategy_none(self):
        """Fill strategy 'none' fills missing list items with None."""
        d = {}
        set_at(d, "a.3", 7, fill_strategy="none")
        assert d == {"a": [None, None, None, 7]}
    
    def test_set_fill_strategy_dict(self):
        """Fill strategy 'dict' always creates dicts."""
        d = {}
        set_at(d, "a.0.b", 1, fill_strategy="dict")
        assert d == {"a": {"0": {"b": 1}}}
    
    def test_set_fill_strategy_list(self):
        """Fill strategy 'list' always creates lists."""
        d = {}
        set_at(d, "a.0.1", 42, fill_strategy="list")
        assert d == {"a": [[None, 42]]}
    
    def test_set_invalid_fill_strategy(self):
        """Invalid fill_strategy should raise PathError."""
        d = {}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.b", 1, fill_strategy="unknown")
        assert exc_info.value.code == PathErrorCode.INVALID_FILL_STRATEGY
    
    def test_all_numeric_path_with_dict_strategy(self):
        """Numeric strings should be dict keys with dict strategy."""
        d = {}
        set_at(d, "0.1.2", 5, fill_strategy="dict")
        assert d == {"0": {"1": {"2": 5}}}
    
    def test_all_numeric_path_with_auto_strategy(self):
        """All numeric path with auto should create nested lists."""
        d = {}
        set_at(d, "0.1", 5, fill_strategy="auto")
        assert isinstance(d["0"], list)
        assert d["0"][1] == 5
    
    def test_multiple_operations_different_strategies(self):
        """Multiple sets with different strategies on same structure."""
        d = {}
        set_at(d, "a.0", 1, fill_strategy="auto")
        set_at(d, "a.5", 2, fill_strategy="dict")  # Should still be list
        assert isinstance(d["a"], list)
        assert len(d["a"]) == 6
    
    @pytest.mark.parametrize("strategy", ["auto", "none", "dict", "list"])
    def test_fill_strategy_creates_correct_type(self, strategy):
        """Each fill strategy creates appropriate container type."""
        d = {}
        if strategy == "dict":
            set_at(d, "a.b.c", 1, fill_strategy=strategy)
            assert isinstance(d["a"], dict)
            assert isinstance(d["a"]["b"], dict)
        elif strategy == "list":
            set_at(d, "a.0.1", 1, fill_strategy=strategy)
            assert isinstance(d["a"], list)
            assert isinstance(d["a"][0], list)
        else:  # auto or none
            set_at(d, "a.0.b", 1, fill_strategy=strategy)
            assert isinstance(d["a"], list)
            assert isinstance(d["a"][0], dict)


class TestSetNoneValues:
    """Tests for handling None values."""
    
    def test_set_through_existing_none_in_list(self):
        """Should replace None with a container when navigating deeper."""
        d = {"a": [None, None, None]}
        set_at(d, "a.1.x", 5)
        assert d == {"a": [None, {"x": 5}, None]}
    
    def test_set_through_none_created_by_sparse_fill(self):
        """Auto-filled None should be replaceable."""
        d = {}
        set_at(d, "a.5", 1)  # Creates [None, None, None, None, None, 1]
        set_at(d, "a.2.b", 99)  # Should replace None at index 2
        assert d["a"][2] == {"b": 99}
    
    def test_set_through_none_in_dict(self):
        """Should replace None value in dict when navigating deeper."""
        d = {"a": None}
        set_at(d, "a.b.c", 10)
        assert d == {"a": {"b": {"c": 10}}}
    
    def test_set_none_value_explicitly(self):
        """Setting None as a value should work."""
        d = {"a": 1}
        set_at(d, "a", None)
        assert d == {"a": None}
    
    def test_set_none_in_nested_path(self):
        """Setting None deep in path."""
        d = {}
        set_at(d, "a.b.c", None)
        assert d == {"a": {"b": {"c": None}}}
    
    def test_set_none_then_replace(self):
        """Set None then replace with container."""
        d = {}
        set_at(d, "a", None)
        set_at(d, "a.b", 1)
        assert d == {"a": {"b": 1}}


class TestSetImmutableContainers:
    """Tests for setting into immutable containers."""
    
    def test_set_into_tuple_fails(self):
        """Setting into tuple should fail."""
        d = {"a": (1, 2, 3)}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.0", 9)
        assert exc_info.value.code == PathErrorCode.IMMUTABLE_CONTAINER
    
    def test_set_navigating_into_tuple_fails(self):
        """Navigating into tuple should fail."""
        d = {"a": ({"x": 1},)}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.0.x.y", 1)
        assert exc_info.value.code == PathErrorCode.IMMUTABLE_CONTAINER


class TestSetErrorCases:
    """Error cases for set_at."""
    
    def test_set_list_index_non_integer(self):
        """Setting with non-integer key on list should fail."""
        d = {"a": [1]}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.x", 1)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_replace_list_with_dict_key(self):
        """Setting dict key where list exists should fail."""
        d = {"a": [1, 2, 3]}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.notanumber", 5)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_set_at_invalid_type(self):
        """Setting into non-container type should fail."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.b", 10)
        assert exc_info.value.code == PathErrorCode.INVALID_PATH
    
    def test_empty_string_path(self):
        """Empty path should raise PathError."""
        d = {"a": 1}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "", 5)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_empty_key_in_middle(self):
        """Set with empty key in middle of path should raise PathError."""
        d = {}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a..b", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        with pytest.raises(PathError) as exc_info:
            set_at(d, ["a", "", "b"], 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_set_path_validation_edge_cases(self):
        """Test path validation for various edge cases with dots."""
        d = {}
        
        # Leading dot
        with pytest.raises(PathError) as exc_info:
            set_at(d, ".a.b", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Trailing dot
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.b.", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Just dots
        with pytest.raises(PathError) as exc_info:
            set_at(d, "...", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Multiple consecutive dots
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a...b", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
        
        # Leading and trailing dots
        with pytest.raises(PathError) as exc_info:
            set_at(d, ".a.b.", 1)
        assert exc_info.value.code == PathErrorCode.EMPTY_PATH
    
    def test_set_negative_index_on_empty_list(self):
        """Can't use negative index on empty list."""
        d = {"a": []}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.-1", 5)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_set_negative_index_on_empty_list(self):
        """Can't use negative index on empty list."""
        d = {"a": []}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.-1", 5)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_set_negative_index_on_empty_dict(self):
        """Can't create list with negative index as first operation."""
        d = {}
        with pytest.raises(PathError) as exc_info:
            set_at(d, "a.-1", 5)
        assert exc_info.value.code == PathErrorCode.INVALID_INDEX
    
    def test_numeric_key_on_existing_dict(self):
        """Setting numeric key on existing dict creates string key."""
        d = {"a": {"b": 1}}
        set_at(d, "a.0", 5)
        assert d == {"a": {"b": 1, "0": 5}}
    
    def test_invalid_negative_format(self):
        """String starting with - but not a valid negative number."""
        d = {}
        set_at(d, "a.-5x", 1)
        assert d == {"a": {"-5x": 1}}  # Should be dict key
    
    def test_just_minus_sign(self):
        """Just a minus sign should be dict key."""
        d = {}
        set_at(d, "a.-", 1)
        assert d == {"a": {"-": 1}}
    
    def test_multiple_minus_signs(self):
        """Multiple minus signs."""
        d = {}
        set_at(d, "a.--5", 1)
        assert d == {"a": {"--5": 1}}


class TestSetPathNormalization:
    """Tests for path normalization in set_at."""
    
    def test_path_as_list_form(self):
        """Set using list form path."""
        d = {}
        set_at(d, ["a", "b", "c"], 1)
        assert d == {"a": {"b": {"c": 1}}}
    
    def test_keys_with_dots_in_list_form(self):
        """Using list form allows keys with dots."""
        d = {}
        set_at(d, ["a.b", "c.d"], 10)
        assert d == {"a.b": {"c.d": 10}}
    
    def test_unicode_keys(self):
        """Unicode in keys should work."""
        d = {}
        set_at(d, "你好.world.🌍", 42)
        assert d["你好"]["world"]["🌍"] == 42
    
    def test_path_list_with_integers(self):
        """List form path with integer keys."""
        d = {}
        set_at(d, ["a", 0, "b"], 1)
        assert d == {"a": [{"b": 1}]}


class TestSetComplex:
    """Complex set_at scenarios."""
    
    def test_set_deep_mixed_structure(self):
        """Set in deeply nested mixed structure."""
        d = {}
        set_at(d, "x.0.y.1.z", 42)
        assert d == {
            "x": [
                {
                    "y": [
                        None,
                        {"z": 42}
                    ]
                }
            ]
        }
    
    def test_set_at_creates_correct_types_auto(self):
        """Auto strategy creates correct types."""
        d = {}
        set_at(d, "root.0.child.0", 10)
        assert d == {"root": [{"child": [10]}]}
    
    def test_overwrite_value_with_container(self):
        """Overwrite a value then navigate into it."""
        d = {"a": 5}
        set_at(d, "a", {"b": 1})
        assert d == {"a": {"b": 1}}
        set_at(d, "a.c", 2)
        assert d == {"a": {"b": 1, "c": 2}}
    
    def test_final_key_extends_list(self):
        """Final key extending list should always fill with None."""
        d = {"a": []}
        set_at(d, "a.5", 99)
        assert d == {"a": [None, None, None, None, None, 99]}
    
    def test_set_positive_extension_from_docstring(self):
        """Positive index extension example from docstring."""
        data = [1, 2, 3]
        set_at(data, "5", 99)
        assert data == [1, 2, 3, None, None, 99]
    
    def test_very_large_sparse_list(self):
        """Creating very large sparse list should work."""
        d = {}
        set_at(d, "a.1000", 1)
        assert len(d["a"]) == 1001
        assert d["a"][1000] == 1
        assert all(d["a"][i] is None for i in range(1000))
    
    def test_set_multiple_values_same_structure(self):
        """Set multiple values in same structure."""
        d = {}
        set_at(d, "a.b.c", 1)
        set_at(d, "a.b.d", 2)
        set_at(d, "a.e", 3)
        assert d == {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
    
    def test_set_overwrite_existing_value(self):
        """Overwrite existing value."""
        d = {"a": {"b": 1}}
        set_at(d, "a.b", 2)
        assert d == {"a": {"b": 2}}


class TestSetInvalidPaths:
    """Tests for invalid path types in set_at."""
    
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
    def test_set_at_invalid_path_types(self, invalid_path):
        """set_at should raise PathError with INVALID_PATH code for invalid path types."""
        d = {}
        with pytest.raises(PathError) as exc_info:
            set_at(d, invalid_path, "value")
        assert exc_info.value.code == PathErrorCode.INVALID_PATH


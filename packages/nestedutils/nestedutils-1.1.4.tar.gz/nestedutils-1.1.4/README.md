# Nested Utils

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://github.com/ysskrishna/nestedutils/actions/workflows/test.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
[![PyPI](https://img.shields.io/pypi/v/nestedutils)](https://pypi.org/project/nestedutils/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/nestedutils?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/nestedutils)
[![Documentation](https://img.shields.io/badge/docs-ysskrishna.github.io%2Fnestedutils-blue.svg)](https://ysskrishna.github.io/nestedutils/)

The lightweight Python library for safe, simple, dot-notation access to nested dicts and lists. Effortlessly get, set, and delete values deep in your complex JSON, API responses, and config files without verbose error-checking or handling KeyError exceptions.

![OG Image](https://raw.githubusercontent.com/ysskrishna/nestedutils/main/media/og.png)

## Why nestedutils?

Working with deeply nested data (like JSON API responses) often leads to verbose, error-prone boilerplate:

```python
# The Standard Way: Verbose and hard to read
user_name = None
if data and "users" in data and len(data["users"]) > 0:
    user = data["users"][0]
    if "profile" in user:
        user_name = user["profile"].get("name")

# With nestedutils: Clean, safe, and readable
from nestedutils import get_at

user_name = get_at(data, "users.0.profile.name")
```

## Features

- **Simple Path Syntax**: Use dot-notation strings (`"a.b.c"`) or lists (`["a", "b", "c"]`) to navigate nested structures
- **Mixed Data Types**: Seamlessly work with dictionaries, lists, and tuples (read-only for tuples)
- **List Index Support**: Access list elements using numeric indices, including negative indices
- **Auto-creation**: Automatically create missing intermediate containers when setting values
- **Flexible Fill Strategies**: Control how missing containers are created with different fill strategies
- **Type Safety**: Comprehensive error handling with descriptive error messages and error codes
- **Safety Limits**: Built-in protection against excessive nesting (max depth: 100) and oversized lists (max index: 10,000)
- **Zero Dependencies**: Pure Python implementation with no external dependencies

## Use Cases

- **JSON API Responses**: Safely extract values from complex, unpredictable JSON responses without dozens of checks.
- **Configuration Management**: Easily read and modify deeply nested settings in configuration dictionaries.
- **Data Transformation**: Rapidly remap data from one complex structure to another using `get_at` and `set_at`.

## Installation

```bash
pip install nestedutils
```

## Quick Start

```python
from nestedutils import get_at, set_at, delete_at, exists_at

# Create a nested structure
data = {}

# Set values using dot-notation
set_at(data, "user.name", "John")
set_at(data, "user.age", 30)
set_at(data, "user.hobbies.0", "reading")
set_at(data, "user.hobbies.1", "coding")

# Access values
name = get_at(data, "user.name")  # "John"
age = get_at(data, "user.age")    # 30
first_hobby = get_at(data, "user.hobbies.0")  # "reading"

# Check if path exists
if exists_at(data, "user.name"):
    print("User name exists!")

# Delete values
delete_at(data, "user.age")
```

## API Reference

### `get_at(data, path, default=None)`

Retrieve a value from a nested data structure.

**Parameters:**

- `data`: The data structure to navigate (dict, list, tuple, or nested combinations)
- `path`: Path to the value (string with dot notation or list of keys/indices)
- `default`: Value to return if path doesn't exist (default: `None`)

**Returns:** The value at the path, or `default` if not found

**Examples:**

```python
data = {"a": {"b": {"c": 5}}}
get_at(data, "a.b.c")  # 5
get_at(data, "a.b.d", default=99)  # 99

data = {"items": [{"name": "apple"}, {"name": "banana"}]}
get_at(data, "items.1.name")  # "banana"
get_at(data, "items.-1.name")  # "banana" (negative index)
```

### `set_at(data, path, value, fill_strategy="auto")`

Set a value in a nested data structure, creating intermediate containers as needed.

**Parameters:**

- `data`: The data structure to modify (must be mutable: dict or list)
- `path`: Path where to set the value (string with dot notation or list of keys/indices)
- `value`: The value to set
- `fill_strategy`: How to fill missing containers (default: `"auto"`)
  - `"auto"`: Intelligently creates `{}` for dict keys, `[]` for list indices, and `None` for sparse list gaps
  - `"none"`: Fills missing list items with `None`
  - `"dict"`: Always creates dictionaries
  - `"list"`: Always creates lists

**Note:** Positive indices can extend lists (filling gaps as needed), but negative indices can only modify existing elements.

**Examples:**

```python
data = {}
set_at(data, "user.profile.name", "Alice")
# Creates: {"user": {"profile": {"name": "Alice"}}}

data = {}
set_at(data, "items.0.name", "Item 1")
# Creates: {"items": [{"name": "Item 1"}]}

data = {}
set_at(data, "items.5", "Item 6", fill_strategy="none")
# Creates: {"items": [None, None, None, None, None, "Item 6"]}

data = [1, 2, 3]
set_at(data, "5", 99)  # Extends list with None gaps
# Creates: [1, 2, 3, None, None, 99]

data = [1, 2, 3]
set_at(data, "-1", 100)  # Updates existing last element
# Creates: [1, 2, 100]
```

### `exists_at(data, path)`

Check if a path exists in a nested data structure.

**Parameters:**

- `data`: The data structure to navigate (dict, list, tuple, or nested combinations)
- `path`: Path to check (string with dot notation or list of keys/indices)

**Returns:** `True` if the path exists, `False` otherwise

**Raises:** `PathError` if the path format is invalid

**Examples:**

```python
data = {"a": {"b": {"c": 5}}}
exists_at(data, "a.b.c")  # True
exists_at(data, "a.b.d")  # False

data = {"items": [{"name": "apple"}, {"name": "banana"}]}
exists_at(data, "items.1.name")  # True
exists_at(data, "items.5.name")  # False
exists_at(data, "items.-1.name")  # True (negative index)
```

### `delete_at(data, path, allow_list_mutation=False)`

Delete a value from a nested data structure.

**Parameters:**

- `data`: The data structure to modify
- `path`: Path to the value to delete
- `allow_list_mutation`: If `True`, allows deletion from lists (default: `False`)

**Returns:** The deleted value

**Raises:** `PathError` if the path doesn't exist or deletion is not allowed

**Examples:**

```python
data = {"a": {"b": 1, "c": 2}}
delete_at(data, "a.b")  # Returns 1, data becomes {"a": {"c": 2}}

data = {"items": [1, 2, 3]}
delete_at(data, "items.1", allow_list_mutation=True)  # Returns 2
# data becomes {"items": [1, 3]}
```

## Error Handling

The library uses `PathError` exceptions with error codes for different failure scenarios:

```python
from nestedutils import PathError, PathErrorCode

try:
    set_at(data, "invalid.path", 1)
except PathError as e:
    print(e.message)  # Error message
    print(e.code)     # Error code (PathErrorCode enum)
```

**Error Codes:**

- `INVALID_PATH`: Invalid path format or type
- `INVALID_INDEX`: Invalid list index
- `MISSING_KEY`: Key doesn't exist in dictionary
- `EMPTY_PATH`: Path is empty
- `IMMUTABLE_CONTAINER`: Attempted to modify a tuple
- `INVALID_FILL_STRATEGY`: Invalid fill strategy value

## Advanced Usage

### Using List Paths

List paths are useful when keys contain dots:

```python
data = {}
set_at(data, ["user.name", "first"], "John")
set_at(data, ["user.name", "last"], "Doe")
# Creates: {"user.name": {"first": "John", "last": "Doe"}}
```

### Negative List Indices

Negative indices work like Python list indexing for reading and updating existing elements:

```python
data = {"items": [10, 20, 30]}
get_at(data, "items.-1")  # 30 (last item)
set_at(data, "items.-1", 999)  # Updates last item (must exist)
```

**Important**: Negative indices can only reference existing elements. They cannot extend lists - attempting to use a negative index that's out of bounds will raise a `PathError`.

### Working with Tuples

Tuples are read-only. You can read from them but cannot modify:

```python
data = {"items": (1, 2, 3)}
get_at(data, "items.0")  # 1 (works)
set_at(data, "items.0", 9)  # Raises PathError (tuples are immutable)
```

### Handling None Values

The library can navigate through `None` values when setting:

```python
data = {"a": None}
set_at(data, "a.b.c", 10)
# Replaces None with container: {"a": {"b": {"c": 10}}}
```

## Safety Limits

The library includes built-in safety limits to prevent excessive resource usage:

- **Maximum Path Depth**: 100 levels (prevents deeply nested paths that could cause stack issues)
- **Maximum List Index**: 10,000 (prevents creating extremely large sparse lists)

These limits help protect against accidental memory exhaustion or performance issues. If you hit these limits, you'll receive a `PathError` with a clear message.


## Links

- **PyPI**: [pypi.org/project/nestedutils](https://pypi.org/project/nestedutils/)
- **Documentation**: [ysskrishna.github.io/nestedutils](https://ysskrishna.github.io/nestedutils/)
- **Repository**: [github.com/ysskrishna/nestedutils.git](https://github.com/ysskrishna/nestedutils.git)
- **Issues**: [github.com/ysskrishna/nestedutils/issues](https://github.com/ysskrishna/nestedutils/issues)

## Contributing

Contributions are welcome! Please read our [Contributing Guide](https://github.com/ysskrishna/nestedutils/blob/main/CONTRIBUTING.md) for details on our code of conduct, development setup, and the process for submitting pull requests.

## Support

If you find this library useful, please consider:

- ⭐ **Starring** the repository on GitHub to help others discover it.
- 💖 **Sponsoring** to support ongoing maintenance and development.

[Become a Sponsor on GitHub](https://github.com/sponsors/ysskrishna) | [Support on Patreon](https://patreon.com/ysskrishna)

## License

MIT License - see [LICENSE](https://github.com/ysskrishna/nestedutils/blob/main/LICENSE) file for details.


## Author

**Y. Siva Sai Krishna**

- GitHub: [@ysskrishna](https://github.com/ysskrishna)
- LinkedIn: [ysskrishna](https://linkedin.com/in/ysskrishna)

# Frozen Cub

[![pypi version](https://img.shields.io/pypi/v/frozen-cub.svg)](https://pypi.org/project/frozen-cub/)

A high-performance library for immutable, hashable data structures in Python. Built with Cython for speed.

## Features

- **FrozenDict**: An immutable dictionary that can be used as a dict key or in sets
- **freeze()**: Recursively freeze nested data structures (dicts, lists, tuples, sets)
- **LRUCache**: A fast LRU cache with O(1) operations
- **Dispatcher**: A predicate-based function dispatcher with cached handler resolution

## Installation

> **Note**: Windows is not supported at this time due to pthread-based code paths. Windows support is on the roadmap.

```bash
pip install frozen-cub
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv add frozen-cub
```

## Quick Start

### Freezing Data Structures

```python
from frozen_cub import freeze, FrozenDict

# Freeze a nested dictionary
data = {
    "user": "bear",
    "settings": {"theme": "dark", "notifications": True},
    "tags": ["python", "cython"],
}
frozen = freeze(data)

# Now it's hashable - use as dict key or in sets
cache = {frozen: "some_result"}
unique_configs = {frozen}
```

### FrozenDict

```python
from frozen_cub import FrozenDict

# Create directly from items
fd = FrozenDict([("a", 1), ("b", 2)])

# Access like a regular dict
print(fd["a"])  # 1
print(fd.get("c", "default"))  # "default"
print(list(fd.keys()))  # ["a", "b"]

# Use as a dict key (it's hashable!)
lookup = {fd: "found it"}
```

### LRU Cache

```python
from frozen_cub.lru_cache import LRUCache

# Create a cache with max 100 items
cache: LRUCache[str, dict] = LRUCache(capacity=100)

# Basic operations
cache["key"] = {"data": "value"}
result = cache.get("key")  # Returns {"data": "value"}
result = cache.get("missing", "default")  # Returns "default"

# Dict-like interface
"key" in cache  # True
del cache["key"]
len(cache)  # 0
```

### Dispatcher

Route function calls based on predicates:

```python
from frozen_cub.dispatcher import Dispatcher

dispatcher = Dispatcher()

@dispatcher.register(lambda x: isinstance(x, str))
def handle_string(obj):
    return f"Got string: {obj}"

@dispatcher.register(lambda x: isinstance(x, int), lambda x: x > 0)
def handle_positive_int(obj):
    return f"Got positive int: {obj}"

@dispatcher.dispatcher()
def process(obj):
    return f"No handler for: {obj}"

process("hello")  # "Got string: hello"
process(42)       # "Got positive int: 42"
process(-1)       # "No handler for: -1"
```

## API Reference

### `freeze(obj)`

Recursively converts mutable objects to immutable equivalents:

| Input Type | Output Type  |
| ---------- | ------------ |
| `dict`     | `FrozenDict` |
| `list`     | `tuple`      |
| `set`      | `frozenset`  |


### `FrozenDict`

An immutable, hashable dictionary.

**Methods:**
- `get(key, default=None)` - Get value with optional default
- `keys()` - Return list of keys
- `values()` - Return list of values
- `items()` - Return list of (key, value) tuples
- `__getitem__(key)` - Get value, raises `KeyError` if missing
- `__contains__(key)` - Check if key exists
- `__hash__()` - Returns cached hash value
- `__len__()` - Return number of items

### `LRUCache[K, V]`

A generic LRU cache with configurable capacity.

**Constructor:**
- `LRUCache(capacity=512)` - Create cache with max capacity

**Methods:**
- `get(key, default=None)` - Get value with optional default
- `set(key, value)` - Set value (alias for `__setitem__`)
- `pop(key, default=None)` - Remove and return value
- `clear()` - Remove all items
- `__getitem__(key)` - Get value, raises `KeyError` if missing
- `__setitem__(key, value)` - Set value
- `__delitem__(key)` - Delete key, raises `KeyError` if missing
- `__contains__(key)` - Check if key exists
- `__len__()` - Return number of items

## Requirements

- Python 3.12+
- macOS or Linux (Windows not yet supported)

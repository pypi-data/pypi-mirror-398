# TypedProtocol

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Typed protocols with runtime validation and structural typing for Python**

TypedProtocol provides a way to define and validate protocols (interfaces) in Python with runtime type checking. It extends Python's standard `typing.Protocol` by enforcing type annotations at class definition time and performing structural subtyping checks.

## Features

- **Type Enforcement**: All protocol members require type annotations
- **Runtime Validation**: Structural subtyping checks at runtime with `issubclass()`
- **Generic Support**: Support for generic protocols with TypeVar unification
- **Protocol Inheritance**: Inheritance between protocols
- **Type Checking**: Method signatures, return types, and parameter validation
- **Minimal Overhead**: Type checking only happens during `issubclass()` calls

## Installation

```bash
pip install typedprotocol
```

## Quick Start

```python
from typedprotocol import TypedProtocol

# Define a protocol
class Drawable(TypedProtocol):
    x: int
    y: int

    def draw(self) -> None: ...
    def move(self, dx: int, dy: int) -> None: ...

# Implement the protocol
class Circle:
    x: int
    y: int
    radius: float  # Extra fields are allowed

    def __init__(self, x: int, y: int, radius: float):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self) -> None:
        print(f"Drawing circle at ({self.x}, {self.y})")

    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

# Check protocol compliance
assert issubclass(Circle, Drawable)
```

### Generic Protocols

```python
from typedprotocol import TypedProtocol
from typing import TypeVar

T = TypeVar('T')

class Container(TypedProtocol[T]):
    def add(self, item: T) -> None: ...
    def get(self) -> T: ...

class StringContainer:
    def __init__(self):
        self.items = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def get(self) -> str:
        return self.items[0] if self.items else ""

# Test protocol compliance and implementation
assert issubclass(StringContainer, Container)

```

### Protocol Inheritance

```python
from typedprotocol import TypedProtocol

class Drawable(TypedProtocol):
    x: int
    y: int
    def draw(self) -> None: ...
    def move(self, dx: int, dy: int) -> None: ...

class Serializable(TypedProtocol):
    def to_dict(self) -> dict: ...

class PersistentDrawable(Drawable, Serializable):
    """Protocol combining drawing and serialization"""
    pass

class SmartCircle:
    x: int
    y: int
    radius: float

    def __init__(self, x: int, y: int, radius: float):
        self.x = x
        self.y = y
        self.radius = radius

    def draw(self) -> None:
        print(f"Drawing at ({self.x}, {self.y})")

    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "radius": self.radius}

assert issubclass(SmartCircle, PersistentDrawable)
```

### Async Method Support

```python
from typedprotocol import TypedProtocol

class AsyncProcessor(TypedProtocol):
    async def process(self, data: bytes) -> str: ...

class MyProcessor:
    async def process(self, data: bytes) -> str:
        return data.decode()

assert issubclass(MyProcessor, AsyncProcessor)
```

## Key Differences from typing.Protocol

| Feature                           | `typing.Protocol` | `TypedProtocol`           |
| --------------------------------- | ----------------- | ------------------------- |
| Type annotation enforcement       | Optional          | Required                  |
| Runtime type checking             | Basic             | Enhanced                  |
| Generic protocol support          | Limited           | With unification          |
| Instantiation prevention          | No                | Yes                       |
| Method signature validation       | Basic             | Parameter/return types    |
| Protocol inheritance restrictions | None              | Protocol-only inheritance |

### Required Annotations

```python notest
from typedprotocol import TypedProtocol

# This will raise TypeError at class definition time
class BadProtocol(TypedProtocol):
    unannotated_field = "invalid"  # Missing type annotation

```

### Type Checking

```python
from typedprotocol import TypedProtocol

class DataProcessor(TypedProtocol):
    def process(self, data: bytes) -> str: ...

class BadImplementation:
    def process(self, data: str) -> str:  # Wrong parameter type
        return data

# This should return False due to wrong parameter type
assert not issubclass(BadImplementation, DataProcessor)
```

## Requirements

- Python 3.12+
- No external dependencies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 0.1.0 (2024-12-19)

- Initial release
- Core TypedProtocol implementation
- Generic protocol support

# Sturnus

**A lightweight Python core library for the Sturnus ecosystem.**

[![PyPI version](https://img.shields.io/pypi/v/sturnus.svg)](https://pypi.org/project/sturnus/)
[![Python versions](https://img.shields.io/pypi/pyversions/sturnus.svg)](https://pypi.org/project/sturnus/)
[![License](https://img.shields.io/pypi/l/sturnus.svg)](https://pypi.org/project/sturnus/)

---

## Installation

Install Sturnus using pip:

```bash
pip install sturnus
```

---

## Quick Start

### Basic Usage

```python
from sturnus import hello

# Simple greeting
print(hello("World"))
# Output: Hello, World! Welcome to the sturnus library.

print(hello("Alice"))
# Output: Hello, Alice! Welcome to the sturnus library.
```

### Custom Greetings

```python
from sturnus import greet

# Customizable greeting
print(greet("Alice"))
# Output: Hello, Alice!

print(greet("Bob", "Hi"))
# Output: Hi, Bob!

print(greet("Charlie", greeting="Hey"))
# Output: Hey, Charlie!
```

### Message Formatting

```python
from sturnus import format_message

# Basic message
print(format_message("Alice", "Welcome aboard"))
# Output: Alice: Welcome aboard

# With prefix
print(format_message("Bob", "Great work", prefix="[INFO]"))
# Output: [INFO] Bob: Great work

# With suffix
print(format_message("Charlie", "Task completed", suffix="✓"))
# Output: Charlie: Task completed ✓

# With both
print(format_message("Diana", "Login successful", prefix="[SUCCESS]", suffix="🎉"))
# Output: [SUCCESS] Diana: Login successful 🎉
```

---

## Command-Line Interface

Sturnus also provides a simple CLI:

```bash
# Basic greeting
python -m sturnus Alice
# Output: Hello, Alice! Welcome to the sturnus library.

# Show version
python -m sturnus --version

# Verbose output
python -m sturnus Bob --verbose
# Output: 
# Hello, Bob! Welcome to the sturnus library.
# [Sturnus v0.1.2]

# Help
python -m sturnus --help
```

---

## Features

- **Simple API**: Easy-to-use functions for common greeting tasks
- **Type-safe**: Full type hints for better IDE support
- **Validated**: Input validation with helpful error messages
- **CLI Support**: Use as a command-line tool
- **Namespace Package**: Designed to support ecosystem extensions
- **Well-documented**: Comprehensive docstrings and examples

---

## API Reference

### `hello(name: str) -> str`

Returns a welcoming greeting message.

**Parameters:**
- `name` (str): The name to greet (non-empty string)

**Returns:**
- str: A formatted greeting message

**Raises:**
- `TypeError`: If name is not a string
- `ValueError`: If name is empty or whitespace-only

---

### `greet(name: str, greeting: str = "Hello") -> str`

Returns a customizable greeting message.

**Parameters:**
- `name` (str): The name to greet (non-empty string)
- `greeting` (str): The greeting word (default: "Hello")

**Returns:**
- str: A formatted greeting with custom greeting

**Raises:**
- `TypeError`: If name or greeting is not a string
- `ValueError`: If name or greeting is empty or whitespace-only

---

### `format_message(name: str, message: str, prefix: str | None = None, suffix: str | None = None) -> str`

Formats a message with optional prefix and suffix.

**Parameters:**
- `name` (str): The name to include in the message
- `message` (str): The main message content
- `prefix` (str | None): Optional prefix before the message
- `suffix` (str | None): Optional suffix after the message

**Returns:**
- str: A formatted message string

**Raises:**
- `TypeError`: If arguments are not strings (where required)
- `ValueError`: If name or message is empty or whitespace-only

---

## Requirements

- Python >= 3.12, < 3.13

---

## License

Proprietary License. Copyright © 2025 [Starling Associates](https://www.starling.studio).

---

## Links

- **Homepage**: [https://www.starling.cloud](https://www.starling.cloud)
- **PyPI**: [https://pypi.org/project/sturnus/](https://pypi.org/project/sturnus/)
- **Issues**: Report bugs and request features on our issue tracker

---

## Support

For questions and support, please contact [info@starling.studio](mailto:info@starling.studio).

---

**Made with ❤️ by Starling Cloud**

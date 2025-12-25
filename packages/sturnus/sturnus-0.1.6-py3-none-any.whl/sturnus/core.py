# -*- coding: utf-8 -*-


# =============================================================================
# Docstring
# =============================================================================

"""
Sturnus - Core Module
=====================

This module contains the core functionality of the Sturnus library.

Examples:
    Basic greeting::

        >>> from sturnus.core import hello
        >>> hello("Starling")
        'Hello, Starling! Welcome to the sturnus library.'

    Customized greeting::

        >>> greet("Starling", greeting="Hi")
        'Hi, Starling!'

"""

# =============================================================================
# Imports
# =============================================================================

from typing import Optional

# =============================================================================
# Functions
# =============================================================================


def hello(name: str) -> str:
    """
    Return a simple greeting message.

    This function provides a welcoming greeting message for the sturnus library.

    Args:
        name: The name of the person or entity to greet. Must be a non-empty string.

    Returns:
        A formatted greeting string.

    Raises:
        ValueError: If name is empty or contains only whitespace.
        TypeError: If name is not a string.

    Examples:
        >>> hello("World")
        'Hello, World! Welcome to the sturnus library.'

        >>> hello("Alice")
        'Hello, Alice! Welcome to the sturnus library.'

    """
    if not isinstance(name, str):
        raise TypeError(
            f"Expected string for 'name', got {type(name).__name__}"
        )

    if not name.strip():
        raise ValueError("Name cannot be empty or contain only whitespace")

    return f"Hello, {name}! Welcome to the sturnus library."


def greet(name: str, greeting: str = "Hello") -> str:
    """
    Return a customizable greeting message.

    This function provides a flexible greeting with customizable greeting text.

    Args:
        name: The name of the person or entity to greet. Must be a non-empty string.
        greeting: The greeting word to use (default: "Hello").

    Returns:
        A formatted greeting string with the custom greeting.

    Raises:
        ValueError: If name or greeting is empty or contains only whitespace.
        TypeError: If name or greeting is not a string.

    Examples:
        >>> greet("Alice")
        'Hello, Alice!'

        >>> greet("Bob", "Hi")
        'Hi, Bob!'

        >>> greet("Charlie", greeting="Hey")
        'Hey, Charlie!'

    """
    if not isinstance(name, str):
        raise TypeError(
            f"Expected string for 'name', got {type(name).__name__}"
        )

    if not isinstance(greeting, str):
        raise TypeError(
            f"Expected string for 'greeting', got {type(greeting).__name__}"
        )

    if not name.strip():
        raise ValueError("Name cannot be empty or contain only whitespace")

    if not greeting.strip():
        raise ValueError("Greeting cannot be empty or contain only whitespace")

    return f"{greeting}, {name}!"


def format_message(
    name: str,
    message: str,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
) -> str:
    """
    Format a message with optional prefix and suffix.

    This function provides advanced message formatting capabilities.

    Args:
        name: The name to include in the message.
        message: The main message content.
        prefix: Optional prefix to add before the message.
        suffix: Optional suffix to add after the message.

    Returns:
        A formatted message string.

    Raises:
        ValueError: If name or message is empty.
        TypeError: If arguments are not strings (where required).

    Examples:
        >>> format_message("Alice", "Welcome aboard")
        'Alice: Welcome aboard'

        >>> format_message("Bob", "Great work", prefix="[INFO]")
        '[INFO] Bob: Great work'

        >>> format_message("Charlie", "Task completed", suffix="✓")
        'Charlie: Task completed ✓'

    """
    if not isinstance(name, str):
        raise TypeError(
            f"Expected string for 'name', got {type(name).__name__}"
        )

    if not isinstance(message, str):
        raise TypeError(
            f"Expected string for 'message', got {type(message).__name__}"
        )

    if prefix is not None and not isinstance(prefix, str):
        raise TypeError(
            f"Expected string for 'prefix', got {type(prefix).__name__}"
        )

    if suffix is not None and not isinstance(suffix, str):
        raise TypeError(
            f"Expected string for 'suffix', got {type(suffix).__name__}"
        )

    if not name.strip():
        raise ValueError("Name cannot be empty or contain only whitespace")

    if not message.strip():
        raise ValueError("Message cannot be empty or contain only whitespace")

    result = f"{name}: {message}"

    if prefix:
        result = f"{prefix} {result}"

    if suffix:
        result = f"{result} {suffix}"

    return result


# =============================================================================
# Exports
# =============================================================================

__all__: list[str] = [
    "hello",
    "greet",
    "format_message",
]

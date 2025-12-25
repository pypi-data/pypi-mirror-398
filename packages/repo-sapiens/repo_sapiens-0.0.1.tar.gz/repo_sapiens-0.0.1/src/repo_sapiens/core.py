"""Core functionality for hello-python-test package."""

from typing import Optional


def greet(name: Optional[str] = None) -> None:
    """
    Print a greeting message.

    Args:
        name: Optional name to greet. Defaults to "World" if not provided.

    Examples:
        >>> greet()
        Hello, World!
        >>> greet("Python")
        Hello, Python!
    """
    greeting_name = name if name is not None else "World"
    print(f"Hello, {greeting_name}!")


def get_greeting(name: str = "World") -> str:
    """
    Generate a greeting message string.

    Args:
        name: The name to include in the greeting. Defaults to "World".

    Returns:
        A greeting message string.

    Examples:
        >>> get_greeting()
        'Hello, World!'
        >>> get_greeting("Python")
        'Hello, Python!'
    """
    return f"Hello, {name}!"

"""
Testing Ash SDK for Python
A simple demo SDK
"""

__version__ = "1.0.0"


def greet() -> str:
    """Returns a friendly greeting message"""
    return "hurray have a nice day"


def greet_user(name: str) -> str:
    """Returns a personalized greeting message"""
    return f"hurray {name}, have a nice day"

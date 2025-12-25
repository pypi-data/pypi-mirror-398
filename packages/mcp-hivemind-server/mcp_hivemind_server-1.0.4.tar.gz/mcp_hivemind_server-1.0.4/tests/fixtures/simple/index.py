"""Simple test file with basic functions."""

def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x: int) -> int:
        """Add to result."""
        self.result += x
        return self.result
    
    def reset(self) -> None:
        """Reset the result."""
        self.result = 0

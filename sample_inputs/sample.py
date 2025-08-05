"""Module-level docstring"""

def timer(func):
    """A simple decorator that logs execution time."""
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# This is a simple utility function
@timer
def add(a, b):
    """Add two numbers and return the result."""
    return a + b

class Calculator:
    """Performs basic calculations."""

    def __init__(self):
        """Initialize the calculator."""
        self.total = 0

    @staticmethod
    def square(x):
        """Return the square of a number."""
        return x * x

    @timer
    def multiply(self, x, y):
        """
        Multiply two numbers.

        Args:
            x: First number.
            y: Second number.

        Returns:
            The product.
        """
        return x * y
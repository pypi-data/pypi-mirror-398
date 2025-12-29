"""Common arithmetic tools for GLLM agent examples."""


def add_numbers(a: int, b: int) -> str:
    """Adds two integer numbers together and returns the result as a string.

    For example, to add 5 and 3, you would call this with a=5 and b=3.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of the two numbers as a string, or an error message if addition fails.
    """
    try:
        result = a + b
        return str(result)
    except Exception as e:
        return f"Error: Could not add numbers. Reason: {str(e)}"


def sum_numbers(a: int, b: int) -> int:
    """Adds two integer numbers together and returns the integer result.

    Used specifically in Google ADK examples where an integer return is expected.

    Args:
        a: The first number.
        b: The second number.

    Returns:
        The sum of the two numbers as an integer.
    """
    print(f"Tool executed: sum_numbers({a}, {b})")
    return a + b

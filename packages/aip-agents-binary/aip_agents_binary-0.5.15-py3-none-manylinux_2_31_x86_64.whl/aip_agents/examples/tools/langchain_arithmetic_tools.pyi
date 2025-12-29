from langchain_core.tools import tool

@tool
def add_numbers(a: int, b: int) -> str:
    """Adds two numbers and returns the result as a string.

    This is a self-contained LangChain tool.
    For example:
    add_numbers(a=5, b=3)

    Args:
        a (int): First number to add.
        b (int): Second number to add.

    Returns:
        str: Sum of the two numbers as a string.
    """

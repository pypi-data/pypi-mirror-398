"""Common reusable tool functions for MCP server examples."""

import base64
import random
import uuid
from datetime import datetime

# ===== Random Selection Tools =====


def get_random_item_from_list(items: list[str]) -> str:
    """Return a random item from the given list."""
    return random.choice(items)


def get_random_fact() -> str:
    """Return a random fun fact."""
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible!",
        "A group of flamingos is called a 'flamboyance'.",
        "The shortest war in history was between Britain and Zanzibar in 1896. Zanzibar surrendered after 38 minutes.",
        "There are more stars in the universe than grains of sand on all of Earth's beaches.",
        "A banana is technically a berry, but a strawberry is not.",
    ]
    return get_random_item_from_list(facts)


def get_random_quote() -> str:
    """Return a random inspirational quote."""
    quotes = [
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "Life is what happens when you're busy making other plans. - John Lennon",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle",
    ]
    return get_random_item_from_list(quotes)


def random_name_generator(name_list: list[str]) -> str:
    """Generate random name from the provided list."""
    return get_random_item_from_list(name_list)


# ===== Time & UUID Tools =====


def get_current_time() -> str:
    """Return the current time with format YYYY-MM-DD HH:MM:SS."""
    return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def generate_uuid() -> str:
    """Generate a random UUID."""
    return f"Generated UUID: {uuid.uuid4()}"


# ===== Text Utilities =====


def convert_to_base64(text: str) -> str:
    """Convert text to base64 representation."""
    try:
        encoded = base64.b64encode(text.encode()).decode()
        return f"Base64: {encoded}"
    except Exception as e:
        return f"Error converting to base64: {str(e)}"


def word_count(text: str) -> str:
    """Count words in the given text."""
    if not text.strip():
        return "Word count: 0 (empty text)"

    words = text.split()
    return f"Word count: {len(words)} words"

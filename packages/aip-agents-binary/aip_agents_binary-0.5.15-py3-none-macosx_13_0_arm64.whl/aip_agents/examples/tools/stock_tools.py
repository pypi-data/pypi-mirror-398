"""Defines tools for stock market data.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import random
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class StockPriceInput(BaseModel):
    """Input for the stock price tool."""

    symbol: str = Field(description="The stock symbol (e.g., AAPL, MSFT) to get the price for.")


@tool(args_schema=StockPriceInput)
def get_stock_price(symbol: str) -> dict[str, Any]:
    """Get current stock price and performance data for a given symbol.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT) to get the price for.

    Returns:
        dict[str, Any]: Dictionary containing stock price and performance data.
    """
    logger.info(f"Getting stock price for {symbol}")
    # Simulate stock price data
    price = round(random.uniform(100, 1000), 2)
    change = round(random.uniform(-10, 10), 2)
    change_percent = round((change / price) * 100, 2)
    return {
        "symbol": symbol.upper(),
        "price": price,
        "change": change,
        "change_percent": change_percent,
        "currency": "USD",
    }


class StockNewsInput(BaseModel):
    """Input for the stock news tool."""

    symbol: str = Field(description="The stock symbol (e.g., AAPL, MSFT) to get news for.")
    days: int = Field(default=7, description="Number of days of news to retrieve.")


@tool(args_schema=StockNewsInput)
def get_stock_news(symbol: str, days: int = 7) -> dict[str, Any]:
    """Get recent news for a stock for a specified number of days.

    Args:
        symbol (str): The stock symbol (e.g., AAPL, MSFT) to get news for.
        days (int, optional): Number of days of news to retrieve. Defaults to 7.

    Returns:
        dict[str, Any]: Dictionary containing stock news data.
    """
    logger.info(f"Getting stock news for {symbol} for the last {days} days")
    # Simulate news data
    news_items = [
        f"{symbol.upper()} announces breakthrough in AI technology",
        f"Analysts raise price target for {symbol.upper()}",
        f"{symbol.upper()} reports better than expected earnings",
        f"New product launch boosts {symbol.upper()} shares",
        f"{symbol.upper()} partners with a major tech firm",
        f"Regulatory changes impact {symbol.upper()}'s sector",
        f"{symbol.upper()} to release new sustainability report",
    ]
    return {
        "symbol": symbol.upper(),
        "news": random.sample(news_items, min(days, len(news_items))),
        "days": days,
    }

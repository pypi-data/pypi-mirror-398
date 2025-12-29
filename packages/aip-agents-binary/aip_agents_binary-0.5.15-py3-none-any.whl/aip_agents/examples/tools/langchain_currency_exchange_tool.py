"""Simple currency exchange tool demonstrating RunnableConfig tool configuration."""

import asyncio

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.types import Command
from pydantic import BaseModel, Field


class CurrencyConfig(BaseModel):
    """Tool configuration schema."""

    tenant_id: str = Field(description="Tenant identifier")
    auth_key: str = Field(description="Authentication key")


class CurrencyInput(BaseModel):
    """Input schema for currency exchange."""

    amount: float = Field(description="Amount to convert", gt=0)
    from_currency: str = Field(description="Source currency (USD, EUR)")
    to_currency: str = Field(description="Target currency (USD, EUR)")


class CurrencyExchangeTool(BaseTool):
    """Simple currency exchange tool with SDK auto-injection configuration."""

    name: str = "currency_exchange"
    description: str = "Convert currencies with tenant-specific rates"
    args_schema: type[BaseModel] = CurrencyInput
    tool_config_schema: type[BaseModel] = CurrencyConfig

    def _run(self, amount: float, from_currency: str, to_currency: str, config: RunnableConfig, **kwargs) -> str:
        """Run the tool asynchronously.

        Args:
            amount (float): Amount to convert.
            from_currency (str): Source currency (USD, EUR).
            to_currency (str): Target currency (USD, EUR).
            config (RunnableConfig): Tool configuration containing tenant and auth info.
            **kwargs: Additional keyword arguments.

        Returns:
            str: Conversion result text.
        """
        return asyncio.run(self._arun(amount, from_currency, to_currency, config, **kwargs))

    async def _arun(self, amount: float, from_currency: str, to_currency: str, config: RunnableConfig, **kwargs) -> str:
        """Convert currency using effective configuration.

        Args:
            amount (float): Amount to convert.
            from_currency (str): Source currency (USD, EUR).
            to_currency (str): Target currency (USD, EUR).
            config (RunnableConfig): Tool configuration containing tenant and auth info.
            **kwargs: Additional keyword arguments.

        Returns:
            str: Command with conversion result and metadata.
        """
        # Get effective config (runtime override or agent default)
        effective_config = self.get_tool_config(config)

        if not effective_config:
            return "❌ No configuration provided"

        # Simple tenant validation
        rates = {"premium_corp": 0.85, "standard_business": 1.5}
        keys = {"premium_corp": "premium_key_123", "standard_business": "standard_key_456"}

        if effective_config.tenant_id not in rates or effective_config.auth_key != keys.get(effective_config.tenant_id):
            return f"❌ Invalid tenant: {effective_config.tenant_id}"

        # Simple USD/EUR conversion
        rate = rates[effective_config.tenant_id] if from_currency == "USD" else 1 / rates[effective_config.tenant_id]
        result = amount * rate

        result_text = f"💱 {amount} {from_currency} = {result:.2f} {to_currency} (tenant: {effective_config.tenant_id})"

        return Command(
            update={
                "result": result_text,
                "metadata": {
                    "message": "Conversion successful",
                },
            }
        )

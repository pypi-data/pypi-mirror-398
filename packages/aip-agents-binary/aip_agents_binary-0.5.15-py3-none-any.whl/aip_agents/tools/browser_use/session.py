"""Session management for browser-use framework.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)

References:
    https://github.com/browser-use/browser-use/blob/0.5.9/browser_use/browser/session.py
"""

import asyncio

from browser_use.agent.views import DOMElementNode
from browser_use.browser.session import BrowserSession as BrowserUseSession
from browser_use.browser.session import require_healthy_browser
from browser_use.browser.views import BrowserError
from browser_use.observability import observe_debug
from browser_use.utils import _log_pretty_url, time_execution_async


class BrowserSession(BrowserUseSession):
    """Represents an active browser session with a running browser process somewhere."""

    @require_healthy_browser(usable_page=True, reopen_page=True)
    @time_execution_async("--input_text_element_node")
    @observe_debug(ignore_input=True, name="input_text_element_node")
    async def _input_text_element_node(self, element_node: DOMElementNode, text: str):
        """Input text into an element with proper error handling and state management.

        Args:
            element_node (DOMElementNode): The element node to input text into.
            text (str): The text to input into the element.
        """
        try:
            element_handle = await self.get_locate_element(element_node)

            if element_handle is None:
                raise BrowserError(f"Element: {repr(element_node)} not found")

            # Ensure element is ready for input
            try:
                await element_handle.wait_for_element_state("stable", timeout=1_000)
                is_visible = await self._is_visible(element_handle)
                if is_visible:
                    await element_handle.scroll_into_view_if_needed(timeout=1_000)
            except Exception as state_error:
                self.logger.debug(
                    "Skipping pre-input visibility preparation for %s due to %s",
                    repr(element_node),
                    state_error,
                )

            # let's first try to click and type
            try:
                await element_handle.evaluate('el => {el.textContent = ""; el.value = "";}')
                await element_handle.click()
                await asyncio.sleep(0.1)  # Increased sleep time
                page = await self.get_current_page()
                await page.keyboard.insert_text(text)
                return
            except Exception as e:
                self.logger.debug(f"Input text with click and type failed, trying element handle method: {e}")
                # fall through to BrowserUseSession fallback below

        except Exception as e:
            # Get current page URL safely for error message
            try:
                page = await self.get_current_page()
                page_url = _log_pretty_url(page.url)
            except Exception:
                page_url = "unknown page"

            self.logger.debug(
                f"❌ Failed to input text into element: {repr(element_node)} "
                f"on page {page_url}: {type(e).__name__}: {e}"
            )
            raise BrowserError(f"Failed to input text into index {element_node.highlight_index}") from e

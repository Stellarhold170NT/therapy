"""
Setup Playwright browser tools for web search
Based on AgentsWithRAGAndTools.ipynb cell 3-4
"""

from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_async_playwright_browser
from typing import List, Optional
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


# Global browser instance (singleton)
_async_browser = None
_playwright_tools = None


def get_playwright_tools() -> List:
    """
    Get Playwright browser tools (like notebook cell 3-4)

    Returns:
        List of tools: ClickTool, NavigateTool, NavigateBackTool,
                       ExtractTextTool, ExtractHyperlinksTool,
                       GetElementsTool, CurrentWebPageTool
    """
    global _async_browser, _playwright_tools

    if _playwright_tools is not None:
        return _playwright_tools

    try:
        print("[Playwright] Initializing browser...")

        # Create async playwright browser
        _async_browser = create_async_playwright_browser()

        # Create toolkit
        toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=_async_browser)

        # Get all tools
        _playwright_tools = toolkit.get_tools()

        print(f"[Playwright] Loaded {len(_playwright_tools)} tools")
        return _playwright_tools

    except Exception as e:
        print(f"[Playwright] Error loading tools: {str(e)}")
        return []


def close_playwright_browser():
    """Close playwright browser"""
    global _async_browser
    if _async_browser:
        try:
            # Browser will be cleaned up automatically
            _async_browser = None
        except Exception as e:
            print(f"[Playwright] Error closing browser: {str(e)}")

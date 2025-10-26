# web_scraper.py
# Based on: https://medium.com/@tim.dolan_49671/how-to-use-ollama-with-tool-calling-and-playwright-to-scrape-websites-4b55c92a8cff

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Try to import stealth, but make it optional
try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    print("[WebScraper] Warning: playwright_stealth not available, stealth mode disabled")


class WebScraper:
    """
    Web scraper using Playwright to handle JavaScript-heavy sites.
    Returns structured data that can be used by Ollama tool calling.
    """

    def __init__(self, headless=True, browser_type="chromium"):
        self.headless = headless
        self.browser_type = browser_type

    def scrape_page(self, url: str) -> str:
        """Scrape raw HTML from a URL using Playwright."""
        with sync_playwright() as p:
            browser = getattr(p, self.browser_type).launch(
                headless=self.headless,
                args=["--disable-gpu", "--no-sandbox"]
            )
            context = browser.new_context()
            page = context.new_page()

            # Use stealth if available
            if HAS_STEALTH:
                stealth_sync(page)

            page.goto(url, timeout=30000)  # 30 second timeout

            html_content = page.content()
            browser.close()

        return html_content

    def extract_titles_articles_links(self, raw_html: str) -> list:
        """Extract structured data from HTML."""
        soup = BeautifulSoup(raw_html, 'html.parser')
        extracted_data = []

        for article in soup.find_all(['article', 'section', 'div']):
            title_tag = article.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            link_tag = article.find('a', href=True)
            content = article.get_text(separator="\n", strip=True)

            # Only add if we have meaningful content
            if title_tag and link_tag and content and len(content) > 50:
                extracted_data.append({
                    'title': title_tag.get_text(strip=True),
                    'link': link_tag['href'],
                    'content': content[:500]  # Limit content length
                })

        return extracted_data

    def query_page_content(self, url: str) -> dict:
        """
        Main method: Scrape URL and return structured data.
        This is the function that will be called by Ollama tool.
        """
        try:
            print(f"[WebScraper] Scraping URL: {url}")
            raw_html = self.scrape_page(url)

            extracted_data = self.extract_titles_articles_links(raw_html)

            structured_data = {
                "url": url,
                "success": True,
                "extracted_data": extracted_data,
                "raw_html_length": len(raw_html)
            }

            print(f"[WebScraper] Successfully scraped {len(extracted_data)} items")
            return structured_data

        except Exception as e:
            print(f"[WebScraper] Error: {str(e)}")
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "extracted_data": []
            }


# Tool function that will be registered with Ollama
def query_web_scraper(url: str) -> dict:
    """
    Scrapes a web page and returns structured data.
    This function will be called by Ollama when the model decides to use the tool.

    Args:
        url: The URL to scrape

    Returns:
        dict with extracted titles, links, and content
    """
    scraper = WebScraper(headless=True)
    return scraper.query_page_content(url)


def search_web(query: str) -> dict:
    """
    Search the web using DuckDuckGo and return results.
    Use this when you need to find information but don't have a specific URL.

    Args:
        query: The search query (e.g., "xu hướng tuyển dụng 2025")

    Returns:
        dict with search results (titles, links, snippets)
    """
    try:
        from duckduckgo_search import DDGS

        print(f"[DuckDuckGo] Searching for: {query}")

        results = []
        with DDGS() as ddgs:
            # Get top 5 results
            for r in ddgs.text(query, max_results=5):
                results.append({
                    'title': r.get('title', ''),
                    'link': r.get('href', ''),
                    'snippet': r.get('body', '')
                })

        print(f"[DuckDuckGo] Found {len(results)} results")

        return {
            "query": query,
            "success": True,
            "results": results,
            "num_results": len(results)
        }

    except Exception as e:
        print(f"[DuckDuckGo] Error: {str(e)}")
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "results": []
        }

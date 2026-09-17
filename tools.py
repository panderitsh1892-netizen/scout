import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from rich import print

load_dotenv()


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Returns Titles, URLs and snippets."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=tavily_key)
            results = tavily.search(query=query, max_results=5)
            out = []
            for r in results.get('results', []):
                out.append(
                    f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:300]}\n"
                )
            if out:
                return "\n----\n".join(out)
        except Exception:
            pass

    # Free DuckDuckGo Search (no API key required)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            out = []
            for r in results:
                title = r.get('title', 'No Title')
                url = r.get('href', '')
                snippet = r.get('body', '')[:300]
                out.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\n")
            return "\n----\n".join(out) if out else f"No search results found for: {query}"
    except Exception as e:
        return f"Error executing web search: {str(e)}"


@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"

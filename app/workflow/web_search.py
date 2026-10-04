"""
Web Search Tool — DuckDuckGo (free, no API key required).
Used by the Creativity Agent to fetch fresh ideas and research.
"""
from ddgs import DDGS
from typing import List


# Domains where web search is appropriate (open knowledge topics).
# Sensitive/regulated domains skip search to avoid noisy external data.
_SEARCH_ALLOWED_DOMAINS = {
    "General",
    "Technology",
    "Academic/Educational",
    "Geography/Travel",
}


class WebSearchTool:
    """Thin wrapper around DuckDuckGo search for use inside agents."""

    def is_search_allowed(self, domain: str) -> bool:
        """Return True if web search is appropriate for this domain."""
        return domain in _SEARCH_ALLOWED_DOMAINS

    def search(self, query: str, max_results: int = 5) -> List[dict]:
        """
        Run a DuckDuckGo text search and return structured results.

        Returns:
            List of dicts with keys: title, snippet, url
        """
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            return [
                {
                    "title":   r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url":     r.get("href", ""),
                }
                for r in raw
            ]
        except Exception as e:
            print(f"[WebSearch] DuckDuckGo search failed: {e}")
            return []


# Global singleton
web_search_tool = WebSearchTool()

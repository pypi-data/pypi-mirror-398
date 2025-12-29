from typing import List, Dict, Any
from ddgs import DDGS

class WebSearchTool:
    """A tool for performing web searches using DuckDuckGo."""
    def __init__(self):
        self._client = DDGS()
        self.description = "A tool for searching the web using DuckDuckGo. Input should be a search query string."

    def run(self, query: str) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo and return the results."""
        try:
            search_results = []
            results = self._client.text(query, max_results=5,region="in-en")
            for result in results:
                search_results.append(result.get("body", ""))
            return search_results
        except Exception as e:
            # Handle rate limit or other exceptions gracefully
            return [{"error": f"Search failed: {str(e)}"}]
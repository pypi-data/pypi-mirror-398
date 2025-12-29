from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

class WikipediaTool:
    def __init__(self):
        """Initialize the wikipedia tool."""
        self._client = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        self.description = "A tool for searching Wikipedia articles. Input should be a search query string."
        
    def run(self, query: str = None, language : str = "en", numResults: int = 5, max_chars_per_page: int = 4000):
        if query:
            self._client.api_wrapper.top_k_results = numResults
            self._client.api_wrapper.lang=language
            self._client.api_wrapper.doc_content_chars_max=max_chars_per_page
            result = self._client.run(query)
            return result


from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper

class WolframAlphaTool:
    def __init__(self):
        """Initialize the wolfram alpha tool."""
        self.client = WolframAlphaAPIWrapper()
        self.description = "A tool for querying Wolfram Alpha. Input should be a query string."
        
    def run(self, query: str = None):
        if query:
            result = self.client.run(query)
            return result


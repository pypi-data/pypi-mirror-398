from langchain_community.tools import YouTubeSearchTool

class YoutubeSearch:
    def __init__(self):
        """Initialize the yahoo finance news tool."""
        self.client = YouTubeSearchTool()
        self.description = "A tool for searching YouTube videos. Input should be a search query string."

    def run(self, query: str = None, numResults: int = 5):
        if query:
            query = f"{query},{numResults}"
            result = self.client.run(query)
            return result

from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool

class YFinanceNews:
    def __init__(self):
        """Initialize the yahoo finance news tool."""
        self.client = YahooFinanceNewsTool()
        self.description = "A tool for retrieving the latest news articles related to finance and stocks from Yahoo Finance. Input should be a query string."
        
    def run(self, query: str = None):
        if query:
            result = self.client.invoke(query)
            return result


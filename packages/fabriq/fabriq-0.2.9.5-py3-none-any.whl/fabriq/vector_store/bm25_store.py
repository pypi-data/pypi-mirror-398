from langchain_community.retrievers import BM25Retriever
 
class BM25:
    """BM25 Retriever for document retrieval using BM25 algorithm."""

    def __init__(self, config):
        """
        Initialize the BM25Retriever with a list of documents.
        """
        self.config = config
        self.top_k = self.config.get("retriever").get("params").get("top_k", 5)
        self.retriever = BM25Retriever(k=self.top_k)
    
    def add_documents(self, documents, metadata=None):
            """Add documents to the BM25"""
            return self.retriever.from_texts(documents,metadatas=metadata)
    
    def retrieve(self, query):
        """
        Retrieve documents based on the query using BM25 algorithm.
        :param query: The query string to search for.
        :return: List of retrieved documents.
        """
        return self.retriever.get_relevant_documents(query)
from langchain_classic.retrievers import EnsembleRetriever
from fabriq.retriever import VectorRetriever
from fabriq.vector_store.bm25_store import BM25
from langchain_core.documents import Document
from typing import List


class HybridRetriever:
    def __init__(self, config):
        self.config = config
        weights = self.config.get("retriever").get("params").get("weights", [0.5, 0.5])
        retrievers = [VectorRetriever(self.config), BM25(self.config)]
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=retrievers, weights=weights
        )

    def retrieve(self, query: str) -> List[Document]:
        documents = self.ensemble_retriever.invoke(query)
        return documents

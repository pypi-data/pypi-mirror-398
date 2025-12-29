from fabriq.vector_store import VectorStore
from langchain_core.documents import Document
from typing import List
from collections import defaultdict


class VectorRetriever:
    def __init__(self, config):
        """Initialize the retriever with a vector store."""
        self.config = config
        self.vector_store = VectorStore(self.config)

    def reciprocal_rank_fusion(
        self, documents_list: List[List[Document]], k: int = 60
    ) -> List[Document]:
        """
        Apply Reciprocal Rank Fusion (RRF) to rerank documents from multiple lists.
        Since we don't have scores, we use the rank positions.
        Args:
            documents_list: List of lists of Documents (each list is a ranked list from a retriever).
            k: RRF constant (default 60).
        Returns:
            List[Document]: Reranked documents by RRF score.
        """

        doc_scores = defaultdict(float)
        doc_instances = {}

        for docs in documents_list:
            for rank, doc in enumerate(docs):
                doc_id = getattr(doc, "id", id(doc))
                doc_scores[doc_id] += 1.0 / (k + rank + 1)
                # Store the first instance of the doc for output
                if doc_id not in doc_instances:
                    doc_instances[doc_id] = doc

        # Sort by RRF score descending
        reranked_docs = sorted(
            doc_instances.values(),
            key=lambda d: doc_scores[getattr(d, "id", id(d))],
            reverse=True,
        )
        return reranked_docs

    def retrieve(
        self, query: str, top_k: int = 5, filter=None, rank_fusion: bool = False
    ) -> List[Document]:
        """Retrieve relevant documents based on the query."""
        documents = self.vector_store.retrieve(query, k=top_k, filter=filter)
        if rank_fusion:
            documents = self.reciprocal_rank_fusion([documents], k=60)
            # Ensure documents are unique and sorted by their RRF score
            unique_documents = {getattr(doc, "id", id(doc)): doc for doc in documents}
            documents = list(unique_documents.values())
            documents.sort(key=lambda d: getattr(d, "score", 0), reverse=True)

        if not documents:
            return None

        return documents

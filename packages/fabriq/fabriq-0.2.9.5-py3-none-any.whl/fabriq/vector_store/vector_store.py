# from langchain_community.vectorstores import AzureSearch
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
# from langchain_pinecone import PineconeVectorStore
from langchain_postgres import PGVector
from fabriq.embeddings import EmbeddingModel
from typing import List
import os


class VectorStore:
    def __init__(self, config):
        """Initialize the vector store with the specified type."""
        self.config = config
        vector_store_type = self.config.get("vector_store").get("type", "chromadb")
        self.collection_name = (
            self.config.get("vector_store")
            .get("params")
            .get("collection_name", "vector_store_collection")
        )
        self.embedding_model = EmbeddingModel(self.config)
        self.persist_directory = self.config.get("vector_store").get(
            "store_path", "assets/vector_store"
        )
        self.kwargs = self.config.get("vector_store").get("kwargs", {})

        if vector_store_type not in [
            "chromadb",
            "faiss",
            "pinecone",
            "weaviate",
            "pgvector",
            "azure_ai_search",
        ]:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
        if self.embedding_model is None:
            raise ValueError("Embedding model must be provided.")

        if vector_store_type == "chromadb":
            self.store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory,
                **self.kwargs,
            )

        elif vector_store_type == "faiss":
            self.store = FAISS(embedding_function=self.embedding_model, **self.kwargs)

        # elif vector_store_type == "pinecone":
        #     self.store = PineconeVectorStore(
        #         index=self.collection_name,
        #         embedding=self.embedding_model,
        #         pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        #         **self.kwargs,
        #     )

        elif vector_store_type == "pgvector":
            self.store = PGVector(
                connection_string=self.kwargs.get("connection_string"),
                collection_name=self.collection_name,
                embeddings=self.embedding_model,
                use_jsonb=True,
            )

        # elif vector_store_type == "azure_ai_search":
        #     if "AZURE_SEARCH_KEY" in os.environ:
        #         self.store = AzureSearch(
        #             azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        #             azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
        #             index_name=self.collection_name,
        #             embedding_function=self.embedding_model,
        #         )
        #     else:
        #         self.store = AzureSearch(
        #             azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        #             azure_ad_access_token=self.kwargs.get("azure_ad_access_token"),
        #             index_name=self.collection_name,
        #             embedding_function=self.embedding_model,
        #         )
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")

    def add_documents(self, documents) -> None:
        """Add documents to the vector store."""
        self.store.add_documents(documents)

    def create_filter(self, filter_dict: dict) -> dict:
        """Create a filter for metadata-based searches across supported vectorstores."""
        if not isinstance(filter_dict, dict):
            raise ValueError("Filter must be a dictionary.")

        store = self.get_store().lower()

        if store in ["chroma", "pgvector", "faiss"]:
            out = {}
            for k, v in filter_dict.items():
                if isinstance(v, dict):
                    out[k] = v
                elif isinstance(v, list):
                    out[k] = {"$in": v}
                else:
                    out[k] = {"$eq": v}
            return out

        elif store in ["azuresearch"]:
            clauses = []
            for k, v in filter_dict.items():
                if isinstance(v, list):
                    sub = []
                    for val in v:
                        if isinstance(val, str):
                            val = val.replace("'", "''")  # escape single quotes
                            sub.append(f"{k} eq '{val}'")
                        else:
                            sub.append(f"{k} eq {val}")
                    clauses.append("(" + " or ".join(sub) + ")")
                else:
                    if isinstance(v, str):
                        v = v.replace("'", "''")
                        clauses.append(f"{k} eq '{v}'")
                    else:
                        clauses.append(f"{k} eq {v}")
            return " and ".join(clauses)

        elif store in ["pineconevectorstore", "pinecone"]:
            pinecone_filter = {}
            for k, v in filter_dict.items():
                if isinstance(v, list):
                    pinecone_filter[k] = {"$in": v}
                else:
                    pinecone_filter[k] = {"$eq": v}
            return pinecone_filter

        elif store in ["weaviate"]:
            operands = []
            for k, v in filter_dict.items():
                if isinstance(v, list):
                    or_operands = []
                    for val in v:
                        operand = {
                            "path": [k],
                            "operator": "Equal",
                            "valueText": val if isinstance(val, str) else None,
                            "valueNumber": (
                                val if isinstance(val, (int, float)) else None
                            ),
                            "valueBoolean": val if isinstance(val, bool) else None,
                        }
                        operand = {
                            kk: vv for kk, vv in operand.items() if vv is not None
                        }
                        or_operands.append(operand)
                    operands.append({"operator": "Or", "operands": or_operands})
                else:
                    operand = {
                        "path": [k],
                        "operator": "Equal",
                        "valueText": v if isinstance(v, str) else None,
                        "valueNumber": v if isinstance(v, (int, float)) else None,
                        "valueBoolean": v if isinstance(v, bool) else None,
                    }
                    operand = {kk: vv for kk, vv in operand.items() if vv is not None}
                    operands.append(operand)

            if len(operands) == 1:
                return operands[0]
            else:
                return {"operator": "And", "operands": operands}

    def retrieve(self, query, k=5, filter=None) -> List:
        """Search for similar documents in the vector store."""
        if filter is not None:
            filter = self.create_filter(filter)
        return self.store.similarity_search(query, k=k, filter=filter)

    def persist(self) -> None:
        """Persist the vector store to the specified directory."""
        if self.get_store() == "FAISS":
            self.store.save_local(self.persist_directory)
        elif self.get_store() == [
            "Chroma",
            "PGVector",
            "AzureSearch",
            "PineconeVectorStore",
        ]:
            print("Already persisted")

    def load(self, persist_directory: str) -> None:
        """Load the vector store from the specified directory."""
        if isinstance(self.store, Chroma):
            self.store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_model,
            )
        elif isinstance(self.store, FAISS):
            self.store = FAISS.load_local(persist_directory)
        elif isinstance(self.store, PGVector):
            self.store = PGVector(
                connection_string=self.kwargs.get("connection_string"),
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                use_jsonb=True,
            )
        # elif isinstance(self.store, AzureSearch):
        #     if "AZURE_SEARCH_KEY" in os.environ:
        #         self.store = AzureSearch(
        #             azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        #             azure_search_key=os.getenv("AZURE_SEARCH_KEY"),
        #             index_name=self.collection_name,
        #             embedding_function=self.embedding_model,
        #         )
        #     else:
        #         self.store = AzureSearch(
        #             azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        #             azure_ad_access_token=self.kwargs.get("azure_ad_access_token"),
        #             index_name=self.collection_name,
        #             embedding_function=self.embedding_model,
        #         )
        # elif isinstance(self.store, PineconeVectorStore):
        #     self.store = PineconeVectorStore.from_existing_index(
        #         self.collection_name, self.embedding_model
        #     )
        else:
            raise ValueError("Unsupported vector store type for loading.")

    def get_store(self) -> str:
        """Get the underlying vector store instance."""
        return self.store.__class__.__name__

    def delete_collection(self) -> None:
        """Delete the entire collection from the vector store."""
        if isinstance(self.store, Chroma):
            self.store.delete_collection()
        elif isinstance(self.store, FAISS):
            self.store.delete()
        elif isinstance(self.store, PGVector):
            self.store.delete_collection()
        else:
            raise ValueError("Unsupported vector store type for deletion.")

    def delete_documents(self, ids) -> None:
        """Delete specific documents from the vector store by their IDs."""
        if isinstance(self.store, Chroma):
            self.store.delete(ids=ids)
        elif isinstance(self.store, FAISS):
            self.store.delete(ids=ids)
        elif isinstance(self.store, PGVector):
            self.store.delete(ids=ids)
        else:
            raise ValueError("Unsupported vector store type for deletion.")

    def delete_chunks_by_filename(self, filename) -> None:
        """Delete chunks associated with a specific filename."""
        if isinstance(self.store, Chroma):
            if isinstance(filename, str):
                filename = [filename]
            ids_to_delete = self.store.get(where={"filename": {"$in": filename}})['ids']
            self.delete_documents(ids=ids_to_delete)
            
        elif isinstance(self.store, FAISS):
            raise NotImplementedError(
                "FAISS does not support deletion by metadata filter."
            )
        elif isinstance(self.store, PGVector):
            if isinstance(filename, str):
                filename = [filename]
            placeholders = ', '.join(['%s'] * len(filename))
            query = f"DELETE FROM {self.collection_name} WHERE filename IN ({placeholders});"
            self.store.client.execute(query, tuple(filename))
        else:
            raise ValueError("Unsupported vector store type for deletion.")

    def get_all_documents(self) -> List:
        """Retrieve all documents from the vector store."""
        if isinstance(self.store, Chroma):
            return self.store.get()["documents"]
        elif isinstance(self.store, FAISS):
            return self.store.index.reconstruct_n(0, self.store.index.ntotal)
        elif isinstance(self.store, PGVector):
            query = f"SELECT * FROM {self.collection_name};"
            return self.store.client.execute(query).fetchall()
        # elif isinstance(self.store, AzureSearch):
        #     results = self.store.client.search(self.store.index_name, "*")
        #     return [result for result in results]
        # elif isinstance(self.store, PineconeVectorStore):
        #     query = f"SELECT * FROM {self.collection_name};"
        #     return self.store.client.fetch(self.collection_name, ids=None).records
        else:
            raise ValueError("Unsupported vector store type for retrieval.")

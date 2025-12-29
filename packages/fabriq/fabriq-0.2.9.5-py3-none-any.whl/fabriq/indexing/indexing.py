import os
from fabriq.vector_store import VectorStore
from fabriq.embeddings import EmbeddingModel
from fabriq.document_loader import DocumentLoader
from fabriq.text_splitter import TextSplitter
from fabriq.llm import LLM
from typing import List, Dict, Any
import pandas as pd
from tqdm import tqdm


class DocumentIndexer:
    def __init__(self, config):
        """Initialize the document indexer with a specified vector store type."""
        self.config = config
        self.embedding_model = EmbeddingModel(self.config)
        self.vector_store = VectorStore(self.config)
        self.llm = LLM(self.config)

    def index_document(self, file_path: str, metadata: Dict = {}):
        """Load a document and add it to the vector store."""
        loader = DocumentLoader(self.config)
        splitter = TextSplitter(self.config)
        llm = (
            self.llm
            if self.config.get("document_loader")
            .get("params")
            .get("multimodal_option", None)
            else None
        )
        document = loader.load_document(file_path, metadata=metadata, llm=llm)
        chunks = splitter.split_text(document)
        self.vector_store.add_documents(chunks)

    def index_documents(
        self, file_paths: List[str], metadatas: List[Dict[str, Any]] = []
    ):
        """Index multiple documents."""
        error_files = pd.DataFrame(columns=["file_path", "error"])
        if len(metadatas) == 0:
            metadatas = [{"file_name": os.path.basename(fp)} for fp in file_paths]

        for file_path, metadata in tqdm(
            zip(file_paths, metadatas), desc="Indexing documents", total=len(file_paths)
        ):
            print(f"Indexing document: {file_path}")
            try:
                self.index_document(file_path, metadata)
            except Exception as e:
                print(f"Error indexing document {file_path}: {e}")
                error_files = pd.concat(
                    [
                        error_files,
                        pd.DataFrame({"file_path": [file_path], "error": [str(e)]}),
                    ],
                    ignore_index=True,
                )
                error_files.to_excel("error_files.xlsx", index=False)
        return len(error_files)
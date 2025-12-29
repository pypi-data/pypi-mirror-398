from unstructured.partition.text import partition_text
from unstructured.chunking.basic import chunk_elements
from unstructured.chunking.title import chunk_by_title
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fabriq.embeddings import EmbeddingModel
from langchain_core.documents import Document
from typing import List
from langchain_experimental.text_splitter import SemanticChunker

class TextSplitter:
    def __init__(self, config):
        """
        Initializes the TextSplitter with the specified parameters.

        Args:
            splitter_type (str): The type of text splitter to use (default is "markdown").
            chunking_strategy (str): The strategy for chunking text (default is "by_title").
            chunk_size (int): The maximum size of each text chunk (default is 1000).
            chunk_overlap (int): The number of overlapping characters between chunks (default is 200).
        """
        self.config = config
        self.splitter_type = self.config.get("text_splitter").get(
            "type", "unstructured"
        )
        if self.splitter_type == "semantic":
            self.embedding_model = EmbeddingModel(self.config)
            self.semantic_chunker = SemanticChunker(self.embedding_model)
        self.chunking_strategy = (
            self.config.get("text_splitter")
            .get("params")
            .get("chunking_strategy", "by_title")
        )
        self.chunk_size = (
            self.config.get("text_splitter").get("params").get("chunk_size", 1000)
        )
        self.chunk_overlap = (
            self.config.get("text_splitter").get("params").get("chunk_overlap", 200)
        )
        if self.splitter_type not in ["recursive", "unstructured","semantic"]:
            raise ValueError(
                f"Unsupported splitter type: {self.splitter_type}. "
                "Supported types are 'recursive', 'unstructured' and 'semantic'."
            )

    def split_text(self, documents: List[Document]) -> List[Document]:
        """
        Splits the input text into smaller chunks based on the specified splitting strategy.

        Args:
            text (str): The text to be split.

        Returns:
            List[Document]: A list of Document objects containing the split text chunks.
        """
        if self.splitter_type == "recursive":
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=100,
                chunk_overlap=20,
            ).split_documents(documents)
            return chunks

        elif self.splitter_type == "unstructured":
            documents_out = []

            for doc in documents:
                parts = partition_text(text=doc.page_content)
                metadata = {
                    "page_number": doc.metadata.get("page_num", ""),
                    "file_name": doc.metadata.get("file_name", ""),
                }

                if self.chunking_strategy == "by_title":
                    chunks = chunk_by_title(
                        parts,
                        multipage_sections=True,
                        overlap=self.chunk_overlap,
                        max_characters=self.chunk_size,
                    )
                else:
                    chunks = chunk_elements(
                        parts, overlap=self.chunk_overlap, max_characters=self.chunk_size
                    )

                for chunk in chunks:
                    documents_out.append(Document(page_content=chunk.text, metadata=metadata))

            return documents_out
                          
        elif self.splitter_type == "semantic":
            metadatas = []
            for doc in documents:
                metadatas.append(doc.metadata)
            
            return self.semantic_chunker.create_documents([doc.page_content for doc in documents],metadatas)

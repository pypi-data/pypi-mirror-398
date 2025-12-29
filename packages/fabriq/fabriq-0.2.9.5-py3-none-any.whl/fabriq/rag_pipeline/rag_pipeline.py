import asyncio
from fabriq.llm import LLM
from fabriq.retriever import VectorRetriever
from fabriq.reranking import Reranker
from typing import List, Dict, Any
from langchain_core.messages import AIMessage


class RAGPipeline:
    def __init__(self, config):
        """Initialize the RAG pipeline with an LLM model, retriever, and prompt template."""
        self.config = config
        self.llm = LLM(self.config)
        self.retriever = VectorRetriever(self.config)
        if self.config.get("reranker").get("type") != "none":
            self.reranker = Reranker(self.config)
        else:
            self.reranker = None
        self.prompt_template: str = (
            self.config.get("prompts").get("params").get("rag_prompt", None)
        )

    def query_rewrite(self, query: str) -> str:
        """Rewrites the query to get better retrieval."""
        prompt = f"""You are an expert search query optimizer for a Retrieval-Augmented Generation (RAG) system.
        Your task:
        Given the user's original query, rewrite it into a single, well-formed, search-optimized query that:
        - Preserves the original meaning and intent.
        - Uses clear, unambiguous language.
        - Includes relevant keywords and synonyms that improve retrieval.
        - Expands abbreviations or acronyms if needed and write the original abbreviation in bracket after it.
        - Matches the style of queries that would return the most relevant results from a mixed keyword + semantic search system.

        Return only the rewritten query as plain text — no explanations.

        Example:
        Original Query: "best EV range"
        Rewritten Query: "electric vehicles (EV) with the longest driving range"

        Original Query: "{query}"
        Rewritten Query:
        """
        return self.llm.generate(prompt).strip()

    def is_small_talk(self, query: str) -> bool:
        """Check if the query is a small talk or a greeting using LLM."""
        prompt = f"""You are an AI assistant that classifies user queries.
        Your task:
        Given the user's query, determine if it is a small talk or greeting.

        Stricly Return True if it is small talk or greeting, otherwise return False. No explanations.

        Example:
        User Query: "Hello, how are you?"
        Response: True

        User Query: "What is the capital of France?"
        Response: False

        User Query: "{query}"
        Response:"""
        response = self.llm.generate(prompt).strip().lower()
        return "true" in response.lower()

    def is_query_relevant(self, query: str, documents_content: str) -> bool:
        """Check if the query is relevant to the retrieved documents using LLM."""
        prompt = f"""You are an AI assistant that determines the relevance of a user's query to a set of documents.
        Your task:
        Given the user's query and the content of retrieved documents, determine if the query is relevant to the documents.

        Stricly Return True if it is relevant, otherwise return False. No explanations.

        Example:
        User Query: "What is the capital of France?"
        Documents Content: "France is a country in Europe. Its capital is Paris."
        Response: True

        User Query: "What is the capital of France?"
        Documents Content: "The Great Wall of China is a historic fortification."
        Response: False

        User Query: "{query}"
        Documents Content: "{documents_content}"
        Response:"""
        response = self.llm.generate(prompt).strip().lower()
        return "true" in response.lower()

    def get_response(self, query: str, filter=None, stream=False) -> Dict | Any:
        """Run the RAG pipeline to retrieve relevant documents and generate a response."""
        if not self.prompt_template:
            raise ValueError("Prompt is not set.")
        if not self.llm:
            raise ValueError("LLM model is not initialized.")

        rewritten_query = self.query_rewrite(query)
        expanded_query = rewritten_query + " " + query
        top_k = self.config.get("retriever").get("params").get("top_k", 15)
        documents = self.retriever.retrieve(expanded_query, top_k=top_k, filter=filter)
        if self.reranker:
            documents = self.reranker.rerank(expanded_query, documents)
        documents = documents[:top_k]

        if not documents:
            return {
                "text": "No relevant documents found.",
                "chunks": [],
                "metadata": [],
            }

        # Format the retrieved documents for the prompt
        documents_content = "\n\n----------\n\n".join(
            [doc.page_content for doc in documents]
        )

        fallback_response = (
            self.config.get("prompts")
            .get("params")
            .get(
                "fallback_response",
                "I cannot find relevant information to answer your question. Please ask your question relevant to the documents or rephrase it.",
            )
        )

        if self.is_small_talk(query):
            result = {
                "text": self.llm.generate(query),
                "chunks": [],
                "metadata": [],
            }

        else:
            if not self.is_query_relevant(rewritten_query, documents_content[:1024]):
                return {
                    "text": fallback_response,
                    "chunks": [],
                    "metadata": [],
                }

            else:
                # Prepare the prompt with retrieved documents
                prompt = self.prompt_template.format(
                    query=rewritten_query, context=documents_content
                )

                # Generate a response using the LLM model
                response = self.llm.generate(prompt, stream=stream)
        
                result = {
                    "text": response if response else fallback_response,
                    "chunks": documents,
                    "metadata": (
                        [getattr(doc, "metadata", {}) for doc in documents]
                        if response
                        else []
                    ),
                }
        return result

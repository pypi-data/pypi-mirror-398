import os
import re
import torch
from fabriq.llm import LLM
from typing import List
import cohere
import yaml
from langchain_core.documents import Document


class Reranker:
    def __init__(self, config):
        """Initialize the reranking model based on the specified type."""
        self.config = config
        model_name = (
            self.config.get("reranker")
            .get("params")
            .get("model_name", "BAAI/bge-reranker-base")
        )
        self.model_type = self.config.get("reranker").get("type", "cross_encoder")
        self.top_k = self.config.get("retriever").get("params").get("top_k", 25)
        self.device = self.config.get("reranker").get("params").get("device", "cpu")
        self.kwargs = self.config.get("reranker").get("kwargs", {})
        self.artifacts_path = self.config.get("reranker").get("params").get("artifacts_path", "./assets/models")

        if self.model_type == "cross_encoder":
            from sentence_transformers import CrossEncoder

            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

            self.reranker = CrossEncoder(
                model_name,
                device=self.device,
                automodel_args={
                    "torch_dtype": self.kwargs.pop("torch_dtype", "float16")
                },
                cache_dir=self.artifacts_path,
                **self.kwargs,
            )
        elif self.model_type == "llm":
            self.reranker = LLM(self.config)
        elif self.model_type == "cohere":
            self.reranker = cohere.ClientV2(
                base_url=self.config.reranker.get("params").get("endpoint"),
                api_key=os.getenv("CO_API_KEY"),
            )
        else:
            raise ValueError(f"Unsupported embedding model type: {self.model_type}")

    def get_reranking_model(self):
        """Return the initialized reranking model."""
        return self.reranker

    def llm_rerank(self, query, documents):
        ranked_results = []
        for doc in documents:
            prompt = f"""
            Query: {query}
            Document: {doc}
            
            On a scale of 0-10, how relevant is this document to the query?
            Provide your score in the following format:
            Score: <score>
            """
            score_response = self.reranker.generate(prompt)
            score_pattern = r"Score:\s*(\d+(?:\.\d+)?)"
            match = re.search(score_pattern, score_response)
            if match:
                score = float(match.group(1))
            else:
                score = 0.0
            ranked_results.append((score, doc))
        sorted_results = sorted(ranked_results, key=lambda x: x[0], reverse=True)
        sorted_results = sorted_results[: self.top_k]
        return [
            Document(
                page_content=doc.page_content,
                metadata={
                    **(doc.metadata if hasattr(doc, "metadata") else {}),
                    "relevance_score": score,
                },
            )
            for score, doc in sorted_results
        ]

    def cohere_rerank(self, query: str, documents: List) -> List:
        """Rerank a list of documents using Cohere Reranker."""

        yaml_docs = [yaml.dump(doc.page_content, sort_keys=False) for doc in documents]
        results = self.reranker.rerank(
            model="rerank-v3.5", query=query, documents=yaml_docs, top_k=self.top_k
        )
        reranked_docs = []
        for hit in results.results:
            matched_doc = documents[hit["index"]]
            metadata = getattr(matched_doc, "metadata", {})
            metadata["relevance_score"] = hit["relevance_score"]
            reranked_docs.append(
                Document(
                    page_content=matched_doc.page_content,
                    metadata=metadata,
                )
            )

    def cross_encoder_rerank(self, query: str, documents: List) -> List:
        """Rerank a list of documents using a cross-encoder."""
        reranked_docs = []
        model_inputs = [[query, doc.page_content] for doc in documents]
        scores = self.reranker.predict(model_inputs)

        # Sort the scores in decreasing order
        results = [
            {"input": inp, "relevance_score": score}
            for inp, score in zip(model_inputs, scores)
        ]
        results = sorted(results, key=lambda x: x["relevance_score"], reverse=True)

        for hit in results[: self.top_k]:
            # Find the original document by matching page_content
            matched_doc = next(
                (doc for doc in documents if doc.page_content == hit["input"][1]), None
            )
            if matched_doc:
                reranked_docs.append(
                    Document(
                        page_content=matched_doc.page_content,
                        metadata={
                            **(getattr(matched_doc, "metadata", {})),
                            "relevance_score": hit["relevance_score"],
                        },
                    )
                )
        return reranked_docs

    def rerank(self, query, documents):
        """Rerank a list of documents."""
        if self.model_type == "cross_encoder":
            return self.cross_encoder_rerank(query, documents)
        elif self.model_type == "llm":
            return self.llm_rerank(query, documents)
        elif self.model_type == "cohere":
            base_url = (
                self.config.get("reranker")
                .get("params")
                .get("base_url", os.getenv("CO_API_URL"))
            )
            api_key = self.kwargs.get("api_key", os.getenv("CO_API_KEY"))
            if base_url == "" or api_key == "" or api_key is None or base_url is None:
                raise ValueError("Cohere base_url and api_key must be provided.")
            return self.cohere_rerank(query, documents, base_url, api_key)
        else:
            raise ValueError("Unsupported reranking model type.")

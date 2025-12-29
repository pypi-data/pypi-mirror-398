import os
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain_azure_ai.embeddings import AzureAIEmbeddingsModel
from langchain.embeddings.base import Embeddings
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_google_vertexai.embeddings import VertexAIEmbeddings
from azure.core.credentials import AzureKeyCredential
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import jaccard_score
from typing import List
import torch

class EmbeddingModel:
    def __init__(self, config):
        """Initialize the embedding model based on the specified type."""
        self.config = config
        self.model_type = self.config.get("embeddings").get("type", "huggingface")
        self.model_name = (
            self.config.get("embeddings").get("params").get("model_name", "all-MiniLM-L6-v2")
        )
        self.deployment_name = self.config.get("embeddings").get("params").get("deployment_name")
        self.endpoint = self.config.get("embeddings").get("params").get("endpoint",None)
        self.project_connection_string = self.config.get("embeddings").get("params").get("project_connection_string",None)
        self.device = self.config.get("embeddings").get("params").get("device", "auto")
        self.kwargs = self.config.get("embeddings").get("params").get("kwargs", {})
        
        if self.model_type == "huggingface":
            if self.device == "auto":
                self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs = {'device': self.device},
                **self.kwargs
            )
        
        elif self.model_type == "openai":
            self.embedding_model = OpenAIEmbeddings(model=self.model_name, **self.kwargs)
        
        elif self.model_type == "azure_openai":
            self.embedding_model = AzureOpenAIEmbeddings(
                model=self.model_name,
                azure_endpoint=self.endpoint,
                azure_deployment=self.deployment_name,
                **self.kwargs,
            )
        
        elif self.model_type == "azure_ai":
            #TODO: check credential to be passed
            # token_provider = get_bearer_token_provider(
            #     DefaultAzureCredential(),
            #     "https://cognitiveservices.azure.com/.default",
            # )
            self.embedding_model = AzureAIEmbeddingsModel(
                model_name=self.model_name,
                project_connection_string=self.project_connection_string,
                endpoint=self.endpoint,
                model=self.model_name,
                credential=AzureKeyCredential(os.getenv("AZURE_EMBEDDINGS_KEY"))
                # azure_ad_token_provider=token_provider,
                **self.kwargs,
            )
        
        elif self.model_type == "gemini":
            self.embedding_model = GoogleGenerativeAIEmbeddings(model=self.model_name)
        
        elif self.model_type == "vertex":
            self.embedding_model = VertexAIEmbeddings(
                model_name=self.model_name,
                project=self.kwargs.get("project_name", None),
                location=self.kwargs.get("region", "us-central1"),
                **self.kwargs
            )
        
        elif self.model_type == "bedrock":
            self.embedding_model = BedrockEmbeddings(
                model_id=self.model_name,
                model_kwargs=self.kwargs,
                credentials_profile_name=self.kwargs.get("credentials_profile_name", None),
                region_name=self.kwargs.get("region", "us-east-1"),
            )
        
        elif self.model_type == "ollama":
            self.embedding_model = OllamaEmbeddings(model=self.model_name)
        
        else:
            raise ValueError(f"Unsupported embedding model type: {self.model_type}")

    def get_embedding_model(self) -> Embeddings:
        """Return the initialized embedding model."""
        return self.embedding_model

    def embed_documents(self, documents) -> list:
        """Embed a list of documents."""
        return self.embedding_model.embed_documents(documents)

    def embed_query(self, query: str) -> list:
        """Embed a single query."""
        return self.embedding_model.embed_query(query)

    async def async_embed_documents(self, documents) -> list:
        """Asynchronously embed a list of documents."""
        return await self.embedding_model.aembed_documents(documents)

    async def async_embed_query(self, query: str) -> list:
        """Asynchronously embed a single query."""
        return await self.embedding_model.aembed_query(query)
    
    def get_similarity(self, text1: str | List, text2: str | List, metric: str = "cosine"):
        """Calculate the similarity between two texts."""
        if isinstance(text1, list) and isinstance(text2, list):
            embedding1 = self.embedding_model.embed_documents(text1)
            embedding2 = self.embedding_model.embed_documents(text2)
        elif isinstance(text1, str) and isinstance(text2, str):
            embedding1 = self.embedding_model.embed_query(text1)
            embedding2 = self.embedding_model.embed_query(text2)
        else:
            raise ValueError("Both text1 and text2 must be either both strings or both lists.")

        if metric not in ["cosine", "jaccard"]:
            raise ValueError(f"Unsupported metric: {metric}. Available metrics: cosine, jaccard")
        
        if metric == "cosine":
            similarity = cosine_similarity([embedding1], [embedding2])
        elif metric == "jaccard":
            similarity = jaccard_score([embedding1], [embedding2], average="micro")
        return similarity[0][0]

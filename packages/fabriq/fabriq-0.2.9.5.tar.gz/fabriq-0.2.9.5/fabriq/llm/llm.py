from langchain_openai.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_groq import ChatGroq
from azure.core.credentials import AzureKeyCredential
from langchain_aws.chat_models import ChatBedrockConverse
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
# from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_ollama.chat_models import ChatOllama
from langchain_huggingface.chat_models import ChatHuggingFace
# from langchain_litellm import ChatLiteLLM
from pydantic import BaseModel
from typing import Any, List, Dict
import base64
from io import BytesIO
import numpy as np
from PIL import Image
import requests
import os
from tenacity import retry, stop_after_attempt


class LLM:
    def __init__(self, config: Dict):
        """Initialize the LLM model based on the specified type."""
        self.config = config
        model_type = self.config.get("llm").get("type")
        self.model_name = self.config.get("llm").get("params").get("model_name", None)
        self.device = self.config.get("llm").get("params").get("device", "auto")
        self.endpoint = self.config.get("llm").get("params", {}).get("endpoint", None)
        self.project_endpoint = (
            self.config.get("llm")
            .get("params", {})
            .get("project_endpoint", None)
        )
        self.api_version = (
            self.config.get("llm").get("params", {}).get("api_version", None)
        )
        self.deployment_name = (
            self.config.get("llm").get("params", {}).get("deployment_name", None)
        )
        self.model_kwargs = self.config.get("llm").get("kwargs", {})

        self.system_prompt = (
            self.config.get("prompts")
            .get("params")
            .get("system_prompt", "You are a helpful AI assistant.")
        )

        if model_type == "openai":
            self.llm = ChatOpenAI(
                model=self.model_name, base_url=self.endpoint, **self.model_kwargs
            )

        elif model_type == "azure_openai":
            self.llm = AzureChatOpenAI(
                azure_deployment=self.deployment_name,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
                seed=42,
                **self.model_kwargs,
            )

        elif model_type == "azure_ai":
            self.llm = AzureAIChatCompletionsModel(
                model=self.model_name,
                project_endpoint=self.project_endpoint,
                endpoint=self.endpoint,
                credential=AzureKeyCredential(os.getenv("AZURE_AI_KEY")),
                seed=42,
                **self.model_kwargs,
            )

        elif model_type == "gemini":
            self.llm = ChatGoogleGenerativeAI(
                model=self.model_name, **self.model_kwargs
            )

        elif model_type == "bedrock":
            self.llm = ChatBedrockConverse(
                name=self.model_name,
                region=self.model_kwargs.get("region", "us-east-1"),
                **self.model_kwargs,
            )

        elif model_type == "ollama":
            self.llm = ChatOllama(model=self.model_name, **self.model_kwargs)

        elif model_type == "huggingface":
            import torch
            from transformers import pipeline
            from langchain_huggingface.llms import HuggingFacePipeline

            if self.device == "auto":
                self.device = (
                    "cuda"
                    if torch.cuda.is_available()
                    else "mps" if torch.backends.mps.is_available() else "cpu"
                )

            hf_pipeline = pipeline(
                "text-generation",
                model=self.model_name,
                device_map=self.device,
                torch_dtype=self.model_kwargs.get("torch_dtype", torch.float16),
                max_new_tokens=self.model_kwargs.get("max_tokens", 1024),
                temperature=self.model_kwargs.get("temperature", 0.1),
                top_p=self.model_kwargs.get("top_p", 0.9),
                top_k=self.model_kwargs.get("top_k", 50),
                **self.model_kwargs,
            )
            pipeline_ = HuggingFacePipeline(pipeline=hf_pipeline)
            self.llm = ChatHuggingFace(llm=pipeline_)

        elif model_type == "groq":
            self.llm = ChatGroq(
                model=self.model_name,
                temperature=self.model_kwargs.get("temperature", 0.1),
                max_tokens=self.model_kwargs.get("max_tokens", 1024),
                timeout=self.model_kwargs.get("timeout", 60),
                max_retries=self.model_kwargs.get("max_retries", 3),
            )
        
        elif model_type == "mistral":
            self.llm = ChatMistralAI(
                model=self.model_name,
                **self.model_kwargs,
            )

        else:
            raise ValueError(
                f"Unsupported LLM model type: {model_type}. Possible values are 'openai', 'azure_openai', 'azure_ai', 'bedrock', 'gemini', 'vertex', 'huggingface', 'groq', 'mistral'."
            )

    def get_llm(self):
        """Return the initialized LLM model."""
        return self.llm

    def create_base64_image(self, image: Any) -> str:
        """Convert any image type to base64 string."""

        if isinstance(image, str):
            if image.startswith("http://") or image.startswith("https://"):
                response = requests.get(image)
                image = BytesIO(response.content)
                image = Image.open(image)
            elif image.startswith("data:image/"):
                image = BytesIO(base64.b64decode(image.split(",")[1]))
                image = Image.open(image)
            else:
                image = Image.open(image)
        elif isinstance(image, bytes):
            image = Image.open(BytesIO(image))
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        else:
            raise ValueError(
                "Unsupported image type. Must be a file path, URL, bytes, NumPy array, or base64 string."
            )

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str

    @retry(reraise=True, stop=stop_after_attempt(3))
    def generate(
        self,
        prompt: str,
        image: Any = None,
        system_prompt: str = None,
        stream: bool = False,
        response_format: Dict | BaseModel = None,
        **kwargs,
    ) -> str:
        """Generate text based on the provided prompt."""
        if system_prompt:
            system_message = SystemMessage(system_prompt)
        else:
            system_message = SystemMessage("You are a helpful AI assistant.")

        if image:
            base64_image = self.create_base64_image(image)
            image_url = f"data:image/png;base64,{base64_image}"

            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
            human_message = HumanMessage(content)
        else:
            human_message = HumanMessage(prompt)

        if kwargs.get("ai_message"):
            ai_message = AIMessage(kwargs.get("ai_message"))
            prompt = [system_message, human_message, ai_message]
        else:
            prompt = [system_message, human_message]

        if response_format:
            self.llm_structured = self.llm.with_structured_output(response_format)
            if stream:
                return self.llm_structured.stream(prompt, **kwargs)
            else:
                responses = self.llm_structured.invoke(prompt, **kwargs)
                return responses

        else:
            if stream:
                return self.llm.stream(prompt, **kwargs)
            else:
                responses = self.llm.invoke(prompt, **kwargs)
                return responses.content

    @retry(reraise=True, stop=stop_after_attempt(3))
    async def generate_async(
        self,
        prompt: str,
        image: Any = None,
        system_prompt: str = None,
        stream: bool = False,
        response_format: Dict | BaseModel = None,
        **kwargs,
    ):
        """Asynchronously generate text based on the provided prompt."""
        if system_prompt:
            system_message = SystemMessage(system_prompt)
        else:
            system_message = SystemMessage("You are a helpful AI assistant.")

        if image:
            base64_image = self.create_base64_image(image)
            image_url = f"data:image/png;base64,{base64_image}"

            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
            human_message = HumanMessage(content)
        else:
            human_message = HumanMessage(prompt)

        if kwargs.get("ai_message"):
            ai_message = AIMessage(kwargs.get("ai_message"))
            prompt = [system_message, human_message, ai_message]
        else:
            prompt = [system_message, human_message]

        if response_format:
            self.llm_structured = self.llm.with_structured_output(response_format)
            if stream:
                return self.llm_structured.astream(prompt, **kwargs)
            else:
                responses = await self.llm_structured.ainvoke(prompt, **kwargs)
                return responses.content

        else:
            if stream:
                return self.llm.astream(prompt, **kwargs)
            else:
                responses = await self.llm.ainvoke(prompt, **kwargs)
                return responses.content

    @retry(reraise=True, stop=stop_after_attempt(3))
    def generate_batch(
        self,
        prompts: List[str],
        images: List[Any] = None,
        system_prompt: str = None,
        stream: bool = False,
        response_format: Dict | BaseModel = None,
        **kwargs,
    ) -> List[str]:
        """Generate text in batches based on the provided prompts."""
        if system_prompt:
            system_message = SystemMessage(system_prompt)
        else:
            system_message = SystemMessage("You are a helpful AI assistant.")

        prompts_batch = []
        for idx, prompt in enumerate(prompts):
            if images and idx < len(images) and images[idx] is not None:
                base64_image = self.create_base64_image(images[idx])
                image_url = f"data:image/png;base64,{base64_image}"
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
                human_message = HumanMessage(content)
            else:
                human_message = HumanMessage(prompt)

            if kwargs.get("ai_message"):
                ai_message = AIMessage(kwargs.get("ai_message"))
                prompts_batch.append([system_message, human_message, ai_message])
            else:
                prompts_batch.append([system_message, human_message])

        if response_format is not None:
            self.llm_structured = self.llm.with_structured_output(response_format)
            if stream:
                responses = self.llm_structured.batch_as_completed(
                    prompts_batch, **kwargs
                )
            else:
                responses = self.llm_structured.batch(prompts_batch, **kwargs)
            return responses

        else:
            if stream:
                responses = self.llm.batch_as_completed(prompts_batch, **kwargs)
                return responses
            else:
                responses = self.llm.batch(prompts_batch, **kwargs)
                return [resp.content.strip() for resp in responses]

    @retry(reraise=True, stop=stop_after_attempt(3))
    async def generate_batch_async(
        self,
        prompts: List[str],
        images: List[Any] = None,
        system_prompt: str = None,
        stream: bool = False,
        response_format: Dict | BaseModel = None,
        **kwargs,
    ) -> List[str]:
        """Asynchronously generate text in batches based on the provided prompts."""
        if system_prompt:
            system_message = SystemMessage(system_prompt)
        else:
            system_message = SystemMessage("You are a helpful AI assistant.")

        prompts_batch = []
        for idx, prompt in enumerate(prompts):
            if images and idx < len(images) and images[idx] is not None:
                base64_image = self.create_base64_image(images[idx])
                image_url = f"data:image/png;base64,{base64_image}"
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
                human_message = HumanMessage(content)
            else:
                human_message = HumanMessage(prompt)

            if kwargs.get("ai_message"):
                ai_message = AIMessage(kwargs.get("ai_message"))
                prompts_batch.append([system_message, human_message, ai_message])
            else:
                prompts_batch.append([system_message, human_message])

        if response_format is not None:
            self.llm_structured = self.llm.with_structured_output(response_format)
            if stream:
                # abatch_as_completed is likely an async generator, so should be iterated
                return [
                    resp
                    async for resp in self.llm_structured.abatch_as_completed(
                        prompts_batch, **kwargs
                    )
                ]
            else:
                responses = await self.llm_structured.abatch(prompts_batch, **kwargs)
                return responses

        else:
            if stream:
                return [
                    resp
                    async for resp in self.llm.abatch_as_completed(
                        prompts_batch, **kwargs
                    )
                ]
            else:
                responses = await self.llm.abatch(prompts_batch, **kwargs)
                return [resp.content.strip() for resp in responses]

from pydantic import Field, BaseModel
from typing import List
import json


class ResponseFormat(BaseModel):
    categories: str = Field(description="a category for text to be classified.")


class ResponseFormat_MultiClass(BaseModel):
    categories: List[str] = Field(
        description="List of categories in which text can be classified."
    )


class TextClassification:
    def __init__(self, llm=None):
        """Initialize the Text Classification tool."""
        self.llm = llm
        self._multiclass_prompt = """You are an expert text classification tool. Classify the given text into the following categories:
            {categories}

            Text:
            {text}

            Follow this output format stricly:
            {{
            "categories" : ["<category_1>","<category_2>","<category_3>", ...]
            }}
            """
        self._singleclass_prompt = """You are an expert text classification tool. Classify the given text in strictly one of the following categories:
            {categories}

            Text:
            {text}

            Follow this output format stricly:
            {{
            "categories" : ["<category>"]
            }}
            """
        if not self.llm:
            raise ValueError(
                "Missing Required Parameter: 'llm'. Please pass LLM model to init method."
            )

    def run(
        self, text: str = None, categories: List[str] = [], multiclass: bool = False
    ):
        if text and len(categories) > 0:
            if multiclass:
                prompt = self._multiclass_prompt.format(
                    text=text, categories=categories
                )
                categories = self.llm.generate(prompt,response_format=ResponseFormat_MultiClass.model_json_schema())
            else:
                prompt = self._singleclass_prompt.format(
                    text=text, categories=categories
                )
                categories = self.llm.generate(prompt,response_format=ResponseFormat.model_json_schema())
            categories = json.loads(categories)

            return categories

        else:
            raise ValueError("Missing one or more parameters: text, categories.")

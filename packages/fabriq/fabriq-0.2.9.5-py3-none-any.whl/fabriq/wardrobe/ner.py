from pydantic import Field, BaseModel
from typing import List, Dict
import json


class ResponseFormat(BaseModel):
    entities: Dict = Field(description="Words as keys and Entities as Values")

class NER:
    def __init__(self, llm=None):
        """Initialize the Named Entity Recognition tool."""
        self.llm = llm
        if not self.llm:
            raise ValueError(
                "Missing Required Parameter: 'llm'. Please pass LLM model to init method."
            )

    def run(self, text: str = None, entities: List[str] = []):
        if text and len(entities) > 0:
            prompt = """You are an expert entity extraction tool. From the given text, extract the following entities:\n
            {entities}

            Text:
            {text}

            Follow this output format strictly:
            {{
            "words" : ["<word_1 corresponding to entity_1>", "<word_2 corresponding to entity_2>", ...]
            "entities" : ["<entity_1 corresponding to word_1>", "<entity_2 corresponding to word_2>", ...]
            }}
            """

            prompt = prompt.format(entities=entities, text=text)
            entities = self.llm.generate(prompt,response_format=ResponseFormat.model_json_schema())
            entities = json.loads(entities)
            entity_dict = {word: entity for word, entity in zip(entities['words'], entities['entities'])}
            return entity_dict

        else:
            raise ValueError("Missing one or more parameters: text, entities.")

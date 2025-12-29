from langchain_core.documents import Document
from langchain_classic.chains.summarize import load_summarize_chain
from typing import List

class TextSummarization:
    def __init__(self, llm=None, summary_prompt: str = None):
        """Initialize the Text Summarization tool."""
        self.llm = llm
        if not self.llm:
            raise ValueError(
                "Missing Required Parameter: 'llm'. Please pass LLM model to init method."
            )
        self.summary_prompt = (
            summary_prompt
            if summary_prompt
            else """You are an expert text summarizer who excels in writing concise summary from any kind of text 
                while retaining key informations and insights from it. Summarize the given text.
                
                Text:
                {text}"""
        )

    def summarize_text(self, text: str = None):
        if text:
            prompt = self.summary_prompt.format(text=text)
            summary = self.llm.generate(prompt)
            return summary
        else:
            raise ValueError("Missing parameter: 'text'.")
        

    def summarize_docs(self, documents: List[str] = None):
        if documents or len(documents)>0:
            docs = [Document(page_content=doc) for doc in documents]
            chain = load_summarize_chain(llm=self.llm,chain_type="map_reduce")
            summary = chain.invoke(docs)
            return summary['output_text']

        else:
            raise ValueError("Missing list of documents to be passed to 'docs'.")
        
    def summarize_large_docs(self, documents: List[str] = None):
        if documents or len(documents)>0:
            docs = [Document(page_content=doc) for doc in documents]
            chain = load_summarize_chain(llm=self.llm,chain_type="refine")
            summary = chain.invoke(docs)
            return summary['output_text']
        
        else:
            raise ValueError("Missing list of documents to be passed to 'docs'.")
        
    def run(self, document: str | List[str] = None, summary_type: str = "text"):
        if summary_type == "text":
            return self.summarize_text(document)
        
        elif summary_type == "docs":
            return self.summarize_docs(document)
        
        elif summary_type == "large_docs":
            return self.summarize_large_docs(document)
        
        else:
            raise ValueError(f"Unsupported summary_type: {summary_type}. Possible values are: 'text', 'docs', 'large_docs'.")
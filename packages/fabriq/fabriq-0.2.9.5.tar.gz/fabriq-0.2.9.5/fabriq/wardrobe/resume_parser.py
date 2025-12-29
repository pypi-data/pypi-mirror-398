import json
import time
from fabriq.document_loader.document_loader import DocumentLoader
from fabriq.llm import LLM
from pydantic import BaseModel, Field
from typing import List, Dict

class ResumeSchema(BaseModel):
    name: str = Field(..., description="Full name of the candidate")
    email: str = Field(..., description="Email address of the candidate")
    phone: str = Field(..., description="Phone number of the candidate")
    links: List[str] = Field(..., description="List of links such as LinkedIn, GitHub, Portfolio etc.")
    education: List[Dict[str,str]] = Field(..., description="List of educational qualifications with degree name, institution, year of passing as dictionary")
    experience: Dict[str,str] = Field(..., description="dictionary of company name as keys and duration of experience including dates as values")
    skills: List[str] = Field(..., description="List of skills")
    projects: List[str] = Field(..., description="Details of projects undertaken")
    misc: List[str] = Field(..., description="Any additional information such as certifications, languages, achievements etc.")
    employment_gap: List[str] = Field(..., description="List of any employment gaps if any else empty list")

class ResumeParser:
    def __init__(self, config):
        self.doc_loader = DocumentLoader(config)
        self.llm = LLM(config)

    def parse_resume(self, file_path):
        doc = self.doc_loader.load_document(file_path, mode="single")
        text = doc[0].page_content if doc else ""
        system_prompt = "You are an expert resume parser. You will be provided with resume text and you need to extract relevant information in a structured JSON format."
        prompt = (
            f"""Parse the given Resume text accurately:\n
            {text}\n
            Extract the following fields: name, email, phone, links, education, experience, skills, projects, misc, employment_gap.
            Think thoroughly and ensure the extracted information is accurate.
            JSON:
            """
        )
        response = self.llm.generate(prompt,system_prompt=system_prompt, response_format=ResumeSchema.model_json_schema())
        try:
            resume_json = json.loads(response) if isinstance(response, str) else response
        except Exception:
            resume_json = {"name": "", "email": "", "phone": "", "links": [], "experience": {}, "skills": [], "projects": [], "misc": [], "employment_gap": []}

        return resume_json
    
    def parse_resumes(self, file_paths: List[str]) -> List[Dict]:
        parsed_resumes = []
        for file_path in file_paths:
            parsed_resume = self.parse_resume(file_path)
            parsed_resumes.append(parsed_resume)
            time.sleep(5)
        return parsed_resumes
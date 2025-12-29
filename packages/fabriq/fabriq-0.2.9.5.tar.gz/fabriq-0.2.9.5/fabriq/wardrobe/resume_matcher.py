import pandas as pd
from fabriq.wardrobe.resume_parser import ResumeParser
from fabriq.llm import LLM
from typing import List, Dict
from pydantic import BaseModel, Field

class MatchScoreSchema(BaseModel):
    score: int = Field(..., description="Match score either 0 or 1")
    reasoning: str = Field(..., description="Reasoning for the score")

class ResumeMatcher:
    def __init__(self, config):
        self.resume_parser = ResumeParser(config)
        self.llm = LLM(config)
    
    def get_match_score(self, resume_paths: List[str], job_description: str, criteria_fields: List[str]) -> List[Dict]:
        prompts = []
        resume_indices = []
        parsed_resumes = self.resume_parser.parse_resumes(resume_paths)

        for i, resume in enumerate(parsed_resumes):
            resume_text = "\n\n".join([f"{key}: {value}" for key, value in resume.items()])
            for field in criteria_fields:
                prompt = (
                    f"Job Description:\n{job_description}\n\n"
                    f"Resume:\n{resume_text}\n\n"
                    f"Criteria: {field}\n\n"
                    "Does this resume satisfy the given criteria when compared to the job description? "
                    "Answer should be a score with '1' (matches) or '0' (does not match) and brief reasoning.\n\n"
                )
                prompts.append(prompt)
                resume_indices.append((i, field))

        results = self.llm.generate_batch(prompts, response_format=MatchScoreSchema.model_json_schema())

        # Aggregate scores per resume
        match_counts = {i: 0 for i in range(len(parsed_resumes))}
        criteria_breakdown = {i: [] for i in range(len(parsed_resumes))}

        for idx_field, result in zip(resume_indices, results):
            idx, field = idx_field
            idx += 1
            try:
                score = int(result.get("score"))
                score = 1 if score == 1 else 0
                reasoning = result.get("reasoning", "").strip()
            except Exception:
                score = 0
                reasoning = ""

            match_counts[idx] += score
            criteria_breakdown[idx].append({
            'criteria_index': criteria_fields.index(field),
            'criteria_statement': field,
            'score': score,
            'reasoning': reasoning
            })

        # Store results
        score_list = []
        for i, resume in enumerate(parsed_resumes):
            resume_scores = {}
            total_criteria = len(criteria_fields)
            raw_score = match_counts[i]
            match_percentage = (raw_score / total_criteria * 100) if total_criteria > 0 else 0

            resume_scores['name'] = resume.get('name', "").title()
            resume_scores['email'] = resume.get('email', "")
            resume_scores['phone'] = resume.get('phone', "")
            resume_scores['match_score'] = round(match_percentage, 2)
            resume_scores['criteria_breakdown'] = criteria_breakdown[i]
            score_list.append(resume_scores)

        return score_list
    
    def rank_resumes(self, resume_paths: List[str], job_description: str, criteria_fields: List[str]) -> List[Dict]:
        resumes_with_score = self.get_match_score(resume_paths, job_description, criteria_fields)
        resumes_with_score = sorted(resumes_with_score, key=lambda x: x.get('match_score', 0), reverse=True)
        for rank, resume in enumerate(resumes_with_score, start=1):
            resume['rank'] = rank
        ranked_df = pd.DataFrame(resumes_with_score)
        return ranked_df
                
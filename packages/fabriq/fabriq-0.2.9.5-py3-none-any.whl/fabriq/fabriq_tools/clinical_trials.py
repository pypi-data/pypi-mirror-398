from pytrials.client import ClinicalTrials
from typing import List


class ClinicalTrialsTool:
    def __init__(self):
        """Initialize the clinical trial tool."""
        self._client = ClinicalTrials()
        self._study_fields = self._client.study_fields["json"]
        self.description = "A tool for searching clinical trials. You can search for trials by providing a query string. You can also specify study fields to retrieve specific information about the trials."

    def get_trials_by_fields(
        self, query: str = None, studyFields: List[str] = None, max_studies: int = 100
    ):
        if max_studies > 1000 or max_studies < 1:
            raise ValueError("The number of studies can only be between 1 and 1000")

        for field in studyFields:
            if field not in self._study_fields:
                raise ValueError(
                    f"Unknown Study Field: '{field}'. Possible Values: {self._study_fields}"
                )

        if query:
            results = self._client.get_study_fields(
                search_expr=query,
                fields=studyFields,
                max_studies=max_studies,
                fmt="json",
            )
            return results
        else:
            return None

    def get_all_trials(self, query: str = None, max_studies: int = 100):
        if query:
            results = self._client.get_full_studies(
                search_expr=query, max_studies=max_studies, fmt="json"
            )
            return results
        else:
            return None

    def run(
        self,
        query: str = None,
        max_studies: int = 100,
        studyFields: List[str] = None,
        trial_type="all",
    ):
        if trial_type == "all":
            return self.get_all_trials(query=query, max_studies=max_studies)

        elif trial_type == "by_field":
            return self.get_trials_by_fields(
                query=query, studyFields=studyFields, max_studies=max_studies
            )

        else:
            raise ValueError(
                f"Unknown trial_type: {trial_type}. Possible values are: 'all', 'by_field'."
            )

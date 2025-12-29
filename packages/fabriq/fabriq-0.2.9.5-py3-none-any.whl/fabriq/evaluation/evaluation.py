from deepeval import evaluate
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    ContextualRelevancyMetric,
    GEval,
    FaithfulnessMetric,
    HallucinationMetric,
    SummarizationMetric,
)
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics.base_metric import BaseMetric
from fabriq.llm import LLM
import traceback
from typing import Dict, List, Any


class _CustomModel(DeepEvalBaseLLM):
    def __init__(self, config):
        self.config = config
        self.model = LLM(config).llm

    def load_model(self):
        return self.model

    def generate(self, prompt: str):
        resp = self.model.invoke(prompt).content
        return resp

    async def a_generate(self, prompt: str):
        resp = await self.model.ainvoke(prompt)
        return resp.content

    def get_model_name(self):
        return self.model.name


class Evaluation:
    def __init__(self, config):
        self.config = config
        self.model = _CustomModel(config)

    def run_evaluation(self, test_cases: List[LLMTestCase], metrics: List[str]):
        try:
            eval_result = evaluate(test_cases=test_cases, metrics=metrics)
            return eval_result
        except Exception as e:
            print(e, traceback.format_exc())

    def get_metrics(self, metric_name: str) -> BaseMetric:
        custom_criteria = (
                    self.config.get("evaluation")
                    .get("params")
                    .get("custom_eval_prompt")
                )
        all_metrics = {
            "answer_relevancy": AnswerRelevancyMetric,
            "contextual_precision": ContextualPrecisionMetric,
            "contextual_recall": ContextualRecallMetric,
            "contextual_relevancy": ContextualRelevancyMetric,
            "custom": GEval(
                name="custom_metric",
                criteria=custom_criteria,
                evaluation_params=[
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                    LLMTestCaseParams.EXPECTED_OUTPUT,
                ],
            ) if custom_criteria else None,
            "faithfulness": FaithfulnessMetric,
            "hallucination": HallucinationMetric,
            "summarization": SummarizationMetric,
        }
        if metric_name.lower() not in all_metrics.keys():
            raise ValueError(
                f"No metric found with name: {metric_name}. Available metrics are: {list(all_metrics.keys())}"
            )
        return all_metrics[metric_name]

    def rag_evaluation(
        self,
        retrieved_docs: List[str],
        query: str = None,
        answer: str = None,
        expected_answer: str = None,
    ) -> Dict[str, Any]:

        input_metrics = self.config.get("evaluation").get("params").get("metrics")
        metrics = [self.get_metrics(metric) for metric in input_metrics]

        test_case = LLMTestCase(
            input=query,
            actual_output=answer,
            expected_output=expected_answer,
            retrieval_context=retrieved_docs,
            context=retrieved_docs,
        )
        async_mode = self.config.get("evaluation").get("params").get("async_mode")

        results = {}
        for metric_name in metrics:
            include_reason = (
                self.config.get("evaluation").get("params").get("explanation")
            )
            metric = metric_name(
                model=self.model,
                include_reason=include_reason,
                async_mode=async_mode,
            )
            try:
                metric_result = evaluate(test_cases=[test_case], metrics=[metric])
                results[metric.__name__] = {
                    "Score": metric_result.test_results[0].metrics_data[0].score,
                    "Reason": metric_result.test_results[0].metrics_data[0].reason,
                }
            except Exception as e:
                results[metric.__name__] = f"Skipped (insufficient parameters): {e}"
                print(traceback.format_exc())
        return results

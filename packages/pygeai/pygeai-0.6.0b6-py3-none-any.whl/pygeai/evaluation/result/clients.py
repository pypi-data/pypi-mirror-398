import json

from pygeai.evaluation.clients import EvaluationClient
from pygeai.evaluation.result.endpoints import LIST_EVALUATION_RESULTS, GET_EVALUATION_RESULT


class EvaluationResultClient(EvaluationClient):

    def list_evaluation_results(self, evaluation_plan_id: str) -> dict:
        """
        Retrieves a list of evaluation results for a given evaluation plan ID.

        :param evaluation_plan_id: str - The ID of the evaluation plan.

        :return: dict - API response containing a list of evaluation results.
        """
        endpoint = LIST_EVALUATION_RESULTS.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def get_evaluation_result(self, evaluation_result_id: str) -> dict:
        """
        Retrieves a specific evaluation result by its ID.

        :param evaluation_result_id: str - The ID of the evaluation result.

        :return: dict - The evaluation result metadata as a dictionary.
        """
        endpoint = GET_EVALUATION_RESULT.format(evaluationResultId=evaluation_result_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

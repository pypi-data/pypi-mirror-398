import json

from pygeai.evaluation.clients import EvaluationClient
from pygeai.evaluation.plan.endpoints import LIST_EVALUATION_PLANS, CREATE_EVALUATION_PLAN, GET_EVALUATION_PLAN, \
    UPDATE_EVALUATION_PLAN, DELETE_EVALUATION_PLAN, LIST_EVALUATION_PLAN_SYSTEM_METRICS, \
    ADD_EVALUATION_PLAN_SYSTEM_METRIC, GET_EVALUATION_PLAN_SYSTEM_METRIC, UPDATE_EVALUATION_PLAN_SYSTEM_METRIC, \
    DELETE_EVALUATION_PLAN_SYSTEM_METRIC, LIST_SYSTEM_METRICS, GET_SYSTEM_METRIC, EXECUTE_EVALUATION_PLAN


class EvaluationPlanClient(EvaluationClient):

    def list_evaluation_plans(self) -> dict:
        """
        Retrieves a list of all evaluation plans.

        :return: dict - API response containing a list of evaluation plans.
        """
        response = self.api_service.get(
            endpoint=LIST_EVALUATION_PLANS
        )
        result = json.loads(response.content)
        return result

    def create_evaluation_plan(
            self,
            name: str,
            type: str,
            assistant_id: str = None,
            assistant_name: str = None,
            assistant_revision: str = None,
            profile_name: str = None,
            dataset_id: str = None,
            system_metrics: list = None,
    ) -> dict:
        """
        Creates a new evaluation plan.

        :param name: str - Name of the evaluation plan.
        :param type: str - Type of assistant (e.g., "TextPromptAssistant", "RAG Assistant").
        :param assistant_id: str (optional) - ID of the assistant (required for "TextPromptAssistant").
        :param assistant_name: str (optional) - Name of the assistant (required for "TextPromptAssistant").
        :param assistant_revision: str (optional) - Revision of the assistant (required for "TextPromptAssistant").
        :param profile_name: str (optional) - Name of the RAG profile (required for "RAG Assistant").
        :param dataset_id: str (optional) - ID of the dataset.
        :param system_metrics: list (optional) - Array of system metrics, each containing:
            - systemMetricId: str - ID of the system metric.
            - systemMetricWeight: float - Weight of the system metric (between 0 and 1).

        :return: dict - API response with the created evaluation plan.
        """
        data = {
            "evaluationPlanName": name,
            "evaluationPlanType": type,
            "systemMetrics": system_metrics,
        }
        if assistant_id is not None:
            data["evaluationPlanAssistantId"] = assistant_id
        if assistant_name is not None:
            data["evaluationPlanAssistantName"] = assistant_name
        if assistant_revision is not None:
            data["evaluationPlanAssistantRevision"] = assistant_revision
        if profile_name is not None:
            data["evaluationPlanProfileName"] = profile_name
        if dataset_id is not None:
            data["dataSetId"] = dataset_id

        response = self.api_service.post(
            endpoint=CREATE_EVALUATION_PLAN,
            data=data
        )
        result = json.loads(response.content)
        return result

    def get_evaluation_plan(self, evaluation_plan_id: str) -> dict:
        """
        Retrieves a specific evaluation plan by ID.

        :param evaluation_plan_id: str - The ID of the evaluation plan.

        :return: dict - The evaluation plan metadata as a dictionary.
        """
        endpoint = GET_EVALUATION_PLAN.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def update_evaluation_plan(
            self,
            evaluation_plan_id: str,
            name: str = None,
            type: str = None,
            assistant_id: str = None,
            assistant_name: str = None,
            assistant_revision: str = None,
            profile_name: str = None,
            dataset_id: str = None,
            system_metrics: list = None,
    ) -> dict:
        """
        Updates an existing evaluation plan by ID.

        :param evaluation_plan_id: str - The unique identifier of the evaluation plan to update.
        :param name: str, optional - The new name of the evaluation plan.
        :param type: str, optional - The type of the evaluation plan.
        :param assistant_id: str, optional - The ID of the assistant associated with the evaluation plan.
        :param assistant_name: str, optional - The name of the assistant associated with the evaluation plan.
        :param assistant_revision: str, optional - The revision identifier of the assistant.
        :param profile_name: str, optional - The profile name associated with the evaluation plan.
        :param dataset_id: str, optional - The ID of the dataset linked to the evaluation plan.
        :param system_metrics: list, optional - A list of system metrics, each containing:
            - systemMetricId (str): The metric identifier.
            - systemMetricWeight (float): The weight of the metric (0 to 1).

        :return: dict - API response containing the updated evaluation plan.
        """
        data = dict()

        if name is not None:
            data["evaluationPlanName"] = name
        if type is not None:
            data["evaluationPlanType"] = type
        if system_metrics is not None:
            data["systemMetrics"] = system_metrics
        if assistant_id is not None:
            data["evaluationPlanAssistantId"] = assistant_id
        if assistant_name is not None:
            data["evaluationPlanAssistantName"] = assistant_name
        if assistant_revision is not None:
            data["evaluationPlanAssistantRevision"] = assistant_revision
        if profile_name is not None:
            data["evaluationPlanProfileName"] = profile_name
        if dataset_id is not None:
            data["dataSetId"] = dataset_id

        endpoint = UPDATE_EVALUATION_PLAN.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        result = json.loads(response.content)
        return result

    def delete_evaluation_plan(self, evaluation_plan_id: str) -> dict:
        """
        Deletes a specific evaluation plan by ID.

        :param evaluation_plan_id: str - The ID of the evaluation plan.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_EVALUATION_PLAN.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def list_evaluation_plan_system_metrics(self, evaluation_plan_id: str) -> dict:
        """
        Retrieves system metrics associated with a specific evaluation plan.

        :param evaluation_plan_id: str - The ID of the evaluation plan.

        :return: dict - List of system metrics for the evaluation plan.
        """
        endpoint = LIST_EVALUATION_PLAN_SYSTEM_METRICS.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def add_evaluation_plan_system_metric(
            self,
            evaluation_plan_id: str,
            system_metric_id: str,
            system_metric_weight: float
    ) -> dict:
        """
        Adds a system metric to an existing evaluation plan.

        :param evaluation_plan_id: str - The unique identifier of the evaluation plan.
        :param system_metric_id: str - The unique identifier of the system metric to add.
        :param system_metric_weight: float - The weight of the system metric (0 to 1).

        :return: dict - API response containing the added system metric details.
        """
        data = {
            "systemMetricId": system_metric_id,
            "systemMetricWeight":system_metric_weight
        }
        endpoint = ADD_EVALUATION_PLAN_SYSTEM_METRIC.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data=data
        )
        result = json.loads(response.content)
        return result

    def get_evaluation_plan_system_metric(self, evaluation_plan_id: str, system_metric_id: str) -> dict:
        """
        Retrieves a specific system metric from an evaluation plan.

        :param evaluation_plan_id: str - The ID of the evaluation plan.
        :param system_metric_id: str - The ID of the system metric.

        :return: dict - The system metric metadata.
        """
        endpoint = GET_EVALUATION_PLAN_SYSTEM_METRIC.format(evaluationPlanId=evaluation_plan_id, systemMetricId=system_metric_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def update_evaluation_plan_system_metric(
            self,
            evaluation_plan_id: str,
            system_metric_id: str,
            system_metric_weight: float
    ) -> dict:
        """
        Updates the weight of a system metric in an evaluation plan.

        :param evaluation_plan_id: str - The unique identifier of the evaluation plan.
        :param system_metric_id: str - The unique identifier of the system metric to update.
        :param system_metric_weight: float - The new weight of the system metric (0 to 1).

        :return: dict - API response containing the updated system metric details.
        """
        data = {
            "systemMetricWeight": system_metric_weight
        }
        endpoint = UPDATE_EVALUATION_PLAN_SYSTEM_METRIC.format(evaluationPlanId=evaluation_plan_id, systemMetricId=system_metric_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        result = json.loads(response.content)
        return result

    def delete_evaluation_plan_system_metric(self, evaluation_plan_id: str, system_metric_id: str) -> dict:
        """
        Deletes a specific system metric from an evaluation plan.

        :param evaluation_plan_id: str - The ID of the evaluation plan.
        :param system_metric_id: str - The ID of the system metric.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_EVALUATION_PLAN_SYSTEM_METRIC.format(evaluationPlanId=evaluation_plan_id, systemMetricId=system_metric_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def list_system_metrics(self) -> dict:
        """
        Retrieves a list of all available system metrics.

        :return: dict - List of all system metrics.
        """
        response = self.api_service.get(
            endpoint=LIST_SYSTEM_METRICS
        )
        result = json.loads(response.content)
        return result

    def get_system_metric(self, system_metric_id: str) -> dict:
        """
        Retrieves a specific system metric by ID.

        :param system_metric_id: str - The ID of the system metric.

        :return: dict - The system metric metadata.
        """
        endpoint = GET_SYSTEM_METRIC.format(systemMetricId=system_metric_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = json.loads(response.content)
        return result

    def execute_evaluation_plan(self, evaluation_plan_id: str) -> dict:
        """
        Executes a specific evaluation plan.

        :param evaluation_plan_id: str - The ID of the evaluation plan.

        :return: dict - API response confirming the execution of the evaluation plan.
        """
        endpoint = EXECUTE_EVALUATION_PLAN.format(evaluationPlanId=evaluation_plan_id)
        response = self.api_service.post(
            endpoint=endpoint,
        )
        result = json.loads(response.content)
        return result

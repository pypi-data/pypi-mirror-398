from json import JSONDecodeError

from pygeai import logger
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.lab.clients import AILabClient
from pygeai.lab.strategies.endpoints import LIST_REASONING_STRATEGIES_V2, CREATE_REASONING_STRATEGY_V2, \
    UPDATE_REASONING_STRATEGY_V2, UPSERT_REASONING_STRATEGY_V2, GET_REASONING_STRATEGY_V2


class ReasoningStrategyClient(AILabClient):

    def list_reasoning_strategies(
            self,
            name: str = "",
            start: str = "0",
            count: str = "100",
            allow_external: bool = True,
            access_scope: str = "public"
    ):
        """
        Retrieves a list of reasoning strategies filtered by specified criteria.

        :param name: str, optional - Name to filter strategies (default: "").
        :param start: str, optional - Starting index for pagination (default: "0").
        :param count: str, optional - Number of strategies to retrieve (default: "100").
        :param allow_external: bool, optional - Include external strategies (default: True).
        :param access_scope: str, optional - Access scope, "public" or "private" (default: "public").
        :return: dict - List of reasoning strategies.
        :raises ValueError: If access_scope is not "public" or "private".
        :raises InvalidAPIResponseException: If the API response cannot be parsed.
        """
        valid_access_scopes = ["public", "private"]
        if access_scope not in valid_access_scopes:
            raise ValueError("Access scope must be either 'public' or 'private'.")

        endpoint = LIST_REASONING_STRATEGIES_V2
        headers = {"Authorization": self.api_service.token}
        params = {
            "name": name,
            "start": start,
            "count": count,
            "allowExternal": allow_external,
            "accessScope": access_scope,
        }

        logger.debug("Listing reasoning strategies")

        response = self.api_service.get(endpoint=endpoint, headers=headers, params=params)
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list reasoning strategies: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list reasoning strategies: {response.text}")

        return result

    def create_reasoning_strategy(
            self,
            name: str,
            system_prompt: str,
            access_scope: str = "public",
            strategy_type: str = "addendum",
            localized_descriptions: list = None,
            automatic_publish: bool = False
    ):
        """
        Creates a new reasoning strategy in the specified project.

        :param name: str - Name of the reasoning strategy.
        :param system_prompt: str - System prompt for the strategy.
        :param access_scope: str, optional - Access scope, "public" or "private" (default: "public").
        :param strategy_type: str, optional - Strategy type, e.g., "addendum" (default: "addendum").
        :param localized_descriptions: list, optional - List of localized description dictionaries.
        :param automatic_publish: bool, optional - Publish strategy after creation (default: False).
        :return: dict - Created strategy details.
        :raises InvalidAPIResponseException: If the API response cannot be parsed.
        """
        endpoint = CREATE_REASONING_STRATEGY_V2
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "strategyDefinition": {
                "name": name,
                "systemPrompt": system_prompt,
                "accessScope": access_scope,
                "type": strategy_type,
                "localizedDescriptions": localized_descriptions or []
            }
        }

        logger.debug(f"Creating reasoning strategy with data: {data}")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create reasoning strategy for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create reasoning strategy for project {self.project_id}: {response.text}")

        return result

    def update_reasoning_strategy(
            self,
            reasoning_strategy_id: str,
            name: str = None,
            system_prompt: str = None,
            access_scope: str = None,
            strategy_type: str = None,
            localized_descriptions: list = None,
            automatic_publish: bool = False,
            upsert: bool = False
    ):
        """
        Updates or upserts a reasoning strategy in the specified project.

        :param reasoning_strategy_id: str - Unique identifier of the strategy.
        :param name: str, optional - Updated strategy name.
        :param system_prompt: str, optional - Updated system prompt.
        :param access_scope: str, optional - Updated access scope, "public" or "private".
        :param strategy_type: str, optional - Updated strategy type, e.g., "addendum".
        :param localized_descriptions: list, optional - Updated localized descriptions.
        :param automatic_publish: bool, optional - Publish strategy after update (default: False).
        :param upsert: bool, optional - Create strategy if it doesn't exist (default: False).
        :return: dict - Updated strategy details.
        :raises ValueError: If access_scope is not "public" or "private", or strategy_type is not "addendum".
        :raises InvalidAPIResponseException: If the API response cannot be parsed.
        """
        if access_scope is not None:
            valid_access_scopes = ["public", "private"]
            if access_scope not in valid_access_scopes:
                raise ValueError("Access scope must be either 'public' or 'private'.")
        if strategy_type is not None:
            valid_types = ["addendum"]
            if strategy_type not in valid_types:
                raise ValueError("Type must be 'addendum'.")

        data = {
            "strategyDefinition": {}
        }
        if name is not None:
            data["strategyDefinition"]["name"] = name
        if system_prompt is not None:
            data["strategyDefinition"]["systemPrompt"] = system_prompt
        if access_scope is not None:
            data["strategyDefinition"]["accessScope"] = access_scope
        if strategy_type is not None:
            data["strategyDefinition"]["type"] = strategy_type
        if localized_descriptions is not None:
            data["strategyDefinition"]["localizedDescriptions"] = localized_descriptions

        logger.debug(f"Updating reasoning strategy with ID {reasoning_strategy_id} with data: {data}")

        endpoint = UPSERT_REASONING_STRATEGY_V2 if upsert else UPDATE_REASONING_STRATEGY_V2
        endpoint = endpoint.format(reasoningStrategyId=reasoning_strategy_id)

        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        response = self.api_service.put(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to update reasoning strategy {reasoning_strategy_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update reasoning strategy {reasoning_strategy_id} in project {self.project_id}: {response.text}")

        return result

    def get_reasoning_strategy(
            self,
            reasoning_strategy_id: str = None,
            reasoning_strategy_name: str = None
    ):
        """
        Retrieves a reasoning strategy by ID or name in the specified project.

        :param reasoning_strategy_id: str, optional - Unique identifier of the strategy.
        :param reasoning_strategy_name: str, optional - Name of the strategy.
        :return: dict - Strategy details.
        :raises ValueError: If neither reasoning_strategy_id nor reasoning_strategy_name is provided.
        :raises InvalidAPIResponseException: If the API response cannot be parsed.
        """
        if not (reasoning_strategy_id or reasoning_strategy_name):
            raise ValueError("Either reasoning_strategy_id or reasoning_strategy_name must be provided.")

        identifier = reasoning_strategy_id if reasoning_strategy_id else reasoning_strategy_name
        endpoint = GET_REASONING_STRATEGY_V2.format(reasoningStrategyId=identifier)

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if reasoning_strategy_id:
            logger.debug(f"Retrieving reasoning strategy detail with ID {reasoning_strategy_id}")
        else:
            logger.debug(f"Retrieving reasoning strategy detail with name {reasoning_strategy_name}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve reasoning strategy {reasoning_strategy_id or reasoning_strategy_name} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve reasoning strategy {reasoning_strategy_id or reasoning_strategy_name} for project {self.project_id}: {response.text}")

        return result
    
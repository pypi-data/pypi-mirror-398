from json import JSONDecodeError
from typing import Optional, List, Dict

from pygeai import logger
from pygeai.core.common.exceptions import MissingRequirementException, InvalidAPIResponseException
from pygeai.lab.agents.endpoints import CREATE_AGENT_V2, LIST_AGENTS_V2, GET_AGENT_V2, CREATE_SHARING_LINK_V2, \
    PUBLISH_AGENT_REVISION_V2, DELETE_AGENT_V2, UPDATE_AGENT_V2, UPSERT_AGENT_V2, EXPORT_AGENT_V2, IMPORT_AGENT_V2
from pygeai.lab.constants import VALID_ACCESS_SCOPES
from pygeai.lab.clients import AILabClient


class AgentClient(AILabClient):

    def list_agents(
            self,
            status: str = "",
            start: int = "",
            count: int = "",
            access_scope: str = "public",
            allow_drafts: bool = True,
            allow_external: bool = False
    ) -> dict:
        """
        Retrieves a list of agents associated with the specified project.

        :param status: str, optional - Filter agents by status (e.g., "active", "draft"). Defaults to "" (no filtering).
        :param start: int, optional - Starting index for pagination. Defaults to "" (no offset).
        :param count: int, optional - Maximum number of agents to retrieve. Defaults to "" (no limit).
        :param access_scope: str, optional - Filter agents by access scope ("public" or "private"). Defaults to "public".
        :param allow_drafts: bool, optional - Include draft agents in the results. Defaults to True.
        :param allow_external: bool, optional - Include external agents in the results. Defaults to False.
        :return: dict - JSON response containing the list of agents.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        """
        endpoint = LIST_AGENTS_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Listing agents for project with ID {self.project_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={
                "status": status,
                "start": start,
                "count": count,
                "accessScope": access_scope,
                "allowDrafts": allow_drafts,
                "allowExternal": allow_external
            }
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list agents for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list agents for project {self.project_id}: {response.text}")

        return result

    def create_agent(
            self,
            name: str,
            access_scope: str,
            public_name: str,
            job_description: str,
            avatar_image: str,
            description: str,
            agent_data_prompt: dict,
            agent_data_llm_config: dict,
            agent_data_strategy_name: str,
            agent_data_models: list,
            agent_data_resource_pools: Optional[List[Dict]] = None,
            automatic_publish: bool = False
    ) -> dict:
        """
        Creates a new agent in the specified project.

        :param name: str - Name of the agent (must be unique within the project, non-empty, and exclude ':' or '/').
        :param access_scope: str - Access scope of the agent ("public" or "private").
        :param public_name: str - Public name for the agent, required if access_scope is "public" (must follow domain/library convention, e.g., 'com.example.my-agent').
        :param job_description: str - Description of the agent's role (optional).
        :param avatar_image: str - URL for the agent's avatar image (optional).
        :param description: str - Detailed description of the agent’s purpose (optional).
        :param agent_data_prompt: dict - Prompt configuration, including 'context', 'instructions', and optional 'examples' (e.g., {'context': str, 'instructions': str, 'examples': [{'inputData': str, 'output': str}]}).
        :param agent_data_llm_config: dict - LLM configuration (e.g., {'maxTokens': int, 'timeout': int, 'sampling': {'temperature': float}}).
        :param agent_data_strategy_name: str - Strategy name to be used.
        :param agent_data_models: list - List of models the agent can use (e.g., [{'name': 'gpt-4o', 'llmConfig': dict}]).
        :param agent_data_resource_pools: Optional[List[Dict]] - Resource pools for tools and helper agents (e.g., [{'name': str, 'tools': [{'name': str, 'revision': int}], 'agents': [{'name': str, 'revision': int}]}]).
        :param automatic_publish: bool - Automatically publish the agent after creation (default: False).
        :return: dict - JSON response containing the created agent details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises ValueError: If access_scope is invalid.
        """
        if access_scope is not None and access_scope not in VALID_ACCESS_SCOPES:
            raise ValueError(f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

        data = {
            "agentDefinition": {
                "name": name,
                "accessScope": access_scope,
                "publicName": public_name,
                "jobDescription": job_description,
                "avatarImage": avatar_image,
                "description": description,
            }
        }
        if (
                agent_data_prompt or agent_data_strategy_name or agent_data_prompt or agent_data_resource_pools or
                agent_data_llm_config or agent_data_models
        ):
            data["agentDefinition"]["agentData"] = {}
        if agent_data_resource_pools is not None:
            data["agentDefinition"]["agentData"]["resourcePools"] = agent_data_resource_pools
        if agent_data_prompt is not None:
            data["agentDefinition"]["agentData"]["prompt"] = agent_data_prompt
        if agent_data_llm_config is not None:
            data["agentDefinition"]["agentData"]["llmConfig"] = agent_data_llm_config
        if agent_data_strategy_name is not None:
            data["agentDefinition"]["agentData"]["strategyName"] = agent_data_strategy_name
        if agent_data_models is not None:
            data["agentDefinition"]["agentData"]["models"] = agent_data_models
        logger.debug(f"Creating agent with data: {data}")

        endpoint = CREATE_AGENT_V2
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data=data
        )

        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create agent for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create agent for project {self.project_id}: {response.text}")

        return result

    def get_agent(
            self,
            agent_id: str,
            revision: str = 0,
            version: int = 0,
            allow_drafts: bool = True
    ) -> dict:
        """
        Retrieves details of a specific agent from the specified project.

        :param agent_id: str - Unique identifier of the agent to retrieve.
        :param revision: str, optional - Specific revision of the agent to retrieve (default: 0, latest revision).
        :param version: int, optional - Specific version of the agent to retrieve (default: 0, latest version).
        :param allow_drafts: bool, optional - Include draft agents in the results (default: True).
        :return: dict - JSON response containing the agent details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises MissingRequirementException: If project_id or agent_id is not provided.
        """
        if not agent_id:
            raise MissingRequirementException("agent_id must be specified in order to retrieve the agent")

        endpoint = GET_AGENT_V2.format(agentId=agent_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Retrieving agent detail with ID {agent_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={
                "revision": revision,
                "version": version,
                "allowDrafts": allow_drafts,
            }
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve agent {agent_id} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve agent {agent_id} for project {self.project_id}: {response.text}")

        return result

    def create_sharing_link(
            self,
            agent_id: str,
    ) -> dict:
        """
        Creates a sharing link for a specific agent in the specified project.

        :param agent_id: str - Unique identifier of the agent for which to create a sharing link.
        :return: dict - JSON response containing the sharing link details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises MissingRequirementException: If project_id or agent_id is not provided.
        """
        if not agent_id:
            raise MissingRequirementException("agent_id must be specified in order to create sharing link")

        endpoint = CREATE_SHARING_LINK_V2.format(agentId=agent_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Creating sharing link for agent with ID {agent_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={}
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create sharing link for agent {agent_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create sharing link for agent {agent_id} in project {self.project_id}: {response.text}")

        return result

    def publish_agent_revision(
            self,
            agent_id: str,
            revision: str
    ) -> dict:
        """
        Publishes a specific revision of an agent in the specified project.

        :param agent_id: str - Unique identifier of the agent to publish.
        :param revision: str - Revision of the agent to publish.
        :return: dict - JSON response containing the result of the publish operation.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        """
        endpoint = PUBLISH_AGENT_REVISION_V2.format(agentId=agent_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Publishing revision {revision} for agent with ID {agent_id}")

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data={
                "revision": revision,
            }
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to publish revision {revision} for agent {agent_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to publish revision {revision} for agent {agent_id} in project {self.project_id}: {response.text}")

        return result

    def delete_agent(
            self,
            agent_id: str,
    ) -> dict:
        """
        Deletes a specific agent from the specified project.

        :param agent_id: str - Unique identifier of the agent to delete.
        :return: dict - JSON response confirming the deletion.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        """
        endpoint = DELETE_AGENT_V2.format(agentId=agent_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Deleting agent with ID {agent_id}")

        response = self.api_service.delete(
            endpoint=endpoint,
            headers=headers,
            data={}
        )
        if response.status_code != 204:
            logger.error(f"Unable to delete agent {agent_id} from project {self.project_id}: JSON parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete agent {agent_id} from project {self.project_id}: {response.text}")
        else:
            return {}

    def update_agent(
            self,
            agent_id: str,
            name: str,
            access_scope: str,
            public_name: str,
            job_description: str,
            avatar_image: str,
            description: str,
            agent_data_prompt: dict,
            agent_data_llm_config: dict,
            agent_data_strategy_name: dict,
            agent_data_models: list,
            agent_data_resource_pools: Optional[List[Dict]] = None,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> dict:
        """
        Updates an existing agent in the specified project or upserts it if specified.

        :param agent_id: str - Unique identifier of the agent to update (required for updates).
        :param name: str - Updated name of the agent (must be unique, non-empty, exclude ':' or '/'; optional).
        :param access_scope: str - Updated access scope ("public" or "private").
        :param public_name: str - Updated public name, required if access_scope is "public" (must follow domain/library convention).
        :param job_description: str - Updated role description (optional).
        :param avatar_image: str - Updated avatar image URL (optional).
        :param description: str - Updated purpose description (optional).
        :param agent_data_prompt: dict - Updated prompt configuration (e.g., {'context': str, 'instructions': str, 'examples': [{'inputData': str, 'output': str}]}).
        :param agent_data_llm_config: dict - Updated LLM configuration (e.g., {'maxTokens': int, 'timeout': int, 'sampling': {'temperature': float}}).
        :param agent_data_strategy_name: str - Updated StrategyName configuration.
        :param agent_data_models: list - Updated model list (e.g., [{'name': 'gpt-4o', 'llmConfig': dict}]).
        :param agent_data_resource_pools: Optional[List[Dict]] - Updated resource pools (e.g., [{'name': str, 'tools': [{'name': str, 'revision': int}], 'agents': [{'name': str, 'revision': int}]}]).
        :param automatic_publish: bool - Automatically publish the agent after updating (default: False).
        :param upsert: bool - Create the agent if it does not exist (default: False).
        :return: dict - JSON response containing the updated or created agent details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises ValueError: If access_scope is invalid.
        """
        if access_scope is not None and access_scope not in VALID_ACCESS_SCOPES:
            raise ValueError(f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

        data = {
            "agentDefinition": {
                "name": name,
                "accessScope": access_scope,
                "publicName": public_name,
                "jobDescription": job_description,
                "avatarImage": avatar_image,
                "description": description,
            }
        }
        if (
                agent_data_prompt or agent_data_strategy_name or agent_data_prompt or agent_data_resource_pools or
                agent_data_llm_config or agent_data_models
        ):
            data["agentDefinition"]["agentData"] = {}
        if agent_data_resource_pools is not None:
            data["agentDefinition"]["agentData"]["resourcePools"] = agent_data_resource_pools
        if agent_data_prompt is not None:
            data["agentDefinition"]["agentData"]["prompt"] = agent_data_prompt
        if agent_data_llm_config is not None:
            data["agentDefinition"]["agentData"]["llmConfig"] = agent_data_llm_config
        if agent_data_strategy_name is not None:
            data["agentDefinition"]["agentData"]["strategyName"] = agent_data_strategy_name
        if agent_data_models is not None:
            data["agentDefinition"]["agentData"]["models"] = agent_data_models

        logger.debug(f"Updating agent with ID {agent_id} with data: {data}")

        endpoint = UPSERT_AGENT_V2 if upsert else UPDATE_AGENT_V2
        endpoint = endpoint.format(agentId=agent_id) if agent_id else endpoint.format(agentId=name)

        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        response = self.api_service.put(
            endpoint=endpoint,
            headers=headers,
            data=data
        )

        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to update agent {agent_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update agent {agent_id} in project {self.project_id}: {response.text}")

        return result

    def export_agent(
            self,
            agent_id: str,
    ) -> dict:
        """
        Retrieves details of a specific agent from the specified project.

        :param agent_id: str - Unique identifier of the agent to retrieve.
        :return: dict - JSON response containing the agent details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises MissingRequirementException: If project_id or agent_id is not provided.
        """
        if not agent_id:
            raise MissingRequirementException("agent_id must be specified in order to export the agent")

        endpoint = EXPORT_AGENT_V2.format(agentId=agent_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Exporting agent with ID {agent_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to export agent {agent_id} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to export agent {agent_id} for project {self.project_id}: {response.text}")

        return result

    def import_agent(
            self,
            data: dict,
    ) -> dict:
        """
        Retrieves details of a specific agent from the specified project.

        :param data: dict - Agent specification to import
        :return: dict - JSON response containing the agent details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises MissingRequirementException: If project_id or agent_id is not provided.
        """
        if not data:
            raise MissingRequirementException("data for spec must be specified in order to import the agent")

        endpoint = IMPORT_AGENT_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to import agent for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to import agent for project {self.project_id}: {response.text}")

        return result

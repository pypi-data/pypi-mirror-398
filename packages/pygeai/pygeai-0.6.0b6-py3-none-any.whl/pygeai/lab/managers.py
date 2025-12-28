from typing import Union, Optional, List

from pygeai import logger
from pygeai.admin.clients import AdminClient
from pygeai.core.base.mappers import ResponseMapper
from pygeai.core.base.responses import EmptyResponse
from pygeai.core.common.exceptions import APIError, MissingRequirementException
from pygeai.core.handlers import ErrorHandler
from pygeai.lab.agents.clients import AgentClient
from pygeai.lab.agents.mappers import AgentMapper
from pygeai.lab.models import FilterSettings, Agent, AgentList, SharingLink, Tool, ToolList, ToolParameter, \
    ReasoningStrategyList, ReasoningStrategy, AgenticProcess, AgenticProcessList, ProcessInstanceList, Task, TaskList, \
    ProcessInstance, Variable, VariableList, KnowledgeBase, KnowledgeBaseList, JobList
from pygeai.lab.processes.clients import AgenticProcessClient
from pygeai.lab.processes.mappers import AgenticProcessMapper, ProcessInstanceMapper, TaskMapper, KnowledgeBaseMapper, \
    JobMapper
from pygeai.lab.strategies.clients import ReasoningStrategyClient
from pygeai.lab.strategies.mappers import ReasoningStrategyMapper
from pygeai.lab.tools.clients import ToolClient
from pygeai.lab.tools.mappers import ToolMapper


class AILabManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default", project_id: str = None):
        self.__agent_client = AgentClient(api_key=api_key, base_url=base_url, alias=alias, project_id=project_id)
        self.__tool_client = ToolClient(api_key=api_key, base_url=base_url, alias=alias, project_id=project_id)
        self.__reasoning_strategy_client = ReasoningStrategyClient(api_key=api_key, base_url=base_url, alias=alias, project_id=project_id)
        self.__process_client = AgenticProcessClient(api_key=api_key, base_url=base_url, alias=alias, project_id=project_id)

    def get_agent_list(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> AgentList:
        """
        Retrieves a list of agents for a given project based on filter settings.

        This method queries the agent client to fetch a list of agents associated with the specified
        project ID, applying the provided filter settings.

        :param filter_settings: The filter settings to apply to the agent list query.
            Includes fields such as status, start, count, access_scope, allow_drafts, and allow_external.
        :return: An `AgentList` containing the retrieved agents.
        :raises APIError: If the API returns errors.
        """
        if not filter_settings:
            filter_settings = FilterSettings()

        response_data = self.__agent_client.list_agents(
            status=filter_settings.status,
            start=filter_settings.start,
            count=filter_settings.count,
            access_scope=filter_settings.access_scope,
            allow_drafts=filter_settings.allow_drafts,
            allow_external=filter_settings.allow_external
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while obtaining agent list: {error}")
            raise APIError(f"Error received while obtaining agent list: {error}")

        result = AgentMapper.map_to_agent_list(response_data)
        return result

    def create_agent(
            self,
            agent: Agent,
            automatic_publish: bool = False
    ) -> Agent:
        """
        Creates a new agent in the specified project using the provided agent configuration.

        This method sends a request to the agent client to create an agent based on the attributes
        of the provided `Agent` object.

        :param agent: The agent configuration object containing all necessary details,
            including name, access scope, public name, job description, avatar image, description,
            and agent data (prompt, LLM config, and models).
        :param automatic_publish: Whether to automatically publish the agent after creation.
            Defaults to False.
        :return: An `Agent` object representing the created agent.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__agent_client.create_agent(
            name=agent.name,
            access_scope=agent.access_scope,
            public_name=agent.public_name,
            job_description=agent.job_description,
            avatar_image=agent.avatar_image,
            description=agent.description,
            agent_data_prompt=agent.agent_data.prompt.to_dict() if agent.agent_data is not None else None,
            agent_data_strategy_name=agent.agent_data.strategy_name if agent.agent_data is not None else None,
            agent_data_llm_config=agent.agent_data.llm_config.to_dict() if agent.agent_data is not None else None,
            agent_data_models=agent.agent_data.models.to_dict() if agent.agent_data is not None else None,
            agent_data_resource_pools=agent.agent_data.resource_pools.to_dict() if agent.agent_data and agent.agent_data.resource_pools else None,
            automatic_publish=automatic_publish
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating agent: {error}")
            raise APIError(f"Error received while creating agent: {error}")

        result = AgentMapper.map_to_agent(response_data)
        return result

    def update_agent(
            self,
            agent: Agent,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Agent:
        """
        Updates an existing agent in the specified project using the provided agent configuration.

        This method sends a request to the agent client to update an agent identified by `agent.id`
        based on the attributes of the provided `Agent` object. It can optionally publish the agent
        automatically or perform an upsert if the agent doesn’t exist.

        :param agent: The agent configuration object containing updated details,
            including id, name, access scope, public name, job description, avatar image, description,
            and agent data (prompt, LLM config, and models).
        :param automatic_publish: Whether to automatically publish the agent after updating.
            Defaults to False.
        :param upsert: Whether to insert the agent if it does not exist (upsert) instead of
            just updating. Defaults to False.
        :return: An `Agent` object representing the updated agent.
        :raises MissingRequirementException: If `agent.id` is not provided.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__agent_client.update_agent(
            agent_id=agent.id,
            name=agent.name,
            access_scope=agent.access_scope,
            public_name=agent.public_name,
            job_description=agent.job_description,
            avatar_image=agent.avatar_image,
            description=agent.description,
            agent_data_prompt=agent.agent_data.prompt.to_dict() if agent.agent_data is not None else None,
            agent_data_llm_config=agent.agent_data.llm_config.to_dict() if agent.agent_data is not None else None,
            agent_data_strategy_name=agent.agent_data.strategy_name if agent.agent_data is not None else None,
            agent_data_models=agent.agent_data.models.to_dict() if agent.agent_data is not None else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating agent: {error}")
            raise APIError(f"Error received while updating agent: {error}")

        result = AgentMapper.map_to_agent(response_data)
        return result

    def get_agent(
            self,
            agent_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Agent:
        """
        Retrieves details of a specific agent from the specified project.

        This method sends a request to the agent client to retrieve an agent identified by `agent_id`
        from the specified project. Optional filter settings can be provided to specify the revision,
        version, and whether to allow drafts.

        :param agent_id: Unique identifier of the agent to retrieve.
        :param filter_settings: Settings to filter the agent retrieval,
            including revision (defaults to "0"), version (defaults to "0"), and allow_drafts (defaults to True).
        :return: An `Agent` object representing the retrieved agent.
        :raises APIError: If the API returns errors.
        """
        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__agent_client.get_agent(
            agent_id=agent_id,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving agent: {error}")
            raise APIError(f"Error received while retrieving agent: {error}")

        result = AgentMapper.map_to_agent(response_data)
        return result

    def create_sharing_link(
            self,
            agent_id: str
    ) -> SharingLink:
        """
        Creates a sharing link for a specific agent in the specified project.

        This method sends a request to the agent client to create a sharing link for the agent
        identified by `agent_id` in the specified project.

        :param agent_id: Unique identifier of the agent for which to create a sharing link.
        :return: A `SharingLink` object representing the sharing link details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__agent_client.create_sharing_link(
            agent_id=agent_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating sharing link: {error}")
            raise APIError(f"Error received while creating sharing link: {error}")

        result = AgentMapper.map_to_sharing_link(response_data)
        return result

    def publish_agent_revision(
            self,
            agent_id: str,
            revision: str
    ) -> Agent:
        """
        Publishes a specific revision of an agent in the specified project.

        This method sends a request to the agent client to publish the specified revision of the agent
        identified by `agent_id` in the specified project.

        :param agent_id: Unique identifier of the agent to publish.
        :param revision: Revision of the agent to publish.
        :return: An `Agent` object representing the published agent.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__agent_client.publish_agent_revision(
            agent_id=agent_id,
            revision=revision
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while publishing agent revision: {error}")
            raise APIError(f"Error received while publishing agent revision: {error}")

        result = AgentMapper.map_to_agent(response_data)
        return result

    def delete_agent(
            self,
            agent_id: str
    ) -> EmptyResponse:
        """
        Deletes a specific agent from the specified project.

        This method sends a request to the agent client to delete the agent identified by `agent_id`
        from the specified project.

        :param agent_id: Unique identifier of the agent to delete.
        :return: `EmptyResponse` if the agent was deleted successfully.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__agent_client.delete_agent(
            agent_id=agent_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting agent: {error}")
            raise APIError(f"Error received while deleting agent: {error}")

        response_data = response_data if response_data else "Agent deleted successfully"
        result = ResponseMapper.map_to_empty_response(response_data)
        return result

    def create_tool(
            self,
            tool: Tool,
            automatic_publish: bool = False
    ) -> Tool:
        """
        Creates a new tool in the specified project using the provided tool configuration.

        This method sends a request to the tool client to create a tool based on the attributes
        of the provided `Tool` object, including name, description, scope, access_scope, public_name,
        icon, open_api, open_api_json, report_events, and parameters.

        :param tool: The tool configuration object containing name, description, scope,
            access_scope, public_name, icon, open_api, open_api_json, report_events, and parameters.
            Optional fields (e.g., id, access_scope) are included if set in the `Tool` object.
        :param automatic_publish: Whether to automatically publish the tool after creation.
            Defaults to False.
        :return: A `Tool` object representing the created tool.
        :raises APIError: If the API returns errors.
        """
        parameters = [param.to_dict() for param in tool.parameters] if tool.parameters else []

        response_data = self.__tool_client.create_tool(
            name=tool.name,
            description=tool.description,
            scope=tool.scope,
            access_scope=tool.access_scope,
            public_name=tool.public_name,
            icon=tool.icon,
            open_api=tool.open_api,
            open_api_json=tool.open_api_json,
            report_events=tool.report_events,
            parameters=parameters,
            automatic_publish=automatic_publish
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating tool: {error}")
            raise APIError(f"Error received while creating tool: {error}")

        result = ToolMapper.map_to_tool(response_data)
        return result

    def update_tool(
            self,
            tool: Tool,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Tool:
        """
        Updates an existing tool in the specified project or upserts it if specified.

        This method sends a request to the tool client to update a tool identified by `tool.id`
        based on the attributes of the provided `Tool` object, including name, description, scope,
        access_scope, public_name, icon, open_api, open_api_json, report_events, and parameters.
        It can optionally publish the tool automatically or perform an upsert if the tool doesn’t exist.

        :param tool: The tool configuration object containing updated details, including
            id, name, description, scope, access_scope, public_name, icon, open_api, open_api_json,
            report_events, and parameters.
        :param automatic_publish: Whether to automatically publish the tool after updating.
            Defaults to False.
        :param upsert: Whether to insert the tool if it does not exist (upsert) instead of
            just updating. Defaults to False.
        :return: A `Tool` object representing the updated tool.
        :raises APIError: If the API returns errors.
        """
        parameters = [param.to_dict() for param in tool.parameters] if tool.parameters else []

        response_data = self.__tool_client.update_tool(
            tool_id=tool.id,
            name=tool.name,
            description=tool.description,
            scope=tool.scope,
            access_scope=tool.access_scope,
            public_name=tool.public_name,
            icon=tool.icon,
            open_api=tool.open_api,
            open_api_json=tool.open_api_json,
            report_events=tool.report_events,
            parameters=parameters,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating tool: {error}")
            raise APIError(f"Error received while updating tool: {error}")

        result = ToolMapper.map_to_tool(response_data)
        return result

    def get_tool(
            self,
            tool_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Tool:
        """
        Retrieves details of a specific tool from the specified project.

        This method sends a request to the tool client to retrieve a tool identified by `tool_id`
        from the specified project. Optional filter settings can be provided to specify the revision,
        version, and whether to allow drafts.

        :param tool_id: Unique identifier of the tool to retrieve.
        :param filter_settings: Settings to filter the tool retrieval,
            including revision (defaults to "0"), version (defaults to "0"), and allow_drafts (defaults to True).
        :return: A `Tool` object representing the retrieved tool.
        :raises APIError: If the API returns errors.
        """
        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__tool_client.get_tool(
            tool_id=tool_id,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving tool: {error}")
            raise APIError(f"Error received while retrieving tool: {error}")

        result = ToolMapper.map_to_tool(response_data)
        return result

    def delete_tool(
            self,
            tool_id: Optional[str] = None,
            tool_name: Optional[str] = None
    ) -> EmptyResponse:
        """
        Deletes a specific tool from the specified project.

        This method sends a request to the tool client to delete the tool identified by either
        `tool_id` or `tool_name`.

        :param tool_id: Unique identifier of the tool to delete.
        :param tool_name: Name of the tool to delete.
        :return: `EmptyResponse` if the tool was deleted successfully.
        :raises MissingRequirementException: If neither tool_id nor tool_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (tool_id or tool_name):
            raise MissingRequirementException("Either tool_id or tool_name must be provided.")

        response_data = self.__tool_client.delete_tool(
            tool_id=tool_id,
            tool_name=tool_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting tool: {error}")
            raise APIError(f"Error received while deleting tool: {error}")

        response_data = response_data if response_data else "Tool deleted successfully"
        result = ResponseMapper.map_to_empty_response(response_data)
        return result

    def list_tools(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> ToolList:
        """
        Retrieves a list of tools associated with the specified project.

        This method queries the tool client to fetch a list of tools for the given project ID,
        applying the specified filter settings.

        :param filter_settings: Settings to filter the tool list query,
            including id (defaults to ""), count (defaults to "100"), access_scope (defaults to "public"),
            allow_drafts (defaults to True), scope (defaults to "api"), and allow_external (defaults to True).
        :return: A `ToolList` object containing the retrieved tools.
        :raises APIError: If the API returns errors.
        """
        if filter_settings is None:
            filter_settings = FilterSettings(
                id="",
                count="100",
                access_scope="public",
                allow_drafts=True,
                scope="api",
                allow_external=True
            )

        response_data = self.__tool_client.list_tools(
            id=filter_settings.id,
            count=filter_settings.count,
            access_scope=filter_settings.access_scope,
            allow_drafts=filter_settings.allow_drafts,
            scope=filter_settings.scope,
            allow_external=filter_settings.allow_external
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing tools: {error}")
            raise APIError(f"Error received while listing tools: {error}")

        result = ToolMapper.map_to_tool_list(response_data)
        return result

    def publish_tool_revision(
            self,
            tool_id: str,
            revision: str
    ) -> Tool:
        """
        Publishes a specific revision of a tool in the specified project.

        This method sends a request to the tool client to publish the specified revision of the tool
        identified by `tool_id`.

        :param tool_id: Unique identifier of the tool to publish.
        :param revision: Revision of the tool to publish.
        :return: A `Tool` object representing the published tool.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__tool_client.publish_tool_revision(
            tool_id=tool_id,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while publishing tool revision: {error}")
            raise APIError(f"Error received while publishing tool revision: {error}")

        result = ToolMapper.map_to_tool(response_data)
        return result

    def get_parameter(
            self,
            tool_id: Optional[str] = None,
            tool_public_name: Optional[str] = None,
            filter_settings: Optional[FilterSettings] = None
    ) -> List[ToolParameter]:
        """
        Retrieves details of parameters for a specific tool in the specified project.

        This method sends a request to the tool client to retrieve parameters for a tool identified
        by either `tool_id` or `tool_public_name`. Optional filter settings can specify revision,
        version, and whether to allow drafts.

        :param tool_id: Unique identifier of the tool whose parameters are to be retrieved.
        :param tool_public_name: Public name of the tool whose parameters are to be retrieved.
        :param filter_settings: Settings to filter the parameter retrieval,
            including revision (defaults to "0"), version (defaults to "0"), and allow_drafts (defaults to True).
        :return: A list of `ToolParameter` objects.
        :raises MissingRequirementException: If neither tool_id nor tool_public_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (tool_id or tool_public_name):
            raise MissingRequirementException("Either tool_id or tool_public_name must be provided.")

        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__tool_client.get_parameter(
            tool_id=tool_id,
            tool_public_name=tool_public_name,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving tool parameters: {error}")
            raise APIError(f"Error received while retrieving tool parameters: {error}")

        result = ToolMapper.map_to_parameter_list(response_data)
        return result

    def set_parameter(
            self,
            tool_id: Optional[str] = None,
            tool_public_name: Optional[str] = None,
            parameters: List[ToolParameter] = None
    ) -> EmptyResponse:
        """
        Sets or updates parameters for a specific tool in the specified project.

        This method sends a request to the tool client to set parameters for a tool identified by
        either `tool_id` or `tool_public_name`.

        :param tool_id: Unique identifier of the tool whose parameters are to be set.
        :param tool_public_name: Public name of the tool whose parameters are to be set.
        :param parameters: List of parameter objects defining the tool's parameters.
        :return: A `Tool` object representing the updated tool.
        :raises MissingRequirementException: If neither tool_id nor tool_public_name is provided, or if parameters is None or empty.
        :raises APIError: If the API returns errors.
        """
        if not (tool_id or tool_public_name):
            raise MissingRequirementException("Either tool_id or tool_public_name must be provided.")
        if not parameters:
            raise MissingRequirementException("Parameters list must be provided and non-empty.")

        params_dict = [param.to_dict() for param in parameters]

        response_data = self.__tool_client.set_parameter(
            tool_id=tool_id,
            tool_public_name=tool_public_name,
            parameters=params_dict
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while setting tool parameters: {error}")
            raise APIError(f"Error received while setting tool parameters: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "Parameter set successfully")
        return result

    def list_reasoning_strategies(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> ReasoningStrategyList:
        """
        Retrieves a list of reasoning strategies.

        This method queries the reasoning strategy client to fetch a list of reasoning strategies,
        applying the specified filter settings.

        :param filter_settings: Settings to filter the reasoning strategy list query,
            including name (defaults to ""), start (defaults to "0"), count (defaults to "100"),
            allow_external (defaults to True), and access_scope (defaults to "public").
        :return: A `ReasoningStrategyList` object containing the retrieved reasoning strategies.
        :raises APIError: If the API returns errors.
        """
        if filter_settings is None:
            filter_settings = FilterSettings(
                start="0",
                count="100",
                allow_external=True,
                access_scope="public"
            )

        response_data = self.__reasoning_strategy_client.list_reasoning_strategies(
            name=filter_settings.name or "",
            start=filter_settings.start,
            count=filter_settings.count,
            allow_external=filter_settings.allow_external,
            access_scope=filter_settings.access_scope
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing reasoning strategies: {error}")
            raise APIError(f"Error received while listing reasoning strategies: {error}")

        result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(response_data)
        return result

    def create_reasoning_strategy(
            self,
            strategy: ReasoningStrategy,
            automatic_publish: bool = False
    ) -> ReasoningStrategy:
        """
        Creates a new reasoning strategy in the specified project.

        This method sends a request to the reasoning strategy client to create a reasoning strategy
        based on the attributes of the provided `ReasoningStrategy` object.

        :param strategy: The reasoning strategy configuration object containing name, system_prompt,
            access_scope, type, and localized_descriptions.
        :param automatic_publish: Whether to automatically publish the reasoning strategy after creation.
            Defaults to False.
        :return: A `ReasoningStrategy` object representing the created reasoning strategy.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__reasoning_strategy_client.create_reasoning_strategy(
            name=strategy.name,
            system_prompt=strategy.system_prompt,
            access_scope=strategy.access_scope,
            strategy_type=strategy.type,
            localized_descriptions=[desc.to_dict() for desc in strategy.localized_descriptions],
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating reasoning strategy: {error}")
            raise APIError(f"Error received while creating reasoning strategy: {error}")

        result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)
        return result

    def update_reasoning_strategy(
            self,
            strategy: ReasoningStrategy,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> ReasoningStrategy:
        """
        Updates an existing reasoning strategy in the specified project or upserts it if specified.

        This method sends a request to the reasoning strategy client to update a reasoning strategy
        identified by `strategy.id` based on the attributes of the provided `ReasoningStrategy` object.

        :param strategy: The reasoning strategy configuration object containing updated details,
            including id, name, system_prompt, access_scope, type, and localized_descriptions.
        :param automatic_publish: Whether to automatically publish the reasoning strategy after updating.
            Defaults to False.
        :param upsert: Whether to insert the reasoning strategy if it does not exist.
            Defaults to False.
        :return: A `ReasoningStrategy` object representing the updated reasoning strategy.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__reasoning_strategy_client.update_reasoning_strategy(
            reasoning_strategy_id=strategy.id,
            name=strategy.name,
            system_prompt=strategy.system_prompt,
            access_scope=strategy.access_scope,
            strategy_type=strategy.type,
            localized_descriptions=[desc.to_dict() for desc in strategy.localized_descriptions],
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating reasoning strategy: {error}")
            raise APIError(f"Error received while updating reasoning strategy: {error}")

        result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)
        return result

    def get_reasoning_strategy(
            self,
            reasoning_strategy_id: Optional[str] = None,
            reasoning_strategy_name: Optional[str] = None
    ) -> ReasoningStrategy:
        """
        Retrieves details of a specific reasoning strategy from the specified project.

        This method sends a request to the reasoning strategy client to retrieve a reasoning strategy
        identified by either `reasoning_strategy_id` or `reasoning_strategy_name`.

        :param reasoning_strategy_id: Unique identifier of the reasoning strategy to retrieve.
        :param reasoning_strategy_name: Name of the reasoning strategy to retrieve.
        :return: A `ReasoningStrategy` object representing the retrieved reasoning strategy.
        :raises MissingRequirementException: If neither reasoning_strategy_id nor reasoning_strategy_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (reasoning_strategy_id or reasoning_strategy_name):
            raise MissingRequirementException("Either reasoning_strategy_id or reasoning_strategy_name must be provided.")

        response_data = self.__reasoning_strategy_client.get_reasoning_strategy(
            reasoning_strategy_id=reasoning_strategy_id,
            reasoning_strategy_name=reasoning_strategy_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving reasoning strategy: {error}")
            raise APIError(f"Error received while retrieving reasoning strategy: {error}")

        result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)
        return result

    def create_process(
            self,
            process: AgenticProcess,
            automatic_publish: bool = False
    ) -> AgenticProcess:
        """
        Creates a new process in the specified project.

        This method sends a request to the process client to create a process based on the attributes
        of the provided `AgenticProcess` object.

        :param process: The process configuration to create, including key, name, description, kb,
            agentic_activities, artifact_signals, user_signals, start_event, end_event, sequence_flows,
            and variables.
        :param automatic_publish: Whether to publish the process after creation. Defaults to False.
        :return: An `AgenticProcess` object representing the created process.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__process_client.create_process(
            key=process.key,
            name=process.name,
            description=process.description,
            kb=process.kb.to_dict() if process.kb else None,
            agentic_activities=[activity.to_dict() for activity in process.agentic_activities] if process.agentic_activities else None,
            artifact_signals=[signal.to_dict() for signal in process.artifact_signals] if process.artifact_signals else None,
            user_signals=[signal.to_dict() for signal in process.user_signals] if process.user_signals else None,
            start_event=process.start_event.to_dict() if process.start_event else None,
            end_event=process.end_event.to_dict() if process.end_event else None,
            sequence_flows=[flow.to_dict() for flow in process.sequence_flows] if process.sequence_flows else None,
            variables=[variable.to_dict() for variable in process.variables] if process.variables else None,
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating process: {error}")
            raise APIError(f"Error received while creating process: {error}")

        result = AgenticProcessMapper.map_to_agentic_process(response_data)
        return result

    def update_process(
            self,
            process: AgenticProcess,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> AgenticProcess:
        """
        Updates an existing process in the specified project or upserts it if specified.

        This method sends a request to the process client to update a process identified by `process.id`
        based on the attributes of the provided `AgenticProcess` object.

        :param process: The process configuration to update, including id, key, name, description, kb,
            agentic_activities, artifact_signals, user_signals, start_event, end_event, sequence_flows,
            and variables.
        :param automatic_publish: Whether to publish the process after updating. Defaults to False.
        :param upsert: Whether to insert the process if it does not exist. Defaults to False.
        :return: An `AgenticProcess` object representing the updated process.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__process_client.update_process(
            process_id=process.id,
            name=process.name,
            key=process.key,
            description=process.description,
            kb=process.kb.to_dict() if process.kb else None,
            agentic_activities=[activity.to_dict() for activity in process.agentic_activities] if process.agentic_activities else None,
            artifact_signals=[signal.to_dict() for signal in process.artifact_signals] if process.artifact_signals else None,
            user_signals=[signal.to_dict() for signal in process.user_signals] if process.user_signals else None,
            start_event=process.start_event.to_dict() if process.start_event else None,
            end_event=process.end_event.to_dict() if process.end_event else None,
            sequence_flows=[flow.to_dict() for flow in process.sequence_flows] if process.sequence_flows else None,
            variables=[variable.to_dict() for variable in process.variables] if process.variables else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating process: {error}")
            raise APIError(f"Error received while updating process: {error}")

        result = AgenticProcessMapper.map_to_agentic_process(response_data)
        return result

    def get_process(
            self,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None,
            filter_settings: Optional[FilterSettings] = None
    ) -> AgenticProcess:
        """
        Retrieves details of a specific process in the specified project.

        This method sends a request to the process client to retrieve a process identified by either
        `process_id` or `process_name`. Optional filter settings can specify revision, version, and
        whether to allow drafts.

        :param process_id: Unique identifier of the process to retrieve.
        :param process_name: Name of the process to retrieve.
        :param filter_settings: Settings to filter the process retrieval (revision, version, allow_drafts).
        :return: An `AgenticProcess` object representing the retrieved process.
        :raises MissingRequirementException: If neither process_id nor process_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (process_id or process_name):
            raise MissingRequirementException("Either process_id or process_name must be provided.")

        filter_settings = filter_settings or FilterSettings(revision="0", version="0", allow_drafts=True)
        response_data = self.__process_client.get_process(
            process_id=process_id,
            process_name=process_name,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving process: {error}")
            raise APIError(f"Error received while retrieving process: {error}")

        result = AgenticProcessMapper.map_to_agentic_process(response_data)
        return result

    def list_processes(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> AgenticProcessList:
        """
        Retrieves a list of processes in the specified project.

        This method queries the process client to fetch a list of processes for the given project ID,
        applying the specified filter settings.

        :param filter_settings: Settings to filter the process list (id, name, status, start, count, allow_drafts).
        :return: An `AgenticProcessList` object containing the retrieved processes.
        :raises APIError: If the API returns errors.
        """
        filter_settings = filter_settings or FilterSettings(start="0", count="100", allow_drafts=True)
        response_data = self.__process_client.list_processes(
            id=filter_settings.id,
            name=filter_settings.name,
            status=filter_settings.status,
            start=filter_settings.start,
            count=filter_settings.count,
            allow_draft=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing processes: {error}")
            raise APIError(f"Error received while listing processes: {error}")

        result = AgenticProcessMapper.map_to_agentic_process_list(response_data)
        return result

    def list_process_instances(
            self,
            process_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> ProcessInstanceList:
        """
        Retrieves a list of process instances for a specific process in the specified project.

        This method queries the process client to fetch a list of process instances for the given
        process ID, applying the specified filter settings.

        :param process_id: Unique identifier of the process to list instances for.
        :param filter_settings: Settings to filter the instance list (is_active, start, count).
        :return: A `ProcessInstanceList` object containing the retrieved process instances.
        :raises APIError: If the API returns errors.
        """
        filter_settings = filter_settings or FilterSettings(start="0", count="10", is_active=True)
        response_data = self.__process_client.list_process_instances(
            process_id=process_id,
            is_active=filter_settings.is_active,
            start=filter_settings.start,
            count=filter_settings.count
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing process instances: {error}")
            raise APIError(f"Error received while listing process instances: {error}")

        result = ProcessInstanceMapper.map_to_process_instance_list(response_data)
        return result

    def delete_process(
            self,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None
    ) -> EmptyResponse:
        """
        Deletes a specific process in the specified project.

        This method sends a request to the process client to delete a process identified by either
        `process_id` or `process_name`.

        :param process_id: Unique identifier of the process to delete.
        :param process_name: Name of the process to delete.
        :return: `EmptyResponse` if the process was deleted successfully.
        :raises MissingRequirementException: If neither process_id nor process_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (process_id or process_name):
            raise MissingRequirementException("Either process_id or process_name must be provided.")

        response_data = self.__process_client.delete_process(
            process_id=process_id,
            process_name=process_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting process: {error}")
            raise APIError(f"Error received while deleting process: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "Process deleted successfully")
        return result

    def publish_process_revision(
            self,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None,
            revision: str = None
    ) -> AgenticProcess:
        """
        Publishes a specific revision of a process in the specified project.

        This method sends a request to the process client to publish the specified revision of the
        process identified by either `process_id` or `process_name`.

        :param process_id: Unique identifier of the process to publish.
        :param process_name: Name of the process to publish.
        :param revision: Revision of the process to publish.
        :return: An `AgenticProcess` object representing the published process.
        :raises MissingRequirementException: If neither process_id nor process_name is provided, or if revision is not specified.
        :raises APIError: If the API returns errors.
        """
        if not (process_id or process_name) or not revision:
            raise MissingRequirementException("Either process_id or process_name and revision must be provided.")

        response_data = self.__process_client.publish_process_revision(
            process_id=process_id,
            process_name=process_name,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while publishing process revision: {error}")
            raise APIError(f"Error received while publishing process revision: {error}")

        result = AgenticProcessMapper.map_to_agentic_process(response_data)
        return result

    def create_task(
            self,
            task: Task,
            automatic_publish: bool = False
    ) -> Task:
        """
        Creates a new task in the specified project.

        This method sends a request to the process client to create a task based on the attributes
        of the provided `Task` object.

        :param task: The task configuration to create, including name (required), description,
            title_template, id, prompt_data, and artifact_types. Optional fields are included if set.
        :param automatic_publish: Whether to publish the task after creation. Defaults to False.
        :return: A `Task` object representing the created task.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__process_client.create_task(
            name=task.name,
            description=task.description,
            title_template=task.title_template,
            id=task.id,
            prompt_data=task.prompt_data.to_dict() if task.prompt_data else None,
            artifact_types=task.artifact_types.to_dict() if task.artifact_types else None,
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating task: {error}")
            raise APIError(f"Error received while creating task: {error}")

        result = TaskMapper.map_to_task(response_data)
        return result

    def get_task(
            self,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None
    ) -> Task:
        """
        Retrieves details of a specific task in the specified project.

        This method sends a request to the process client to retrieve a task identified by either
        `task_id` or `task_name`.

        :param task_id: Unique identifier of the task to retrieve.
        :param task_name: Name of the task to retrieve.
        :return: A `Task` object representing the retrieved task.
        :raises MissingRequirementException: If neither task_id nor task_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (task_id or task_name):
            raise MissingRequirementException("Either task_id or task_name must be provided.")

        response_data = self.__process_client.get_task(
            task_id=task_id,
            task_name=task_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving task: {error}")
            raise APIError(f"Error received while retrieving task: {error}")

        result = TaskMapper.map_to_task(response_data)
        return result

    def list_tasks(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> TaskList:
        """
        Retrieves a list of tasks in the specified project.

        This method queries the process client to fetch a list of tasks for the given project ID,
        applying the specified filter settings.

        :param filter_settings: Settings to filter the task list (id, start, count, allow_drafts).
        :return: A `TaskList` object containing the retrieved tasks.
        :raises APIError: If the API returns errors.
        """
        filter_settings = filter_settings or FilterSettings(start="0", count="100", allow_drafts=True)
        response_data = self.__process_client.list_tasks(
            id=filter_settings.id,
            start=filter_settings.start,
            count=filter_settings.count,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing tasks: {error}")
            raise APIError(f"Error received while listing tasks: {error}")

        result = TaskMapper.map_to_task_list(response_data)
        return result

    def update_task(
            self,
            task: Task,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Task:
        """
        Updates an existing task in the specified project or upserts it if specified.

        This method sends a request to the process client to update a task identified by `task.id`
        based on the attributes of the provided `Task` object.

        :param task: The task configuration to update, including id (required), name, description,
            title_template, prompt_data, and artifact_types. Optional fields are included if set.
        :param automatic_publish: Whether to publish the task after updating. Defaults to False.
        :param upsert: Whether to insert the task if it does not exist. Defaults to False.
        :return: A `Task` object representing the updated task.
        :raises MissingRequirementException: If task.id is not provided.
        :raises APIError: If the API returns errors.
        """
        if not task.id:
            raise MissingRequirementException("Task ID must be provided for update.")

        response_data = self.__process_client.update_task(
            task_id=task.id,
            name=task.name,
            description=task.description,
            title_template=task.title_template,
            id=task.id,
            prompt_data=task.prompt_data.to_dict() if task.prompt_data else None,
            artifact_types=task.artifact_types.to_dict() if task.artifact_types else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating task: {error}")
            raise APIError(f"Error received while updating task: {error}")

        result = TaskMapper.map_to_task(response_data)
        return result

    def delete_task(
            self,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None
    ) -> EmptyResponse:
        """
        Deletes a specific task in the specified project.

        This method sends a request to the process client to delete a task identified by either
        `task_id` or `task_name`.

        :param task_id: Unique identifier of the task to delete.
        :param task_name: Name of the task to delete.
        :return: `EmptyResponse` if the task was deleted successfully.
        :raises MissingRequirementException: If neither task_id nor task_name is provided.
        :raises APIError: If the API returns errors.
        """
        if not (task_id or task_name):
            raise MissingRequirementException("Either task_id or task_name must be provided.")

        response_data = self.__process_client.delete_task(
            task_id=task_id,
            task_name=task_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting task: {error}")
            raise APIError(f"Error received while deleting task: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "Task deleted successfully")
        return result

    def publish_task_revision(
            self,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None,
            revision: str = None
    ) -> Task:
        """
        Publishes a specific revision of a task in the specified project.

        This method sends a request to the process client to publish the specified revision of the
        task identified by either `task_id` or `task_name`.

        :param task_id: Unique identifier of the task to publish.
        :param task_name: Name of the task to publish.
        :param revision: Revision of the task to publish.
        :return: A `Task` object representing the published task.
        :raises MissingRequirementException: If neither task_id nor task_name is provided, or if revision is not specified.
        :raises APIError: If the API returns errors.
        """
        if not (task_id or task_name) or not revision:
            raise MissingRequirementException("Either task_id or task_name and revision must be provided.")

        response_data = self.__process_client.publish_task_revision(
            task_id=task_id,
            task_name=task_name,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while publishing task revision: {error}")
            raise APIError(f"Error received while publishing task revision: {error}")

        result = TaskMapper.map_to_task(response_data)
        return result

    def start_instance(
            self,
            process_name: str,
            subject: Optional[str] = None,
            variables: Optional[Union[List[Variable], VariableList]] = None
    ) -> ProcessInstance:
        """
        Starts a new process instance in the specified project.

        This method sends a request to the process client to start a new process instance for the
        specified `process_name`.

        :param process_name: Name of the process to start an instance for.
        :param subject: Subject of the process instance. Defaults to None.
        :param variables: List of variables for the instance. Defaults to None.
        :return: A `ProcessInstance` object representing the started instance.
        :raises APIError: If the API returns errors.
        """
        if not isinstance(variables, VariableList):
            variables = VariableList(variables=variables)

        response_data = self.__process_client.start_instance(
            process_name=process_name,
            subject=subject,
            variables=variables.to_dict()
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while starting process instance: {error}")
            raise APIError(f"Error received while starting process instance: {error}")

        result = ProcessInstanceMapper.map_to_process_instance(response_data)
        return result

    def abort_instance(
            self,
            instance_id: str
    ) -> EmptyResponse:
        """
        Aborts a specific process instance in the specified project.

        This method sends a request to the process client to abort a process instance identified
        by `instance_id`.

        :param instance_id: Unique identifier of the instance to abort.
        :return: `EmptyResponse` if the instance was aborted successfully.
        :raises MissingRequirementException: If instance_id is not provided.
        :raises APIError: If the API returns errors.
        """
        if not instance_id:
            raise MissingRequirementException("Instance ID must be provided.")

        response_data = self.__process_client.abort_instance(
            instance_id=instance_id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while aborting process instance: {error}")
            raise APIError(f"Error received while aborting process instance: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "Instance aborted successfully")
        return result

    def get_instance(
            self,
            instance_id: str
    ) -> ProcessInstance:
        """
        Retrieves details of a specific process instance in the specified project.

        This method sends a request to the process client to retrieve a process instance identified
        by `instance_id`.

        :param instance_id: Unique identifier of the instance to retrieve.
        :return: A `ProcessInstance` object representing the retrieved instance.
        :raises MissingRequirementException: If instance_id is not provided.
        :raises APIError: If the API returns errors.
        """
        if not instance_id:
            raise MissingRequirementException("Instance ID must be provided.")

        response_data = self.__process_client.get_instance(
            instance_id=instance_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving process instance: {error}")
            raise APIError(f"Error received while retrieving process instance: {error}")

        result = ProcessInstanceMapper.map_to_process_instance(response_data)
        return result

    def get_instance_history(
            self,
            instance_id: str
    ) -> dict:
        """
        Retrieves the history of a specific process instance in the specified project.

        This method sends a request to the process client to retrieve the history of a process instance
        identified by `instance_id`.

        :param instance_id: Unique identifier of the instance to retrieve history for.
        :return: A dictionary containing the instance history.
        :raises MissingRequirementException: If instance_id is not provided.
        :raises APIError: If the API returns errors.
        """
        if not instance_id:
            raise MissingRequirementException("Instance ID must be provided.")

        response_data = self.__process_client.get_instance_history(
            instance_id=instance_id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving instance history: {error}")
            raise APIError(f"Error received while retrieving instance history: {error}")

        result = response_data
        return result

    def get_thread_information(
            self,
            thread_id: str
    ) -> dict:
        """
        Retrieves information about a specific thread in the specified project.

        This method sends a request to the process client to retrieve information about a thread
        identified by `thread_id`.

        :param thread_id: Unique identifier of the thread to retrieve information for.
        :return: A dictionary containing the thread information.
        :raises MissingRequirementException: If thread_id is not provided.
        :raises APIError: If the API returns errors.
        """
        if not thread_id:
            raise MissingRequirementException("Thread ID must be provided.")

        response_data = self.__process_client.get_thread_information(
            thread_id=thread_id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving thread information: {error}")
            raise APIError(f"Error received while retrieving thread information: {error}")

        result = response_data
        return result

    def send_user_signal(
            self,
            instance_id: str,
            signal_name: str
    ) -> EmptyResponse:
        """
        Sends a user signal to a specific process instance in the specified project.

        This method sends a request to the process client to send a user signal identified by
        `signal_name` to a process instance identified by `instance_id`.

        :param instance_id: Unique identifier of the instance to send the signal to.
        :param signal_name: Name of the user signal to send.
        :return: `EmptyResponse` if the signal was sent successfully.
        :raises MissingRequirementException: If instance_id or signal_name is not provided.
        :raises APIError: If the API returns errors.
        """
        if not instance_id or not signal_name:
            raise MissingRequirementException("Instance ID and signal name must be provided.")

        response_data = self.__process_client.send_user_signal(
            instance_id=instance_id,
            signal_name=signal_name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while sending user signal: {error}")
            raise APIError(f"Error received while sending user signal: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "Signal sent successfully")
        return result

    def create_knowledge_base(
            self,
            knowledge_base: KnowledgeBase,
    ) -> KnowledgeBase:
        """
        Creates a new knowledge base in the specified project using the provided configuration.

        This method sends a request to the process client to create a knowledge base based on
        the attributes of the provided `KnowledgeBase` object.

        :param knowledge_base: The knowledge base configuration object containing name
            and artifact type names.
        :return: A `KnowledgeBase` object representing the created knowledge base.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__process_client.create_kb(
            name=knowledge_base.name,
            artifacts=knowledge_base.artifacts if knowledge_base.artifacts else None,
            metadata=knowledge_base.metadata if knowledge_base.metadata else None
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while creating knowledge base: {error}")
            raise APIError(f"Error received while creating knowledge base: {error}")

        result = KnowledgeBaseMapper.map_to_knowledge_base(response_data)
        return result

    def list_knowledge_bases(
            self,
            name: Optional[str] = None,
            start: Optional[int] = 0,
            count: Optional[int] = 10
    ) -> KnowledgeBaseList:
        """
        Retrieves a list of knowledge bases for the specified project.

        This method queries the process client to fetch a list of knowledge bases associated
        with the specified project ID, applying optional filters for name and pagination.

        :param name: Name filter to narrow down the list of knowledge bases.
        :param start: Starting index for pagination, defaults to 0.
        :param count: Number of knowledge bases to return, defaults to 10.
        :return: A `KnowledgeBaseList` containing the retrieved knowledge bases.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__process_client.list_kbs(
            name=name,
            start=start,
            count=count
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing knowledge bases: {error}")
            raise APIError(f"Error received while listing knowledge bases: {error}")

        result = KnowledgeBaseMapper.map_to_knowledge_base_list(response_data)
        return result

    def get_knowledge_base(
            self,
            kb_name: Optional[str] = None,
            kb_id: Optional[str] = None
    ) -> KnowledgeBase:
        """
        Retrieves details of a specific knowledge base from the specified project.

        This method sends a request to the process client to retrieve a knowledge base
        identified by either `kb_name` or `kb_id`.

        :param kb_name: Name of the knowledge base to retrieve.
        :param kb_id: Unique identifier of the knowledge base to retrieve.
        :return: A `KnowledgeBase` object representing the retrieved knowledge base.
        :raises MissingRequirementException: If neither `kb_name` nor `kb_id` is provided.
        :raises APIError: If the API returns errors.
        """
        if not (kb_name or kb_id):
            raise MissingRequirementException("Either kb_name or kb_id must be provided.")

        response_data = self.__process_client.get_kb(
            kb_name=kb_name,
            kb_id=kb_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving knowledge base: {error}")
            raise APIError(f"Error received while retrieving knowledge base: {error}")

        result = KnowledgeBaseMapper.map_to_knowledge_base(response_data)
        return result

    def delete_knowledge_base(
            self,
            kb_name: Optional[str] = None,
            kb_id: Optional[str] = None
    ) -> EmptyResponse:
        """
        Deletes a specific knowledge base from the specified project.

        This method sends a request to the process client to delete a knowledge base
        identified by either `kb_name` or `kb_id`.

        :param kb_name: Name of the knowledge base to delete.
        :param kb_id: Unique identifier of the knowledge base to delete.
        :return: `EmptyResponse` if the knowledge base was deleted successfully.
        :raises MissingRequirementException: If neither `kb_name` nor `kb_id` is provided.
        :raises APIError: If the API returns errors.
        """
        if not (kb_name or kb_id):
            raise MissingRequirementException("Either kb_name or kb_id must be provided.")

        response_data = self.__process_client.delete_kb(
            kb_name=kb_name,
            kb_id=kb_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting knowledge base: {error}")
            raise APIError(f"Error received while deleting knowledge base: {error}")

        response_data = response_data if response_data else "Knowledge base deleted successfully"
        result = ResponseMapper.map_to_empty_response(response_data)
        return result

    def list_jobs(
            self,
            filter_settings: Optional[FilterSettings] = None,
            topic: Optional[str] = None,
            token: Optional[str] = None
    ) -> JobList:
        """
        Retrieves a list of jobs in the specified project.

        This method queries the process client to fetch a list of jobs associated with the specified
        project ID, applying optional filter settings.

        :param filter_settings: Settings to filter the job list (start, count).
        :param topic: Topic to filter the jobs (e.g., 'Default', 'Event'). Defaults to None.
        :param token: Unique token identifier to filter a specific job. Defaults to None.
        :return: A `JobList` containing the retrieved jobs.
        :raises MissingRequirementException: If project_id is not provided.
        :raises APIError: If the API returns errors.
        """

        filter_settings = filter_settings or FilterSettings(start="0", count="100")
        response_data = self.__process_client.list_jobs(
            start=filter_settings.start,
            count=filter_settings.count,
            topic=topic,
            token=token,
            name=filter_settings.name
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while listing jobs: {error}")
            raise APIError(f"Error received while listing jobs: {error}")

        result = JobMapper.map_to_job_list(response_data)
        return result

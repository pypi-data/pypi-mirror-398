import json
from json import JSONDecodeError
from typing import List

from pygeai.lab.models import Tool, ToolParameter, ToolMessage, ToolList


class ToolMapper:
    @classmethod
    def _map_parameters(cls, params_data: List[dict]) -> List[ToolParameter]:
        """
        Maps a list of parameter dictionaries to a list of ToolParameter objects.

        :param params_data: List[dict] - List of raw parameter data.
        :return: List[ToolParameter] - List of mapped ToolParameter objects.
        """
        return [
            ToolParameter(
                key=param.get("key"),
                data_type=param.get("dataType"),
                description=param.get("description"),
                is_required=param.get("isRequired"),
                type=param.get("type"),
                from_secret=param.get("fromSecret"),
                value=param.get("value")
            )
            for param in params_data
        ]

    @classmethod
    def _map_messages(cls, messages_data: List[dict]) -> List[ToolMessage]:
        """
        Maps a list of message dictionaries to a list of ToolMessage objects.

        :param messages_data: List[dict] - List of raw message data.
        :return: List[ToolMessage] - List of mapped ToolMessage objects.
        """
        return [
            ToolMessage(
                description=msg.get("description"),
                type=msg.get("type")
            )
            for msg in messages_data
        ]

    @classmethod
    def map_to_tool(cls, data: dict) -> Tool:
        """
        Maps a dictionary to a Tool object with explicit field mapping.

        :param data: dict - The raw data, either input (under 'tool' key) or output (flat structure).
            Expected fields include name, description, scope, parameters, accessScope, publicName,
            icon, openApi, openApiJson, reportEvents, id, isDraft, messages, revision, and status.
        :return: Tool - A Tool object representing the tool configuration.
        """
        tool_data = data.get("tool", data)

        name = tool_data.get("name")
        description = tool_data.get("description")
        scope = tool_data.get("scope")
        parameter_data = tool_data.get("parameters")
        parameters = cls._map_parameters(parameter_data) if parameter_data else None

        access_scope = tool_data.get("accessScope")
        public_name = tool_data.get("publicName")
        icon = tool_data.get("icon")
        open_api = tool_data.get("openApi")
        open_api_json = tool_data.get("openApiJson")
        if isinstance(open_api_json, str):
            try:
                open_api_json = json.loads(open_api_json)
            except JSONDecodeError as e:
                raise ValueError("open_api_json must be a valid JSON string or a dict")

        report_events = tool_data.get("reportEvents", "None")
        id = tool_data.get("id")
        is_draft = tool_data.get("isDraft")
        messages_data = tool_data.get("messages")
        messages = cls._map_messages(messages_data) if messages_data else None
        revision = tool_data.get("revision")
        status = tool_data.get("status")

        return Tool(
            name=name,
            description=description,
            scope=scope,
            parameters=parameters,
            access_scope=access_scope,
            public_name=public_name,
            icon=icon,
            open_api=open_api,
            open_api_json=open_api_json,
            report_events=report_events,
            id=id,
            is_draft=is_draft,
            messages=messages,
            revision=revision,
            status=status
        )

    @classmethod
    def map_to_tool_list(cls, data: dict) -> ToolList:
        """
        Maps an API response dictionary to a `ToolList` object.

        This method extracts tools from the given data, converts them into a list of `Tool` objects,
        and returns a `ToolList` containing the list.

        :param data: dict - The dictionary containing tool response data, expected to have a 'tools' key or be a list.
        :return: ToolList - A structured response containing a list of tools.
        """
        tool_list = []
        tools = data if isinstance(data, list) else data.get("tools", [])
        if tools and any(tools):
            for tool_data in tools:
                tool = cls.map_to_tool(tool_data)
                tool_list.append(tool)

        return ToolList(tools=tool_list)

    @classmethod
    def map_to_parameter_list(cls, data: dict) -> List[ToolParameter]:
        """
        Maps an API response dictionary to a list of ToolParameter objects.

        :param data: dict - The dictionary containing parameter response data, expected to have a 'parameters' key or be a list.
        :return: List[ToolParameter] - A list of ToolParameter objects.
        """
        params_data = data if isinstance(data, list) else data.get("parameters", [])
        return cls._map_parameters(params_data)


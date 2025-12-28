from typing import Any
import json


class ProxiedTool:
    """
    Represents a tool exposed by an ToolServer (Multi-Channel Proxy).

    :param server_name: str - Name of the server exposing the tool
    :param name: str - Name of the tool
    :param description: str - Description of the tool's functionality
    :param public_prefix: str - Public prefix of the tool
    :param input_schema: dict[str, Any] - JSON schema defining the expected input for the tool
    :return: ProxiedTool - Instance of the ProxiedTool class
    :raises: ValueError - If any required parameter is invalid or missing
    """

    def __init__(
        self,
        server_name: str,
        name: str,
        description: str,
        public_prefix: str,
        input_schema: dict[str, Any]
    ) -> None:
        self.server_name: str = server_name
        self.name: str = name
        self.openai_compatible_name: str = self._get_openai_compatible_name(name)
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema
        self.public_prefix: str = public_prefix

    def get_full_name(self) -> str:
        """Get the full name of the tool."""
        return f"{self.server_name}__{self.openai_compatible_name}"

    def is_public(self) -> bool:
        """Check if the tool is public."""
        return self.public_prefix is not None

    def get_public_name(self) -> str:
        """Get the public name of the tool."""
        if not self.public_prefix:
            return ""
        if self.server_name in self.public_prefix:
            return f"{self.public_prefix}.{self.name}"
        else:
            return f"{self.public_prefix}.{self.get_full_name()}"

    def format_for_llm(self) -> str:
        """Format tool information for LLM.

        Returns:
            A formatted string describing the tool.
        """
        return json.dumps({
            'type': 'function',
            'function': {
                'name': self.get_full_name(),
                'description': self.description or '',
                'parameters': self.input_schema
            }
        })
    
    def _get_openai_compatible_name(self, name: str) -> str:
        compatible_name = ''.join(
            c if c.isalnum() or c in '-_' else '_' for c in name.lower()
        )
        return compatible_name

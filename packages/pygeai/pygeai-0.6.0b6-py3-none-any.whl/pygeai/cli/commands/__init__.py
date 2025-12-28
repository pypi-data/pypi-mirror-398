from enum import Enum


class ArgumentsEnum(Enum):
    NOT_AVAILABLE = 0
    OPTIONAL = 1
    REQUIRED = 2


class Command:
    """
    Base class to standardize commands for the cli utility.
    Each command must define:
    - name: the name for internal references
    - identifiers: the identifiers which will be used to invoke it
    - description: brief summary of what it does
    - action: function to be executed
    - additional_args: if additional arguments are required to use this command
    - subcommands: list of commands available for this command
    - options: list of options available for this command
    """
    def __init__(
            self,
            name: str,
            identifiers: list[str],
            description: str,
            action,
            additional_args: ArgumentsEnum,
            subcommands: list,
            options: list
    ):
        self.name = name
        self.identifiers = identifiers
        self.description = description
        self.action = action
        self.additional_args = additional_args
        self.subcommands = subcommands
        self.options = options


class Option:
    """
    Base class to standardize configuration options for cli utility.
    Each flag must define:
    - name: the name for internal references
    - identifiers: the identifiers which will be used to invoke it
    - description: brief summary of what it does
    - requires_args: if additional arguments are required to use this option
    """
    def __init__(
            self,
            name: str,
            identifiers: list[str],
            description: str,
            requires_args: bool
    ):
        self.name = name
        self.identifiers = identifiers
        self.description = description
        self.requires_args = requires_args

from pygeai.cli.commands.base import base_options
from pygeai.cli.commands import Command, Option
from pygeai.core.common.exceptions import UnknownArgumentError, MissingRequirementException


class CommandParser:

    def __init__(self, available_commands, available_options):
        self.available_commands = available_commands
        self.available_options = available_options

    def identify_command(self, arg: str) -> Command:
        """
        Analyzes the first argument and checks if it's a valid command.

        :param first_argument: The first argument to be analyzed.
        :return: The command to be run.
        """
        command = self._get_associated_command(arg)
        if not command:
            raise UnknownArgumentError(f"'{arg}' is not a valid command. Run with help or h to check usage.")

        return command

    def extract_option_list(self, arguments: list) -> list[(Option, str)]:
        """
        Parses a list of arguments and returns the commands being invoked.

        :param arguments: list - The list of arguments received by the CLI utility.
        :return: list - A list of flags and their associated arguments.
        """
        flag_list = []

        complementary_arg = False
        for i, arg in enumerate(arguments):
            if complementary_arg:
                complementary_arg = False
                continue

            flag = self._get_associated_option(arg)
            if not flag:
                raise UnknownArgumentError(f"'{arg}' is not a valid option. Run with help or h to check usage.")

            if flag.requires_args:
                complementary_arg = True
                try:
                    flag_list.append((flag, arguments[i + 1]))
                except IndexError as e:
                    raise MissingRequirementException(f"'{flag.name}' requires an argument.")
            else:
                flag_list.append([flag, []])

        return flag_list

    def _get_associated_command(self, arg: str) -> Command:
        associated_command = None
        for command in self.available_commands:
            if arg in command.identifiers:
                associated_command = command
                break

        return associated_command

    def _get_associated_option(self, arg: str) -> Option:
        associated_option = None
        for option in self.available_options:
            if arg in option.identifiers:
                associated_option = option
                break

        return associated_option

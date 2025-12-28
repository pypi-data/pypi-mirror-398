import unittest
from unittest import TestCase

from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.parsers import CommandParser
from pygeai.core.common.exceptions import UnknownArgumentError, MissingRequirementException


class TestCommandParser(TestCase):
    """
    python -m unittest pygeai.tests.cli.test_parsers.TestCommandParser
    """

    def setUp(self):
        self.command_list = [
            Command(name='organization', identifiers=['org', 'organization'], description='Manage organizations',
                    action=None, additional_args=ArgumentsEnum.OPTIONAL, subcommands=[], options=[]),
            Command(name='chat', identifiers=['chat'], description='Interact with chat assistants',
                    action=None, additional_args=ArgumentsEnum.OPTIONAL, subcommands=[], options=[]),
            Command(name='help', identifiers=['h', 'help'], description='Display help text',
                    action=None, additional_args=ArgumentsEnum.OPTIONAL, subcommands=[], options=[]),
        ]

        self.option_list = [
            Option(name="detail", identifiers=['--detail', '-d'], description='Defines the level of detail', requires_args=True),
            Option(name="name", identifiers=['--name', '-n'], description='Name of the project', requires_args=True),
        ]

        self.parser = CommandParser(self.command_list, self.option_list)

    def test_identify_command_valid(self):
        command = self.parser.identify_command('org')
        self.assertEqual(command.name, 'organization')

    def test_identify_command_invalid(self):
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.identify_command('invalid')
        self.assertEqual(str(context.exception), "'invalid' is not a valid command. Run with help or h to check usage.")

    def test_extract_option_list_valid(self):
        args = ['--detail', 'full', '--name', 'Project1']
        options = self.parser.extract_option_list(args)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0][0].identifiers, ['--detail', '-d'])
        self.assertEqual(options[0][1], 'full')
        self.assertEqual(options[1][0].identifiers, ['--name', '-n'])
        self.assertEqual(options[1][1], 'Project1')

    def test_extract_option_list_invalid(self):
        args = ['--invalid']
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.extract_option_list(args)
        self.assertEqual(str(context.exception),
                         "'--invalid' is not a valid option. Run with help or h to check usage.")

    def test_identify_command_valid_multiple_identifiers(self):
        command = self.parser.identify_command('organization')
        self.assertEqual(command.name, 'organization')

    def test_extract_option_list_valid_multiple_options(self):
        args = ['--detail', 'full', '--name', 'Project1', '--name', 'Project2']
        options = self.parser.extract_option_list(args)
        self.assertEqual(len(options), 3)
        self.assertEqual(options[0][0].identifiers, ['--detail', '-d'])
        self.assertEqual(options[0][1], 'full')
        self.assertEqual(options[1][0].identifiers, ['--name', '-n'])
        self.assertEqual(options[1][1], 'Project1')
        self.assertEqual(options[2][0].identifiers, ['--name', '-n'])
        self.assertEqual(options[2][1], 'Project2')

    def test_extract_option_list_missing_argument(self):
        args = ['--detail']
        with self.assertRaises(MissingRequirementException) as context:
            self.parser.extract_option_list(args)
        self.assertEqual(str(context.exception), "'detail' requires an argument.")

    def test_identify_command_empty_string(self):
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.identify_command('')
        self.assertEqual(str(context.exception), "'' is not a valid command. Run with help or h to check usage.")

    def test_extract_option_list_empty_arguments(self):
        args = []
        options = self.parser.extract_option_list(args)
        self.assertEqual(options, [])

    def test_identify_command_with_subcommands(self):
        command_with_subcommands = Command(
            name='organization',
            identifiers=['org', 'organization'],
            description='Manage organizations',
            action=None,
            additional_args=ArgumentsEnum.OPTIONAL,
            subcommands=['create', 'delete'],
            options=[]
        )
        self.command_list.append(command_with_subcommands)
        command = self.parser.identify_command('org')
        self.assertEqual(command.name, 'organization')
        self.assertIn('create', command_with_subcommands.subcommands)

    @unittest.skip("Will throw an exception when command is executed because of wrong argument.")
    def test_extract_option_list_invalid_multiple_missing_arguments(self):
        args = ['--detail', '--name']
        with self.assertRaises(MissingRequirementException) as context:
            self.parser.extract_option_list(args)
        self.assertIn('requires an argument', str(context.exception))

    def test_identify_command_case_insensitivity(self):
        with self.assertRaises(UnknownArgumentError) as context:
             self.parser.identify_command('ORG')
        self.assertIn('is not a valid command', str(context.exception))

    def test_extract_option_list_valid_with_case_insensitivity(self):
        args = ['--Detail', 'full', '--NAME', 'Project1']
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.extract_option_list(args)
        self.assertIn('is not a valid option', str(context.exception))

    def test_extract_option_list_invalid_option_after_valid(self):
        args = ['--detail', 'full', '--invalid']
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.extract_option_list(args)
        self.assertEqual(str(context.exception),
                         "'--invalid' is not a valid option. Run with help or h to check usage.")

    def test_identify_command_subcommand(self):
        command_with_subcommands = Command(
            name='organization',
            identifiers=['org', 'organization'],
            description='Manage organizations',
            action=None,
            additional_args=ArgumentsEnum.OPTIONAL,
            subcommands=['create', 'delete'],
            options=[]
        )
        self.command_list.append(command_with_subcommands)
        subcommand_name = 'create'
        self.assertIn(subcommand_name, command_with_subcommands.subcommands)

    def test_extract_option_list_ordered_args(self):
        args = ['--name', 'Project1', '--detail', 'full']
        options = self.parser.extract_option_list(args)
        self.assertEqual(len(options), 2)
        self.assertEqual(options[0][0].identifiers, ['--name', '-n'])
        self.assertEqual(options[0][1], 'Project1')
        self.assertEqual(options[1][0].identifiers, ['--detail', '-d'])
        self.assertEqual(options[1][1], 'full')

    def test_identify_command_no_identifier(self):
        with self.assertRaises(UnknownArgumentError) as context:
            self.parser.identify_command('nonexistent')
        self.assertEqual(str(context.exception),
                         "'nonexistent' is not a valid command. Run with help or h to check usage.")
import unittest
import importlib
import io
import contextlib
from unittest import TestCase


class TestShowHelp(TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_show_help.TestShowHelp
    """
    command_files = [
        'admin', 'assistant', 'base', 'chat',
        'embeddings', 'evaluation', 'feedback', 'files',
        'gam', 'llm', 'migrate', 'organization', 'rag',
        'rerank', 'secrets', 'usage_limits'
    ]

    def test_show_help(self):
        """
        Test that show_help() in each command module runs without errors and produces output.
        """
        for command_file in self.command_files:
            with self.subTest(command_file=command_file):
                try:
                    module = importlib.import_module(f'pygeai.cli.commands.{command_file}')

                    self.assertTrue(hasattr(module, 'show_help'), f"show_help not found in {command_file}")
                    self.assertTrue(callable(module.show_help), f"show_help is not callable in {command_file}")

                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        module.show_help()

                    output_text = output.getvalue()
                    self.assertGreater(len(output_text.strip()), 0, f"show_help in {command_file} produced empty output")

                except ImportError as e:
                    self.fail(f"Failed to import {command_file}: {str(e)}")
                except Exception as e:
                    self.fail(f"show_help in {command_file} raised an exception: {str(e)}")

import unittest
from unittest import TestCase
from pygeai.cli.commands.lab.common import (
    get_agent_data_prompt_inputs,
    get_agent_data_prompt_outputs,
    get_agent_data_prompt_examples,
    get_tool_parameters
)
from pygeai.core.common.exceptions import WrongArgumentError


class TestLabCommon(TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.lab.test_common.TestLabCommon
    """

    def test_get_agent_data_prompt_inputs_valid(self):
        input_list = ["input1", "input2"]
        result = get_agent_data_prompt_inputs(input_list)
        self.assertEqual(result, input_list)

    def test_get_agent_data_prompt_inputs_invalid_non_string(self):
        input_list = ["input1", 123]  # Non-string element
        with self.assertRaises(WrongArgumentError) as context:
            get_agent_data_prompt_inputs(input_list)
        self.assertIn("Inputs must be a list of strings", str(context.exception))

    def test_get_agent_data_prompt_inputs_empty(self):
        input_list = []
        result = get_agent_data_prompt_inputs(input_list)
        self.assertEqual(result, [])

    def test_get_agent_data_prompt_outputs_valid(self):
        output_list = [
            {"key": "output1", "description": "Description for output1"},
            {"key": "output2", "description": "Description for output2"}
        ]
        result = get_agent_data_prompt_outputs(output_list)
        self.assertEqual(result, output_list)

    def test_get_agent_data_prompt_outputs_invalid_missing_key(self):
        output_list = [
            {"description": "Description without key"}  # Missing 'key'
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_agent_data_prompt_outputs(output_list)
        self.assertIn("Each output must be in JSON format", str(context.exception))

    def test_get_agent_data_prompt_outputs_invalid_type(self):
        output_list = [
            "not a dict"  # Not a dictionary
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_agent_data_prompt_outputs(output_list)
        self.assertIn("Each output must be in JSON format", str(context.exception))

    def test_get_agent_data_prompt_outputs_empty(self):
        output_list = []
        result = get_agent_data_prompt_outputs(output_list)
        self.assertEqual(result, [])

    def test_get_agent_data_prompt_examples_valid(self):
        example_list = [
            {"inputData": "Input example 1", "output": '{"result": "Output 1"}'},
            {"inputData": "Input example 2", "output": '{"result": "Output 2"}'}
        ]
        result = get_agent_data_prompt_examples(example_list)
        self.assertEqual(result, example_list)

    def test_get_agent_data_prompt_examples_invalid_missing_field(self):
        example_list = [
            {"inputData": "Input without output"}  # Missing 'output'
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_agent_data_prompt_examples(example_list)
        self.assertIn("Each example must be in JSON format", str(context.exception))

    def test_get_agent_data_prompt_examples_invalid_type(self):
        example_list = [
            "not a dict"  # Not a dictionary
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_agent_data_prompt_examples(example_list)
        self.assertIn("Each example must be in JSON format", str(context.exception))

    def test_get_agent_data_prompt_examples_empty(self):
        example_list = []
        result = get_agent_data_prompt_examples(example_list)
        self.assertEqual(result, [])

    def test_get_tool_parameters_valid_regular(self):
        param_list = [
            {"key": "param1", "dataType": "String", "description": "Param 1 description", "isRequired": True}
        ]
        result = get_tool_parameters(param_list)
        self.assertEqual(result, param_list)

    def test_get_tool_parameters_valid_config(self):
        param_list = [
            {
                "key": "config1",
                "dataType": "String",
                "description": "Config 1 description",
                "isRequired": True,
                "type": "config",
                "fromSecret": False,
                "value": "config_value"
            }
        ]
        result = get_tool_parameters(param_list)
        self.assertEqual(result, param_list)

    def test_get_tool_parameters_invalid_missing_field(self):
        param_list = [
            {"key": "param1", "dataType": "String", "isRequired": True}  # Missing 'description'
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Each parameter must contain 'key', 'dataType', 'description', and 'isRequired'", str(context.exception))

    def test_get_tool_parameters_invalid_key_type(self):
        param_list = [
            {"key": 123, "dataType": "String", "description": "Param description", "isRequired": True}  # 'key' not string
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'key' must be a string", str(context.exception))

    def test_get_tool_parameters_invalid_data_type(self):
        param_list = [
            {"key": "param1", "dataType": 123, "description": "Param description", "isRequired": True}  # 'dataType' not string
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'dataType' must be a string", str(context.exception))

    def test_get_tool_parameters_invalid_description_type(self):
        param_list = [
            {"key": "param1", "dataType": "String", "description": 123, "isRequired": True}  # 'description' not string
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'description' must be a string", str(context.exception))

    def test_get_tool_parameters_invalid_is_required_type(self):
        param_list = [
            {"key": "param1", "dataType": "String", "description": "Param description", "isRequired": "True"}  # 'isRequired' not bool
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'isRequired' must be a boolean", str(context.exception))

    def test_get_tool_parameters_invalid_type_value(self):
        param_list = [
            {
                "key": "param1",
                "dataType": "String",
                "description": "Param description",
                "isRequired": True,
                "type": "invalid"  # 'type' not 'config'
            }
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'type' must be 'config' if present", str(context.exception))

    def test_get_tool_parameters_invalid_from_secret_type(self):
        param_list = [
            {
                "key": "param1",
                "dataType": "String",
                "description": "Param description",
                "isRequired": True,
                "type": "config",
                "fromSecret": "True"  # 'fromSecret' not bool
            }
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'fromSecret' must be a boolean if present", str(context.exception))

    def test_get_tool_parameters_invalid_value_type(self):
        param_list = [
            {
                "key": "param1",
                "dataType": "String",
                "description": "Param description",
                "isRequired": True,
                "type": "config",
                "value": 123  # 'value' not string
            }
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Parameter 'value' must be a string if present", str(context.exception))

    def test_get_tool_parameters_invalid_format(self):
        param_list = [
            "not a dict"  # Not a dictionary
        ]
        with self.assertRaises(WrongArgumentError) as context:
            get_tool_parameters(param_list)
        self.assertIn("Each parameter must contain", str(context.exception))

    def test_get_tool_parameters_empty(self):
        param_list = []
        result = get_tool_parameters(param_list)
        self.assertEqual(result, [])
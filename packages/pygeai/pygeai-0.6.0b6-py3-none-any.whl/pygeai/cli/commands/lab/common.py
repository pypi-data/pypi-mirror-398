from pygeai.core.common.exceptions import WrongArgumentError


def get_agent_data_prompt_inputs(input_list: list):
    """
    Processes a list of input strings.

    :param input_list: list - A list of strings representing input names.
    :return: list - A list of input strings.
    :raises WrongArgumentError: If the input list contains non-string elements.
    """
    if not all(isinstance(item, str) for item in input_list):
        raise WrongArgumentError(
            "Inputs must be a list of strings: '[\"input_name\", \"another_input\"]'. "
            "Each element in the list must be a string representing an input name."
        )
    return input_list


def get_agent_data_prompt_outputs(output_list: list):
    """
    Processes a list of output dictionaries and extracts the "key" and "description" fields.

    :param output_list: list - A list of dictionaries, where each dictionary must contain the keys "key" and "description".
    :return: list - A list of dictionaries, each containing the "key" and "description" fields.
    :raises WrongArgumentError: If a dictionary in the list is not in the expected format or missing required keys.
    """
    outputs = []
    if any(output_list):
        try:
            for output_dict in output_list:
                outputs.append({
                    "key": output_dict["key"],
                    "description": output_dict["description"]
                })
        except (KeyError, TypeError):
            raise WrongArgumentError(
                "Each output must be in JSON format: '{\"key\": \"output_key\", \"description\": \"description of the output\"}' "
                "It must be a dictionary or a list of dictionaries. Each dictionary must contain 'key' and 'description'."
            )
    return outputs


def get_agent_data_prompt_examples(example_list: list):
    """
    Processes a list of example dictionaries and extracts the "inputData" and "output" fields.

    :param example_list: list - A list of dictionaries, where each dictionary must contain the keys "inputData" and "output".
    :return: list - A list of dictionaries, each containing the "inputData" and "output" fields.
    :raises WrongArgumentError: If a dictionary in the list is not in the expected format or missing required keys.
    """
    examples = []
    if any(example_list):
        try:
            for example_dict in example_list:
                examples.append({
                    "inputData": example_dict["inputData"],
                    "output": example_dict["output"]
                })
        except (KeyError, TypeError):
            raise WrongArgumentError(
                "Each example must be in JSON format: '{\"inputData\": \"example input\", \"output\": \"expected output in JSON string format\"}' "
                "Each dictionary must contain 'inputData' and 'output'."
            )
    return examples


def get_tool_parameters(parameter_list: list) -> list:
    """
    Processes a list of parameter dictionaries and validates their format.

    :param parameter_list: list - A list of dictionaries, where each dictionary represents a parameter.
        Regular parameters must contain "key", "dataType", "description", and "isRequired".
        Config parameters must additionally include "type" as "config", and may include "fromSecret" and "value".
    :return: list - A list of validated parameter dictionaries.
    :raises WrongArgumentError: If a dictionary in the list is not in the expected format or missing required keys.
    """
    parameters = []

    if not parameter_list:
        return parameters

    try:
        for param_dict in parameter_list:
            required_fields = ["key", "dataType", "description", "isRequired"]
            if not all(field in param_dict for field in required_fields):
                raise WrongArgumentError(
                    "Each parameter must contain 'key', 'dataType', 'description', and 'isRequired'. "
                    "For regular parameters: '{\"key\": \"param_name\", \"dataType\": \"String\", \"description\": \"param description\", \"isRequired\": true}'. "
                    "For config parameters: additionally include '\"type\": \"config\", \"fromSecret\": boolean, \"value\": \"config_value\"'."
                )

            if not isinstance(param_dict["key"], str):
                raise WrongArgumentError("Parameter 'key' must be a string.")
            if not isinstance(param_dict["dataType"], str):
                raise WrongArgumentError("Parameter 'dataType' must be a string.")
            if not isinstance(param_dict["description"], str):
                raise WrongArgumentError("Parameter 'description' must be a string.")
            if not isinstance(param_dict["isRequired"], bool):
                raise WrongArgumentError("Parameter 'isRequired' must be a boolean.")

            if "type" in param_dict:
                if param_dict["type"] != "config":
                    raise WrongArgumentError("Parameter 'type' must be 'config' if present.")
                if "fromSecret" in param_dict and not isinstance(param_dict["fromSecret"], bool):
                    raise WrongArgumentError("Parameter 'fromSecret' must be a boolean if present.")
                if "value" in param_dict and not isinstance(param_dict["value"], str):
                    raise WrongArgumentError("Parameter 'value' must be a string if present.")

            validated_param = {
                "key": param_dict["key"],
                "dataType": param_dict["dataType"],
                "description": param_dict["description"],
                "isRequired": param_dict["isRequired"]
            }

            if "type" in param_dict:
                validated_param["type"] = param_dict["type"]
            if "fromSecret" in param_dict:
                validated_param["fromSecret"] = param_dict["fromSecret"]
            if "value" in param_dict:
                validated_param["value"] = param_dict["value"]

            parameters.append(validated_param)

    except (KeyError, TypeError) as e:
        raise WrongArgumentError(
            "Each parameter must be in JSON format: "
            "'{\"key\": \"param_name\", \"dataType\": \"String\", \"description\": \"param description\", \"isRequired\": true}' "
            "or for config parameters: "
            "'{\"key\": \"config_name\", \"dataType\": \"String\", \"description\": \"config description\", \"isRequired\": true, \"type\": \"config\", \"fromSecret\": false, \"value\": \"config_value\"}'"
        )

    return parameters


import unittest
from unittest.mock import patch

from pygeai.cli.commands.common import (
    get_llm_settings,
    get_welcome_data,
    get_messages,
    get_boolean_value,
    get_penalty_float_value,
    get_search_options,
    get_index_options,
    get_welcome_data_feature_list,
    get_welcome_data_example_prompt
)
from pygeai.core.common.exceptions import WrongArgumentError


class TestCommon(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_common.TestCommon
    """
    def test_get_llm_settings_all_values(self):
        result = get_llm_settings(
            provider_name="OpenAI",
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000
        )
        expected = {
            "providerName": "OpenAI",
            "modelName": "gpt-3.5-turbo",
            "temperature": 0.7,
            "maxTokens": 1000
        }
        self.assertEqual(result, expected)

    def test_get_llm_settings_partial_values(self):
        result = get_llm_settings(
            provider_name="OpenAI",
            model_name="",
            temperature=0.0,
            max_tokens=0
        )
        expected = {"providerName": "OpenAI"}
        self.assertEqual(result, expected)

    def test_get_welcome_data_full(self):
        feature_list = [{"title": "Feature1", "description": "Desc1"}]
        examples_list = [{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}]
        result = get_welcome_data(
            welcome_data_title="Welcome",
            welcome_data_description="Description",
            feature_list=feature_list,
            examples_prompt_list=examples_list
        )
        expected = {
            "title": "Welcome",
            "description": "Description",
            "features": [{"title": "Feature1", "description": "Desc1"}],
            "examplesPrompt": [{"title": "Example1", "description": "Desc1", "promptText": "Prompt1"}]
        }
        self.assertEqual(result, expected)

    def test_get_welcome_data_empty_lists(self):
        result = get_welcome_data(
            welcome_data_title="Welcome",
            welcome_data_description="Description",
            feature_list=[],
            examples_prompt_list=[]
        )
        expected = {
            "title": "Welcome",
            "description": "Description",
            "features": [],
            "examplesPrompt": []
        }
        self.assertEqual(result, expected)

    def test_get_welcome_data_invalid_feature(self):
        feature_list = [{"title": "Feature1"}]
        with self.assertRaises(KeyError):
            get_welcome_data(
                welcome_data_title="Welcome",
                welcome_data_description="Description",
                feature_list=feature_list,
                examples_prompt_list=[]
            )

    def test_get_welcome_data_invalid_example(self):
        examples_list = [{"title": "Example1", "description": "Desc1"}]
        with self.assertRaises(KeyError):
            get_welcome_data(
                welcome_data_title="Welcome",
                welcome_data_description="Description",
                feature_list=[],
                examples_prompt_list=examples_list
            )

    def test_get_messages_valid(self):
        message_list = [{"role": "user", "content": "Hello"}]
        result = get_messages(message_list)
        expected = [{"role": "user", "content": "Hello"}]
        self.assertEqual(result, expected)

    def test_get_messages_empty(self):
        result = get_messages([])
        self.assertEqual(result, [])

    def test_get_messages_invalid(self):
        message_list = [{"role": "user"}]
        with self.assertRaises(KeyError):
            get_messages(message_list)

    def test_get_boolean_value_valid(self):
        self.assertTrue(get_boolean_value("1"))
        self.assertFalse(get_boolean_value("0"))

    def test_get_boolean_value_invalid(self):
        with self.assertRaises(WrongArgumentError) as context:
            get_boolean_value("x")
        self.assertEqual(str(context.exception), "Possible values are 0 or 1, for off and on, respectively.")

    def test_get_penalty_float_value_valid(self):
        penalty_value = get_penalty_float_value("0.0")
        self.assertEqual(penalty_value, 0.0)

    def test_get_penalty_float_value_out_of_range(self):
        with self.assertRaises(WrongArgumentError) as context:
            get_penalty_float_value("2.5")
        self.assertEqual(str(context.exception), "If defined, penalty must be a number between -2.0 and 2.0")

    def test_get_penalty_float_value_invalid(self):
        with self.assertRaises(WrongArgumentError) as context:
            get_penalty_float_value("invalid")
        self.assertEqual(str(context.exception), "If defined, penalty must be a number between -2.0 and 2.0")

    def test_get_search_options_full(self):
        result = get_search_options(
            history_count=5,
            llm_cache=True,
            llm_frequency_penalty=0.5,
            llm_max_tokens=1000,
            llm_model_name="gpt-3.5-turbo",
            llm_n=1,
            llm_presence_penalty=0.2,
            llm_provider="OpenAI",
            llm_stream=False,
            llm_temperature=0.7,
            llm_top_p=0.9,
            llm_type={"key": "value"},
            llm_verbose=True,
            search_k=10,
            search_type="similarity",
            search_fetch_k=20,
            search_lambda=0.5,
            search_prompt="test prompt",
            search_return_source_documents=True,
            search_score_threshold=0.8,
            search_template="test template",
            retriever_type="vectorStore",
            retriever_search_type="hybrid",
            retriever_step="all",
            retriever_prompt="custom prompt"
        )
        self.assertEqual(result["history_count"], 5)
        self.assertEqual(result["llm"]["cache"], True)
        self.assertEqual(result["llm"]["frequencyPenalty"], 0.5)
        self.assertEqual(result["llm"]["maxTokens"], 1000)
        self.assertEqual(result["llm"]["modelName"], "gpt-3.5-turbo")
        self.assertEqual(result["search"]["k"], 10)
        self.assertEqual(result["search"]["type"], "similarity")
        self.assertEqual(result["retriever"]["type"], "vectorStore")
        self.assertEqual(result["retriever"]["prompt"], "custom prompt")

    def test_get_search_options_partial(self):
        result = get_search_options(
            history_count=0,
            llm_cache=False,
            llm_frequency_penalty=0.0,
            llm_max_tokens=0,
            llm_model_name="",
            llm_n=0,
            llm_presence_penalty=0.0,
            llm_provider="",
            llm_stream=False,
            llm_temperature=0.0,
            llm_top_p=0.0,
            llm_type={},
            llm_verbose=False,
            search_k=0,
            search_type="",
            search_fetch_k=0,
            search_lambda=0.0,
            search_prompt="",
            search_return_source_documents=False,
            search_score_threshold=0.0,
            search_template="",
            retriever_type="",
            retriever_search_type="",
            retriever_step="",
            retriever_prompt=""
        )
        self.assertIsNone(result["history_count"])
        self.assertEqual(result["llm"], {"cache": False, "stream": False, "verbose": False})
        self.assertEqual(result["search"], {"returnSourceDocuments": False})
        self.assertEqual(result["retriever"], {})

    def test_get_index_options_full(self):
        result = get_index_options(
            chunk_overlap=50,
            chunk_size=500,
            use_parent_document=True,
            child_k=5.0,
            child_chunk_size=100.0,
            child_chunk_overlap=20.0
        )
        expected = {
            "chunks": {"chunkOverlap": 50, "chunkSize": 500},
            "useParentDocument": True,
            "childDocument": {
                "childK": 5.0,
                "child": {"chunkSize": 100.0, "chunkOverlap": 20.0}
            }
        }
        self.assertEqual(result, expected)

    def test_get_index_options_partial(self):
        result = get_index_options(
            chunk_overlap=0,
            chunk_size=0,
            use_parent_document=False,
            child_k=0.0,
            child_chunk_size=0.0,
            child_chunk_overlap=0.0
        )
        expected = {
            "chunks": {"chunkOverlap": 0, "chunkSize": 0},
            "useParentDocument": False,
            "childDocument": {}
        }
        self.assertEqual(result, expected)

    def test_get_welcome_data_feature_list_valid_dict(self):
        feature_list = []
        option_arg = '{"title": "Feature1", "description": "Desc1"}'
        result = get_welcome_data_feature_list(feature_list, option_arg)
        expected = [{"title": "Feature1", "description": "Desc1"}]
        self.assertEqual(result, expected)

    def test_get_welcome_data_feature_list_valid_list(self):
        feature_list = []
        option_arg = '[{"title": "Feature1", "description": "Desc1"}]'
        result = get_welcome_data_feature_list(feature_list, option_arg)
        expected = [{"title": "Feature1", "description": "Desc1"}]
        self.assertEqual(result, expected)

    def test_get_welcome_data_feature_list_invalid_json(self):
        feature_list = []
        option_arg = "invalid_json"
        with self.assertRaises(WrongArgumentError) as context:
            get_welcome_data_feature_list(feature_list, option_arg)
        self.assertIn("Features must be a JSON string", str(context.exception))

    def test_get_welcome_data_example_prompt_valid_dict(self):
        examples_list = []
        option_arg = '{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}'
        result = get_welcome_data_example_prompt(examples_list, option_arg)
        expected = [{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}]
        self.assertEqual(result, expected)

    def test_get_welcome_data_example_prompt_valid_list(self):
        examples_list = []
        option_arg = '[{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}]'
        result = get_welcome_data_example_prompt(examples_list, option_arg)
        expected = [{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}]
        self.assertEqual(result, expected)

    def test_get_welcome_data_example_prompt_invalid_json(self):
        examples_list = []
        option_arg = "invalid_json"
        with self.assertRaises(WrongArgumentError) as context:
            get_welcome_data_example_prompt(examples_list, option_arg)
        self.assertIn("Example prompt text must be a JSON string", str(context.exception))

    def test_get_llm_settings_empty_values(self):
        result = get_llm_settings(
            provider_name="",
            model_name="",
            temperature=0.0,
            max_tokens=0
        )
        expected = {}
        self.assertEqual(result, expected)

    def test_get_penalty_float_value_boundary_values(self):
        self.assertEqual(get_penalty_float_value("2.0"), 2.0)
        self.assertEqual(get_penalty_float_value("-2.0"), -2.0)

    def test_get_search_options_only_history_count(self):
        result = get_search_options(
            history_count=3,
            llm_cache=False,
            llm_frequency_penalty=0.0,
            llm_max_tokens=0,
            llm_model_name="",
            llm_n=0,
            llm_presence_penalty=0.0,
            llm_provider="",
            llm_stream=False,
            llm_temperature=0.0,
            llm_top_p=0.0,
            llm_type={},
            llm_verbose=False,
            search_k=0,
            search_type="",
            search_fetch_k=0,
            search_lambda=0.0,
            search_prompt="",
            search_return_source_documents=False,
            search_score_threshold=0.0,
            search_template="",
            retriever_type="",
            retriever_search_type="",
            retriever_step="",
            retriever_prompt=""
        )
        self.assertEqual(result["history_count"], 3)
        self.assertEqual(result["llm"], {"cache": False, "stream": False, "verbose": False})
        self.assertEqual(result["search"], {"returnSourceDocuments": False})
        self.assertEqual(result["retriever"], {})

    def test_get_welcome_data_feature_list_append_to_existing(self):
        feature_list = [{"title": "Feature1", "description": "Desc1"}]
        option_arg = '{"title": "Feature2", "description": "Desc2"}'
        result = get_welcome_data_feature_list(feature_list, option_arg)
        expected = [
            {"title": "Feature1", "description": "Desc1"},
            {"title": "Feature2", "description": "Desc2"}
        ]
        self.assertEqual(result, expected)

    def test_get_welcome_data_example_prompt_append_to_existing(self):
        examples_list = [{"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"}]
        option_arg = '{"title": "Example2", "description": "Desc2", "prompt_text": "Prompt2"}'
        result = get_welcome_data_example_prompt(examples_list, option_arg)
        expected = [
            {"title": "Example1", "description": "Desc1", "prompt_text": "Prompt1"},
            {"title": "Example2", "description": "Desc2", "prompt_text": "Prompt2"}
        ]
        self.assertEqual(result, expected)
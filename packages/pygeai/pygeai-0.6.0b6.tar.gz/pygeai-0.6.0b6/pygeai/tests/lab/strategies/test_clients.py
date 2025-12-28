import unittest
from unittest.mock import patch
from json import JSONDecodeError
from pygeai.lab.strategies.clients import ReasoningStrategyClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestReasoningStrategyClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.strategies.test_clients.TestReasoningStrategyClient
    """
    def setUp(self):
        self.project_id = "project-123"
        self.client = ReasoningStrategyClient(api_key="test_key", base_url="https://test.url", project_id=self.project_id)
        self.reasoning_strategy_id = "strat-123"
        self.reasoning_strategy_name = "TestStrategy"

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_reasoning_strategies_success(self, mock_get):
        expected_response = {"strategies": [{"id": "strat-1", "name": "Strategy1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_reasoning_strategies(
            name="Strategy1",
            start="0",
            count="50",
            allow_external=True,
            access_scope="public"
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertEqual(params['name'], "Strategy1")
        self.assertEqual(params['start'], "0")
        self.assertEqual(params['count'], "50")
        self.assertTrue(params['allowExternal'])
        self.assertEqual(params['accessScope'], "public")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_reasoning_strategies_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Raw response text"
        mock_response.status_code = 500

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_reasoning_strategies()

        mock_get.assert_called_once()
        self.assertIn("Unable to list reasoning strategies", str(context.exception))

    def test_list_reasoning_strategies_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.client.list_reasoning_strategies(access_scope="invalid")

        self.assertEqual(str(context.exception), "Access scope must be either 'public' or 'private'.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_reasoning_strategy_success(self, mock_post):
        name = "TestStrategy"
        system_prompt = "Test system prompt"
        access_scope = "public"
        strategy_type = "addendum"
        localized_descriptions = [{"language": "english", "description": "Test description"}]
        automatic_publish = True
        expected_response = {"id": "strat-123", "name": name}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_reasoning_strategy(
            name=name,
            system_prompt=system_prompt,
            access_scope=access_scope,
            strategy_type=strategy_type,
            localized_descriptions=localized_descriptions,
            automatic_publish=automatic_publish
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        data = call_args[1]['data']['strategyDefinition']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['systemPrompt'], system_prompt)
        self.assertEqual(data['accessScope'], access_scope)
        self.assertEqual(data['type'], strategy_type)
        self.assertEqual(data['localizedDescriptions'], localized_descriptions)
        self.assertIn("automaticPublish=true", call_args[1]['endpoint'])
        headers = call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_reasoning_strategy_json_decode_error(self, mock_post):
        name = "TestStrategy"
        system_prompt = "Test system prompt"
        mock_response = mock_post.return_value
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Raw response text"
        mock_response.status_code = 500

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_reasoning_strategy(
                name=name,
                system_prompt=system_prompt
            )

        mock_post.assert_called_once()
        self.assertIn("Unable to create reasoning strategy", str(context.exception))

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_reasoning_strategy_success(self, mock_put):
        name = "UpdatedStrategy"
        system_prompt = "Updated prompt"
        access_scope = "private"
        strategy_type = "addendum"
        localized_descriptions = [{"language": "english", "description": "Updated description"}]
        automatic_publish = True
        upsert = False
        expected_response = {"id": self.reasoning_strategy_id, "name": name}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_reasoning_strategy(
            reasoning_strategy_id=self.reasoning_strategy_id,
            name=name,
            system_prompt=system_prompt,
            access_scope=access_scope,
            strategy_type=strategy_type,
            localized_descriptions=localized_descriptions,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        data = call_args[1]['data']['strategyDefinition']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['systemPrompt'], system_prompt)
        self.assertEqual(data['accessScope'], access_scope)
        self.assertEqual(data['type'], strategy_type)
        self.assertEqual(data['localizedDescriptions'], localized_descriptions)
        self.assertIn("automaticPublish=true", call_args[1]['endpoint'])
        headers = call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_reasoning_strategy_json_decode_error(self, mock_put):
        name = "UpdatedStrategy"
        mock_response = mock_put.return_value
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Raw response text"
        mock_response.status_code = 500

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_reasoning_strategy(
                reasoning_strategy_id=self.reasoning_strategy_id,
                name=name
            )

        mock_put.assert_called_once()
        self.assertIn("Unable to update reasoning strategy", str(context.exception))

    def test_update_reasoning_strategy_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_reasoning_strategy(
                reasoning_strategy_id=self.reasoning_strategy_id,
                access_scope="invalid"
            )

        self.assertEqual(str(context.exception), "Access scope must be either 'public' or 'private'.")

    def test_update_reasoning_strategy_invalid_type(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_reasoning_strategy(
                reasoning_strategy_id=self.reasoning_strategy_id,
                strategy_type="invalid"
            )

        self.assertEqual(str(context.exception), "Type must be 'addendum'.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_reasoning_strategy_success_with_id(self, mock_get):
        expected_response = {"id": self.reasoning_strategy_id, "name": "TestStrategy"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_reasoning_strategy(
            reasoning_strategy_id=self.reasoning_strategy_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once()
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_reasoning_strategy_success_with_name(self, mock_get):
        expected_response = {"name": self.reasoning_strategy_name}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_reasoning_strategy(
            reasoning_strategy_name=self.reasoning_strategy_name
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_reasoning_strategy_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Raw response text"
        mock_response.status_code = 500

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_reasoning_strategy(
                reasoning_strategy_id=self.reasoning_strategy_id
            )

        mock_get.assert_called_once()
        self.assertIn("Unable to retrieve reasoning strategy", str(context.exception))

    def test_get_reasoning_strategy_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_reasoning_strategy()

        self.assertEqual(str(context.exception), "Either reasoning_strategy_id or reasoning_strategy_name must be provided.")


if __name__ == '__main__':
    unittest.main()

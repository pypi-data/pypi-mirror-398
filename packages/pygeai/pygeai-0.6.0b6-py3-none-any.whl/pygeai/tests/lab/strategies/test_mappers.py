import unittest
from pygeai.lab.strategies.mappers import ReasoningStrategyMapper
from pygeai.lab.models import ReasoningStrategy, LocalizedDescription, ReasoningStrategyList


class TestReasoningStrategyMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.strategies.test_mappers.TestReasoningStrategyMapper
    """

    def test_map_localized_descriptions_success(self):
        descriptions_data = [
            {"language": "english", "description": "English description"},
            {"language": "spanish", "description": "Descripción en español"}
        ]
        result = ReasoningStrategyMapper._map_localized_descriptions(descriptions_data)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], LocalizedDescription)
        self.assertEqual(result[0].language, "english")
        self.assertEqual(result[0].description, "English description")
        self.assertEqual(result[1].language, "spanish")
        self.assertEqual(result[1].description, "Descripción en español")

    def test_map_localized_descriptions_empty(self):
        descriptions_data = []
        result = ReasoningStrategyMapper._map_localized_descriptions(descriptions_data)

        self.assertEqual(len(result), 0)
        self.assertIsInstance(result, list)

    def test_map_to_reasoning_strategy_success_flat_data(self):
        data = {
            "name": "TestStrategy",
            "systemPrompt": "Test system prompt",
            "accessScope": "private",
            "type": "addendum",
            "localizedDescriptions": [
                {"language": "english", "description": "Test description"}
            ],
            "id": "strategy-123"
        }
        result = ReasoningStrategyMapper.map_to_reasoning_strategy(data)

        self.assertIsInstance(result, ReasoningStrategy)
        self.assertEqual(result.name, "TestStrategy")
        self.assertEqual(result.system_prompt, "Test system prompt")
        self.assertEqual(result.access_scope, "private")
        self.assertEqual(result.type, "addendum")
        self.assertEqual(len(result.localized_descriptions), 1)
        self.assertIsInstance(result.localized_descriptions[0], LocalizedDescription)
        self.assertEqual(result.id, "strategy-123")

    def test_map_to_reasoning_strategy_success_nested_data(self):
        data = {
            "strategyDefinition": {
                "name": "NestedStrategy",
                "systemPrompt": "Nested prompt",
                "accessScope": "public",
                "type": "addendum",
                "localizedDescriptions": [
                    {"language": "english", "description": "Nested description"}
                ],
                "id": "nested-123"
            }
        }
        result = ReasoningStrategyMapper.map_to_reasoning_strategy(data)

        self.assertIsInstance(result, ReasoningStrategy)
        self.assertEqual(result.name, "NestedStrategy")
        self.assertEqual(result.system_prompt, "Nested prompt")
        self.assertEqual(result.access_scope, "public")
        self.assertEqual(result.type, "addendum")
        self.assertEqual(len(result.localized_descriptions), 1)
        self.assertEqual(result.id, "nested-123")

    def test_map_to_reasoning_strategy_no_localized_descriptions(self):
        data = {
            "name": "SimpleStrategy",
            "systemPrompt": "Simple prompt",
            "accessScope": "private",
            "type": "addendum",
            "id": "simple-123"
        }
        result = ReasoningStrategyMapper.map_to_reasoning_strategy(data)

        self.assertIsInstance(result, ReasoningStrategy)
        self.assertEqual(result.name, "SimpleStrategy")
        self.assertEqual(result.localized_descriptions, None)

    def test_map_to_reasoning_strategy_list_success_with_list(self):
        data = [
            {"name": "Strategy1", "systemPrompt": "Prompt1", "accessScope": "private", "type": "addendum"},
            {"name": "Strategy2", "systemPrompt": "Prompt2", "accessScope": "public", "type": "addendum"}
        ]
        result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(data)

        self.assertIsInstance(result, ReasoningStrategyList)
        self.assertEqual(len(result.strategies), 2)
        self.assertIsInstance(result.strategies[0], ReasoningStrategy)
        self.assertEqual(result.strategies[0].name, "Strategy1")
        self.assertEqual(result.strategies[1].name, "Strategy2")

    def test_map_to_reasoning_strategy_list_success_with_dict(self):
        data = {
            "strategies": [
                {"name": "Strategy1", "systemPrompt": "Prompt1", "accessScope": "private", "type": "addendum"},
                {"name": "Strategy2", "systemPrompt": "Prompt2", "accessScope": "public", "type": "addendum"}
            ]
        }
        result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(data)

        self.assertIsInstance(result, ReasoningStrategyList)
        self.assertEqual(len(result.strategies), 2)
        self.assertIsInstance(result.strategies[0], ReasoningStrategy)
        self.assertEqual(result.strategies[0].name, "Strategy1")
        self.assertEqual(result.strategies[1].name, "Strategy2")

    def test_map_to_reasoning_strategy_list_empty(self):
        data = {"strategies": []}
        result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(data)

        self.assertIsInstance(result, ReasoningStrategyList)
        self.assertEqual(len(result.strategies), 0)

    def test_map_to_reasoning_strategy_list_empty_data(self):
        data = {}
        result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(data)

        self.assertIsInstance(result, ReasoningStrategyList)
        self.assertEqual(len(result.strategies), 0)


from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ReasoningStrategy
from pygeai.core.common.exceptions import APIError

ai_lab_manager: AILabManager

class TestAILabGetReasoningStrategyIntegration(TestCase):   

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.strategy_id = "0a3b039e-25bd-4cf9-ad67-7af2b654874b"
        self.strategy_name = "Chain of Thought"

    def __get_reasoning_strategy(self, strategy_id = None, strategy_name = None):
        return self.ai_lab_manager.get_reasoning_strategy(
            reasoning_strategy_id= strategy_id if strategy_id is not None else self.strategy_id,
            reasoning_strategy_name=strategy_name if strategy_name is not None else self.strategy_name
        )

    def test_get_reasoning_strategy_by_id(self):
        strategy = self.__get_reasoning_strategy(strategy_name="")

        self.assertIsInstance(strategy, ReasoningStrategy, "Expected a reasoning strategy")
        self.assertEqual(strategy.id, self.strategy_id, "Expected reasoning strategy ID to match")


    def test_get_reasoning_strategy_by_name(self):
        strategy = self.__get_reasoning_strategy(strategy_id="")
        
        self.assertIsInstance(strategy, ReasoningStrategy, "Expected a reasoning strategy")
        self.assertEqual(
            strategy.name, 
            self.strategy_name,
            "Expected reasoning strategy name to match"
        )


    def test_get_reasoning_strategy_no_id_or_name(self):
        with self.assertRaises(Exception) as context:
            self.__get_reasoning_strategy(strategy_id="", strategy_name="")

        self.assertIn(
            "Either reasoning_strategy_id or reasoning_strategy_name must be provided.",
            str(context.exception),
            "Expected error message for missing id and name"
        )


    def test_get_reasoning_strategy_invalid_id(self):
        invalid_id = "invalid-id-1234"
        with self.assertRaises(APIError) as context:
            self.__get_reasoning_strategy(strategy_id=invalid_id)
        self.assertIn(
            f"Reasoning-Strategy not found (idOrName={invalid_id}",
            str(context.exception),
            "Expected an error for invalid reasoning strategy id"
        )


    def test_get_reasoning_strategy_invalid_name(self):
        invalid_name = "Nonexistent Strategy"
        with self.assertRaises(APIError) as context:
            self.__get_reasoning_strategy(strategy_id="", strategy_name=invalid_name)

        self.assertIn(
            f"Reasoning-Strategy not found (idOrName={invalid_name})",
            str(context.exception),
            "Expected an error for invalid reasoning strategy name"
        )

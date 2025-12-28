from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, ReasoningStrategyList
import copy

ai_lab_manager: AILabManager

class TestAILabListReasoningStrategiesIntegration(TestCase):    

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.filter_settings = FilterSettings(
            name="",
            start=0,
            count=100,
            allow_external=True,
            access_scope="public"
        )

    
    def __list_reasoning_strategies(self, filter_settings: FilterSettings = None):
        filter_settings = filter_settings if filter_settings is not None else self.filter_settings
        return self.ai_lab_manager.list_reasoning_strategies(filter_settings=filter_settings)
    
    
    def test_public_list_reasoning_strategies(self):
        result = self.__list_reasoning_strategies()

        self.assertIsInstance(result, ReasoningStrategyList, "Expected a list of reasoning strategies")
        for strategy in result.strategies:
            self.assertTrue(
                strategy.access_scope == "public",
                "Expected all reasoning strategies to be public"
            )


    def test_private_list_reasoning_strategies(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.access_scope = "private"
        result = self.__list_reasoning_strategies(filter_settings=filter_settings)

        self.assertIsInstance(result, ReasoningStrategyList, "Expected a list of reasoning strategies")
        for strategy in result.strategies:
            self.assertTrue(
                strategy.access_scope == "private",
                "Expected all reasoning strategies to be private"
            )


    def test_list_reasoning_strategies_small_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 2
        result = self.__list_reasoning_strategies(filter_settings=filter_settings)
        self.assertEqual(
            len(result), 2,
            "Expected list of reasoning strategies returned to be 2"
        )


    def test_list_reasoning_strategies_big_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 500
        result = self.__list_reasoning_strategies(filter_settings=filter_settings)
        self.assertLessEqual(
            len(result), 500,
            "Expected list of reasoning strategies returned to be 500 or less"
        )


    def test_list_reasoning_strategies_name_filter(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.name = "Chain of Thought"
        result = self.__list_reasoning_strategies(filter_settings=filter_settings)

        for strategy in result.strategies:
            self.assertIn(
                "Chain of Thought",
                strategy.name,
                "Expected reasoning strategy name to contain filter value"
            )

   
    def test_list_reasoning_strategies_invalid_scope(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.access_scope = "project"

        with self.assertRaises(ValueError) as exception:
            self.__list_reasoning_strategies(filter_settings=filter_settings)
        self.assertIn(
            "Access scope must be either 'public' or 'private'.",
            str(exception.exception),
            "The expected error about invalid scope was not returned"
        )

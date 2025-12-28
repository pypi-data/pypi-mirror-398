from unittest import TestCase
import unittest
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import LocalizedDescription, ReasoningStrategy
from pydantic import ValidationError
from pygeai.core.common.exceptions import APIError, APIResponseError

class TestAILabCreateReasoningStrategyIntegration(TestCase):    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.strategy_to_update = self.__load_strategy()

    
    def __load_strategy(self):
        self.random_str = str(uuid.uuid4())
        return ReasoningStrategy(
            id="323f5f94-5a3d-4717-89f3-3554a33c093f",
            name=f"UpdatedStrategy_{self.random_str}",
            system_prompt=f"Let's think step by step. {self.random_str}",
            access_scope="private",
            type="addendum",
            localized_descriptions=[
                LocalizedDescription(language="spanish", description=f"RSName spanish description {self.random_str}"),
                LocalizedDescription(language="english", description=f"RSName english description {self.random_str}"),
                LocalizedDescription(language="japanese", description=f"RSName japanese description {self.random_str}")
            ]
        )
    

    def __update_strategy(self, strategy=None, upsert = False):
        """
        Helper to create a reasoning strategy using ai_lab_manager.
        """
        return self.ai_lab_manager.update_reasoning_strategy(
            strategy=self.strategy_to_update if strategy is None else strategy,
            upsert=upsert
        )
    

    def test_update_strategy_full_data(self):
        self.updated_strategy = self.__update_strategy()

        self.assertEqual(self.updated_strategy.name, self.strategy_to_update.name)
        self.assertEqual(self.updated_strategy.system_prompt, self.strategy_to_update.system_prompt)

        for locale in self.updated_strategy.localized_descriptions:
            self.assertIn(
                self.random_str, 
                locale.description,
                "Expected the localized description to be updated correctly"
            )


    def test_update_strategy_no_name(self):  
        self.strategy_to_update.name = None

        with self.assertRaises(APIError) as exception:
            self.__update_strategy()
        self.assertIn(
            "ReasoningStrategy name cannot be empty",
            str(exception.exception),
            "The expected error about empty name was not returned"
        )
    

    def test_update_strategy_no_system_prompt(self):
        self.strategy_to_update.system_prompt = None
        
        with self.assertRaises(APIError) as exception:
            self.__update_strategy()
        self.assertIn(
            "ReasoningStrategy template or systemPrompt are required.",
            str(exception.exception),
            "The expected error about empty system_prompt was not returned"
        )


    def test_update_strategy_no_public_name(self):
        self.strategy_to_update.access_scope = "public"
        with self.assertRaises(APIError) as exception:
            self.__update_strategy()
        self.assertIn(
            "ReasoningStrategy publicName is required for public strategies",
            str(exception.exception),
            "The expected error about missing public name was not returned"
        )


    def test_update_strategy_no_access_scope(self):
        self.strategy_to_update.access_scope = ""
        with self.assertRaises(ValueError) as exception:
            self.__update_strategy()
        self.assertIn(
            "Access scope must be either 'public' or 'private'",
            str(exception.exception),
            "The expected error about missing access scope was not returned"
        )

    
    def test_update_strategy_no_type(self):
        self.strategy_to_update.type = ""
        with self.assertRaises(ValueError) as exception:
            self.__update_strategy()
        self.assertIn(
            "Type must be 'addendum'",
            str(exception.exception),
            "The expected error about missing type was not returned"
        )


    def test_update_strategy_invalid_type(self):
        self.strategy_to_update.type = "strategy_type"
        
        with self.assertRaises(ValueError) as exception:
            self.__update_strategy()
        self.assertIn(
            "Type must be 'addendum'",
            str(exception.exception),
            "The expected error about missing type was not returned"
        )

    
    def test_update_strategy_no_localized_descriptions(self):
        self.strategy_to_update.localized_descriptions = []    
        updated_strategy = self.__update_strategy()
        self.assertIsNone(
            updated_strategy.localized_descriptions,
            "Expected no localized descriptions after update"
        )    

    @unittest.skip("Skipping upsert test to avoid creating new strategies during routine testing before having a cleanup mechanism.")
    def test_update_strategy_upsert(self):			
        new_id = str(uuid.uuid4())
        new_strategy = ReasoningStrategy(
            id=new_id,
            name=f"UpsertStrategy_{self.random_str}",
            system_prompt=f"Upsert system prompt {self.random_str}",
            access_scope="private",
            type="addendum",
            localized_descriptions=[
                LocalizedDescription(language="english", description=f"Upsert description {self.random_str}")
            ]
        )
        upserted_strategy = self.__update_strategy(strategy=new_strategy, upsert=True)
        self.assertEqual(upserted_strategy.id, new_id, "Expected the reasoning strategy to be created via upsert")
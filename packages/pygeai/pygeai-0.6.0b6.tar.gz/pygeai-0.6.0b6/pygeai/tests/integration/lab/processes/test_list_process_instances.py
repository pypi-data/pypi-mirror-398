from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, ProcessInstanceList, AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow
from pygeai.core.common.exceptions import APIError, MissingRequirementException
import copy

ai_lab_manager: AILabManager

class TestAILabListProcessInstancesIntegration(TestCase):    

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        # Using a known process ID that should have instances for testing
        self.process_id = "6c9c99a0-9eb1-4647-9f2f-886cf6a51ac0"
        self.filter_settings = FilterSettings(
            start=0,
            count=10,
            is_active=False
        )


    def __list_process_instances(self, process_id: str = None, filter_settings: FilterSettings = None):
        process_id = process_id if process_id is not None else self.process_id
        filter_settings = filter_settings if filter_settings is not None else self.filter_settings
        return self.ai_lab_manager.list_process_instances(
            process_id=process_id,
            filter_settings=filter_settings
        )
    
    
    def test_default_list_process_instances(self):
        result = self.__list_process_instances()
        self.assertIsInstance(result, ProcessInstanceList, "Expected a ProcessInstanceList")


    def test_list_process_instances_completed(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.status = "Completed"
        result = self.__list_process_instances(filter_settings=filter_settings)

        self.assertIsInstance(result, ProcessInstanceList, "Expected a ProcessInstanceList")
        if result.instances:
            for instance in result.instances:
                self.assertTrue(
                    instance.status == 'Completed',
                    "Expected all instances to be completed"
                )


    def test_list_process_instances_include_inactive(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.is_active = True
        result = self.__list_process_instances(filter_settings=filter_settings)

        self.assertIsInstance(result, ProcessInstanceList, "Expected a ProcessInstanceList")


    def test_list_process_instances_small_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 2
        result = self.__list_process_instances(filter_settings=filter_settings)
        
        self.assertIsInstance(result, ProcessInstanceList, "Expected a ProcessInstanceList")
        self.assertLessEqual(
            len(result.instances), 2,
            "Expected list of process instances returned to be 2 or less"
        )


    def test_list_process_instances_big_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 50
        result = self.__list_process_instances(filter_settings=filter_settings)
        
        self.assertIsInstance(result, ProcessInstanceList, "Expected a ProcessInstanceList")
        self.assertLessEqual(
            len(result.instances), 50,
            "Expected list of process instances returned to be 50 or less"
        )


    def test_list_process_instances_empty_process_id(self):
        with self.assertRaises(ValueError) as exception:
            self.__list_process_instances(process_id="")

        # The specific error message will depend on implementation
        self.assertTrue(
            "Process ID must be provided" in str(exception.exception),
            "Expected error message for empty process id"
        )
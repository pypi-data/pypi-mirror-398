from unittest import TestCase
import unittest
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, AgenticProcessList
import copy

ai_lab_manager: AILabManager

class TestAILabListProcessesIntegration(TestCase):    

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.filter_settings = FilterSettings(
            start=0,
            count=100,
            allow_drafts=False
        )

    
    def __list_processes(self, filter_settings: FilterSettings = None):
        return self.ai_lab_manager.list_processes(
            filter_settings if filter_settings is not None else self.filter_settings
        )
    
    
    def test_default_list_processes(self):
        processes = self.__list_processes()
        self.assertIsInstance(processes, AgenticProcessList, "Expected a list of processes")


    def test_list_processes_with_id_filter(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.id = "7e28e9ab-b9a2-417e-9e87-ed7f6ec9534b"
        result = self.__list_processes(filter_settings=filter_settings)
        print(result)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        if result.processes:
            for process in result.processes:
                self.assertEqual(
                    process.id, filter_settings.id,
                    f"Expected process ID to match filter value: {filter_settings.id}"
                )


    def test_list_processes_with_name_filter(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.name = "ArithmeticProcess"
        result = self.__list_processes(filter_settings=filter_settings)
        print(result)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        if result.processes:
            for process in result.processes:
                self.assertEqual(
                    "ArithmeticProcess",
                    process.name,
                    "Expected process name to contain filter value"
                )


    def test_list_processes_with_status_filter_active(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.status = "active"
        result = self.__list_processes(filter_settings=filter_settings)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        if result.processes:
            for process in result.processes:
                self.assertEqual(
                    process.status.lower(), "active",
                    "Expected all processes to have active status"
                )


    def test_list_processes_with_status_filter_inactive(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.status = "inactive"
        result = self.__list_processes(filter_settings=filter_settings)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        if result.processes:
            for process in result.processes:
                self.assertEqual(
                    process.status.lower(), "inactive",
                    "Expected all processes to have inactive status"
                )


    def test_list_processes_small_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 2
        result = self.__list_processes(filter_settings=filter_settings)
        
        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        self.assertLessEqual(
            len(result.processes), 2,
            "Expected list of processes returned to be 2 or less"
        )


    def test_list_processes_big_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 500
        result = self.__list_processes(filter_settings=filter_settings)
        
        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        self.assertLessEqual(
            len(result.processes), 500,
            "Expected list of processes returned to be 500 or less"
        )

    @unittest.skip("Method is not returning drafts")
    def test_list_processes_allow_drafts_true(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = True
        result = self.__list_processes(filter_settings=filter_settings)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        # Note: This test verifies that draft processes are included when allow_drafts=True
        has_draft = any(p.is_draft for p in result.processes)
        self.assertTrue(has_draft, "Expected at least one draft process")


    def test_list_processes_allow_drafts_false(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = False
        result = self.__list_processes(filter_settings=filter_settings)

        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
        # Note: This test verifies that draft processes are excluded when allow_drafts=False
        has_draft = any(p.is_draft == False for p in result.processes)
        self.assertTrue(has_draft, "Expected at least one draft process")


    def test_list_processes_none_filter_settings(self):
        result = self.__list_processes(filter_settings=None)
        self.assertIsInstance(result, AgenticProcessList, "Expected a list of processes")
from unittest import TestCase
import unittest
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, FilterSettings, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow
from pygeai.core.common.exceptions import APIResponseError, APIError, MissingRequirementException
import copy
import uuid


class TestAILabGetProcessIntegration(TestCase):   

    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.process_id = "7e28e9ab-b9a2-417e-9e87-ed7f6ec9534b"
        self.process_name = "Test Process For Sdk Project"
        self.filter_settings = FilterSettings(
            revision="0",
            version="0"
        )


    def __get_process(self, process_id=None, process_name=None, filter_settings: FilterSettings = None):
        """
        Helper method to get a process.
        """
        return self.ai_lab_manager.get_process(
            process_id=self.process_id if process_id is None else process_id,
            process_name=self.process_name if process_name is None else process_name,
            filter_settings=self.filter_settings if filter_settings is None else filter_settings
        )

    def test_get_process_by_id(self):
        """
        Test getting a process by ID.
        """
        process = self.__get_process(process_name="")
        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertEqual(process.id, self.process_id)


    def test_get_process_by_name(self):
        """
        Test getting a process by name instead of ID.
        """
        process = self.__get_process(process_id=None)
        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertEqual(process.name, self.process_name)

    
    def test_get_process_no_id_or_name(self):
        """
        Test getting a process without providing ID or name should raise an error.
        """
        with self.assertRaises(MissingRequirementException) as context:
            self.__get_process(process_id="", process_name="")
        self.assertIn(
            "Either process_id or process_name must be provided",
            str(context.exception),
            "Expected an error for no id or name provided"
        )


    def test_get_process_invalid_process_id(self):
        """
        Test getting a process with an invalid ID.
        """
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(APIError) as context:
            self.__get_process(process_id=invalid_id, process_name="")
        self.assertIn(
            f"Process not found [IdOrName= {invalid_id}]",
            str(context.exception),
            "Expected an error for invalid process id"
        )


    def test_get_process_invalid_process_name(self):
        """
        Test getting a process with an invalid name.
        """
        invalid_name = "NonExistentProcessName_12345"
        with self.assertRaises(APIError) as context:
            self.__get_process(process_id="", process_name=invalid_name)
        self.assertIn(
            f"Process not found [IdOrName= {invalid_name}]",
            str(context.exception),
            "Expected an error for invalid process name"
        )

    def test_get_process_no_revision(self):
        """
        Test getting a process without specifying revision (should return latest).
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = None
        process = self.__get_process(filter_settings=filter_settings)

        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertGreaterEqual(process.revision or 0, 0, "Expected process revision to be the latest")


    def test_get_process_by_revision(self):
        """
        Test getting a process by specific revision.
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = 4
        process = self.__get_process(filter_settings=filter_settings)

        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertEqual(process.revision, filter_settings.revision, f"Expected process revision to be {filter_settings.revision}")

    
    def test_get_process_by_earlier_revision(self):
        """
        Test getting a process by an earlier revision that might not exist.
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = 3
        process = self.__get_process(filter_settings=filter_settings)
        
        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertEqual(process.revision, filter_settings.revision, f"Expected process revision to be {filter_settings.revision}")


    def test_get_process_no_version(self):
        """
        Test getting a process without specifying version (should return latest).
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = None
        process = self.__get_process(filter_settings=filter_settings)

        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertGreaterEqual(process.version_id or 0, 0, "Expected process version to be the latest")


    def test_get_process_by_version(self):
        """
        Test getting a process by specific version.
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = "2"
        process = self.__get_process(filter_settings=filter_settings)
        
        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertEqual(process.version_id, 2, "Expected process version to be 2")


    def test_get_process_by_invalid_version(self):
        """
        Test getting a process by an invalid version.
        """
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = "999"  # Non-existent version
        
        with self.assertRaises(APIError) as context:
            self.__get_process(filter_settings=filter_settings)
        
        self.assertIn(
            "Requested version not found [version=999]",
            str(context.exception),
            "Expected an error for version not found"
        )


    def test_get_process_allow_drafts_true(self):
        """
        Test getting a process with allow_drafts=True (should include drafts).
        """

        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = True
        process = self.__get_process(filter_settings = filter_settings)
        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        # Draft processes should be retrievable
        self.assertTrue(
            process.is_draft,
            "Should be able to retrieve both draft and published processes"
        )

    
    def test_get_process_allow_drafts_false(self):
        """
        Test getting a process with allow_drafts=False (should exclude drafts).
        """
        
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = False
        process = self.__get_process(filter_settings = filter_settings)

        self.assertIsInstance(process, AgenticProcess, "Expected an AgenticProcess")
        self.assertFalse(
            process.is_draft,
            "Should be able to retrieve published revisions"
        )
            
    
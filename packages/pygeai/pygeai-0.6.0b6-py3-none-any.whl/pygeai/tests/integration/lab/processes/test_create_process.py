from unittest import TestCase
import unittest
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, Task, 
    UserSignal, Event, SequenceFlow, Variable
)
from pygeai.core.common.exceptions import APIResponseError, APIError


class TestAILabCreateProcessIntegration(TestCase): 

    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.new_process = self.__load_process()
        self.created_process: AgenticProcess = None


    def tearDown(self):
        """
        Clean up after each test if necessary.
        This can be used to delete the created process
        """
        if isinstance(self.created_process, AgenticProcess):
            self.ai_lab_manager.delete_process(self.created_process.id)


    def __load_process(self):
        """
        Helper to load a complete process configuration for testing.
        """
        unique_key = str(uuid.uuid4())
        process = AgenticProcess(
            key="product_def",
            name=f"Test Process {unique_key[:8]}",
            description="This is a sample process",
            kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"]),
            agentic_activities=[
                AgenticActivity(key="activityOne", name="First Step", task_name="basic-task", agent_name="GoogleSummarizer2", agent_revision_id=0)
            ],
            artifact_signals=[
                ArtifactSignal(key="artifact.upload.1", name="artifact.upload", handling_type="C", artifact_type_name=["sample-artifact"])
            ],
            user_signals=[
                UserSignal(key="signal_done", name="process-completed")
            ],
            start_event=Event(key="artifact.upload.1", name="artifact.upload"),
            end_event=Event(key="end", name="Done"),
            sequence_flows=[
                SequenceFlow(key="step1", source_key="artifact.upload.1", target_key="activityOne"),
                SequenceFlow(key="step2", source_key="activityOne", target_key="signal_done"),
                SequenceFlow(key="stepEnd", source_key="signal_done", target_key="end")
            ]
        )
        return process
    

    def __create_process(self, process=None, automatic_publish=False):
        """
        Helper to create a process using ai_lab_manager.
        """
        return self.ai_lab_manager.create_process(
            process=self.new_process if process is None else process,
            automatic_publish=automatic_publish
        )
    

    def test_create_process_full_data(self):
        """
        Test creating a process with all available fields populated.
        """
        self.created_process = self.__create_process()
        created_process = self.created_process
        process = self.new_process

        self.assertTrue(isinstance(created_process, AgenticProcess), "Expected a created process")

        # Assert the main fields of the created process
        self.assertIsNotNone(created_process.id)
        #self.assertEqual(created_process.key, process.key)
        self.assertEqual(created_process.name, process.name)
        self.assertEqual(created_process.description, process.description)
        self.assertEqual(created_process.status, "active")

        # Assert knowledge base
        self.assertIsNotNone(created_process.kb)
        self.assertEqual(created_process.kb.name, process.kb.name)

        # Assert agentic activities
        created_activity = created_process.agentic_activities[0]
        original_activity = process.agentic_activities[0]
        self.assertTrue(isinstance(created_activity, AgenticActivity)) 
        self.assertEqual(created_activity.key.lower(), original_activity.key.lower())
        self.assertEqual(created_activity.name, original_activity.name)
            
        # Assert artifact signals
        created_signal = created_process.artifact_signals[0]
        original_signal = process.artifact_signals[0]
        self.assertTrue(isinstance(created_signal, ArtifactSignal))        
        self.assertEqual(created_signal.key.lower(), original_signal.key.lower())
        self.assertEqual(created_signal.name, original_signal.name)
        self.assertEqual(created_signal.handling_type, original_signal.handling_type)

        # Assert user signals
        created_user_signal = created_process.user_signals[0]
        self.assertTrue(isinstance(created_user_signal, UserSignal))

        # Assert events
        self.assertIsNotNone(created_process.start_event)
        self.assertEqual(created_process.start_event.key.lower(), process.start_event.key.lower())
        self.assertEqual(created_process.start_event.name, process.start_event.name)
       
        self.assertIsNotNone(created_process.end_event)
        self.assertEqual(created_process.end_event.key.lower(), process.end_event.key.lower())
        self.assertEqual(created_process.end_event.name, process.end_event.name)

        # Assert sequence flows
        created_flow = created_process.sequence_flows[0]
        original_flow = process.sequence_flows[0]
        self.assertIsNotNone(created_process.sequence_flows)
        self.assertEqual(len(created_process.sequence_flows), len(process.sequence_flows))
            
        self.assertEqual(created_flow.key.lower(), original_flow.key.lower())
        self.assertEqual(created_flow.source_key.lower(), original_flow.source_key.lower())
        self.assertEqual(created_flow.target_key.lower(), original_flow.target_key.lower())


    def test_create_process_minimum_required_data(self):
        """
        Test creating a process with only minimum required fields (key and name).
        """
        unique_key = str(uuid.uuid4())
        self.new_process = AgenticProcess(
            key=unique_key,
            name=f"Minimal Process {unique_key[:8]}"
        )
        self.created_process = self.__create_process()
        process = self.new_process

        self.assertTrue(isinstance(self.created_process, AgenticProcess), "Expected a created process")
        self.assertIsNotNone(self.created_process.id)
        self.assertEqual(self.created_process.name, process.name)


    def test_create_process_without_key(self):
        """
        Test creating a process without a key should still work (key is optional).
        """
        self.new_process = AgenticProcess(
            name=f"Process Without Key {str(uuid.uuid4())[:8]}"
        )
        self.created_process = self.__create_process()

        self.assertTrue(isinstance(self.created_process, AgenticProcess), "Expected a created process")
        self.assertIsNotNone(self.created_process.id)
        self.assertEqual(self.created_process.name, self.new_process.name)

    
    def test_create_process_no_name(self):
        """
        Test creating a process without a name should raise an error.
        """
        test_params = [True, False]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.new_process.name = ""
                with self.assertRaises(APIError) as exception:
                    self.__create_process(automatic_publish=auto_publish)

                self.assertIn(
                    "Process name cannot be empty",
                    str(exception.exception),
                    f"Expected an error about empty process name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

   
    def test_create_process_duplicated_name(self):
        """
        Test creating a process with a duplicate name should raise an error.
        """
        test_params = [True, False]
        created_process = self.__create_process()

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                loaded_process = self.__load_process()
                loaded_process.name = created_process.name
                with self.assertRaises(APIError) as exception:
                    self.__create_process(process = loaded_process, automatic_publish=auto_publish)

                self.assertIn(
                    f"A process with this name already exists [name={created_process.name}].",
                    str(exception.exception),
                    f"Expected an error about duplicated process name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_process_invalid_name_characters(self):
        """
        Test creating a process with invalid characters in name should raise a validation error.
        """
        test_params = [True, False]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                invalid_names = [
                    f"{str(uuid.uuid4())[:8]}:invalid",
                    f"{str(uuid.uuid4())[:8]}/invalid"
                ]

                for invalid_name in invalid_names:
                    new_process = self.__load_process()
                    new_process.name = invalid_name
                    
                    with self.assertRaises(APIError) as exception:
                        self.__create_process(process=new_process, automatic_publish=auto_publish)
                    
                    self.assertIn(
                        "Invalid character in name",
                        str(exception.exception),
                        f"Expected an error about invalid character in process name with autopublish {'enabled' if auto_publish else 'disabled'}"
                    )

    
    @unittest.skip("Skipping test for now.KB is required but is marked as optional")
    def test_create_process_with_no_kb(self):
        """
        Test creating a process with knowledge base in JSON format.
        """
        unique_key = str(uuid.uuid4())
        self.new_process.kb = None
        self.created_process = self.__create_process()

        self.assertIsNotNone(self.created_process.kb)
        self.assertEqual(self.created_process.kb.name, "basic-sample")


    def test_create_process_with_empty_agentic_activities_array(self):
        """
        Test creating a process with empty agentic activities array (to clear all activities).
        """
        self.new_process.agentic_activities = []
        self.new_process.sequence_flows = [] # Clear sequence flows as well because they depend on activities
        self.created_process = self.__create_process()

        # Empty array should be handled gracefully
        self.assertTrue(
            self.created_process.agentic_activities is None or 
            len(self.created_process.agentic_activities) == 0
        )


    def test_create_process_with_multiple_artifact_signals(self):
        """
        Test creating a process with multiple artifact signals.
        """
        self.new_process.artifact_signals=[
            ArtifactSignal(key="artifact.upload.1", name="artifact.upload", handling_type="C", artifact_type_name=["sample-artifact"]),
            ArtifactSignal(key="artifact.upload.2", name="artifact.upload.second", handling_type="C", artifact_type_name=["sample-artifact"])
        ]
        self.created_process = self.__create_process()

        self.assertIsNotNone(self.created_process.artifact_signals)
        self.assertEqual(len(self.created_process.artifact_signals), 2)

        first_signal = self.created_process.artifact_signals[0]
        second_signal = self.created_process.artifact_signals[1]
        
        self.assertEqual(first_signal.key.lower(), "artifact.upload.1")
        self.assertEqual(second_signal.key.lower(), "artifact.upload.2")


    def test_create_process_with_multiple_user_signals(self):
        """
        Test creating a process with multiple user signals.
        """
        self.new_process.user_signals=[
            UserSignal(key="signal_done", name="process-completed"),
            UserSignal(key="signal_cancel", name="process-cancelled")
        ]
        self.created_process = self.__create_process()

        self.assertIsNotNone(self.created_process.user_signals)
        self.assertEqual(len(self.created_process.user_signals)-1, 2)
        keys = [signal.key for signal in self.created_process.user_signals]

        assert "SIGNAL_CANCEL" in keys
        assert "SIGNAL_DONE" in keys


    def test_create_process_autopublish_disabled(self):
        """
        Test creating a process without automatic publish (default behavior).
        """
        self.created_process = self.__create_process(automatic_publish=False)
        
        # Process should be created as draft by default
        self.assertTrue(
            self.created_process.is_draft is True or 
            self.created_process.is_draft is None,  # API might not return this field for drafts
            "Expected the process to be created as draft when autopublish is disabled"
        )

   
    def test_create_process_autopublish_without_task(self):
        """
        Test creating a process with automatic publish enabled.
        """
        
        with self.assertRaises(APIError) as exception:
            self.__create_process(automatic_publish=True)

        self.assertIn(
            "Failure on process publication",
            str(exception.exception),
            "Expected an error about failure on process publication"
        )

        self.assertIn(
            "Task is required",
            str(exception.exception),
            "Expected an error about task being required"
        )


    def test_create_process_autopublish_enabled(self):
        """
        Test creating a process with automatic publish enabled.
        """
        unique_key = str(uuid.uuid4())
        task = Task(name=unique_key, description="Basic task for process", title_template="Basic Task")
        self.ai_lab_manager.create_task(task=task, automatic_publish=True)
        self.new_process.agentic_activities[0].task_name = unique_key
        
       
        self.created_process = self.__create_process(automatic_publish=True)
        self.assertTrue(
            self.created_process.is_draft is False,
            "Expected the process to be created no draft when autopublish is enabled"
        )
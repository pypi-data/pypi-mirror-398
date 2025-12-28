from unittest import TestCase
import uuid

from pydantic import ValidationError
from pygeai.core.common.exceptions import APIResponseError, APIError
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, Task, 
    UserSignal, Event, SequenceFlow, Variable
)


class TestAILabUpdateProcessIntegration(TestCase):  
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.process_to_update = self.__load_process()
        self.created_process: AgenticProcess = None
        self.updated_process: AgenticProcess = None


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
        self.random_str = str(uuid.uuid4())
        return AgenticProcess(
            id="3c071d2f-a044-4513-b2c0-6d27d9420693",
            key=f"sdk_project_updated_process_{self.random_str[:8]}",
            name=f"Updated Agentic Process {self.random_str[:8]}",
            description=f"Process updated for SDK testing purposes {self.random_str[:8]}",
            kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"]),
            agentic_activities=[
                AgenticActivity(key="activityOne", name="First Step Updated", task_name="basic-task", agent_name="GoogleSummarizer2", agent_revision_id=0)
            ],
            artifact_signals=[
                ArtifactSignal(key="artifact.upload.1", name="artifact.upload.updated", handling_type="C", artifact_type_name=["sample-artifact"])
            ],
            user_signals=[
                UserSignal(key="signal_done", name="process-completed-updated")
            ],
            start_event=Event(key="artifact.upload.1", name="artifact.upload.updated"),
            end_event=Event(key="end", name="Done Updated"),
            sequence_flows=[
                SequenceFlow(key="step1", source_key="artifact.upload.1", target_key="activityOne"),
                SequenceFlow(key="step2", source_key="activityOne", target_key="signal_done"),
                SequenceFlow(key="stepEnd", source_key="signal_done", target_key="end")
            ]
        )
    

    def __update_process(self, process: AgenticProcess = None, automatic_publish: bool = False, upsert: bool = False):
        """
        Helper method to update a process.
        """
        return self.ai_lab_manager.update_process(
            process=self.process_to_update if process is None else process,
            automatic_publish=automatic_publish,
            upsert=upsert
        )


    def test_update_process_all_fields_success(self):
        """
        Test updating a process with all available fields populated.
        """
        self.updated_process = self.__update_process()
        
        # Assertions
        self.assertEqual(self.updated_process.name, self.process_to_update.name)
        self.assertEqual(self.updated_process.description, self.process_to_update.description)
        
        # Assert knowledge base
        self.assertIsNotNone(self.updated_process.kb)
        self.assertEqual(self.updated_process.kb.name, self.process_to_update.kb.name)
        
        # Assert agentic activities
        self.assertIsNotNone(self.updated_process.agentic_activities)
        updated_activity = self.updated_process.agentic_activities[0]
        original_activity = self.process_to_update.agentic_activities[0]
        self.assertEqual(updated_activity.name, original_activity.name)

        # Assert artifact signals
        updated_signal = self.updated_process.artifact_signals[0]
        original_signal = self.process_to_update.artifact_signals[0]
        self.assertTrue(isinstance(updated_signal, ArtifactSignal))        
        self.assertEqual(updated_signal.key.lower(), original_signal.key.lower())
        self.assertEqual(updated_signal.name, original_signal.name)
        self.assertEqual(updated_signal.handling_type, original_signal.handling_type)
        
        # Assert that the process is in draft state after update
        self.assertTrue(self.updated_process.is_draft, "Expected process to be in draft state after update")


    def test_update_process_minimum_fields_success(self):
        """
        Test updating a process with minimum required fields (only name).
        """
        # Update with minimal data
        minimal_update = AgenticProcess(
            id=self.process_to_update.id,
            name=f"Minimal Updated Process {str(uuid.uuid4())[:8]}"
        )
        
        self.updated_process = self.__update_process(process=minimal_update)
        self.assertEqual(self.updated_process.name, minimal_update.name)


    def test_update_process_invalid_name(self):
        """
        Test updating a process with invalid characters in name.
        """
        test_params = [True, False]
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):                
                # Test invalid characters
                invalid_names = [
                    f"{self.process_to_update.name}:invalid",
                    f"{self.process_to_update.name}/invalid"
                ]

                for invalid_name in invalid_names:
                    with self.assertRaises(APIError) as exception:
                        self.process_to_update.name = invalid_name
                        self.__update_process(automatic_publish=auto_publish)
                    
                    self.assertIn(
                        f"Invalid character in name ({':' if ":" in invalid_name else "/"} is not allowed).",
                        str(exception.exception),                    
                        f"Expected an error about invalid character in process name with autopublish {'enabled' if auto_publish else 'disabled'}"
                    )


    def test_update_process_duplicated_name(self):
        """
        Test updating a process with a name that already exists.
        """
        test_params = [True, False]
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.process_to_update.name = "Test Process For Sdk Project"
                
                with self.assertRaises(APIError) as exception:
                    self.__update_process(automatic_publish=auto_publish)
                
                self.assertIn(
                    "A process with this name already exists",
                    str(exception.exception),                    
                    f"Expected an error about duplicated process name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )
    

    def test_update_process_no_name(self):
        """
        Test updating a process without providing a name.
        """
        test_params = [True, False]
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.process_to_update.name = ""
                
                with self.assertRaises(APIError) as exception:
                    self.__update_process(automatic_publish=auto_publish)
                
                self.assertIn(
                    "Process name cannot be empty",
                    str(exception.exception),                    
                    f"Expected an error when process name is empty with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_process_invalid_id(self):
        """
        Test updating a process with an invalid ID.
        """
        test_params = [True, False]
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
                self.process_to_update.id = invalid_id
                
                with self.assertRaises(APIError) as exception:
                    self.__update_process(automatic_publish=auto_publish)
                
                self.assertIn(
                    f"Process-Definition not found [IdOrName= {invalid_id}]",
                    str(exception.exception),                    
                    f"Expected an error when process id is invalid and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_process_no_id_invalid_name(self):
        """
        Test updating a process without ID.
        """
        test_params = [True, False]
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.process_to_update.id = ""
                
                with self.assertRaises(APIError) as exception:
                    self.__update_process(automatic_publish=auto_publish)
                
                self.assertIn(
                    f"Process-Definition not found [IdOrName= {self.process_to_update.name}]",
                    str(exception.exception),                    
                    f"Expected an error when process id is invalid and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_process_knowledge_base(self):
        """
        Test updating a process with different knowledge base configurations.
        """
        
        # Update with different KB
        self.process_to_update.kb = KnowledgeBase(name="updated-kb", artifact_type_name=["updated-artifact"])
        
        self.updated_process = self.__update_process()
        self.assertEqual(self.updated_process.kb.name, "updated-kb")
        self.assertEqual(self.updated_process.kb.artifact_type_name, ["updated-artifact"])


    def test_update_process_automatic_publish(self):
        """
        Test updating a process with automatic publish enabled.
        """        
        # Create a task for publishing
        unique_key = str(uuid.uuid4())
        task = Task(name=unique_key, description="Basic task for process", title_template="Basic Task")
        self.ai_lab_manager.create_task(task=task, automatic_publish=True)
        
        # Update process with task reference
        self.process_to_update.agentic_activities[0].task_name = unique_key
        
        self.updated_process = self.__update_process(automatic_publish=True)
        self.assertFalse(self.updated_process.is_draft, "Expected process to be published after update with automatic_publish=True")    


    def test_update_process_upsert_existing(self):
        """
        Test updating a process with upsert=True when process exists.
        """
        # Update existing process with upsert
        self.updated_process = self.__update_process(upsert=True)
        self.assertEqual(self.updated_process.name, self.process_to_update.name)
        self.assertEqual(self.updated_process.id, self.process_to_update.id)


    def test_update_process_upsert_new(self):
        """
        Test updating a process with upsert=True when process doesn't exist (should create new).
        """
        new_id = str(uuid.uuid4())
        self.process_to_update.id = new_id
        
        self.created_process = self.__update_process(upsert=True)
        self.assertEqual(self.created_process.name, self.process_to_update.name)
        self.assertIsNotNone(self.created_process.id)


    def test_update_process_by_name_instead_of_id(self):
        """
        Test updating a process by name instead of ID.
        """
        self.process = self.ai_lab_manager.get_process(self.process_to_update.id)
        self.process_to_update.id = None
        self.process_to_update.name = self.process.name
        self.process_to_update.description = "Updated via name instead of ID"
        
        
        self.updated_process = self.__update_process()
        self.assertEqual(self.updated_process.description, "Updated via name instead of ID")
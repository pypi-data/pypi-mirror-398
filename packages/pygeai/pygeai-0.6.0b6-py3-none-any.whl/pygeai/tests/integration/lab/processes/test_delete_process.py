from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow
from pygeai.core.common.exceptions import InvalidAPIResponseException, MissingRequirementException
from pygeai.core.base.responses import EmptyResponse

ai_lab_manager: AILabManager

class TestAILabDeleteProcessIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        

    def __create_process(self):
        """
        Helper to create a process with the current ai_lab_manager.
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

        return self.ai_lab_manager.create_process(
            process=process,
            automatic_publish=False
        )
    

    def __delete_process(self, process_id: str = None, process_name: str = None):
        return self.ai_lab_manager.delete_process(
            process_id=process_id,
            process_name=process_name
        )
    

    def test_delete_process_by_id(self):         
        created_process = self.__create_process()     
        deleted_process = self.__delete_process(process_id=created_process.id)
        print(deleted_process)

        self.assertEqual(
            deleted_process.content,
            "Process deleted successfully",
            "Expected confirmation message after deletion"            
        )


    def test_delete_process_by_name(self):         
        created_process = self.__create_process()     
        deleted_process = self.__delete_process(process_id="",process_name=created_process.name)

        self.assertEqual(
            deleted_process.content,
            "Process deleted successfully",
            "Expected confirmation message after deletion"            
        )


    def test_delete_process_no_parameters(self):
        with self.assertRaises(MissingRequirementException) as exception:
            self.__delete_process()
        self.assertIn(
            "Either process_id or process_name must be provided",
            str(exception.exception),
            "Expected error message for missing parameters"
        )


    def test_delete_process_invalid_process_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__delete_process(process_id=invalid_id)

        self.assertIn(
            f"Unable to delete process {invalid_id}",
            str(exception.exception),
            "Expected error message for invalid process id"
        )


    def test_delete_process_invalid_process_name(self):
        invalid_name = "NonExistentProcessName123"
        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__delete_process(process_name=invalid_name)

        self.assertIn(
            f"Unable to delete process {invalid_name}",
            str(exception.exception),
            "Expected error message for invalid process name"
        )
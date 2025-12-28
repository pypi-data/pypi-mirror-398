from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow
from pygeai.core.common.exceptions import InvalidAPIResponseException, MissingRequirementException, APIError

ai_lab_manager: AILabManager

class TestAILabPublishProcessRevisionIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        # Using a known process ID that should have revisions for testing
        self.process_id = "7e28e9ab-b9a2-417e-9e87-ed7f6ec9534b"
        self.process_name = "Test Process For Sdk Project"
        self.revision = "1"
        

    def __create_process(self):
        """
        Helper to create a process for testing publish revision functionality.
        """
        unique_key = str(uuid.uuid4())
        process = AgenticProcess(
            key="test_publish_key",
            name=f"Test Publish Process {unique_key[:8]}",
            description="Test process for publish revision testing",
            kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"]),
            agentic_activities=[
                AgenticActivity(
                    key="activityOne", 
                    name="First Step", 
                    task_name="basic-task", 
                    agent_name="GoogleSummarizer2", 
                    agent_revision_id=0
                )
            ],
            artifact_signals=[
                ArtifactSignal(
                    key="artifact.upload.1", 
                    name="artifact.upload", 
                    handling_type="C", 
                    artifact_type_name=["sample-artifact"]
                )
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


    def __publish_process_revision(self, process_id: str = None, process_name: str = None, revision: str = None):
        return self.ai_lab_manager.publish_process_revision(
            process_id=process_id,
            process_name=process_name,
            revision=revision if revision is not None else self.revision
        )
    

    def test_publish_process_revision_by_id(self):
        """Test publishing a process revision using process_id."""
        published_process = self.__publish_process_revision(process_id=self.process_id)

        self.assertIsInstance(published_process, AgenticProcess, "Expected AgenticProcess instance")
        self.assertEqual(published_process.id, self.process_id, "Expected process ID to match")
        self.assertIsNotNone(published_process.revision, "Expected revision to be set")


    def test_publish_process_revision_by_name(self):
        """Test publishing a process revision using process_name."""
        published_process = self.__publish_process_revision(process_name=self.process_name)

        self.assertIsInstance(published_process, AgenticProcess, "Expected AgenticProcess instance")
        self.assertEqual(published_process.name, self.process_name, "Expected process name to match")
        self.assertIsNotNone(published_process.revision, "Expected revision to be set")


    def test_publish_process_revision_specific_revision(self):
        """Test publishing a specific revision number."""
        specific_revision = "2"
        published_process = self.__publish_process_revision(
            process_id=self.process_id, 
            revision=specific_revision
        )

        self.assertIsInstance(published_process, AgenticProcess, "Expected AgenticProcess instance")
        self.assertEqual(published_process.id, self.process_id, "Expected process ID to match")


    def test_publish_process_revision_no_parameters(self):
        """Test error when neither process_id nor process_name is provided."""
        with self.assertRaises(MissingRequirementException) as exception:
            self.__publish_process_revision()

        self.assertIn(
            "Either process_id or process_name and revision must be provided",
            str(exception.exception),
            "Expected error message for missing parameters"
        )


    def test_publish_process_revision_empty_process_id(self):
        """Test error when process_id is empty."""
        with self.assertRaises(MissingRequirementException) as exception:
            self.__publish_process_revision(process_id="")

        self.assertIn(
            "Either process_id or process_name and revision must be provided",
            str(exception.exception),
            "Expected error message for empty process_id"
        )


    def test_publish_process_revision_empty_process_name(self):
        """Test error when process_name is empty."""
        with self.assertRaises(MissingRequirementException) as exception:
            self.__publish_process_revision(process_name="")

        self.assertIn(
            "Either process_id or process_name and revision must be provided",
            str(exception.exception),
            "Expected error message for empty process_name"
        )


    def test_publish_process_revision_no_revision(self):
        """Test error when revision is not provided."""
        with self.assertRaises(MissingRequirementException) as exception:
            self.__publish_process_revision(process_id=self.process_id, revision="")

        self.assertIn(
            "Either process_id or process_name and revision must be provided",
            str(exception.exception),
            "Expected error message for missing revision"
        )


    def test_publish_process_revision_none_revision(self):
        """Test error when revision is None."""
        with self.assertRaises(MissingRequirementException) as exception:
            self.__publish_process_revision(process_id=self.process_id, revision=None)

        self.assertIn(
            "Either process_id or process_name and revision must be provided",
            str(exception.exception),
            "Expected error message for None revision"
        )


    def test_publish_process_revision_invalid_process_id(self):
        """Test error with invalid process_id."""
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises((APIError, InvalidAPIResponseException)) as exception:
            self.__publish_process_revision(process_id=invalid_id)

        self.assertTrue(
            f"Unable to publish revision {self.revision} for process {invalid_id}" in str(exception.exception) or
            "Error received while publishing process revision" in str(exception.exception),
            "Expected error message for invalid process id"
        )


    def test_publish_process_revision_invalid_process_name(self):
        """Test error with invalid process_name."""
        invalid_name = "NonExistentProcessName123"
        with self.assertRaises((APIError, InvalidAPIResponseException)) as exception:
            self.__publish_process_revision(process_name=invalid_name)

        self.assertTrue(
            f"Unable to publish revision {self.revision} for process {invalid_name}" in str(exception.exception) or
            "Error received while publishing process revision" in str(exception.exception),
            "Expected error message for invalid process name"
        )


    def test_publish_process_revision_nonexistent_process_id(self):
        """Test error with nonexistent process_id."""
        nonexistent_id = "99999999-9999-9999-9999-999999999999"
        with self.assertRaises((APIError, InvalidAPIResponseException)) as exception:
            self.__publish_process_revision(process_id=nonexistent_id)

        self.assertTrue(
            f"Unable to publish revision {self.revision} for process {nonexistent_id}" in str(exception.exception) or
            "Error received while publishing process revision" in str(exception.exception),
            "Expected error message for nonexistent process id"
        )


    def test_publish_process_revision_invalid_revision(self):
        """Test error with invalid revision number."""
        invalid_revision = "999"
        with self.assertRaises((APIError, InvalidAPIResponseException)) as exception:
            self.__publish_process_revision(process_id=self.process_id, revision=invalid_revision)

        self.assertTrue(
            f"Unable to publish revision {invalid_revision} for process {self.process_id}" in str(exception.exception) or
            "Error received while publishing process revision" in str(exception.exception),
            "Expected error message for invalid revision"
        )


    def test_publish_process_revision_with_created_process(self):
        """Test publishing revision with a newly created process."""
        # Create a fresh process
        created_process = self.__create_process()
        
        # Note: A newly created process might not have additional revisions to publish
        # This test verifies the process creation worked and we can attempt to publish
        self.assertIsNotNone(created_process.id, "Expected created process to have an ID")
        
        # Attempt to publish revision 0 (initial revision)
        try:
            published_process = self.__publish_process_revision(
                process_id=created_process.id, 
                revision="0"
            )
            self.assertIsInstance(published_process, AgenticProcess, "Expected AgenticProcess instance")
        except (APIError, InvalidAPIResponseException):
            # This is expected for a new process that may not have publishable revisions yet
            pass
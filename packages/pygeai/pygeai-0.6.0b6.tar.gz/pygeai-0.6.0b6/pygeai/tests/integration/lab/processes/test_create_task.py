from unittest import TestCase
import unittest
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Task, Prompt, ArtifactTypeList, ArtifactType
from pygeai.core.common.exceptions import APIResponseError, APIError


class TestAILabCreateTaskIntegration(TestCase): 

    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.new_task = self.__load_task()
        self.created_task: Task = None


    def tearDown(self):
        """
        Clean up after each test if necessary.
        This can be used to delete the created task
        """
        if isinstance(self.created_task, Task):
            self.ai_lab_manager.delete_task(task_id=self.created_task.id)


    def __load_task(self):
        """
        Helper to load a complete task configuration for testing.
        """
        unique_key = str(uuid.uuid4())
        task = Task(
            name=f"test_task_{unique_key[:8]}",
            description=f"This is a sample task for testing 'test_task_{unique_key[:8]}'"
        )
        return task
    

    def __create_task(self, task=None, automatic_publish=False):
        """
        Helper to create a task using ai_lab_manager.
        """
        return self.ai_lab_manager.create_task(
            task=self.new_task if task is None else task,
            automatic_publish=automatic_publish
        )
    

    def test_create_task(self):
        """
        Test creating a task with all available fields populated.
        """
        self.created_task = self.__create_task()
        created_task = self.created_task
        task = self.new_task

        self.assertTrue(isinstance(created_task, Task), "Expected a created task")

        # Assert the main fields of the created task
        self.assertIsNotNone(created_task.id)
        self.assertEqual(created_task.name, task.name)
        self.assertEqual(created_task.description, task.description)

        # Assert revision and status
        self.assertEqual(self.created_task.revision, 1)
        self.assertEqual(self.created_task.status, 'active')


    def test_create_task_with_prompt_data(self):
        """
        Test creating a task with prompt data.
        """
        unique_key = str(uuid.uuid4())
        self.new_task = task = Task(
            name=f"test_task_{unique_key[:8]}",
            description=f"This is a sample task for testing 'test_task_{unique_key[:8]}'",
            title_template="Test Task: {{issue}}",
            prompt_data=Prompt(
                instructions="Analyze the provided data and generate a summary.",
                inputs=["input_data"],
                outputs=[]
            )
        )
        self.created_task = self.__create_task()
        
        # Assert prompt data
        self.assertIsNotNone(self.created_task.prompt_data)
        self.assertEqual(self.created_task.prompt_data.instructions, "Analyze the provided data and generate a summary.")
        self.assertEqual(self.created_task.prompt_data.inputs, ["input_data"])


    def test_create_task_with_custom_id(self):
        """
        Test creating a task with a custom ID.
        """
        unique_key = str(uuid.uuid4())
        custom_id = unique_key
        self.new_task = Task(
            name=f"task_with_custom_id_{unique_key[:8]}",
            id=custom_id
        )
        self.created_task = self.__create_task()

        self.assertTrue(isinstance(self.created_task, Task), "Expected a created task")
        self.assertEqual(self.created_task.id, custom_id)


    def test_create_task_empty_name(self):
        """
        Test creating a task with empty name should raise an error.
        """
        test_params = [True, False]

        for auto_publish in test_params:
            with self.subTest(auto_publish=auto_publish):
                self.new_task.name = ""
                with self.assertRaises((APIError, ValueError)) as exception:
                    self.__create_task(automatic_publish=auto_publish)

                self.assertTrue(
                    "Task name cannot be empty" in str(exception.exception),
                    f"Expected an error about empty task name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

   
    def test_create_task_duplicated_name(self):
        """
        Test creating a task with a duplicate name should raise an error.
        """
        test_params = [True, False]
        created_task = self.__create_task()

        for auto_publish in test_params:
            with self.subTest(auto_publish=auto_publish):
                loaded_task = self.__load_task()
                loaded_task.name = created_task.name
                with self.assertRaises(APIError) as exception:
                    self.__create_task(task=loaded_task, automatic_publish=auto_publish)

                self.assertIn(
                    "already exists",
                    str(exception.exception).lower(),
                    f"Expected an error about duplicated task name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_task_invalid_name_characters(self):
        """
        Test creating a task with invalid characters in name should raise a validation error.
        """
        test_params = [True, False]

        for auto_publish in test_params:
            with self.subTest(auto_publish=auto_publish):
                invalid_names = [
                    f"task_{str(uuid.uuid4())[:8]}:invalid",
                    f"task_{str(uuid.uuid4())[:8]}/invalid"
                ]

                for invalid_name in invalid_names:
                    new_task = self.__load_task()
                    new_task.name = invalid_name
                    
                    with self.assertRaises((APIError, ValueError)) as exception:
                        self.__create_task(task=new_task, automatic_publish=auto_publish)
                        
                    self.assertTrue(
                        f"Invalid character in name ({':' if ':' in invalid_name else '/'} is not allowed).",
                        f"Expected an error about invalid character in task name with autopublish {'enabled' if auto_publish else 'disabled'}"
                    )


    def test_create_task_autopublish_disabled(self):
        """
        Test creating a task without automatic publish (default behavior).
        """
        self.created_task = self.__create_task(automatic_publish=False)
        
        # Task should be created as draft by default
        self.assertTrue(
            self.created_task.is_draft is True or 
            self.created_task.is_draft is None,
            "Expected the task to be created as draft when autopublish is disabled"
        )


    def test_create_task_with_complex_prompt_data(self):
        """
        Test creating a task with complex prompt data including outputs.
        """
        unique_key = str(uuid.uuid4())
        self.new_task = Task(
            name=f"task_complex_prompt_{unique_key[:8]}",
            prompt_data=Prompt(
                instructions="Analyze the provided data and generate multiple outputs.",
                inputs=["input_data", "parameters"],
                outputs=[
                    {"key": "summary", "description": "Data summary"},
                    {"key": "analysis", "description": "Detailed analysis"}
                ]
            )
        )
        self.created_task = self.__create_task()

        self.assertIsNotNone(self.created_task.prompt_data)
        self.assertEqual(len(self.created_task.prompt_data.inputs), 2)
        self.assertIn("input_data", self.created_task.prompt_data.inputs)
        self.assertIn("parameters", self.created_task.prompt_data.inputs)
    
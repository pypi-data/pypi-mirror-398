import unittest
from unittest.mock import patch, Mock
from pygeai.cli.commands.rag import (
    show_help,
    get_assistants_from_project,
    get_assistant_detail,
    create_assistant,
    update_assistant,
    delete_assistant,
    list_documents,
    delete_all_documents,
    get_document_data,
    upload_document,
    delete_document,
    Option
)
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError


class TestRagCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_rag.TestRagCommands
    """
    def setUp(self):
        # Helper to create Option objects for testing
        self.mock_option = lambda name, value: (Option(name, [f"--{name}"], f"Description for {name}", True), value)

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.build_help_text')
    def test_show_help(self, mock_build_help, mock_write_stdout):
        mock_help_text = "Mocked help text"
        mock_build_help.return_value = mock_help_text

        show_help()

        mock_build_help.assert_called_once()
        mock_write_stdout.assert_called_once_with(mock_help_text)

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_get_assistants_from_project(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_assistants_from_project.return_value = {"assistants": ["assistant1", "assistant2"]}

        get_assistants_from_project()

        mock_instance.get_assistants_from_project.assert_called_once()
        mock_write_stdout.assert_called_once_with("RAG Assistants in project: \n{'assistants': ['assistant1', 'assistant2']}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_get_assistant_detail_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_assistant_data.return_value = {"name": "test_assistant"}
        option_list = [self.mock_option("name", "test_assistant")]

        get_assistant_detail(option_list)

        mock_instance.get_assistant_data.assert_called_once_with("test_assistant")
        mock_write_stdout.assert_called_once_with("Assistant detail: \n{'name': 'test_assistant'}")

    def test_get_assistant_detail_missing_name(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_assistant_detail(option_list)

        self.assertEqual(str(context.exception), "Cannot retrieve assistant detail without name")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    @patch('pygeai.cli.commands.rag.get_search_options')
    @patch('pygeai.cli.commands.rag.get_index_options')
    @patch('pygeai.cli.commands.rag.get_welcome_data')
    @patch('pygeai.cli.commands.rag.get_boolean_value')
    @patch('pygeai.cli.commands.rag.get_welcome_data_feature_list')
    @patch('pygeai.cli.commands.rag.get_welcome_data_example_prompt')
    def test_create_assistant_success(self, mock_example_prompt, mock_feature_list, mock_boolean, mock_welcome, mock_index, mock_search, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.create_assistant.return_value = {"name": "new_assistant"}
        mock_search.return_value = {"search": "options"}
        mock_index.return_value = {"index": "options"}
        mock_welcome.return_value = {"welcome": "data"}
        mock_boolean.return_value = True
        mock_feature_list.return_value = []
        mock_example_prompt.return_value = []
        option_list = [
            self.mock_option("name", "new_assistant"),
            self.mock_option("description", "A test assistant"),
            self.mock_option("llm_cache", "true"),
            self.mock_option("chunk_size", "1000"),
            self.mock_option("welcome_data_title", "Welcome Title")
        ]

        create_assistant(option_list)

        mock_instance.create_assistant.assert_called_once_with(
            name="new_assistant",
            description="A test assistant",
            template=None,
            search_options={"search": "options"},
            index_options={"index": "options"},
            welcome_data={"welcome": "data"}
        )
        mock_write_stdout.assert_called_once_with("New RAG Assistant: \n{'name': 'new_assistant'}")

    def test_create_assistant_missing_name(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            create_assistant(option_list)

        self.assertEqual(str(context.exception), "Cannot create RAG assistant without name")

    @patch('pygeai.cli.commands.rag.get_boolean_value')
    def test_create_assistant_invalid_mmr_options(self, mock_boolean):
        mock_boolean.return_value = True
        option_list = [
            self.mock_option("name", "test_assistant"),
            self.mock_option("search_type", "similarity"),
            self.mock_option("search_fetch_k", "5")
        ]

        with self.assertRaises(WrongArgumentError) as context:
            create_assistant(option_list)

        self.assertEqual(str(context.exception), "--fetch-k and --lambda are only valid for --search-type 'mmr'")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    @patch('pygeai.cli.commands.rag.get_search_options')
    @patch('pygeai.cli.commands.rag.get_welcome_data')
    @patch('pygeai.cli.commands.rag.get_boolean_value')
    @patch('pygeai.cli.commands.rag.get_welcome_data_feature_list')
    @patch('pygeai.cli.commands.rag.get_welcome_data_example_prompt')
    def test_update_assistant_success(self, mock_example_prompt, mock_feature_list, mock_boolean, mock_welcome, mock_search, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.update_assistant.return_value = {"name": "updated_assistant"}
        mock_search.return_value = {"search": "options"}
        mock_welcome.return_value = {"welcome": "data"}
        mock_boolean.return_value = True
        mock_feature_list.return_value = []
        mock_example_prompt.return_value = []
        option_list = [
            self.mock_option("name", "updated_assistant"),
            self.mock_option("status", "1"),
            self.mock_option("llm_cache", "true"),
            self.mock_option("welcome_data_title", "Welcome Title")
        ]

        update_assistant(option_list)

        mock_instance.update_assistant.assert_called_once_with(
            name="updated_assistant",
            status="1",
            description=None,
            template=None,
            search_options={"search": "options"},
            welcome_data={"welcome": "data"}
        )
        mock_write_stdout.assert_called_once_with("Updated RAG Assistant: \n{'name': 'updated_assistant'}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_delete_assistant_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_assistant.return_value = {"status": "deleted"}
        option_list = [self.mock_option("name", "test_assistant")]

        delete_assistant(option_list)

        mock_instance.delete_assistant.assert_called_once_with("test_assistant")
        mock_write_stdout.assert_called_once_with("Deleted assistant: \n{'status': 'deleted'}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_list_documents_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_documents.return_value = {"documents": ["doc1", "doc2"]}
        option_list = [
            self.mock_option("name", "test_assistant"),
            self.mock_option("skip", "5"),
            self.mock_option("count", "20")
        ]

        list_documents(option_list)

        mock_instance.get_documents.assert_called_once_with(name="test_assistant", skip=5, count=20)
        mock_write_stdout.assert_called_once_with("Assistant's documents: \n{'documents': ['doc1', 'doc2']}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_delete_all_documents_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_all_documents.return_value = {"status": "deleted"}
        option_list = [self.mock_option("name", "test_assistant")]

        delete_all_documents(option_list)

        mock_instance.delete_all_documents.assert_called_once_with(name="test_assistant")
        mock_write_stdout.assert_called_once_with("Deleted documents: \n{'status': 'deleted'}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_get_document_data_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.retrieve_document.return_value = {"id": "doc123"}
        option_list = [
            self.mock_option("name", "test_assistant"),
            self.mock_option("document_id", "doc123")
        ]

        get_document_data(option_list)

        mock_instance.retrieve_document.assert_called_once_with(name="test_assistant", document_id="doc123")
        mock_write_stdout.assert_called_once_with("Document detail: \n{'id': 'doc123'}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    @patch('pathlib.Path.is_file')
    def test_upload_document_success(self, mock_is_file, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.upload_document.return_value = {"status": "uploaded"}
        mock_is_file.return_value = False
        option_list = [
            self.mock_option("name", "test_assistant"),
            self.mock_option("file_path", "/path/to/file"),
            self.mock_option("upload_type", "multipart")
        ]

        upload_document(option_list)

        mock_instance.upload_document.assert_called_once_with(
            name="test_assistant",
            file_path="/path/to/file",
            upload_type="multipart",
            metadata={},
            content_type=None
        )
        mock_write_stdout.assert_called_once_with("Uploaded: \n{'status': 'uploaded'}")

    @patch('pygeai.cli.commands.rag.Console.write_stdout')
    @patch('pygeai.cli.commands.rag.RAGAssistantClient')
    def test_delete_document_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_document.return_value = {"status": "deleted"}
        option_list = [
            self.mock_option("name", "test_assistant"),
            self.mock_option("document_id", "doc123")
        ]

        delete_document(option_list)

        mock_instance.delete_document.assert_called_once_with(name="test_assistant", document_id="doc123")
        mock_write_stdout.assert_called_once_with("Deleted document: \n{'status': 'deleted'}")


import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pygeai.assistant.managers import AssistantManager
from pygeai.core.common.exceptions import MissingRequirementException, APIError
from pygeai.core.models import Assistant, TextAssistant, ChatAssistant, ChatWithDataAssistant, \
    ChatMessageList, AssistantRevision, ChatVariableList, LlmSettings, ChatToolList, ToolChoice, ChatMessage
from pygeai.assistant.rag.models import Document, UploadDocument, RAGAssistant
from pygeai.core.feedback.models import FeedbackRequest
from pygeai.core.responses import NewAssistantResponse, ChatResponse
from pygeai.assistant.rag.responses import DocumentListResponse
from pygeai.core.base.responses import EmptyResponse


class TestAssistantManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.test_managers.TestAssistantManager
    """
    def setUp(self):
        self.manager = AssistantManager(api_key="test_key", base_url="test_url", alias="test_alias")
        self.manager._AssistantManager__assistant_client = MagicMock()
        self.manager._AssistantManager__rag_client = MagicMock()
        self.manager._AssistantManager__chat_client = MagicMock()
        self.manager._AssistantManager__feedback_client = MagicMock()

    def test_get_assistant_data_by_id_success(self):
        mock_response = {"data": "assistant_data"}
        self.manager._AssistantManager__assistant_client.get_assistant_data.return_value = mock_response
        with patch('pygeai.assistant.managers.AssistantResponseMapper.map_to_assistant_response') as mock_mapper:
            mock_mapper.return_value = Assistant()

            result = self.manager.get_assistant_data(assistant_id="test_id", detail="summary")

            self.manager._AssistantManager__assistant_client.get_assistant_data.assert_called_once_with(
                assistant_id="test_id", detail="summary"
            )
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, Assistant)

    def test_get_assistant_data_by_name_success(self):
        mock_response = {"data": "rag_assistant_data"}
        self.manager._AssistantManager__rag_client.get_assistant_data.return_value = mock_response
        with patch('pygeai.assistant.managers.RAGAssistantMapper.map_to_rag_assistant') as mock_mapper:
            mock_mapper.return_value = RAGAssistant(name="test_name")

            result = self.manager.get_assistant_data(assistant_name="test_name")

            self.manager._AssistantManager__rag_client.get_assistant_data.assert_called_once_with(name="test_name")
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, RAGAssistant)

    def test_get_assistant_data_missing_parameters(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.manager.get_assistant_data()

        self.assertEqual(str(context.exception), "Either assistant_id or assistant_name must be defined to retrieve assistant data.")

    def test_create_chat_assistant_success(self):
        assistant = ChatAssistant(name="test_chat", prompt="test_prompt", description="test_desc")
        mock_response = {"data": "created_assistant"}
        self.manager._AssistantManager__assistant_client.create_assistant.return_value = mock_response
        with patch('pygeai.assistant.managers.AssistantResponseMapper.map_to_assistant_created_response') as mock_mapper:
            mock_mapper.return_value = NewAssistantResponse()

            result = self.manager.create_assistant(assistant)

            self.manager._AssistantManager__assistant_client.create_assistant.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, NewAssistantResponse)

    def test_create_rag_assistant_success(self):
        assistant = RAGAssistant(name="test_rag", description="test_desc")
        mock_response = {"data": "created_rag_assistant"}
        self.manager._AssistantManager__rag_client.create_assistant.return_value = mock_response
        with patch('pygeai.assistant.managers.RAGAssistantMapper.map_to_rag_assistant') as mock_mapper:
            mock_mapper.return_value = RAGAssistant(name="test_rag")

            result = self.manager.create_assistant(assistant)

            self.manager._AssistantManager__rag_client.create_assistant.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, RAGAssistant)

    def test_update_chat_assistant_success(self):
        assistant = ChatAssistant(id="test_id", name="test_chat", prompt="test_prompt")
        mock_response = {"data": "updated_assistant"}
        self.manager._AssistantManager__assistant_client.update_assistant.return_value = mock_response
        with patch('pygeai.assistant.managers.AssistantResponseMapper.map_to_assistant_created_response') as mock_mapper:
            mock_mapper.return_value = NewAssistantResponse()

            result = self.manager.update_assistant(assistant, action="saveNewRevision")

            self.manager._AssistantManager__assistant_client.update_assistant.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, NewAssistantResponse)

    def test_update_chat_assistant_invalid_action(self):
        assistant = ChatAssistant(id="test_id", name="test_chat", prompt="test_prompt")
        with self.assertRaises(ValueError) as context:
            self.manager.update_assistant(assistant, action="invalid_action")

        self.assertEqual(str(context.exception), "Valid actions are: 'save', 'saveNewRevision', 'savePublishNewRevision'")

    def test_delete_assistant_by_id_success(self):
        mock_response = "Assistant deleted successfully"
        self.manager._AssistantManager__assistant_client.delete_assistant.return_value = mock_response
        with patch('pygeai.assistant.managers.ResponseMapper.map_to_empty_response') as mock_mapper:
            mock_mapper.return_value = EmptyResponse()

            result = self.manager.delete_assistant(assistant_id="test_id")

            self.manager._AssistantManager__assistant_client.delete_assistant.assert_called_once_with(assistant_id="test_id")
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, EmptyResponse)

    def test_send_chat_request_success(self):
        assistant = ChatAssistant(name="test_chat")
        messages = ChatMessageList(messages=[ChatMessage(role="user", content="Hello")])
        mock_response = {"data": "chat_response"}
        self.manager._AssistantManager__assistant_client.send_chat_request.return_value = mock_response
        with patch('pygeai.assistant.managers.AssistantResponseMapper.map_to_chat_request_response') as mock_mapper:
            mock_mapper.return_value = ChatResponse()

            result = self.manager.send_chat_request(assistant, messages)

            self.manager._AssistantManager__assistant_client.send_chat_request.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, ChatResponse)

    def test_chat_completion_success(self):
        messages = ChatMessageList(messages=[ChatMessage(role="user", content="Hello")])
        llm_settings = LlmSettings(temperature=0.7, max_tokens=100)
        mock_response = {"data": "completion_response"}
        self.manager._AssistantManager__chat_client.chat_completion.return_value = mock_response
        with patch('pygeai.assistant.managers.AssistantResponseMapper.map_to_provider_response') as mock_mapper:
            mock_mapper.return_value = ChatResponse()

            result = self.manager.chat_completion(model="test_model", messages=messages, llm_settings=llm_settings)

            self.manager._AssistantManager__chat_client.chat_completion.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, ChatResponse)

    def test_get_document_list_success(self):
        mock_response = {"data": "document_list"}
        self.manager._AssistantManager__rag_client.get_documents.return_value = mock_response
        with patch('pygeai.assistant.managers.RAGAssistantMapper.map_to_document_list_response') as mock_mapper:
            mock_mapper.return_value = DocumentListResponse(count=1, documents=[])

            result = self.manager.get_document_list(name="test_name")

            self.manager._AssistantManager__rag_client.get_documents.assert_called_once_with(name="test_name", skip=0, count=10)
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, DocumentListResponse)

    def test_upload_document_success(self):
        assistant = RAGAssistant(name="test_name")
        document = UploadDocument(path="test_path", upload_type="multipart", content_type="application/pdf")
        mock_response = {"data": "uploaded_document"}
        self.manager._AssistantManager__rag_client.upload_document.return_value = mock_response
        with patch('pygeai.assistant.managers.RAGAssistantMapper.map_to_document') as mock_mapper:
            mock_mapper.return_value = Document(
                id="test_id",
                chunks="test_chunks",
                extension="pdf",
                index_status="indexed",
                url="test_url"
            )

            result = self.manager.upload_document(assistant, document)

            self.manager._AssistantManager__rag_client.upload_document.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, Document)

    def test_send_feedback_success(self):
        feedback = FeedbackRequest(request_id="test_request", origin="test_origin", answer_score=5)
        mock_response = "Feedback sent successfully"
        self.manager._AssistantManager__feedback_client.send_feedback.return_value = mock_response
        with patch('pygeai.assistant.managers.ResponseMapper.map_to_empty_response') as mock_mapper:
            mock_mapper.return_value = EmptyResponse()

            result = self.manager.send_feedback(feedback)

            self.manager._AssistantManager__feedback_client.send_feedback.assert_called_once()
            mock_mapper.assert_called_once_with(mock_response)
            self.assertIsInstance(result, EmptyResponse)

    def test_api_error_handling(self):
        mock_response = {"error": "API error occurred"}
        self.manager._AssistantManager__assistant_client.get_assistant_data.return_value = mock_response
        with patch('pygeai.assistant.managers.ErrorHandler.has_errors', return_value=True):
            with patch('pygeai.assistant.managers.ErrorHandler.extract_error', return_value="API error occurred"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_assistant_data(assistant_id="test_id")

                self.assertIn("Error received while retrieving assistant data by ID", str(context.exception))


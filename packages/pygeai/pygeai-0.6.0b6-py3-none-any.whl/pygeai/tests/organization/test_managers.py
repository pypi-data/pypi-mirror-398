import unittest
from unittest.mock import patch

from pygeai.core.base.mappers import ResponseMapper
from pygeai.core.common.exceptions import APIError
from pygeai.core.handlers import ErrorHandler
from pygeai.core.models import Project
from pygeai.core.base.responses import EmptyResponse
from pygeai.organization.managers import OrganizationManager
from pygeai.organization.mappers import OrganizationResponseMapper
from pygeai.organization.responses import AssistantListResponse, ProjectListResponse, ProjectDataResponse, \
    ProjectTokensResponse, ProjectItemListResponse


class TestOrganizationManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.test_managers.TestOrganizationManager
    """

    def setUp(self):
        self.manager = OrganizationManager()
        self.project = Project(
            id="123",
            name="Test Project",
            description="Test Description",
            email="test@example.com",
            usage_limit=None
        )
        self.error_response = {"errors": [{"id": 404, "description": "Project not found"}]}

    @patch("pygeai.organization.clients.OrganizationClient.get_assistant_list")
    def test_get_assistant_list(self, mock_get_assistant_list):
        mock_response = AssistantListResponse(assistants=[])
        mock_get_assistant_list.return_value = {}

        with patch.object(OrganizationResponseMapper, 'map_to_assistant_list_response', return_value=mock_response):
            response = self.manager.get_assistant_list(detail="summary")

        self.assertIsInstance(response, AssistantListResponse)
        self.assertEqual(response.assistants, [])
        mock_get_assistant_list.assert_called_once_with(detail="summary")

    @patch("pygeai.organization.clients.OrganizationClient.get_assistant_list")
    def test_get_assistant_list_error(self, mock_get_assistant_list):
        mock_get_assistant_list.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Project not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_assistant_list(detail="summary")

        self.assertIn("Error received while retrieving assistant list", str(context.exception))
        mock_get_assistant_list.assert_called_once_with(detail="summary")

    @patch("pygeai.organization.clients.OrganizationClient.get_project_list")
    def test_get_project_list(self, mock_get_project_list):
        mock_response = ProjectListResponse(projects=[])
        mock_get_project_list.return_value = {}

        with patch.object(OrganizationResponseMapper, 'map_to_project_list_response', return_value=mock_response):
            response = self.manager.get_project_list(detail="summary")

        self.assertIsInstance(response, ProjectListResponse)
        self.assertEqual(response.projects, [])
        mock_get_project_list.assert_called_once_with(detail="summary", name=None)

    @patch("pygeai.organization.clients.OrganizationClient.get_project_list")
    def test_get_project_list_error(self, mock_get_project_list):
        mock_get_project_list.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Project not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_project_list(detail="summary")

        self.assertIn("Error received while retrieving project list", str(context.exception))
        mock_get_project_list.assert_called_once_with(detail="summary", name=None)

    @patch("pygeai.organization.clients.OrganizationClient.get_project_data")
    def test_get_project_data(self, mock_get_project_data):
        mock_response = ProjectDataResponse(project=self.project)
        mock_get_project_data.return_value = {}

        with patch.object(OrganizationResponseMapper, 'map_to_project_data', return_value=mock_response):
            response = self.manager.get_project_data("123")

        self.assertIsInstance(response, ProjectDataResponse)
        self.assertEqual(response.project.name, "Test Project")
        mock_get_project_data.assert_called_once_with(project_id="123")

    @patch("pygeai.organization.clients.OrganizationClient.get_project_data")
    def test_get_project_data_error_handling(self, mock_get_project_data):
        mock_get_project_data.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Project not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_project_data("invalid_id")

        self.assertIn("Error received while retrieving project data", str(context.exception))
        mock_get_project_data.assert_called_once_with(project_id="invalid_id")

    @patch("pygeai.organization.clients.OrganizationClient.create_project")
    def test_create_project(self, mock_create_project):
        mock_response = ProjectDataResponse(project=self.project)
        mock_create_project.return_value = {}

        with patch.object(OrganizationResponseMapper, 'map_to_project_data', return_value=mock_response):
            response = self.manager.create_project(self.project)

        self.assertIsInstance(response, ProjectDataResponse)
        self.assertEqual(response.project.name, "Test Project")
        mock_create_project.assert_called_once_with(
            name=self.project.name,
            email=self.project.email,
            description=self.project.description,
            usage_limit=None
        )

    @patch("pygeai.organization.clients.OrganizationClient.create_project")
    def test_create_project_error(self, mock_create_project):
        mock_create_project.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Project creation failed"):
                with self.assertRaises(APIError) as context:
                    self.manager.create_project(self.project)

        self.assertIn("Error received while creating project", str(context.exception))
        mock_create_project.assert_called_once_with(
            name=self.project.name,
            email=self.project.email,
            description=self.project.description,
            usage_limit=None
        )

    @patch("pygeai.organization.clients.OrganizationClient.update_project")
    def test_update_project(self, mock_update_project):
        updated_project = Project(
            id="123",
            name="Updated Project",
            description="An updated test project",
            email="test@example.com",
            usage_limit=None
        )
        mock_response = ProjectDataResponse(project=updated_project)
        mock_update_project.return_value = {}

        with patch.object(OrganizationResponseMapper, 'map_to_project_data', return_value=mock_response):
            response = self.manager.update_project(updated_project)

        self.assertIsInstance(response, ProjectDataResponse)
        self.assertEqual(response.project.name, "Updated Project")
        mock_update_project.assert_called_once_with(
            project_id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description
        )

    @patch("pygeai.organization.clients.OrganizationClient.update_project")
    def test_update_project_error(self, mock_update_project):
        updated_project = Project(
            id="123",
            name="Updated Project",
            description="An updated test project",
            email="test@example.com",
            usage_limit=None
        )
        mock_update_project.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Update failed"):
                with self.assertRaises(APIError) as context:
                    self.manager.update_project(updated_project)

        self.assertIn("Error received while updating project", str(context.exception))
        mock_update_project.assert_called_once_with(
            project_id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description
        )

    @patch("pygeai.organization.clients.OrganizationClient.delete_project")
    def test_delete_project(self, mock_delete_project):
        mock_response = EmptyResponse(content={})
        mock_delete_project.return_value = {}

        with patch.object(ResponseMapper, 'map_to_empty_response', return_value=mock_response):
            response = self.manager.delete_project("123")

        self.assertIsInstance(response, EmptyResponse)
        self.assertEqual(response.content, {})
        mock_delete_project.assert_called_once_with(project_id="123")

    @patch("pygeai.organization.clients.OrganizationClient.delete_project")
    def test_delete_project_error_handling(self, mock_delete_project):
        mock_delete_project.return_value = {"errors": [{"id": 403, "description": "Permission denied"}]}

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Permission denied"):
                with self.assertRaises(APIError) as context:
                    self.manager.delete_project("invalid_id")

        self.assertIn("Error received while deleting project", str(context.exception))
        mock_delete_project.assert_called_once_with(project_id="invalid_id")

    @patch("pygeai.organization.clients.OrganizationClient.get_project_tokens")
    def test_get_project_tokens(self, mock_get_project_tokens):
        mock_response = ProjectTokensResponse(tokens=[])
        mock_get_project_tokens.return_value = {"tokens": []}

        with patch.object(OrganizationResponseMapper, 'map_to_token_list_response', return_value=mock_response):
            response = self.manager.get_project_tokens("123")

        self.assertIsInstance(response, ProjectTokensResponse)
        self.assertEqual(response.tokens, [])
        mock_get_project_tokens.assert_called_once_with(project_id="123")

    @patch("pygeai.organization.clients.OrganizationClient.get_project_tokens")
    def test_get_project_tokens_error(self, mock_get_project_tokens):
        mock_get_project_tokens.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Project not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_project_tokens("invalid_id")

        self.assertIn("Error received while retrieving project tokens", str(context.exception))
        mock_get_project_tokens.assert_called_once_with(project_id="invalid_id")

    @patch("pygeai.organization.clients.OrganizationClient.export_request_data")
    def test_export_request_data(self, mock_export_request_data):
        mock_response = ProjectItemListResponse(items=[])
        mock_export_request_data.return_value = {"items": []}

        with patch.object(OrganizationResponseMapper, 'map_to_item_list_response', return_value=mock_response):
            response = self.manager.export_request_data(assistant_name="assistant1", status="completed", skip=10, count=5)

        self.assertIsInstance(response, ProjectItemListResponse)
        self.assertEqual(response.items, [])
        mock_export_request_data.assert_called_once_with(
            assistant_name="assistant1",
            status="completed",
            skip=10,
            count=5
        )

    @patch("pygeai.organization.clients.OrganizationClient.export_request_data")
    def test_export_request_data_error(self, mock_export_request_data):
        mock_export_request_data.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Export failed"):
                with self.assertRaises(APIError) as context:
                    self.manager.export_request_data()

        self.assertIn("Error received while exporting request data", str(context.exception))
        mock_export_request_data.assert_called_once_with(
            assistant_name=None,
            status=None,
            skip=0,
            count=0
        )

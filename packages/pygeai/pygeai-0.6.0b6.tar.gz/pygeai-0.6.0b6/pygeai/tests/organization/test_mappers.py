import unittest
from unittest.mock import patch
from pygeai.core.models import Assistant, Project, ProjectToken, RequestItem
from pygeai.organization.responses import AssistantListResponse, ProjectListResponse, ProjectDataResponse, \
    ProjectTokensResponse, ProjectItemListResponse
from pygeai.organization.mappers import OrganizationResponseMapper


class TestOrganizationResponseMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.test_mappers.TestOrganizationResponseMapper
    """

    def test_map_to_assistant_list_response_with_project_data(self):
        data = {
            "assistants": [{"assistantId": "1", "assistantName": "Assistant1"}],
            "projectId": "proj1",
            "projectName": "Project1"
        }
        expected_assistant = Assistant(
            id="1",
            name="Assistant1",
            project=Project(id="proj1", name="Project1")
        )

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_assistant', return_value=expected_assistant):
            result = OrganizationResponseMapper.map_to_assistant_list_response(data)

        self.assertIsInstance(result, AssistantListResponse)
        self.assertEqual(len(result.assistants), 1)
        self.assertEqual(result.assistants[0].id, "1")
        self.assertEqual(result.assistants[0].project.id, "proj1")
        self.assertEqual(result.assistants[0].project.name, "Project1")

    def test_map_to_assistant_list_response_empty_assistants(self):
        data = {"assistants": []}

        result = OrganizationResponseMapper.map_to_assistant_list_response(data)

        self.assertIsInstance(result, AssistantListResponse)
        self.assertEqual(len(result.assistants), 0)

    def test_map_to_assistant_list_with_valid_data(self):
        data = {"assistants": [{"assistantId": "1", "assistantName": "Assistant1"}]}
        expected_assistant = Assistant(id="1", name="Assistant1")

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_assistant', return_value=expected_assistant):
            result = OrganizationResponseMapper.map_to_assistant_list(data)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].name, "Assistant1")

    def test_map_to_assistant_list_with_empty_data(self):
        data = {"assistants": []}

        result = OrganizationResponseMapper.map_to_assistant_list(data)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_map_to_project_list_response_with_valid_data(self):
        data = {"projects": [{"projectId": "1", "projectName": "Project1"}]}
        expected_project = Project(id="1", name="Project1")

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_project', return_value=expected_project):
            result = OrganizationResponseMapper.map_to_project_list_response(data)

        self.assertIsInstance(result, ProjectListResponse)
        self.assertEqual(len(result.projects), 1)
        self.assertEqual(result.projects[0].id, "1")
        self.assertEqual(result.projects[0].name, "Project1")

    def test_map_to_project_list_response_with_empty_data(self):
        data = {"projects": []}

        result = OrganizationResponseMapper.map_to_project_list_response(data)

        self.assertIsInstance(result, ProjectListResponse)
        self.assertEqual(len(result.projects), 0)

    def test_map_to_project_list_with_valid_data(self):
        data = {"projects": [{"projectId": "1", "projectName": "Project1"}]}
        expected_project = Project(id="1", name="Project1")

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_project', return_value=expected_project):
            result = OrganizationResponseMapper.map_to_project_list(data)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "1")
        self.assertEqual(result[0].name, "Project1")

    def test_map_to_project_list_with_empty_data(self):
        data = {"projects": []}

        result = OrganizationResponseMapper.map_to_project_list(data)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_map_to_project_data_with_valid_data(self):
        data = {"projectId": "1", "projectName": "Project1"}
        expected_project = Project(id="1", name="Project1")

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_project', return_value=expected_project):
            result = OrganizationResponseMapper.map_to_project_data(data)

        self.assertIsInstance(result, ProjectDataResponse)
        self.assertEqual(result.project.id, "1")
        self.assertEqual(result.project.name, "Project1")

    def test_map_to_token_list_response_with_valid_data(self):
        data = {"tokens": [{"id": "1", "name": "Token1", "status": "Active", "timestamp": "2023-01-01T00:00:00+00:00"}]}
        expected_token = ProjectToken(
            token_id="1",
            name="Token1",
            status="Active",
            timestamp="2023-01-01T00:00:00+00:00"
        )

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_token_list', return_value=[expected_token]):
            result = OrganizationResponseMapper.map_to_token_list_response(data)

        self.assertIsInstance(result, ProjectTokensResponse)
        self.assertEqual(len(result.tokens), 1)
        self.assertEqual(result.tokens[0].token_id, "1")
        self.assertEqual(result.tokens[0].name, "Token1")

    def test_map_to_item_list_response_with_valid_data(self):
        data = {"items": [{"assistant": "Assistant1", "timestamp": "2023-01-01T00:00:00", "status": "succeeded"}]}
        expected_item = RequestItem(
            api_token="token123",
            assistant="Assistant1",
            cost=0.5,
            elapsed_time_ms=1000,
            end_timestamp="2023-01-01T00:01:00",
            module="test_module",
            session_id="session123",
            start_timestamp="2023-01-01T00:00:00",
            status="succeeded",
            timestamp="2023-01-01T00:00:00"
        )

        with patch('pygeai.core.base.mappers.ModelMapper.map_to_item_list', return_value=[expected_item]):
            result = OrganizationResponseMapper.map_to_item_list_response(data)

        self.assertIsInstance(result, ProjectItemListResponse)
        self.assertEqual(len(result.items), 1)
        self.assertEqual(result.items[0].assistant, "Assistant1")
        self.assertEqual(result.items[0].status, "succeeded")


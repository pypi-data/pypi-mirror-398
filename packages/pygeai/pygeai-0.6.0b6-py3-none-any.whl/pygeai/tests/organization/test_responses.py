import unittest
from unittest.mock import MagicMock
from datetime import datetime

from pygeai.organization.responses import (
    AssistantListResponse,
    ProjectListResponse,
    ProjectDataResponse,
    ProjectTokensResponse,
    ProjectItemListResponse
)
from pygeai.core.models import Assistant, Project, ProjectToken, RequestItem


class TestOrganizationResponses(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.test_responses.TestOrganizationResponses
    """
    
    def _create_request_item(self, index=1):
        """Helper method to create a valid RequestItem for testing"""
        return RequestItem(
            apiToken=f"token-{index}",
            assistant=f"assistant-{index}",
            cost=0.01 * index,
            elapsedTimeMs=100 * index,
            endTimestamp=datetime.now(),
            module=f"module-{index}",
            sessionId=f"session-{index}",
            startTimestamp=datetime.now(),
            status="succeeded",
            timestamp=datetime.now()
        )

    def test_assistant_list_response(self):
        assistant1 = MagicMock(spec=Assistant)
        assistant2 = MagicMock(spec=Assistant)
        
        response = AssistantListResponse(assistants=[assistant1, assistant2])
        
        self.assertEqual(len(response.assistants), 2)
        self.assertEqual(response.assistants[0], assistant1)

    def test_project_list_response(self):
        project1 = MagicMock(spec=Project)
        project2 = MagicMock(spec=Project)
        
        response = ProjectListResponse(projects=[project1, project2])
        
        self.assertEqual(len(response.projects), 2)
        self.assertEqual(response.projects[0], project1)

    def test_project_data_response(self):
        project = MagicMock(spec=Project)
        
        response = ProjectDataResponse(project=project)
        
        self.assertEqual(response.project, project)

    def test_project_tokens_response(self):
        token1 = MagicMock(spec=ProjectToken)
        token2 = MagicMock(spec=ProjectToken)
        
        response = ProjectTokensResponse(tokens=[token1, token2])
        
        self.assertEqual(len(response.tokens), 2)
        self.assertEqual(response.tokens[0], token1)

    def test_project_item_list_response_to_list(self):
        item1 = self._create_request_item(1)
        item2 = self._create_request_item(2)
        
        response = ProjectItemListResponse(items=[item1, item2])
        result = response.to_list()
        
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)
        self.assertIsInstance(result[1], dict)

    def test_project_item_list_response_to_list_empty(self):
        response = ProjectItemListResponse(items=[])
        result = response.to_list()
        
        self.assertEqual(result, [])

    def test_project_item_list_response_to_list_none(self):
        response = ProjectItemListResponse(items=[])
        result = response.to_list()
        
        self.assertEqual(result, [])

    def test_project_item_list_response_getitem(self):
        item1 = self._create_request_item(1)
        item2 = self._create_request_item(2)
        
        response = ProjectItemListResponse(items=[item1, item2])
        
        self.assertEqual(response[0], item1)
        self.assertEqual(response[1], item2)

    def test_project_item_list_response_len(self):
        item1 = self._create_request_item(1)
        item2 = self._create_request_item(2)
        
        response = ProjectItemListResponse(items=[item1, item2])
        
        self.assertEqual(len(response), 2)

    def test_project_item_list_response_len_empty(self):
        response = ProjectItemListResponse(items=[])
        
        self.assertEqual(len(response), 0)

    def test_project_item_list_response_iter(self):
        item1 = self._create_request_item(1)
        item2 = self._create_request_item(2)
        
        response = ProjectItemListResponse(items=[item1, item2])
        
        items = list(response)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], item1)
        self.assertEqual(items[1], item2)

    def test_project_item_list_response_append(self):
        item1 = self._create_request_item(1)
        item2 = self._create_request_item(2)
        
        response = ProjectItemListResponse(items=[item1])
        response.append(item2)
        
        self.assertEqual(len(response.items), 2)
        self.assertEqual(response.items[1], item2)


if __name__ == '__main__':
    unittest.main()

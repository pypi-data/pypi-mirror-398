import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.core.common.exceptions import InvalidAPIResponseException, MissingRequirementException
from pygeai.lab.agents.clients import AgentClient
from pygeai.lab.agents.endpoints import CREATE_AGENT_V2, LIST_AGENTS_V2, GET_AGENT_V2, CREATE_SHARING_LINK_V2, \
    PUBLISH_AGENT_REVISION_V2, DELETE_AGENT_V2, UPDATE_AGENT_V2, UPSERT_AGENT_V2
from pygeai.lab.constants import VALID_ACCESS_SCOPES


class TestAgentClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.agents.test_clients.TestAgentClient
    """

    def setUp(self):
        self.project_id = "test-project-id"
        self.client = AgentClient(api_key="test_key", base_url="https://test.url", project_id=self.project_id)
        self.agent_id = "test-agent-id"
        self.agent_data_prompt = {"instructions": "Do this task"}
        self.agent_data_llm_config = {"maxTokens": 100, "timeout": 30}
        self.agent_data_strategy_name = "default"
        self.agent_data_models = [{"name": "gpt-4o"}]
        self.agent_data_resource_pools = [{"name": "pool1", "tools": [{"name": "tool1"}]}]

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_agents_success(self, mock_get):
        expected_response = {"agents": [{"id": "agent-1", "name": "Agent1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_agents(
            status="active",
            start=0,
            count=10,
            access_scope="private",
            allow_drafts=True,
            allow_external=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_AGENTS_V2,
            headers=mock_get.call_args[1]['headers'],
            params={
                "status": "active",
                "start": 0,
                "count": 10,
                "accessScope": "private",
                "allowDrafts": True,
                "allowExternal": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_agents_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_agents()

        self.assertEqual(str(context.exception), f"Unable to list agents for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_agent_success(self, mock_post):
        expected_response = {"id": "agent-123", "name": "Test Agent"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_agent(
            name="Test Agent",
            access_scope="private",
            public_name="test-agent",
            job_description="Agent Role",
            avatar_image="http://example.com/avatar.png",
            description="Agent Description",
            agent_data_prompt=self.agent_data_prompt,
            agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
            agent_data_models=self.agent_data_models,
            agent_data_resource_pools=self.agent_data_resource_pools,
            automatic_publish=True
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=f"{CREATE_AGENT_V2}?automaticPublish=true",
            headers=mock_post.call_args[1]['headers'],
            data=mock_post.call_args[1]['data']
        )
        data = mock_post.call_args[1]['data']['agentDefinition']
        self.assertEqual(data['name'], "Test Agent")
        self.assertEqual(data['accessScope'], "private")
        self.assertEqual(data['publicName'], "test-agent")
        self.assertEqual(data['jobDescription'], "Agent Role")
        self.assertEqual(data['avatarImage'], "http://example.com/avatar.png")
        self.assertEqual(data['description'], "Agent Description")
        self.assertEqual(data['agentData']['prompt'], self.agent_data_prompt)
        self.assertEqual(data['agentData']['llmConfig'], self.agent_data_llm_config)
        self.assertEqual(data['agentData']['models'], self.agent_data_models)
        self.assertEqual(data['agentData']['resourcePools'], self.agent_data_resource_pools)
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_agent_without_resource_pools(self, mock_post):
        expected_response = {"id": "agent-123", "name": "Test Agent"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_agent(
            name="Test Agent",
            access_scope="private",
            public_name="test-agent",
            job_description="Agent Role",
            avatar_image="http://example.com/avatar.png",
            description="Agent Description",
            agent_data_prompt=self.agent_data_prompt,
            agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
            agent_data_models=self.agent_data_models,
            automatic_publish=False
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once()
        data = mock_post.call_args[1]['data']['agentDefinition']
        self.assertNotIn("resourcePools", data['agentData'])

    def test_create_agent_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.client.create_agent(
                name="Test Agent",
                access_scope="invalid_scope",
                public_name="test-agent",
                job_description="Agent Role",
                avatar_image="http://example.com/avatar.png",
                description="Agent Description",
                agent_data_prompt=self.agent_data_prompt,
                agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
                agent_data_models=self.agent_data_models
            )
        self.assertEqual(str(context.exception), f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_agent_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_agent(
                name="Test Agent",
                access_scope="private",
                public_name="test-agent",
                job_description="Agent Role",
                avatar_image="http://example.com/avatar.png",
                description="Agent Description",
                agent_data_prompt=self.agent_data_prompt,
                agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
                agent_data_models=self.agent_data_models
            )

        self.assertEqual(str(context.exception), f"Unable to create agent for project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_agent_success(self, mock_get):
        expected_response = {"id": self.agent_id, "name": "Test Agent"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_agent(
            agent_id=self.agent_id,
            revision="1",
            version=2,
            allow_drafts=False
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_AGENT_V2.format(agentId=self.agent_id),
            headers=mock_get.call_args[1]['headers'],
            params={
                "revision": "1",
                "version": 2,
                "allowDrafts": False
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_get_agent_missing_agent_id(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.client.get_agent(agent_id="")
        self.assertEqual(str(context.exception), "agent_id must be specified in order to retrieve the agent")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_agent_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_agent(agent_id=self.agent_id)

        self.assertEqual(str(context.exception), f"Unable to retrieve agent {self.agent_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_create_sharing_link_success(self, mock_get):
        expected_response = {"link": "http://example.com/share"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_sharing_link(
            agent_id=self.agent_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=CREATE_SHARING_LINK_V2.format(agentId=self.agent_id),
            headers=mock_get.call_args[1]['headers'],
            params={}
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_create_sharing_link_missing_agent_id(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.client.create_sharing_link(agent_id="")
        self.assertEqual(str(context.exception), "agent_id must be specified in order to create sharing link")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_create_sharing_link_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_sharing_link(
                agent_id=self.agent_id
            )

        self.assertEqual(str(context.exception), f"Unable to create sharing link for agent {self.agent_id} in project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_agent_revision_success(self, mock_post):
        revision = "2"
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.publish_agent_revision(
            agent_id=self.agent_id,
            revision=revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_AGENT_REVISION_V2.format(agentId=self.agent_id),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": revision}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_agent_revision_json_decode_error(self, mock_post):
        revision = "2"
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.publish_agent_revision(
                agent_id=self.agent_id,
                revision=revision
            )

        self.assertEqual(str(context.exception), f"Unable to publish revision {revision} for agent {self.agent_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_agent_success(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_agent(
            agent_id=self.agent_id
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_AGENT_V2.format(agentId=self.agent_id),
            headers=mock_delete.call_args[1]['headers'],
            data={}
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_agent_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_agent(
                agent_id=self.agent_id
            )

        self.assertEqual(str(context.exception), f"Unable to delete agent {self.agent_id} from project {self.project_id}: Invalid JSON response")
        mock_delete.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_agent_success(self, mock_put):
        expected_response = {"id": self.agent_id, "name": "Updated Agent"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_agent(
            agent_id=self.agent_id,
            name="Updated Agent",
            access_scope="public",
            public_name="updated-agent",
            job_description="Updated Role",
            avatar_image="http://example.com/new-avatar.png",
            description="Updated Description",
            agent_data_prompt=self.agent_data_prompt,
            agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
            agent_data_models=self.agent_data_models,
            agent_data_resource_pools=self.agent_data_resource_pools,
            automatic_publish=True,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=f"{UPDATE_AGENT_V2.format(agentId=self.agent_id)}?automaticPublish=true",
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        data = mock_put.call_args[1]['data']['agentDefinition']
        self.assertEqual(data['name'], "Updated Agent")
        self.assertEqual(data['accessScope'], "public")
        self.assertEqual(data['publicName'], "updated-agent")
        self.assertEqual(data['jobDescription'], "Updated Role")
        self.assertEqual(data['avatarImage'], "http://example.com/new-avatar.png")
        self.assertEqual(data['description'], "Updated Description")
        self.assertEqual(data['agentData']['prompt'], self.agent_data_prompt)
        self.assertEqual(data['agentData']['llmConfig'], self.agent_data_llm_config)
        self.assertEqual(data['agentData']['models'], self.agent_data_models)
        self.assertEqual(data['agentData']['resourcePools'], self.agent_data_resource_pools)
        headers = mock_put.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_agent_with_upsert(self, mock_put):
        expected_response = {"id": self.agent_id, "name": "Upserted Agent"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_agent(
            agent_id=self.agent_id,
            name="Upserted Agent",
            access_scope="private",
            public_name="upserted-agent",
            job_description="Upserted Role",
            avatar_image="http://example.com/upsert-avatar.png",
            description="Upserted Description",
            agent_data_prompt=self.agent_data_prompt,
            agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
            agent_data_models=self.agent_data_models,
            automatic_publish=False,
            upsert=True
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPSERT_AGENT_V2.format(agentId=self.agent_id),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_agent_without_resource_pools(self, mock_put):
        expected_response = {"id": self.agent_id, "name": "Updated Agent No Pools"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_agent(
            agent_id=self.agent_id,
            name="Updated Agent No Pools",
            access_scope="private",
            public_name="updated-agent-no-pools",
            job_description="Updated Role",
            avatar_image="http://example.com/avatar.png",
            description="Updated Description",
            agent_data_prompt=self.agent_data_prompt,
            agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
            agent_data_models=self.agent_data_models,
            automatic_publish=False,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once()
        data = mock_put.call_args[1]['data']['agentDefinition']
        self.assertNotIn("resourcePools", data['agentData'])

    def test_update_agent_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_agent(
                agent_id=self.agent_id,
                name="Updated Agent",
                access_scope="invalid_scope",
                public_name="updated-agent",
                job_description="Updated Role",
                avatar_image="http://example.com/avatar.png",
                description="Updated Description",
                agent_data_prompt=self.agent_data_prompt,
                agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
                agent_data_models=self.agent_data_models
            )
        self.assertEqual(str(context.exception), f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_agent_json_decode_error(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_agent(
                agent_id=self.agent_id,
                name="Updated Agent",
                access_scope="private",
                public_name="updated-agent",
                job_description="Updated Role",
                avatar_image="http://example.com/avatar.png",
                description="Updated Description",
                agent_data_prompt=self.agent_data_prompt,
                agent_data_llm_config=self.agent_data_llm_config,
            agent_data_strategy_name=self.agent_data_strategy_name,
                agent_data_models=self.agent_data_models
            )

        self.assertEqual(str(context.exception), f"Unable to update agent {self.agent_id} in project {self.project_id}: Invalid JSON response")
        mock_put.assert_called_once()


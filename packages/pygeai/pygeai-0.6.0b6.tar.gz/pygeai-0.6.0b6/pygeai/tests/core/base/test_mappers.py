import unittest
from datetime import timezone
from unittest import TestCase

from pygeai.core.base.mappers import ModelMapper
from pygeai.core.models import Organization, Assistant, AssistantIntent, AssistantRevision, \
    AssistantRevisionMetadata, Project, SearchProfile, ProjectToken, UsageLimit, RequestItem, LlmSettings, \
    WelcomeData, WelcomeDataFeature, WelcomeDataExamplePrompt
from pygeai.tests.core.base.data.mappers import ORGANIZATION_ID, ORGANIZATION_NAME, ASSISTANT_ID, ASSISTANT_NAME, \
    ASSISTANT_TYPE_TEXT, ASSISTANT_STATUS_ACTIVE, ASSISTANT_DESCRIPTION, ASSISTANT_PROMPT, ASSISTANT_INTENT_1, \
    ASSISTANT_INTENT_2, ASSISTANT_INTENT_3, ASSISTANT_REVISION_1, ASSISTANT_REVISION_2, ASSISTANT_REVISION_3, \
    ASSISTANT_METADATA_1, ASSISTANT_METADATA_2, PROJECT_ID, PROJECT_NAME, PROJECT_DESCRIPTION


class TestModelMapper(TestCase):
    """
    python -m unittest pygeai.tests.core.base.test_mappers.TestModelMapper
    """

    def test_map_to_organization(self):
        data = {
            'organizationId': ORGANIZATION_ID,
            "organizationName": ORGANIZATION_NAME
        }
        organization = ModelMapper.map_to_organization(data)
        self.assertTrue(isinstance(organization, Organization))
        self.assertEqual(organization.id, ORGANIZATION_ID)
        self.assertEqual(organization.name, ORGANIZATION_NAME)

    def test_map_to_assistant_required(self):
        data = {
            'assistantName': ASSISTANT_NAME
        }
        assistant = ModelMapper.map_to_assistant(data)
        self.assertTrue(isinstance(assistant, Assistant))
        self.assertEqual(assistant.name, ASSISTANT_NAME)

    def test_map_to_assistant_optional(self):
        data = {
            'assistantName': ASSISTANT_NAME,
            'assistantId': ASSISTANT_ID,
            'assistantType': ASSISTANT_TYPE_TEXT,
            'assistantStatus': ASSISTANT_STATUS_ACTIVE,
            'assistantDescription': ASSISTANT_DESCRIPTION,
            'prompt': ASSISTANT_PROMPT
        }
        assistant = ModelMapper.map_to_assistant(data)
        self.assertTrue(isinstance(assistant, Assistant))
        self.assertEqual(assistant.id, ASSISTANT_ID)
        self.assertEqual(assistant.name, ASSISTANT_NAME)
        self.assertEqual(assistant.type, ASSISTANT_TYPE_TEXT)
        self.assertEqual(assistant.status, ASSISTANT_STATUS_ACTIVE)
        self.assertEqual(assistant.description, ASSISTANT_DESCRIPTION)
        self.assertEqual(assistant.prompt, ASSISTANT_PROMPT)

    @unittest.skip("AssistantIntent was refactored into a direct relationship with AssistantRevision")
    def test_map_to_assistant_with_intents(self):
        data = {
            'assistantName': ASSISTANT_NAME,
            'intents': [
                ASSISTANT_INTENT_1,
                ASSISTANT_INTENT_2,
                ASSISTANT_INTENT_3
            ]
        }
        assistant = ModelMapper.map_to_assistant(data)
        self.assertTrue(isinstance(assistant, Assistant))
        self.assertEqual(assistant.name, ASSISTANT_NAME)
        self.assertEqual(
            assistant.revisions[0].id, ASSISTANT_INTENT_1.get('assistantIntentId')
        )
        self.assertEqual(
            assistant.intents[1].id, ASSISTANT_INTENT_2.get('assistantIntentId')
        )
        self.assertEqual(
            assistant.intents[2].id, ASSISTANT_INTENT_3.get('assistantIntentId')
        )

    def test_map_to_intent_list(self):
        data = {
            'intents': [
                ASSISTANT_INTENT_1,
                ASSISTANT_INTENT_2,
                ASSISTANT_INTENT_3
            ]
        }
        intent_list = ModelMapper.map_to_intent_list(data)
        self.assertEqual(len(intent_list), 3)

        self.assertEqual(intent_list[0].id, ASSISTANT_INTENT_1.get("assistantIntentId"))
        self.assertEqual(intent_list[0].name, ASSISTANT_INTENT_1.get("assistantIntentName"))
        self.assertEqual(intent_list[0].description, ASSISTANT_INTENT_1.get("assistantIntentDescription"))
        self.assertEqual(intent_list[0].default_revision, ASSISTANT_INTENT_1.get("assistantIntentDefaultRevision"))

        self.assertEqual(intent_list[1].id, ASSISTANT_INTENT_2.get("assistantIntentId"))
        self.assertEqual(intent_list[1].name, ASSISTANT_INTENT_2.get("assistantIntentName"))
        self.assertEqual(intent_list[1].description, ASSISTANT_INTENT_2.get("assistantIntentDescription"))
        self.assertEqual(intent_list[1].default_revision, ASSISTANT_INTENT_2.get("assistantIntentDefaultRevision"))

        self.assertEqual(intent_list[2].id, ASSISTANT_INTENT_3.get("assistantIntentId"))
        self.assertEqual(intent_list[2].name, ASSISTANT_INTENT_3.get("assistantIntentName"))
        self.assertEqual(intent_list[2].description, ASSISTANT_INTENT_3.get("assistantIntentDescription"))
        self.assertEqual(intent_list[2].default_revision, ASSISTANT_INTENT_3.get("assistantIntentDefaultRevision"))

        for i, intent in enumerate([ASSISTANT_INTENT_1, ASSISTANT_INTENT_2, ASSISTANT_INTENT_3]):
            self.assertEqual(intent_list[i].revisions[0].model_id, intent["revisions"][0]["modelId"])
            self.assertEqual(intent_list[i].revisions[0].model_name, intent["revisions"][0]["modelName"])
            self.assertEqual(intent_list[i].revisions[0].prompt, intent["revisions"][0]["prompt"])
            self.assertEqual(intent_list[i].revisions[0].provider_name, intent["revisions"][0]["providerName"])
            self.assertEqual(intent_list[i].revisions[0].revision_description, intent["revisions"][0]["revisionDescription"])
            self.assertEqual(intent_list[i].revisions[0].revision_id, intent["revisions"][0]["revisionId"])
            self.assertEqual(intent_list[i].revisions[0].revision_name, intent["revisions"][0]["revisionName"])

            actual_timestamp = intent_list[i].revisions[0].timestamp
            expected_timestamp = intent["revisions"][0]["timestamp"]
            actual_timestamp_str = actual_timestamp.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            self.assertEqual(actual_timestamp_str, expected_timestamp)

            for j, metadata_item in enumerate(intent["revisions"][0]["metadata"]):
                self.assertEqual(intent_list[i].revisions[0].metadata[j].key, metadata_item["key"])
                self.assertEqual(intent_list[i].revisions[0].metadata[j].type, metadata_item["type"])
                self.assertEqual(intent_list[i].revisions[0].metadata[j].value, metadata_item["value"])

    def test_map_to_intent(self):
        data = ASSISTANT_INTENT_1
        intent = ModelMapper.map_to_intent(data)

        self.assertTrue(isinstance(intent, AssistantIntent))
        self.assertEqual(intent.id, ASSISTANT_INTENT_1.get("assistantIntentId"))
        self.assertEqual(intent.name, ASSISTANT_INTENT_1.get("assistantIntentName"))
        self.assertEqual(intent.description, ASSISTANT_INTENT_1.get("assistantIntentDescription"))
        self.assertEqual(intent.default_revision, ASSISTANT_INTENT_1.get("assistantIntentDefaultRevision"))

    def test_map_to_revision_list(self):
        data = {
            "revisions": [
                ASSISTANT_REVISION_1,
                ASSISTANT_REVISION_2,
                ASSISTANT_REVISION_3,
            ]
        }
        revision_list = ModelMapper.map_to_revision_list(data)
        self.assertEqual(len(revision_list), 3)
        for revision in revision_list:
            self.assertTrue(isinstance(revision, AssistantRevision))

    def test_map_to_revision(self):
        data = ASSISTANT_REVISION_1
        revision = ModelMapper.map_to_revision(data)
        self.assertTrue(isinstance(revision, AssistantRevision))

        self.assertEqual(revision.model_id, data.get("modelId"))
        self.assertEqual(revision.model_name, data.get("modelName"))
        self.assertEqual(revision.prompt, data.get("prompt"))
        self.assertEqual(revision.provider_name, data.get("providerName"))
        self.assertEqual(revision.revision_description, data.get("revisionDescription"))
        self.assertEqual(revision.revision_id, data.get("revisionId"))
        self.assertEqual(revision.revision_name, data.get("revisionName"))

        expected_timestamp = data.get("timestamp")
        actual_timestamp_str = revision.timestamp.replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.assertEqual(actual_timestamp_str, expected_timestamp)

        self.assertEqual(len(revision.metadata), len(data.get("metadata", [])))

    def test_map_to_metadata_list(self):
        data = {
            'metadata': [
                ASSISTANT_METADATA_1,
                ASSISTANT_METADATA_2,
            ]
        }
        metadata_list = ModelMapper.map_to_metadata_list(data)
        self.assertEqual(len(metadata_list), 2)
        for metadata in metadata_list:
            self.assertTrue(isinstance(metadata, AssistantRevisionMetadata))

    def test_map_to_metadata(self):
        data = ASSISTANT_METADATA_1
        metadata = ModelMapper.map_to_metadata(data)
        self.assertTrue(isinstance(metadata, AssistantRevisionMetadata))
        self.assertEqual(metadata.key, ASSISTANT_METADATA_1.get("key"))
        self.assertEqual(metadata.type, ASSISTANT_METADATA_1.get("type"))
        self.assertEqual(metadata.value, ASSISTANT_METADATA_1.get("value"))

    def test_map_to_project_required(self):
        data = {
            "projectId": PROJECT_ID,
            "projectName": PROJECT_NAME
        }

        project = ModelMapper.map_to_project(data)

        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.id, PROJECT_ID)
        self.assertEqual(project.name, PROJECT_NAME)

        self.assertIsNone(project.active)
        self.assertIsNone(project.description)
        self.assertIsNone(project.status)
        self.assertIsNone(project.organization)
        # self.assertEqual(project.search_profiles, [])
        self.assertEqual(project.tokens, [])
        self.assertIsNone(project.usage_limit)

    def test_map_to_project_optional(self):
        data = {
            "projectId": PROJECT_ID,
            "projectName": PROJECT_NAME,
            "projectActive": True,
            "projectDescription": PROJECT_DESCRIPTION,
            "projectStatus": 0,  # Active
            "organizationId": ORGANIZATION_ID,
            "organizationName": ORGANIZATION_NAME,
            "searchProfiles": [
                {"name": "Search 1", "description": "First search profile"},
                {"name": "Search 2", "description": "Second search profile"}
            ],
            "tokens": [
                {
                    "description": "API token",
                    "id": "token-789",
                    "name": "Test Token",
                    "status": "Active",
                    "timestamp": "2025-02-05T12:00:00Z"
                }
            ],
            "usageLimit": {
                "hardLimit": 1000,
                "id": "limit-111",
                "relatedEntityName": "Test Entity",
                "remainingUsage": 500,
                "renewalStatus": "Renewable",
                "softLimit": 800,
                "status": 1,
                "subscriptionType": "Monthly",
                "usageUnit": "Requests",
                "usedAmount": 200,
                "validFrom": "2025-01-01T00:00:00Z",
                "validUntil": "2025-12-31T23:59:59Z"
            }
        }

        project = ModelMapper.map_to_project(data)

        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.id, PROJECT_ID)
        self.assertEqual(project.name, PROJECT_NAME)
        self.assertEqual(project.active, True)
        self.assertEqual(project.description, PROJECT_DESCRIPTION)
        self.assertEqual(project.status, 0)

        self.assertIsNotNone(project.organization)
        self.assertEqual(project.organization.id, ORGANIZATION_ID)
        self.assertEqual(project.organization.name, ORGANIZATION_NAME)

        # self.assertEqual(len(project.search_profiles), 2)
        #self.assertEqual(project.search_profiles[0].name, "Search 1")
        #self.assertEqual(project.search_profiles[0].description, "First search profile")
        #self.assertEqual(project.search_profiles[1].name, "Search 2")
        #self.assertEqual(project.search_profiles[1].description, "Second search profile")

        self.assertEqual(len(project.tokens), 1)
        self.assertEqual(project.tokens[0].token_id, "token-789")
        self.assertEqual(project.tokens[0].description, "API token")
        self.assertEqual(project.tokens[0].name, "Test Token")
        self.assertEqual(project.tokens[0].status, "Active")
        self.assertEqual(
            project.tokens[0].timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "2025-02-05T12:00:00Z"
        )

        self.assertIsNotNone(project.usage_limit)
        self.assertEqual(project.usage_limit.hard_limit, 1000)
        self.assertEqual(project.usage_limit.id, "limit-111")
        self.assertEqual(project.usage_limit.related_entity_name, "Test Entity")
        self.assertEqual(project.usage_limit.remaining_usage, 500)
        self.assertEqual(project.usage_limit.renewal_status, "Renewable")
        self.assertEqual(project.usage_limit.soft_limit, 800)
        self.assertEqual(project.usage_limit.status, 1)
        self.assertEqual(project.usage_limit.subscription_type, "Monthly")
        self.assertEqual(project.usage_limit.usage_unit, "Requests")
        self.assertEqual(project.usage_limit.used_amount, 200)
        self.assertEqual(
            project.usage_limit.valid_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "2025-01-01T00:00:00Z"
        )
        self.assertEqual(
            project.usage_limit.valid_until.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "2025-12-31T23:59:59Z"
        )

    def test_map_to_search_profile_list(self):
        data = {"searchProfiles": [{"name": "Profile 1", "description": "Description 1"}]}
        profiles = ModelMapper.map_to_search_profile_list(data)

        self.assertTrue(isinstance(profiles, list))
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].name, "Profile 1")
        self.assertEqual(profiles[0].description, "Description 1")

    def test_map_to_search_profile(self):
        data = {"name": "Profile 1", "description": "Description 1"}
        profile = ModelMapper.map_to_search_profile(data)

        self.assertTrue(isinstance(profile, SearchProfile))
        self.assertEqual(profile.name, "Profile 1")
        self.assertEqual(profile.description, "Description 1")

    def test_map_to_token_list(self):
        data = {'tokens':
                    [{"id": "token-123", "name": "Token 1", "description": "Test token", "status": "Active",
                 "timestamp": "2025-02-05T12:00:00Z"}]
                }
        tokens = ModelMapper.map_to_token_list(data)

        self.assertTrue(isinstance(tokens, list))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].token_id, "token-123")
        self.assertEqual(tokens[0].name, "Token 1")

    def test_map_to_token(self):
        data = {"id": "token-123", "name": "Token 1", "description": "Test token", "status": "Active",
                "timestamp": "2025-02-05T12:00:00Z"}
        token = ModelMapper.map_to_token(data)

        self.assertTrue(isinstance(token, ProjectToken))
        self.assertEqual(token.token_id, "token-123")
        self.assertEqual(token.name, "Token 1")

    def test_map_to_usage_limit(self):
        data = {
            "id": "usage-123",
            "relatedEntityName": "entity-name",
            "renewalStatus": "Renewable",
            "hardLimit": 100,
            "softLimit": 80,
            "remainingUsage": 50,
            "subscriptionType": "Daily",
            "usageUnit": "Requests",
            "usedAmount": 20,
            "status": 1,
            "validFrom": "2025-02-05T12:00:00Z",
            "validUntil": "2025-03-05T12:00:00Z"
        }
        usage_limit = ModelMapper.map_to_usage_limit(data)

        self.assertTrue(isinstance(usage_limit, UsageLimit))
        self.assertEqual(usage_limit.id, "usage-123")
        self.assertEqual(usage_limit.hard_limit, 100)
        self.assertEqual(usage_limit.remaining_usage, 50)

    def test_map_to_item(self):
        data = {
            "apiToken": "test-token",
            "assistant": "Assistant 1",
            "cost": 0.5,
            "elapsedTimeMs": 100,
            "endTimestamp": "2025-02-05T12:00:05Z",
            "intent": "Intent 1",
            "module": "test-module",
            "timestamp": "2025-02-05T12:00:00Z",
            "prompt": "Test prompt",
            "output": "Test output",
            "inputText": "Test input",
            "sessionId": "test-session",
            "startTimestamp": "2025-02-05T12:00:00Z",
            "status": "succeeded"
        }
        item = ModelMapper.map_to_item(data)

        self.assertTrue(isinstance(item, RequestItem))
        self.assertEqual(item.assistant, "Assistant 1")
        self.assertEqual(item.intent, "Intent 1")

    def test_map_to_llm_settings(self):
        data = {
            "providerName": "OpenAI",
            "modelName": "GPT-4",
            "temperature": 0.7,
            "maxTokens": 500,
            "uploadFiles": True,
            "llmOutputGuardrail": True,
            "inputModerationGuardrail": True,
            "promptInjectionGuardrail": False
        }
        settings = ModelMapper.map_to_llm_settings(data)

        self.assertTrue(isinstance(settings, LlmSettings))
        self.assertEqual(settings.provider_name, "OpenAI")
        self.assertEqual(settings.model_name, "GPT-4")
        self.assertEqual(settings.temperature, 0.7)
        self.assertEqual(settings.max_tokens, 500)
        self.assertEqual(settings.upload_files, True)
        self.assertEqual(settings.guardrail_settings.llm_output, True)
        self.assertEqual(settings.guardrail_settings.input_moderation, True)
        self.assertEqual(settings.guardrail_settings.prompt_injection, False)

    def test_map_to_welcome_data(self):
        data = {"title": "Welcome", "description": "Welcome message", "features": [], "examplesPrompt": []}
        welcome_data = ModelMapper.map_to_welcome_data(data)

        self.assertTrue(isinstance(welcome_data, WelcomeData))
        self.assertEqual(welcome_data.title, "Welcome")
        self.assertEqual(welcome_data.description, "Welcome message")

    def test_map_to_welcome_data_with_features(self):
        data = {
            "title": "Welcome",
            "description": "Welcome message",
            "features": [
                {"title": "Feature 1", "description": "Feature 1 description"},
                {"title": "Feature 2", "description": "Feature 2 description"}
            ],
            "examplesPrompt": []
        }
        welcome_data = ModelMapper.map_to_welcome_data(data)

        self.assertTrue(isinstance(welcome_data, WelcomeData))
        self.assertEqual(welcome_data.title, "Welcome")
        self.assertEqual(welcome_data.description, "Welcome message")

        self.assertEqual(len(welcome_data.features), 2)
        self.assertEqual(welcome_data.features[0].title, "Feature 1")
        self.assertEqual(welcome_data.features[0].description, "Feature 1 description")
        self.assertEqual(welcome_data.features[1].title, "Feature 2")
        self.assertEqual(welcome_data.features[1].description, "Feature 2 description")

    def test_map_to_welcome_data_with_examples_prompt(self):
        data = {
            "title": "Welcome",
            "description": "Welcome message",
            "features": [],
            "examplesPrompt": [
                {"title": "Example 1", "description": "Example 1 description", "promptText": "What is this?"},
                {"title": "Example 2", "description": "Example 2 description", "promptText": "How does it work?"}
            ]
        }
        welcome_data = ModelMapper.map_to_welcome_data(data)

        self.assertTrue(isinstance(welcome_data, WelcomeData))
        self.assertEqual(welcome_data.title, "Welcome")
        self.assertEqual(welcome_data.description, "Welcome message")

        self.assertEqual(len(welcome_data.examples_prompt), 2)
        self.assertEqual(welcome_data.examples_prompt[0].title, "Example 1")
        self.assertEqual(welcome_data.examples_prompt[0].description, "Example 1 description")
        self.assertEqual(welcome_data.examples_prompt[0].prompt_text, "What is this?")
        self.assertEqual(welcome_data.examples_prompt[1].title, "Example 2")
        self.assertEqual(welcome_data.examples_prompt[1].description, "Example 2 description")
        self.assertEqual(welcome_data.examples_prompt[1].prompt_text, "How does it work?")

    def test_map_to_feature_list(self):
        data = {
            "features": [{"title": "Feature 1", "description": "Feature description"}]
        }
        features = ModelMapper.map_to_feature_list(data)

        self.assertTrue(isinstance(features, list))
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].title, "Feature 1")

    def test_map_to_feature(self):
        data = {"title": "Feature 1", "description": "Feature description"}
        feature = ModelMapper.map_to_feature(data)

        self.assertTrue(isinstance(feature, WelcomeDataFeature))
        self.assertEqual(feature.title, "Feature 1")

    def test_map_to_example_prompt_list(self):
        data = {"examplesPrompt":
                    [{"title": "Example 1", "description": "Example description", "promptText": "Example prompt"}]
                }
        examples = ModelMapper.map_to_example_prompt_list(data)

        self.assertTrue(isinstance(examples, list))
        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0].title, "Example 1")

    def test_map_to_example_prompt(self):
        data = {"title": "Example 1", "description": "Example description", "promptText": "Example prompt"}
        example = ModelMapper.map_to_example_prompt(data)

        self.assertTrue(isinstance(example, WelcomeDataExamplePrompt))
        self.assertEqual(example.title, "Example 1")

    def test_map_to_project_item(self):
        data = {
            "apiToken": "test-token",
            "assistant": "Test Assistant",
            "cost": 0.5,
            "elapsedTimeMs": 100,
            "endTimestamp": "2025-02-05T12:00:05Z",
            "intent": "Test Intent",
            "module": "test-module",
            "timestamp": "2025-02-05T12:00:00Z",
            "prompt": "Test prompt",
            "output": "Test output",
            "inputText": "Test input text",
            "sessionId": "test-session-id",
            "startTimestamp": "2025-02-05T12:00:00Z",
            "status": "succeeded"
        }
        item = ModelMapper.map_to_item(data)

        self.assertTrue(isinstance(item, RequestItem))
        self.assertEqual(item.assistant, "Test Assistant")
        self.assertEqual(item.intent, "Test Intent")
        self.assertEqual(item.prompt, "Test prompt")
        self.assertEqual(item.output, "Test output")
        self.assertEqual(item.input_text, "Test input text")
        self.assertEqual(item.status, "succeeded")

    def test_map_to_item_list(self):
        data = {
            "items": [
                {
                    "apiToken": "test-token-1",
                    "assistant": "Assistant 1",
                    "cost": 0.5,
                    "elapsedTimeMs": 100,
                    "endTimestamp": "2025-02-05T12:00:05Z",
                    "intent": "Intent 1",
                    "module": "test-module",
                    "timestamp": "2025-02-05T12:00:00Z",
                    "prompt": "Prompt 1",
                    "output": "Output 1",
                    "inputText": "Input Text 1",
                    "sessionId": "test-session-1",
                    "startTimestamp": "2025-02-05T12:00:00Z",
                    "status": "succeeded"
                },
                {
                    "apiToken": "test-token-2",
                    "assistant": "Assistant 2",
                    "cost": 0.7,
                    "elapsedTimeMs": 150,
                    "endTimestamp": "2025-02-05T12:05:10Z",
                    "intent": "Intent 2",
                    "module": "test-module",
                    "timestamp": "2025-02-05T12:05:00Z",
                    "prompt": "Prompt 2",
                    "output": "Output 2",
                    "inputText": "Input Text 2",
                    "sessionId": "test-session-2",
                    "startTimestamp": "2025-02-05T12:05:00Z",
                    "status": "succeeded"
                }
            ]
        }
        items = ModelMapper.map_to_item_list(data)

        self.assertEqual(len(items), 2)
        self.assertTrue(isinstance(items[0], RequestItem))
        self.assertTrue(isinstance(items[1], RequestItem))

        self.assertEqual(items[0].assistant, "Assistant 1")
        self.assertEqual(items[0].intent, "Intent 1")
        self.assertEqual(items[0].prompt, "Prompt 1")
        self.assertEqual(items[0].output, "Output 1")
        self.assertEqual(items[0].input_text, "Input Text 1")
        self.assertEqual(items[0].status, "succeeded")

        self.assertEqual(items[1].assistant, "Assistant 2")
        self.assertEqual(items[1].intent, "Intent 2")
        self.assertEqual(items[1].prompt, "Prompt 2")
        self.assertEqual(items[1].output, "Output 2")
        self.assertEqual(items[1].input_text, "Input Text 2")
        self.assertEqual(items[1].status, "succeeded")

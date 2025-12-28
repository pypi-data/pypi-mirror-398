from datetime import datetime
from unittest import TestCase

from pygeai.core.models import UsageLimit, ChatVariable, WelcomeData, WelcomeDataFeature, WelcomeDataExamplePrompt, \
    LlmSettings, GuardrailSettings, RequestItem, Project, Assistant
from pygeai.tests.core.base.data.models import USAGE_LIMIT_1, CHAT_VARIABLE, WELCOME_DATA, WELCOME_DATA_FEATURE_1, \
    WELCOME_DATA_EXAMPLE_PROMPT_1, LLM_SETTINGS_1, LLM_SETTINGS_2, LLM_SETTINGS_3, LLM_SETTINGS_4, LLM_SETTINGS_5, \
    REQUEST_ITEM, PROJECT_1, ASSISTANT_1


class TestModels(TestCase):
    """
    python -m unittest pygeai.tests.core.base.test_models.TestModels
    """

    def test_usage_limit_model_validate(self):
        usage_limit_data = USAGE_LIMIT_1

        usage_limit = UsageLimit.model_validate(usage_limit_data)
        self.assertEqual(usage_limit.hard_limit, usage_limit_data.get('hardLimit'))
        self.assertEqual(usage_limit.id, usage_limit_data.get('id'))
        self.assertEqual(usage_limit.related_entity_name, usage_limit_data.get('relatedEntityName'))
        self.assertEqual(usage_limit.remaining_usage, usage_limit_data.get('remainingUsage'))
        self.assertEqual(usage_limit.renewal_status, usage_limit_data.get('renewalStatus'))
        self.assertEqual(usage_limit.soft_limit, usage_limit_data.get('softLimit'))
        self.assertEqual(usage_limit.status, usage_limit_data.get('status'))
        self.assertEqual(usage_limit.subscription_type, usage_limit_data.get('subscriptionType'))
        self.assertEqual(usage_limit.usage_unit, usage_limit_data.get('usageUnit'))
        self.assertEqual(usage_limit.used_amount, usage_limit_data.get('usedAmount'))
        self.assertEqual(usage_limit.valid_from, datetime.fromisoformat(usage_limit_data.get('validFrom')))
        self.assertEqual(usage_limit.valid_until, datetime.fromisoformat(usage_limit_data.get('validUntil')))

    def test_llm_settings_model_validate(self):
        llm_settings_data = LLM_SETTINGS_1

        llm_settings = LlmSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.provider_name, llm_settings_data.get('providerName'))
        self.assertEqual(llm_settings.model_name, llm_settings_data.get('modelName'))
        self.assertEqual(llm_settings.temperature, llm_settings_data.get('temperature'))
        self.assertEqual(llm_settings.max_tokens, llm_settings_data.get('maxTokens'))
        self.assertEqual(llm_settings.frequency_penalty, llm_settings_data.get('frequencyPenalty'))
        self.assertEqual(llm_settings.presence_penalty, llm_settings_data.get('presencePenalty'))
        self.assertEqual(llm_settings.upload_files, llm_settings_data.get('uploadFiles'))
        self.assertEqual(llm_settings.n, llm_settings_data.get('n'))
        self.assertEqual(llm_settings.stream, llm_settings_data.get('stream'))
        self.assertEqual(llm_settings.top_p, llm_settings_data.get('topP'))
        self.assertEqual(llm_settings.type, llm_settings_data.get('type'))
        self.assertEqual(llm_settings.cache, llm_settings_data.get('cache'))
        self.assertEqual(llm_settings.verbose, llm_settings_data.get('verbose'))

        guardrail_settings = GuardrailSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.guardrail_settings, guardrail_settings)

    def test_llm_settings_model_validate_2(self):
        llm_settings_data = LLM_SETTINGS_2

        llm_settings = LlmSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.provider_name, llm_settings_data.get('providerName'))
        self.assertEqual(llm_settings.model_name, llm_settings_data.get('modelName'))
        self.assertEqual(llm_settings.temperature, llm_settings_data.get('temperature'))
        self.assertEqual(llm_settings.max_tokens, llm_settings_data.get('maxTokens'))
        self.assertEqual(llm_settings.upload_files, llm_settings_data.get('uploadFiles'))
        self.assertEqual(llm_settings.n, llm_settings_data.get('n'))
        self.assertEqual(llm_settings.stream, llm_settings_data.get('stream'))
        self.assertEqual(llm_settings.top_p, llm_settings_data.get('topP'))
        self.assertEqual(llm_settings.type, llm_settings_data.get('type'))
        self.assertEqual(llm_settings.cache, llm_settings_data.get('cache'))
        self.assertEqual(llm_settings.verbose, llm_settings_data.get('verbose'))
        self.assertIsNone(llm_settings.guardrail_settings)

    def test_llm_settings_model_validate_3(self):
        llm_settings_data = LLM_SETTINGS_3

        llm_settings = LlmSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.provider_name, llm_settings_data.get('providerName'))
        self.assertEqual(llm_settings.model_name, llm_settings_data.get('modelName'))
        self.assertEqual(llm_settings.temperature, llm_settings_data.get('temperature'))
        self.assertEqual(llm_settings.max_tokens, llm_settings_data.get('maxTokens'))
        self.assertEqual(llm_settings.upload_files, llm_settings_data.get('uploadFiles'))
        self.assertEqual(llm_settings.n, llm_settings_data.get('n'))
        self.assertEqual(llm_settings.stream, llm_settings_data.get('stream'))
        self.assertEqual(llm_settings.top_p, llm_settings_data.get('topP'))
        self.assertEqual(llm_settings.type, llm_settings_data.get('type'))
        self.assertEqual(llm_settings.cache, llm_settings_data.get('cache'))
        self.assertEqual(llm_settings.verbose, llm_settings_data.get('verbose'))

        guardrail_data = {
            "llmOutputGuardrail": llm_settings_data.get("llmOutputGuardrail"),
            "inputModerationGuardrail": llm_settings_data.get("inputModerationGuardrail"),
            "promptInjectionGuardrail": llm_settings_data.get("promptInjectionGuardrail")
        }
        if any(guardrail_data):
            guardrail_settings = GuardrailSettings.model_validate(guardrail_data)
            self.assertEqual(llm_settings.guardrail_settings, guardrail_settings)
        else:
            self.assertIsNone(llm_settings.guardrail_settings)

    def test_llm_settings_model_validate_4(self):
        llm_settings_data = LLM_SETTINGS_4

        llm_settings = LlmSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.provider_name, llm_settings_data.get('providerName'))
        self.assertEqual(llm_settings.model_name, llm_settings_data.get('modelName'))
        self.assertEqual(llm_settings.temperature, llm_settings_data.get('temperature'))
        self.assertEqual(llm_settings.max_tokens, llm_settings_data.get('maxTokens'))
        self.assertEqual(llm_settings.upload_files, llm_settings_data.get('uploadFiles'))
        self.assertEqual(llm_settings.n, llm_settings_data.get('n'))
        self.assertEqual(llm_settings.stream, llm_settings_data.get('stream'))
        self.assertEqual(llm_settings.top_p, llm_settings_data.get('topP'))
        self.assertEqual(llm_settings.type, llm_settings_data.get('type'))
        self.assertEqual(llm_settings.cache, llm_settings_data.get('cache'))
        self.assertEqual(llm_settings.verbose, llm_settings_data.get('verbose'))

        guardrail_data = {
            "llmOutputGuardrail": llm_settings_data.get("llmOutputGuardrail"),
            "inputModerationGuardrail": llm_settings_data.get("inputModerationGuardrail"),
            "promptInjectionGuardrail": llm_settings_data.get("promptInjectionGuardrail")
        }
        if any(guardrail_data.values()):
            guardrail_settings = GuardrailSettings.model_validate(guardrail_data)
            self.assertEqual(llm_settings.guardrail_settings, guardrail_settings)
        else:
            self.assertIsNone(llm_settings.guardrail_settings)

    def test_llm_settings_model_validate_5(self):
        llm_settings_data = LLM_SETTINGS_5

        llm_settings = LlmSettings.model_validate(llm_settings_data)
        self.assertEqual(llm_settings.provider_name, llm_settings_data.get('providerName'))
        self.assertEqual(llm_settings.model_name, llm_settings_data.get('modelName'))
        self.assertEqual(llm_settings.temperature, llm_settings_data.get('temperature'))
        self.assertEqual(llm_settings.max_tokens, llm_settings_data.get('maxTokens'))
        self.assertEqual(llm_settings.upload_files, llm_settings_data.get('uploadFiles'))
        self.assertEqual(llm_settings.n, llm_settings_data.get('n'))
        self.assertEqual(llm_settings.stream, llm_settings_data.get('stream'))
        self.assertEqual(llm_settings.top_p, llm_settings_data.get('topP'))
        self.assertEqual(llm_settings.type, llm_settings_data.get('type'))
        self.assertEqual(llm_settings.cache, llm_settings_data.get('cache'))
        self.assertEqual(llm_settings.verbose, llm_settings_data.get('verbose'))

        guardrail_data = {
            "llmOutputGuardrail": llm_settings_data.get("llmOutputGuardrail"),
            "inputModerationGuardrail": llm_settings_data.get("inputModerationGuardrail"),
            "promptInjectionGuardrail": llm_settings_data.get("promptInjectionGuardrail")
        }
        if any(guardrail_data.values()):
            guardrail_settings = GuardrailSettings.model_validate(guardrail_data)
            self.assertEqual(llm_settings.guardrail_settings, guardrail_settings)
        else:
            self.assertIsNone(llm_settings.guardrail_settings)

    def test_welcome_data_feature_model_validate(self):
        feature_data = WELCOME_DATA_FEATURE_1

        feature = WelcomeDataFeature.model_validate(feature_data)
        self.assertEqual(feature.title, feature_data.get('title'))
        self.assertEqual(feature.description, feature_data.get('description'))

    def test_welcome_data_example_prompt_model_validate(self):
        example_prompt_data = WELCOME_DATA_EXAMPLE_PROMPT_1

        example_prompt = WelcomeDataExamplePrompt.model_validate(example_prompt_data)
        self.assertEqual(example_prompt.title, example_prompt_data.get('title'))
        self.assertEqual(example_prompt.description, example_prompt_data.get('description'))
        self.assertEqual(example_prompt.prompt_text, example_prompt_data.get('promptText'))

    def test_welcome_data_model_validate(self):
        welcome_data_data = WELCOME_DATA

        welcome_data = WelcomeData.model_validate(welcome_data_data)
        self.assertEqual(welcome_data.title, welcome_data_data.get('title'))
        self.assertEqual(welcome_data.description, welcome_data_data.get('description'))
        self.assertEqual(
            welcome_data.features,
            [WelcomeDataFeature.model_validate(feature) for feature in welcome_data_data.get('features', [])]
        )
        self.assertEqual(
            welcome_data.examples_prompt,
            [WelcomeDataExamplePrompt.model_validate(example) for example in welcome_data_data.get('examplesPrompt', [])]
        )

    def test_chat_variable_model_validate(self):
        chat_variable_data = CHAT_VARIABLE

        chat_variable = ChatVariable.model_validate(chat_variable_data)
        self.assertEqual(chat_variable.key, chat_variable_data.get('key'))
        self.assertEqual(chat_variable.value, chat_variable_data.get('value'))

    def test_request_item_model_validate(self):
        request_item_data = REQUEST_ITEM

        request_item = RequestItem.model_validate(request_item_data)
        self.assertEqual(request_item.assistant, request_item_data.get("assistant"))
        self.assertEqual(request_item.intent, request_item_data.get("intent"))
        # Compare timestamps by checking that the string representation starts with the expected value
        expected_timestamp = request_item_data.get("timestamp").replace("Z", "+00:00") if request_item_data.get("timestamp").endswith("Z") else request_item_data.get("timestamp")
        self.assertTrue(request_item.timestamp.isoformat().startswith(expected_timestamp))
        self.assertEqual(request_item.prompt, request_item_data.get("prompt"))
        self.assertEqual(request_item.output, request_item_data.get("output"))
        self.assertEqual(request_item.input_text, request_item_data.get("inputText"))
        self.assertEqual(request_item.status, request_item_data.get("status"))

    def test_project_model_validate(self):
        project_data = PROJECT_1

        project = Project.model_validate(project_data)
        self.assertEqual(project.id, project_data["projectId"])
        self.assertEqual(project.name, project_data["projectName"])
        self.assertEqual(project.active, project_data["projectActive"])
        self.assertEqual(project.description, project_data["projectDescription"])
        self.assertEqual(project.status, project_data["projectStatus"])
        self.assertEqual(project.organization.id, project_data["organizationId"])
        self.assertEqual(project.organization.name, project_data["organizationName"])
        self.assertEqual(len(project.tokens), len(project_data["tokens"]))

        if project.usage_limit:
            self.assertEqual(project.usage_limit.id, project_data["usageLimit"]["id"])
            self.assertEqual(project.usage_limit.hard_limit, project_data["usageLimit"]["hardLimit"])
            self.assertEqual(project.usage_limit.soft_limit, project_data["usageLimit"]["softLimit"])
            self.assertEqual(project.usage_limit.remaining_usage, project_data["usageLimit"]["remainingUsage"])
            self.assertEqual(project.usage_limit.renewal_status, project_data["usageLimit"]["renewalStatus"])
            self.assertEqual(project.usage_limit.status, project_data["usageLimit"]["status"])
            self.assertEqual(project.usage_limit.subscription_type, project_data["usageLimit"]["subscriptionType"])
            self.assertEqual(project.usage_limit.usage_unit, project_data["usageLimit"]["usageUnit"])
            self.assertEqual(project.usage_limit.used_amount, project_data["usageLimit"]["usedAmount"])
            self.assertEqual(project.usage_limit.valid_from.isoformat(), project_data["usageLimit"]["validFrom"])
            self.assertEqual(project.usage_limit.valid_until.isoformat(), project_data["usageLimit"]["validUntil"])

    def test_assistant_model_validate(self):
        assistant_data = ASSISTANT_1

        assistant = Assistant.model_validate(assistant_data)

        self.assertEqual(assistant.id, assistant_data.get("assistantId"))
        self.assertEqual(assistant.name, assistant_data.get("assistantName"))
        self.assertEqual(assistant.description, assistant_data.get("assistantDescription"))
        self.assertEqual(assistant.status, assistant_data.get("assistantStatus"))
        self.assertEqual(assistant.priority, assistant_data.get("assistantPriority"))
        self.assertEqual(assistant.type, assistant_data.get("type"))
        self.assertEqual(assistant.default_revision, assistant_data.get("assistantIntentDefaultRevision"))
        self.assertEqual(assistant.intent_description, assistant_data.get("assistantIntentDescription"))
        self.assertEqual(assistant.intent_id, assistant_data.get("assistantIntentId"))
        self.assertEqual(assistant.intent_name, assistant_data.get("assistantIntentName"))

        revision = assistant.revisions[0]
        self.assertEqual(revision.model_name, assistant_data['revisions'][0]['modelName'])
        self.assertEqual(revision.prompt, assistant_data['revisions'][0]['prompt'])
        self.assertEqual(revision.provider_name, assistant_data['revisions'][0]['providerName'])
        self.assertEqual(revision.revision_description, assistant_data['revisions'][0]['revisionDescription'])
        self.assertEqual(revision.revision_id, assistant_data['revisions'][0]['revisionId'])
        self.assertEqual(revision.revision_name, assistant_data['revisions'][0]['revisionName'])
        timestamp_str = assistant_data['revisions'][0]['timestamp']
        timestamp_obj = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
        self.assertEqual(revision.timestamp, timestamp_obj)

        project = assistant.project
        self.assertEqual(project.id, assistant_data['project']['projectId'])
        self.assertEqual(project.name, assistant_data['project']['projectName'])

        self.assertEqual(assistant.welcome_data.features, assistant_data['welcomeData']['features'])
        self.assertEqual(assistant.welcome_data.examples_prompt, assistant_data['welcomeData']['examplesPrompt'])
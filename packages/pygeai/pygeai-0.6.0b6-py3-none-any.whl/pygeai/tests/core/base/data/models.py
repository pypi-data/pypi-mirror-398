USAGE_LIMIT_1 = {
    'hardLimit': 2000.0,
    'id': '4bb78b5a-07ea-4d15-84d6-e0baee53ff61',
    'relatedEntityName': 'Pia.Data.Organization',
    'remainingUsage': 1999.98386112,
    'renewalStatus': 'Renewable',
    'softLimit': 1000.0,
    'status': 1,
    'subscriptionType': 'Monthly',
    'usageUnit': 'Cost',
    'usedAmount': 0.01613888,
    'validFrom': '2025-02-20T19:33:00',
    'validUntil': '2025-03-01T00:00:00'
}
USAGE_LIMIT_2 = {
    'hardLimit': 10000.0,
    'id': '6d95069b-bab5-4281-b432-a7f5b4290227',
    'relatedEntityName': 'Pia.Data.Organization',
    'remainingUsage': 10000.0,
    'renewalStatus': 'NonRenewable',
    'softLimit': 5000.0,
    'status': 4,
    'subscriptionType': 'Monthly',
    'usageUnit': 'Cost',
    'usedAmount': 0.0,
    'validFrom': '2025-02-20T16:12:56',
    'validUntil': '2025-03-01T00:00:00'
}
USAGE_LIMIT_3 = {
    'hardLimit': 15000.0,
    'id': '510b8d8a-4911-4f5e-a292-965f012a0112',
    'relatedEntityName': 'Pia.Data.Organization',
    'remainingUsage': 15000.0,
    'renewalStatus': 'NonRenewable',
    'softLimit': 5000.0,
    'status': 4,
    'subscriptionType': 'Monthly',
    'usageUnit': 'Cost',
    'usedAmount': 0.0,
    'validFrom': '2025-02-20T15:34:57',
    'validUntil': '2025-03-01T00:00:00'
}

USAGE_LIMIT_LIST = {
    'usageLimits': [
        USAGE_LIMIT_1,
        USAGE_LIMIT_2,
        USAGE_LIMIT_3
    ]
}

CHAT_VARIABLE = {
    "key": "test_key",
    "value": "test_value"
}


WELCOME_DATA_FEATURE_1 = {
    "title": "First Feature",
    "description": "First Feature Description"
}
WELCOME_DATA_FEATURE_2 = {
    "title": "Second Feature",
    "description": "Second Feature Description"
}

WELCOME_DATA_EXAMPLE_PROMPT_1 = {
    "title": "First Prompt Example",
    "description": "First Prompt Example Description",
    "promptText": "You are an assistant specialized in translating ..."
}

WELCOME_DATA = {
    "title": "Assistant with WelcomeData",
    "description": "It is to test WelcomeData",
    "features": [
        WELCOME_DATA_FEATURE_1,
        WELCOME_DATA_FEATURE_2
    ],
    "examplesPrompt": [
        WELCOME_DATA_EXAMPLE_PROMPT_1
    ]
}

LLM_SETTINGS_1 = {
    "providerName": "OpenAI",
    "modelName": "gpt-3.5-turbo",
    "temperature": 0.7,
    "maxTokens": 150,
    "uploadFiles": True,
    "llmOutputGuardrail": True,
    "inputModerationGuardrail": False,
    "promptInjectionGuardrail": True,
    "verbose": False,
    "stream": False,
    "cache": False,
    "type": ""
}

LLM_SETTINGS_2 = {
    "providerName": "Google",
    "modelName": "bert-base",
    "temperature": 0.5,
    "maxTokens": 100,
    "uploadFiles": False,
    "verbose": True,
    "stream": True,
    "cache": True,
    "type": "example"
}

LLM_SETTINGS_3 = {
    "providerName": "Microsoft",
    "modelName": "turing-nlg",
    "temperature": 0.9,
    "maxTokens": 200,
    "uploadFiles": True,
    "llmOutputGuardrail": False,
    "inputModerationGuardrail": False,
    "promptInjectionGuardrail": False,
    "verbose": True,
    "stream": False,
    "cache": False,
    "type": "test"
}

LLM_SETTINGS_4 = {
    "providerName": "IBM",
    "modelName": "watson-nlp",
    "temperature": 0.0,
    "maxTokens": 50,
    "uploadFiles": True,
    "verbose": False,
    "stream": False,
    "cache": True,
    "type": "sample"
}

LLM_SETTINGS_5 = {
    "providerName": "Hugging Face",
    "modelName": "distilbert-base-uncased",
    "temperature": 0.8,
    "maxTokens": 120,
    "uploadFiles": True,
    "verbose": False,
    "stream": True,
    "cache": False,
    "type": "demo"
}

REQUEST_ITEM = {
    "apiToken": "test-api-token",
    "assistant": "N/D",
    "cost": 0.001,
    "elapsedTimeMs": 1500,
    "endTimestamp": "2025-02-25T15:03:15.144",
    "intent": None,
    "timestamp": "2025-02-25T15:03:13.644",
    "prompt": None,
    "output": None,
    "inputText": None,
    "module": "test-module",
    "sessionId": "test-session-id",
    "startTimestamp": "2025-02-25T15:03:13.644",
    "status": "succeeded"
}


PROJECT_1 = {
    "organizationId": "4aa15b61-d3c7-4a5c-99b8-052d18a04ff2",
    "organizationName": "SDK GEAI",
    "projectActive": True,
    "projectDescription": "An AI project focused on natural language processing and testing",
    "projectId": "1956c032-3c66-4435-acb8-6a06e52f819f",
    "projectName": "AI Project",
    "projectStatus": 0,
    "searchProfiles": [],
    "tokens": [],
    "usageLimit": {
        "hardLimit": 2000.0,
        "id": "349a2ac4-847b-4118-ab22-09eb7ae12420",
        "relatedEntityName": "Pia.Data.Project",
        "remainingUsage": 2000.0,
        "renewalStatus": "Renewable",
        "softLimit": 1000.0,
        "status": 1,
        "subscriptionType": "Monthly",
        "usageUnit": "Requests",
        "usedAmount": 0.0,
        "validFrom": "2025-02-06T15:47:32",
        "validUntil": "2025-03-01T00:00:00"
    }
}

PROJECT_2 = {
    "organizationId": "5eeb3c23-2d77-498d-8c1f-58f4a463f34b",
    "organizationName": "Internal R&D",
    "projectActive": False,
    "projectDescription": "A hidden project for internal testing",
    "projectId": "b25d3141-9a24-4b73-a3dc-1a6bfb7f9fcb",
    "projectName": "Internal Test Project",
    "projectStatus": 2,
    "searchProfiles": [
        {
            "name": "Testing Profile",
            "description": "Used for internal experiments"
        }
    ],
    "tokens": [
        {
            "description": "Test API Token",
            "id": "tkn-12345",
            "name": "Test Token",
            "status": "Active",
            "timestamp": "2025-02-10T12:00:00"
        }
    ],
    "usageLimit": {
        "hardLimit": 500.0,
        "id": "bb98d4f2-8a60-4d1a-9b8c-dc908f5fcf72",
        "relatedEntityName": "Pia.Data.Project",
        "remainingUsage": 250.0,
        "renewalStatus": "NonRenewable",
        "softLimit": 200.0,
        "status": 2,
        "subscriptionType": "One-Time",
        "usageUnit": "Requests",
        "usedAmount": 250.0,
        "validFrom": "2025-01-15T10:00:00",
        "validUntil": "2025-12-31T23:59:59"
    }
}

PROJECT_3 = {
    "organizationId": "8f7b2a97-3a5c-4f5e-b38e-77d6f617d75d",
    "organizationName": "Ethical AI Lab",
    "projectActive": True,
    "projectDescription": "A research project on AI ethics",
    "projectId": "d39b5f73-8f04-41a0-b4a3-2cd1a3a4e55c",
    "projectName": "AI Ethics Research",
    "projectStatus": 0,
    "searchProfiles": [
        {
            "name": "Ethics Compliance",
            "description": "Ensures AI models align with ethical guidelines"
        }
    ],
    "tokens": [
        {
            "description": "Research Token",
            "id": "tkn-67890",
            "name": "Ethics Token",
            "status": "Active",
            "timestamp": "2025-02-15T09:30:00"
        }
    ],
    "usageLimit": {
        "hardLimit": 10000.0,
        "id": "e78a6f64-3f88-489e-92a0-6b8a42e34a27",
        "relatedEntityName": "Pia.Data.Project",
        "remainingUsage": 7500.0,
        "renewalStatus": "Renewable",
        "softLimit": 5000.0,
        "status": 1,
        "subscriptionType": "Annual",
        "usageUnit": "Requests",
        "usedAmount": 2500.0,
        "validFrom": "2025-03-01T00:00:00",
        "validUntil": "2026-03-01T00:00:00"
    }
}

ASSISTANT_1 = {
    "assistantId": "3372b866-36b3-4541-8897-d371dab99f10",
    "assistantName": "Welcome data Assistant 4",
    "assistantDescription": "A chatbot assistant for customer support",
    "assistantStatus": 1,
    "assistantPriority": 0,
    "type": "TextPromptAssistant",
    "assistantIntentDefaultRevision": 1.0,
    "assistantIntentDescription": "Default",
    "assistantIntentId": "064d2945-0fff-4855-a2b6-5d38915728c5",
    "assistantIntentName": "Default",
    "revisions": [
        {
            "metadata": [
                {"key": "input_moderation", "type": "Boolean", "value": "true"},
                {"key": "llm_output", "type": "Boolean", "value": "true"},
                {"key": "max_tokens", "type": "Number", "value": "1000"},
                {"key": "prompt_injection", "type": "Boolean", "value": "true"},
                {"key": "temperature", "type": "Decimal", "value": "0.70"},
                {"key": "upload_files", "type": "Boolean", "value": "false"}
            ],
            "modelName": "gpt-4",
            "prompt": '[{"role":"system","content":"Translate to French"},{"role":"user","content":"{{inputText}}"}]',
            "providerName": "openai",
            "revisionDescription": "GBrain.BL.API.Assistant.AddTextAssistantRevisionImpl",
            "revisionId": 1,
            "revisionName": "1",
            "timestamp": "2025-02-06T19:02:34"
        }
    ],
    "project": {
        "projectId": "2ca6883f-6778-40bb-bcc1-85451fb11107",
        "projectName": "Default",
        "tokens": []
    },
    "welcomeData": {
        "features": [],
        "examplesPrompt": []
    }
}

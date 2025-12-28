ORGANIZATION_ID = "cfbff0d1-9375-5685-968c-48ce8b15ae17"
ORGANIZATION_NAME = "Test Organization"

ASSISTANT_ID = "eac65b96-5ad4-54b4-9baf-449efc21345a"
ASSISTANT_NAME = "Test Assistant"
ASSISTANT_TYPE_TEXT = "text"
ASSISTANT_STATUS_ACTIVE = 1
ASSISTANT_STATUS_HIDDEN = 2
ASSISTANT_DESCRIPTION = "Description"
ASSISTANT_PROMPT = "Your job is to test tests"

ASSISTANT_METADATA_1 = {
    "key": "category",
    "type": "string",
    "value": "support"
}
ASSISTANT_METADATA_2 = {
    "key": "priority",
    "type": "string",
    "value": "high"
}

ASSISTANT_REVISION_1 = {
    "metadata": [
        ASSISTANT_METADATA_1,
        ASSISTANT_METADATA_2,
    ],
    "modelId": "model-001",
    "modelName": "SupportAI",
    "prompt": "How can I assist you with your support request?",
    "providerName": "OpenAI",
    "revisionDescription": "Initial version for support requests",
    "revisionId": 1,
    "revisionName": "v1.0",
    "timestamp": "2025-02-05T12:00:00Z"
}

ASSISTANT_INTENT_1 = {
    "assistantIntentDefaultRevision": 1,
    "assistantIntentDescription": "Handles customer support inquiries",
    "assistantIntentId": "intent-12345",
    "assistantIntentName": "Customer Support",
    "revisions": [
        ASSISTANT_REVISION_1
    ]
}

ASSISTANT_REVISION_2 = {
    "metadata": [
        {
            "key": "category",
            "type": "string",
            "value": "recommendation"
        },
        {
            "key": "model_version",
            "type": "string",
            "value": "v2.1"
        }
    ],
    "modelId": "model-002",
    "modelName": "RecommenderAI",
    "prompt": "Based on your preferences, here are some product recommendations.",
    "providerName": "OpenAI",
    "revisionDescription": "Updated recommendation logic",
    "revisionId": 2,
    "revisionName": "v2.1",
    "timestamp": "2025-02-05T14:30:00Z"
}

ASSISTANT_INTENT_2 = {
    "assistantIntentDefaultRevision": 2,
    "assistantIntentDescription": "Handles product recommendations",
    "assistantIntentId": "intent-67890",
    "assistantIntentName": "Product Recommendation",
    "revisions": [
        ASSISTANT_REVISION_2
    ]
}

ASSISTANT_REVISION_3 = {
    "metadata": [
        {
            "key": "category",
            "type": "string",
            "value": "scheduling"
        },
        {
            "key": "timezone",
            "type": "string",
            "value": "UTC"
        }
    ],
    "modelId": "model-003",
    "modelName": "SchedulerAI",
    "prompt": "Let's find a suitable time for your appointment.",
    "providerName": "Google",
    "revisionDescription": "Enhanced scheduling features",
    "revisionId": 3,
    "revisionName": "v3.0",
    "timestamp": "2025-02-05T16:45:00Z"
}

ASSISTANT_INTENT_3 = {
    "assistantIntentDefaultRevision": 3,
    "assistantIntentDescription": "Handles appointment scheduling",
    "assistantIntentId": "intent-54321",
    "assistantIntentName": "Appointment Scheduler",
    "revisions": [
        ASSISTANT_REVISION_3
    ]
}

PROJECT_ID = "8c7decd3-2155-5e51-b98b-8e332070a269"
PROJECT_NAME = "Test Project"
PROJECT_DESCRIPTION = "This is a test project"


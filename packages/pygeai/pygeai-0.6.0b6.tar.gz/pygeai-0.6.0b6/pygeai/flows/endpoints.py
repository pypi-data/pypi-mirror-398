# Agent Webhook Admin Controller - Service to manage agent webhooks.
RETRIEVE_ALL_AGENTS_WEBHOOKS_V1 = "/api/v1/admin/agent/webhook"  # GET -> Retrieves all agent webhooks.
SAVE_AGENT_WEBHOOK_V1 = "/api/v1/admin/agent/webhook"  # POST -> Save the webhook for Rest API.
RETRIEVE_AGENT_WEBHOOK_V1 = "/api/v1/admin/agent/webhook/{id}"  # GET -> Retrieves webhook configuration for Rest API.
DELETE_AGENT_WEBHOOK_V1 = "/api/v1/admin/agent/webhook/{id}"  # DELETE -> Delete the webhook for Rest API.

# Analytics Controller - Rest APIs for Analytics Events.
CREATE_ANALYTICS_EVENT_V1 = "/api/v1/admin/analytics/events"  # POST -> Creates a record for the Event in Analytics.

# API Key Service - Admin Service to manage API keys.
RETRIEVE_API_KEYS_V1 = "/api/v1/admin/apikey"  # GET -> Retrieve the available API keys.
CREATE_API_KEY_V1 = "/api/v1/admin/apikey"  # POST -> Create an API key.
DELETE_API_KEY_V1 = "/api/v1/admin/apikey/{key-name}"  # DELETE -> Delete an API key.
RETRIEVE_ADMIN_CONSOLE_API_KEY_V1 = "/api/v1/admin/apikey/console"  # GET -> Get the admin console API key.

# B2Chat Properties Service - Service to interact with B2Chat configuration properties.
GET_B2CHAT_CONFIG_V1 = "/api/v1/admin/b2chat/config"  # GET -> Get the B2Chat configuration.
UPSERT_B2CHAT_CONFIG_V1 = "/api/v1/admin/b2chat/config"  # POST -> Upsert B2Chat configuration.
DELETE_B2CHAT_CONFIG_V1 = "/api/v1/admin/b2chat/config"  # DELETE -> Delete the B2Chat configuration.
GET_B2CHAT_INTEGRATION_STATUS_V1 = "/api/v1/admin/b2chat/config/integration"  # GET -> Get the integration status.
ENABLE_DISABLE_B2CHAT_INTEGRATION_V1 = "/api/v1/admin/b2chat/config/integration"  # POST -> Enable or Disable the B2Chat integration.

# Billing Tenant Service - Service to manage the tenant billing.
GET_BILL_DETAIL_V1 = "/api/v1/admin/billing/{billingId}"  # GET -> Get bill detail by ID.
GET_TENANT_BILLS_V1 = "/api/v1/admin/billing/bills"  # GET -> Get the tenant bills for tenant.
GET_ORG_BILLS_V1 = "/api/v1/admin/billing/bills/{organizationId}"  # GET -> Get the tenant bills for organization.
GET_BILLING_CONFIG_V1 = "/api/v1/admin/billing/config"  # GET -> Get a billing configuration for tenant.
GET_ORG_BILLING_CONFIG_V1 = "/api/v1/admin/billing/config/{organizationId}"  # GET -> Get a billing configuration for organization.
GET_CURRENT_BILLING_STATUS_V1 = "/api/v1/admin/billing/current"  # GET -> Get the current billing status for tenant.
GET_ORG_CURRENT_BILLING_STATUS_V1 = "/api/v1/admin/billing/current/{organizationId}"  # GET -> Get the current billing status for organization.
GENERATE_TENANT_BILL_V1 = "/api/v1/admin/billing/generate"  # POST -> Generate tenant bill.
GENERATE_LEGACY_BILL_V1 = "/api/v1/admin/billing/generate-legacy-data"  # POST -> Generate tenant bill.

# Bot Snapshot Service - WebService class to get and apply bot configuration snapshot.
GET_BOT_SNAPSHOT_LIST_V1 = "/api/v1/admin/bot-config/snapshot"  # GET -> Get all list of Snapshot saved in the repository.
CREATE_BOT_SNAPSHOT_V1 = "/api/v1/admin/bot-config/snapshot"  # POST -> Creates a Snapshot version with current Bot Configuration.
UPDATE_BOT_SNAPSHOT_V1 = "/api/v1/admin/bot-config/snapshot/{id}"  # PUT -> Update Bot Configuration with one Snapshot version.
EXPORT_BOT_SNAPSHOT_V1 = "/api/v1/admin/bot-config/snapshot/{id}/export"  # GET -> Export the full configuration from the bot with a given snapshot ID.

# Cache Controller - Service to handle caches.
GET_ALL_CACHES_V1 = "/api/v1/admin/cache"  # GET -> Retrieves a list with all caches.
DELETE_ALL_CACHES_V1 = "/api/v1/admin/cache"  # DELETE -> Delete all caches.

# Context Controller - Service to handle Context information.
GET_ACTIVE_CONTEXTS_V1 = "/api/v1/admin/context"  # GET -> Retrieves a list with the active conversation contexts.
DELETE_ALL_CONTEXTS_V1 = "/api/v1/admin/context"  # DELETE -> Deletes all contexts.
GET_SESSION_CONTEXT_V1 = "/api/v1/admin/context/{sessionId}"  # GET -> Retrieves the active conversation context of given session ID.
DELETE_SESSION_CONTEXT_V1 = "/api/v1/admin/context/{sessionId}"  # DELETE -> Deletes the context of given session ID.
GET_SESSION_LOGS_V1 = "/api/v1/admin/context/logs/{sessionId}"  # GET -> Retrieves the active logs of given session ID.
CLOSE_SESSION_LOGS_V1 = "/api/v1/admin/context/logs/{sessionId}"  # POST -> Closes logs emitter given session ID.

# Conversation Analytics Controller - Rest APIs for Conversation Metrics
CONVERSATION_ANALYTICS_AVG_SENT_MESSAGES = "/api/v1/admin/analytics/conversations/average_sent_messages"  # GET -> Gets average of messages by conversation in the given time period.
CONVERSATION_ANALYTICS_COMPLETED_FLOWS = "/api/v1/admin/analytics/conversations/completed-flows"  # GET -> Get completed flows for the given time period.
CONVERSATION_ANALYTICS_EVENTS = "/api/v1/admin/analytics/conversations/events"  # GET -> Gets list of events grouped by category action and label in the given time period.
CONVERSATION_ANALYTICS_FUNNEL = "/api/v1/admin/analytics/conversations/funnel"  # GET -> Gets a tree of conversation flow in given time period.
CONVERSATION_ANALYTICS_TOP_INTENTS = "/api/v1/admin/analytics/conversations/intents"  # GET -> Gets list of TOP most used intents in the given time period.
CONVERSATION_ANALYTICS_INTENT_QUERIES = "/api/v1/admin/analytics/conversations/intents/{intent_name}/queries"  # GET -> Gets list of queries for an intent in the given time period.
CONVERSATION_ANALYTICS_INTENT_QUERIES_SEARCH = "/api/v1/admin/analytics/conversations/intents/{intent_name}/queries/search"  # GET -> Search list of queries for intents in the given time period.
CONVERSATION_ANALYTICS_INTENTS_PAGE = "/api/v1/admin/analytics/conversations/intents/page"  # GET -> Gets list of TOP most used intents in the given time period.
CONVERSATION_ANALYTICS_INTENTS_PAGE_SEARCH = "/api/v1/admin/analytics/conversations/intents/page/search"  # GET -> Search intents in the given time period.
CONVERSATION_ANALYTICS_INTERACTIONS = "/api/v1/admin/analytics/conversations/interactions"  # GET -> Gets list of events interaction with their count in the given time period.
CONVERSATION_ANALYTICS_SENT_MESSAGES = "/api/v1/admin/analytics/conversations/sent_messages"  # GET -> Gets count of messages in the given time period.
CONVERSATION_ANALYTICS_TOP_FLOWS = "/api/v1/admin/analytics/conversations/top-flows"  # GET -> Get most used flows for the given time period.
CONVERSATION_ANALYTICS_TOP_FLOWS_SEARCH = "/api/v1/admin/analytics/conversations/top-flows/search"  # GET -> Search most used flows for the given time period.
CONVERSATION_ANALYTICS_TOTAL_EVENT = "/api/v1/admin/analytics/conversations/total-event"  # GET -> Gets all events triggered in the given time period.
CONVERSATION_ANALYTICS_TRANSCRIPTS = "/api/v1/admin/analytics/conversations/transcripts"  # GET -> Get list of conversations starting with the given intent path in the given time period.
CONVERSATION_ANALYTICS_UNANSWERED_MESSAGE = "/api/v1/admin/analytics/conversations/unanswered_message"  # GET -> Gets list of events interaction with their count in the given time period.

# Diagnostics Controller - Rest APIs for User Conversation History and Not Handled Intents
DIAGNOSTICS_FALLBACK = "/api/v1/admin/diagnostics/fallback"  # GET -> Gets list of fallback events that matches with params.
DIAGNOSTICS_FALLBACK_CREATE = "/api/v1/admin/diagnostics/fallback"  # POST -> Create new FAQ and update the fallback event to RESOLVED.
DIAGNOSTICS_FALLBACK_UPDATE = "/api/v1/admin/diagnostics/fallback"  # PUT -> Update new FAQ and update the fallback event to RESOLVED.
DIAGNOSTICS_FALLBACK_IGNORE = "/api/v1/admin/diagnostics/fallback/ignore"  # POST -> Mark the queries to be ignored.
DIAGNOSTICS_FALLBACK_INTENT_CREATE = "/api/v1/admin/diagnostics/fallback/intent"  # POST -> Create new FAQ and update the fallback event to RESOLVED.
DIAGNOSTICS_FALLBACK_INTENT_UPDATE = "/api/v1/admin/diagnostics/fallback/intent"  # PUT -> Update new FAQ and update the fallback event to RESOLVED.
DIAGNOSTICS_FALLBACK_REOPEN = "/api/v1/admin/diagnostics/fallback/reopen"  # POST -> Mark the fallback event as RAISED.
DIAGNOSTICS_FALLBACK_RESOLVE = "/api/v1/admin/diagnostics/fallback/resolve"  # POST -> Mark the fallback event as RESOLVED.
DIAGNOSTICS_FALLBACK_TRANSCRIPTS = "/api/v1/admin/diagnostics/fallback/transcripts"  # GET -> Get list of conversations starting with the given query string.
DIAGNOSTICS_HISTORY_CSV = "/api/v1/admin/diagnostics/history/csv"  # GET -> Get conversation history in CSV format.
DIAGNOSTICS_HISTORY_USERS = "/api/v1/admin/diagnostics/history/users"  # GET -> Get user conversation history.
DIAGNOSTICS_HISTORY_USER_INFO = "/api/v1/admin/diagnostics/history/users/{userId}"  # GET -> Get user information.
DIAGNOSTICS_HISTORY_USER_CONVERSATIONS = "/api/v1/admin/diagnostics/history/users/{userId}/conversations"  # GET -> Get user conversations.

# Documents API Service - WebService class to manage documents of document server
GET_LLAMA_DOCUMENTS_V1 = "/api/v1/admin/llama-index/documents"  # GET -> Get documents.
UPLOAD_LLAMA_DOCUMENT_V1 = "/api/v1/admin/llama-index/documents"  # POST -> Upload document.
GET_LLAMA_DOCUMENT_V1 = "/api/v1/admin/llama-index/documents/{documentId}"  # GET -> Get document.
UPDATE_LLAMA_DOCUMENT_V1 = "/api/v1/admin/llama-index/documents/{documentId}"  # PUT -> Update document.
DELETE_LLAMA_DOCUMENT_V1 = "/api/v1/admin/llama-index/documents/{documentId}"  # DELETE -> Delete document.
REINDEX_LLAMA_DOCUMENT_V1 = "/api/v1/admin/llama-index/documents/{documentId}/reindex"  # PUT -> Reindex document.
GET_LLAMA_DOCUMENT_DOWNLOAD_V1 = "/api/v1/admin/llama-index/documents/{documentId}/signed-url"  # GET -> Get document download link.

# FAQ API Service - WebService class to manage FAQ's
GET_FAQS_V1 = "/api/v1/admin/faqs"  # GET -> Get FAQs.
CREATE_FAQ_V1 = "/api/v1/admin/faqs"  # POST -> Create FAQ.
UPDATE_FAQ_V1 = "/api/v1/admin/faqs"  # PUT -> Update FAQ.
GET_FAQ_V1 = "/api/v1/admin/faqs/{faqId}"  # GET -> Get FAQ.
DELETE_FAQ_V1 = "/api/v1/admin/faqs/{faqId}"  # DELETE -> Delete FAQ.
CREATE_FAQ_FLOW_V1 = "/api/v1/admin/faqs/{faqId}/flow"  # POST -> Create a new Flow given a FAQ.
BATCH_FAQ_V1 = "/api/v1/admin/faqs/batch"  # POST -> Batch process FAQs.

# FluentLab Descriptor - Service to get app description
GET_RASA_STATUS_V1 = "/api/v1/admin/description"  # GET -> Get the status of the Rasa server.

# Folder Service - WebService class to manage the Routing Folder CRUD
GET_FOLDERS_V1 = "/api/v1/admin/routing/folders"  # GET -> Get a list with all the folders.
STORE_FOLDER_V1 = "/api/v1/admin/routing/folders"  # POST -> Store a folder.
UPDATE_FOLDER_V1 = "/api/v1/admin/routing/folders/{folder_id}"  # PUT -> Update a flow associated to an ID.
DELETE_FOLDER_V1 = "/api/v1/admin/routing/folders/{folder_id}"  # DELETE -> Delete a folder based on ID.

# Import and Export Configuration Service - WebService class to import/export the bot configuration
EXPORT_BOT_CONFIG_V1 = "/api/v1/admin/bot-config/export"  # GET -> Export the full configuration from the bot.
IMPORT_BOT_CONFIG_V1 = "/api/v1/admin/bot-config/import"  # POST -> Import the full configuration from a bot.

# Input Validator Service - WebService class to manage the input validator from routing
GET_INPUT_VALIDATOR_V1 = "/api/v1/admin/routing/input-validator"  # GET -> Get a list with all the responses.

# Integration Service - Service to setup integrations
GET_INTEGRATION_SETTINGS_V1 = "/api/v1/admin/integration"  # GET -> Get integrations settings
POST_NEW_INTEGRATION_V1 = "/api/v1/admin/integration"  # POST -> Post a new integration
GET_INTEGRATION_SETTINGS_BY_ID_V1 = "/api/v1/admin/integration/{integrationId}"  # GET -> Get integration settings
PUT_UPDATE_INTEGRATION_V1 = "/api/v1/admin/integration/{integrationId}"  # PUT -> Update integration
DELETE_INTEGRATION_V1 = "/api/v1/admin/integration/{integrationId}"  # DELETE -> Delete integration

# LLM Admin Service - Service to manage and interact with LLMs
GET_AVAILABLE_EMBEDDING_MODELS_V1 = "/api/v1/admin/llm/available-embedding-models"  # GET -> Get the LLM available embedding models for a vendor
GET_AVAILABLE_MODELS_V1 = "/api/v1/admin/llm/available-models"  # GET -> Get the LLM available models for a vendor
GET_AVAILABLE_VENDORS_V1 = "/api/v1/admin/llm/available-vendors"  # GET -> Get the LLM available vendors
POST_EVALUATE_PROMPT_V1 = "/api/v1/admin/llm/evaluate"  # POST -> Try a prompt
POST_GENERATE_FAQS_V1 = "/api/v1/admin/llm/generate/faqs"  # POST -> Generate FAQs from a text
POST_GENERATE_RESPONSE_VARIANTS_V1 = "/api/v1/admin/llm/generate/response-variants"  # POST -> Generate response variants from an example
POST_GENERATE_TRAINING_PHRASES_V1 = "/api/v1/admin/llm/generate/training-phrases"  # POST -> Generate training phrases from an example
GET_LIST_PROMPT_TEMPLATES_V1 = "/api/v1/admin/llm/prompt"  # GET -> List all prompt templates
POST_SAVE_PROMPT_TEMPLATE_V1 = "/api/v1/admin/llm/prompt"  # POST -> Save a prompt template
GET_PROMPT_TEMPLATE_BY_ID_V1 = "/api/v1/admin/llm/prompt/{id}"  # GET -> Retrieves the prompt template for given id

# OpenAI Service - Service to manage and interact with OpenAI LLMs
GET_OPENAI_AVAILABLE_EMBEDDING_MODELS_V1 = "/api/v1/admin/openai/available-embedding-models"  # GET -> Get the OpenAI LLM available embedding models for a vendor
GET_OPENAI_AVAILABLE_MODELS_V1 = "/api/v1/admin/openai/available-models"  # GET -> Get the OpenAI LLM available models for a vendor
GET_OPENAI_AVAILABLE_VENDORS_V1 = "/api/v1/admin/openai/available-vendors"  # GET -> Get the OpenAI LLM available vendors
POST_OPENAI_EVALUATE_PROMPT_V1 = "/api/v1/admin/openai/evaluate"  # POST -> Try a prompt
POST_OPENAI_GENERATE_FAQS_V1 = "/api/v1/admin/openai/generate/faqs"  # POST -> Generate FAQs from a text
POST_OPENAI_GENERATE_RESPONSE_VARIANTS_V1 = "/api/v1/admin/openai/generate/response-variants"  # POST -> Generate response variants from an example
POST_OPENAI_GENERATE_TRAINING_PHRASES_V1 = "/api/v1/admin/openai/generate/training-phrases"  # POST -> Generate training phrases from an example
GET_OPENAI_LIST_PROMPT_TEMPLATES_V1 = "/api/v1/admin/openai/prompt"  # GET -> List all prompt templates
POST_OPENAI_SAVE_PROMPT_TEMPLATE_V1 = "/api/v1/admin/openai/prompt"  # POST -> Save a prompt template
GET_OPENAI_PROMPT_TEMPLATE_BY_ID_V1 = "/api/v1/admin/openai/prompt/{id}"  # GET -> Retrieves the prompt template for given id

# Language Detector Service - Service to interact with Language Detector
GET_ALL_LANGUAGES_V1 = "/api/v1/admin/language-detector/entity"  # GET -> Get all languages set for the bot
PUT_ADD_LANGUAGE_V1 = "/api/v1/admin/language-detector/entity"  # PUT -> Add language for the bot
DELETE_LANGUAGE_V1 = "/api/v1/admin/language-detector/entity"  # DELETE -> Delete language for the bot
POST_ADD_LANGUAGE_BY_ENTITY_V1 = "/api/v1/admin/language-detector/entity/{entity}"  # POST -> Add language for the bot by entity
GET_LANGUAGE_BY_ID_V1 = "/api/v1/admin/language-detector/entity/{id}"  # GET -> Get all languages set for the bot by ID
PUT_UPDATE_LANGUAGE_BY_ID_V1 = "/api/v1/admin/language-detector/entity/{id}"  # PUT -> Update language for the bot by ID
DELETE_LANGUAGE_BY_ID_V1 = "/api/v1/admin/language-detector/entity/{id}"  # DELETE -> Delete language for the bot by ID
GET_SEARCH_LANGUAGES_V1 = "/api/v1/admin/language-detector/entity/search"  # GET -> Get all languages set for the bot (search)
GET_ALL_LANGUAGES_FOR_BOT_V1 = "/api/v1/admin/language-detector/language"  # GET -> Get all languages set for the bot
DELETE_ALL_LANGUAGES_V1 = "/api/v1/admin/language-detector/language"  # DELETE -> Delete all languages for the bot
POST_ADD_LANGUAGE_V1 = "/api/v1/admin/language-detector/language/{language}"  # POST -> Add language for the bot
DELETE_LANGUAGE_BY_NAME_V1 = "/api/v1/admin/language-detector/language/{language}"  # DELETE -> Delete language for the bot by name

# Lex Utils Controller - Service to manage utils for AWS Lex
POST_SYNC_LOCAL_DATA_V1 = "/api/v1/admin/lex/sync/model/{model-name}"  # POST -> Sync local data against Lex

# Model Versioning Service - Service to view or change previously trained models
GET_ALL_TRAINED_MODELS_V1 = "/api/v1/admin/model"  # GET -> Get all trained models for locale
PUT_REPLACE_CURRENT_MODEL_V1 = "/api/v1/admin/model"  # PUT -> Replace the current loaded model with a new trained model
DELETE_TRAINED_MODEL_BY_ID_V1 = "/api/v1/admin/model/{id}"  # DELETE -> Delete trained model entry by ID
GET_TRAINED_MODEL_EXPORT_V1 = "/api/v1/admin/model/{id}/export"  # GET -> Exports existing trained rasa model by ID
GET_TRAINED_MODEL_BY_NAME_V1 = "/api/v1/admin/model/{modelName}"  # GET -> Get trained model for specific model name and locale
POST_IMPORT_TRAINED_MODEL_V1 = "/api/v1/admin/model/{modelName}/import"  # POST -> Import trained rasa model for specific model and locale
GET_ALL_TRAINED_MODELS_PAGINATED_V1 = "/api/v1/admin/model/page"  # GET -> Get all trained models paginated

# Multilanguage Service - WebService class to manage the Languages CRUD
GET_AVAILABLE_LANGUAGES_V1 = "/api/v1/admin/multilanguage"  # GET -> Get a list with the available languages
GET_ALLOWED_LANGUAGES_V1 = "/api/v1/admin/multilanguage/allowed"  # GET -> Get a list with the allowed languages

# NLU Personality Data Service - WebService class to manage the Personality CRUD
GET_ALL_PERSONALITY_DATA_V1 = "/api/v1/admin/personality"  # GET -> Get all the Personality data
POST_STORE_PERSONALITY_MODEL_V1 = "/api/v1/admin/personality"  # POST -> Store a Personality model
PUT_UPDATE_PERSONALITY_MODEL_V1 = "/api/v1/admin/personality"  # PUT -> Update a Personality model
DELETE_PERSONALITY_MODEL_V1 = "/api/v1/admin/personality"  # DELETE -> Delete a Personality model
GET_PERSONALITY_DATA_BY_NAME_V1 = "/api/v1/admin/personality/{name}"  # GET -> Get Personality data by name

# NLU Pipeline Configuration Service - Service to configure the NLU pipeline
GET_NLU_PIPELINE_V1 = "/api/v1/admin/nlupipeline"  # GET -> Get the NLU Pipeline
POST_NLU_PIPELINE_V1 = "/api/v1/admin/nlupipeline"  # POST -> Post an NLU Pipeline

# NLU Training Config Service - WebService class to manage the TrainingDataConfig CRUD
GET_ALL_TRAINING_CONFIGS_V1 = "/api/v1/admin/training/config"  # GET -> Get all TrainingData configurations
POST_STORE_TRAINING_CONFIG_V1 = "/api/v1/admin/training/config"  # POST -> Store a TrainingData configuration
GET_TRAINING_CONFIG_BY_NAME_V1 = "/api/v1/admin/training/config/{configName}"  # GET -> Get a TrainingData configuration by name
DELETE_TRAINING_CONFIG_BY_NAME_V1 = "/api/v1/admin/training/config/{configName}"  # DELETE -> Delete a TrainingData configuration

# NLU Training Service - Service to interact with the NLU server
POST_TRAIN_AND_UPLOAD_MODELS_V1 = "/api/v1/admin/training/model"  # POST -> Train and upload all rasa models that have changes
POST_TRAIN_AND_LOAD_MODEL_V1 = "/api/v1/admin/training/model/{model-name}"  # POST -> Train and load a new rasa model
POST_RETRIEVE_AVAILABLE_MODELS_V1 = "/api/v1/admin/training/models"  # POST -> Retrieve the list of available models
GET_RASA_SERVER_STATUS_V1 = "/api/v1/admin/training/status"  # GET -> Get the status of the Rasa server
GET_TRAINING_FILE_BY_MODEL_NAME_V1 = "/api/v1/admin/training/training-file/{model-name}"  # GET -> Get the training file used by RASA to train

# Pipeline API Service - WebService class to manage Pipelines
GET_PIPELINES_V1 = "/api/v1/admin/pipelines"  # GET -> Get Pipelines
POST_CREATE_PIPELINE_V1 = "/api/v1/admin/pipelines"  # POST -> Create Pipeline
PUT_UPDATE_PIPELINE_V1 = "/api/v1/admin/pipelines"  # PUT -> Update Pipeline
GET_PIPELINE_BY_NAME_V1 = "/api/v1/admin/pipelines/{pipeline}"  # GET -> Get Pipeline by name
DELETE_PIPELINE_BY_NAME_V1 = "/api/v1/admin/pipelines/{pipeline}"  # DELETE -> Delete Pipeline by name

# Proxy to Chains API - Proxy to Chains API
GET_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # GET -> Send request to service
HEAD_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # HEAD -> Send request to service
POST_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # POST -> Send request to service
PUT_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # PUT -> Send request to service
DELETE_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # DELETE -> Send request to service
OPTIONS_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # OPTIONS -> Send request to service
PATCH_SEND_REQUEST_TO_SERVICE_V1 = "/api/v1/admin/chains/**"  # PATCH -> Send request to service

# Push Notifications Channels Service - Service to interact with Channels properties
GET_ALLOWED_CHANNELS_V1 = "/api/v1/admin/pn/config/channels"  # GET -> List Allowed Channels for Push Notifications
GET_TEMPLATES_BY_CHANNEL_V1 = "/api/v1/admin/pn/config/channels/{channel}/templates"  # GET -> List Templates by Channel
GET_TEMPLATE_DETAIL_V1 = "/api/v1/admin/pn/config/channels/{channel}/templates/{id}"  # GET -> Get Template detail

# Push Notifications Datasource Service - Service to interact with DataSource properties
GET_PUSH_NOTIFICATION_DATASOURCES_V1 = "/api/v1/admin/pn/config/datasource"  # GET -> List Push Notification DataSources
POST_UPSERT_DATASOURCE_V1 = "/api/v1/admin/pn/config/datasource"  # POST -> Upsert Push Notification DataSource configuration
PUT_UPSERT_DATASOURCE_V1 = "/api/v1/admin/pn/config/datasource"  # PUT -> Upsert Push Notification DataSource configuration
GET_DATASOURCE_CONFIGURATION_V1 = "/api/v1/admin/pn/config/datasource/{id}"  # GET -> Get Push Notification DataSource configuration
DELETE_DATASOURCE_V1 = "/api/v1/admin/pn/config/datasource/{id}"  # DELETE -> Delete the DataSource
GET_DATASOURCE_FIELDS_V1 = "/api/v1/admin/pn/config/datasource/{id}/fields"  # GET -> LOV DataSource Fields
POST_VERIFY_DATASOURCE_FIELDS_V1 = "/api/v1/admin/pn/config/datasource/{id}/verify"  # POST -> LOV DataSource Fields
GET_LOV_PUSH_NOTIFICATION_DATASOURCES_V1 = "/api/v1/admin/pn/config/datasource/lov"  # GET -> LOV Push Notification DataSources

# Push Notifications Service - Service to interact with Push Notifications properties
GET_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications"  # GET -> List Push Notifications
POST_CREATE_PUSH_NOTIFICATION_V1 = "/api/v1/admin/pn/config/pushnotifications"  # POST -> Create Push Notification configuration
PUT_UPDATE_PUSH_NOTIFICATION_V1 = "/api/v1/admin/pn/config/pushnotifications"  # PUT -> Update Push Notification configuration
GET_PUSH_NOTIFICATION_CONFIGURATION_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}"  # GET -> Get Push Notification configuration
DELETE_PUSH_NOTIFICATION_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}"  # DELETE -> Delete the Push Notifications
POST_PREPARE_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/prepare"  # POST -> Prepare Push Notifications recipients
POST_REOPEN_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/reopen"  # POST -> Reopen a Push Notification
POST_SEND_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/send"  # POST -> Send Push Notifications
POST_SETTLE_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/settle"  # POST -> Settle Push Notifications
POST_SETTLE_PREPARE_PUSH_NOTIFICATIONS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/settle-prepare"  # POST -> Settle Push Notifications
GET_PUSH_NOTIFICATION_STATISTICS_V1 = "/api/v1/admin/pn/config/pushnotifications/{id}/statistics"  # GET -> Get Push Notification Statistics

# Routing Labels Service - WebService class to manage the Routing Labels CRUD
GET_ALL_ROUTING_LABELS_V1 = "/api/v1/admin/routing/labels"  # GET -> Get a list with all the labels
GET_ROUTING_LABEL_BY_ID_V1 = "/api/v1/admin/routing/labels/{label_id}"  # GET -> Get a label by ID
POST_STORE_LABEL_BY_ID_V1 = "/api/v1/admin/routing/labels/{label_id}"  # POST -> Store a label associated to an Id
PUT_UPDATE_LABEL_BY_ID_V1 = "/api/v1/admin/routing/labels/{label_id}"  # PUT -> Update a label associated to an Id

# Routing Locale Service - WebService class to manage the Routing Locale CRUD
POST_CREATE_LOCALE_V1 = "/api/v1/admin/routing/locale/{locale}"  # POST -> Create a new locale within the repositories
DELETE_LOCALE_V1 = "/api/v1/admin/routing/locale/{locale}"  # DELETE -> Delete a locale within the response and labels repository

# Routing Reset Service - WebService class to reset the Routing config
GET_RESET_CONFIGURATION_V1 = "/api/v1/admin/reset"  # GET -> Reset the configuration

# Routing Responses Service - WebService class to manage the Routing Responses CRUD
GET_ALL_ROUTING_RESPONSES_V1 = "/api/v1/admin/routing/responses"  # GET -> Get a list with all the responses
GET_ROUTING_RESPONSE_BY_ID_V1 = "/api/v1/admin/routing/responses/{response_id}"  # GET -> Get a response by ID
POST_STORE_RESPONSES_BY_ID_V1 = "/api/v1/admin/routing/responses/{response_id}"  # POST -> Store a list of responses associated to an Id
PUT_UPDATE_RESPONSES_BY_ID_V1 = "/api/v1/admin/routing/responses/{response_id}"  # PUT -> Update a list of responses associated to an Id
DELETE_RESPONSES_BY_ID_V1 = "/api/v1/admin/routing/responses/{response_id}"  # DELETE -> Delete all the responses given an Id and locale
PUT_UPDATE_DEFAULT_TEMPLATES_V1 = "/api/v1/admin/routing/responses/update-default"  # PUT -> Update or Insert the default templates by reading the file

# Routing Service - WebService class to manage the Routing CRUD
GET_ALL_ROUTING_FLOWS_V1 = "/api/v1/admin/routing/flows"  # GET -> Get a list with all the flow names
GET_ROUTING_FLOW_BY_NAME_V1 = "/api/v1/admin/routing/flows/{flow_name}"  # GET -> Get a flow given its name
POST_STORE_ROUTING_FLOW_V1 = "/api/v1/admin/routing/flows/{flow_name}"  # POST -> Store a Routing flow configuration
PUT_UPDATE_ROUTING_FLOW_V1 = "/api/v1/admin/routing/flows/{flow_name}"  # PUT -> Update a Flow configuration
DELETE_ROUTING_FLOW_V1 = "/api/v1/admin/routing/flows/{flow_name}"  # DELETE -> Delete a flow with all related labels and responses
POST_DUPLICATE_ROUTING_FLOW_V1 = "/api/v1/admin/routing/flows/{flow_name}/duplicate"  # POST -> Create a Duplicate flow configuration
PUT_ASSIGN_FLOW_TO_FOLDER_V1 = "/api/v1/admin/routing/flows/{flow_name}/folder"  # PUT -> Assign a flow to a folder
PUT_RENAME_FLOW_V1 = "/api/v1/admin/routing/flows/{flow_name}/rename"  # PUT -> Rename a flow
PUT_SET_FLOW_STATUS_V1 = "/api/v1/admin/routing/flows/{flow_name}/set-status"  # PUT -> Enable or Disable a flow
GET_VALIDATE_FLOW_V1 = "/api/v1/admin/routing/flows/validate/{flow_name}"  # GET -> Validate a flow

# Saia Assistants Service - Service to interact with Saia Assistants
GET_ASSISTANTS_V1 = "/api/v1/admin/saia/assistants/text"  # GET -> Get Assistants
GET_ASSISTANTS_BY_ID_V1 = "/api/v1/admin/saia/assistants/text/{assistantId}"  # GET -> Get Assistants by ID

# Saia Documents Service - Service to interact with Saia documents
GET_SAIA_DOCUMENTS_ASSISTANTS_V1 = "/api/v1/admin/saia-documents/assistants"  # GET -> getAssistants
GET_DOCUMENTS_V1 = "/api/v1/admin/saia-documents/documents"  # GET -> getDocuments
UPLOAD_DOCUMENT_V1 = "/api/v1/admin/saia-documents/documents"  # POST -> uploadDocument
DELETE_DOCUMENT_V1 = "/api/v1/admin/saia-documents/documents/{documentId}"  # DELETE -> deleteDocument
GET_OR_CREATE_PROFILE_V1 = "/api/v1/admin/saia-documents/profile"  # GET -> getOrCreateProfile
UPDATE_PROFILE_V1 = "/api/v1/admin/saia-documents/profile"  # PUT -> updateProfile
GET_DOCUMENTS_BY_PROFILE_V1 = "/api/v1/admin/saia-documents/profile/{profile}/documents"  # GET -> getDocumentsByProfile
GET_PROFILES_V1 = "/api/v1/admin/saia-documents/profiles"  # GET -> getProfiles

# Saia Rag Assistants - Service to interact with Saia Rag assistants
GET_RAG_ASSISTANTS_V1 = "/api/v1/admin/saia/assistants/rag"  # GET -> getRAGAssistants

# Settings Service - Service for bot settings
GET_BOT_SETTINGS_V1 = "/api/v1/admin/settings"  # GET -> Get the bot settings
UPDATE_BOT_SETTINGS_V1 = "/api/v1/admin/settings"  # POST -> Update bot settings

# Slack Properties Service - Service to interact with Slack properties
GET_SLACK_CONFIG_V1 = "/api/v1/admin/slack/config"  # GET -> Get the Slack configuration
UPSERT_SLACK_CONFIG_V1 = "/api/v1/admin/slack/config"  # POST -> Upsert Slack configuration
DELETE_SLACK_CONFIG_V1 = "/api/v1/admin/slack/config"  # DELETE -> Delete the Slack configuration
GET_SLACK_INTEGRATION_STATUS_V1 = "/api/v1/admin/slack/config/integration"  # GET -> Get the integration status
ENABLE_DISABLE_SLACK_INTEGRATION_V1 = "/api/v1/admin/slack/config/integration"  # POST -> Enable or Disable the Slack integration

# Template Context Service - WebService class to manage the Template Context CRUD
GET_TEMPLATE_VARIABLES_V1 = "/api/v1/admin/routing/template-context/template-content"  # GET -> Get a list with all the Template variables
CREATE_UPDATE_TEMPLATE_VARIABLES_V1 = "/api/v1/admin/routing/template-context/template-content"  # POST -> Create or Update Template variables
DELETE_TEMPLATE_VARIABLE_V1 = "/api/v1/admin/routing/template-context/template-content/{id}"  # DELETE -> Delete a template variable
GET_TEMPLATE_VARIABLES_PAGE_V1 = "/api/v1/admin/routing/template-context/template-content/page"  # GET -> Get a list with all the Template variables page wise
GET_TEMPLATE_VARIABLES_SEARCH_V1 = "/api/v1/admin/routing/template-context/template-content/search"  # GET -> Get a list with all the Template variables
GET_TEMPLATE_VARIABLES_SEARCH_PAGE_V1 = "/api/v1/admin/routing/template-context/template-content/search/page"  # GET -> Get a list with all the Template variables page wise

# Webhook Admin Controller - Service to manage webhooks
GET_WEBHOOK_V1 = "/api/v1/admin/webhook"  # GET -> Retrieves webhook configure for Rest API
SAVE_WEBHOOK_V1 = "/api/v1/admin/webhook"  # POST -> Save the webhook for Rest API
DELETE_WEBHOOK_V1 = "/api/v1/admin/webhook"  # DELETE -> Delete the webhook for Rest API

# Whatsapp B2C Properties Service - Service to interact with Whatsapp using B2Chat properties
GET_WHATSAPP_CONFIG_V1 = "/api/v1/admin/whatsappb2c/config"  # GET -> Get the Whatsapp configuration
UPSERT_WHATSAPP_CONFIG_V1 = "/api/v1/admin/whatsappb2c/config"  # POST -> Upsert Whatsapp configuration
DELETE_WHATSAPP_CONFIG_V1 = "/api/v1/admin/whatsappb2c/config"  # DELETE -> Delete the Whatsapp configuration
GET_WHATSAPP_INTEGRATION_STATUS_V1 = "/api/v1/admin/whatsappb2c/config/integration"  # GET -> Get the integration status
ENABLE_DISABLE_WHATSAPP_INTEGRATION_V1 = "/api/v1/admin/whatsappb2c/config/integration"  # POST -> Enable or Disable the Whatsapp integration

# Analytics Management Controller
UPDATE_AGGREGATES_V1 = "/api/v1/admin/analytics/management/aggregates"  # PUT -> Update all aggregates with given refresh interval
UPDATE_AGGREGATE_V1 = "/api/v1/admin/analytics/management/aggregates/{aggregateName}"  # PUT -> Update aggregate with given refresh interval

# Entity Controller Impl
GET_ENTITY_LIST_V1 = "/api/v1/admin/training/data/entity"  # GET -> Get the list of entity by entity type
STORE_ENTITY_DATA_V1 = "/api/v1/admin/training/data/entity"  # POST -> Store an Entity data
GET_ENTITY_BY_NAME_V1 = "/api/v1/admin/training/data/entity/{entity_name}"  # GET -> Get an entity by name
UPDATE_ENTITY_V1 = "/api/v1/admin/training/data/entity/{entity_name}"  # PUT -> Update an entity
DELETE_ENTITY_V1 = "/api/v1/admin/training/data/entity/{entity_name}"  # DELETE -> Delete an entity
GET_ALL_ENTITY_NAMES_V1 = "/api/v1/admin/training/data/entity/name"  # GET -> Get all entity names
SEARCH_ENTITY_DATA_V1 = "/api/v1/admin/training/data/entity/search/{search_term}"  # GET -> Search all entity data

# On Demand Controller
REFRESH_USER_CONVERSATION_V1 = "/api/v1/admin/analytics/ondemand"  # GET -> refreshUserConversation

# Training Data Model Controller Impl
GET_STORED_MODELS_V1 = "/api/v1/admin/training/data/models"  # GET -> Get the list of the stored models
STORE_INTENT_DATA_V1 = "/api/v1/admin/training/data/models"  # POST -> Store an Intent data
GET_MODEL_BY_INTENT_NAME_V1 = "/api/v1/admin/training/data/models/{intent_name}"  # GET -> Get the list of the stored models
UPDATE_TRAINING_DATA_MODEL_V1 = "/api/v1/admin/training/data/models/{intent_name}"  # PUT -> Update a TrainingData model
DELETE_TRAINING_DATA_MODEL_V1 = "/api/v1/admin/training/data/models/{intent_name}"  # DELETE -> Delete a TrainingData model configuration given its id
GET_INTENT_NAMES_V1 = "/api/v1/admin/training/data/models/{model_name}/intent-names"  # GET -> Get the list of the stored models
GET_MODEL_LIST_V1 = "/api/v1/admin/training/data/models/{model_name}/list"  # GET -> Get the list of the stored models
GET_ALL_MODELS_V1 = "/api/v1/admin/training/data/models/list"  # GET -> Get the list of the stored models
GET_MODEL_NAMES_V1 = "/api/v1/admin/training/data/models/model-names"  # GET -> Get the list of the stored models
SEARCH_INTENTS_DATA_V1 = "/api/v1/admin/training/data/models/search"  # GET -> Search all intents data

# User Analytics Controller
GET_ACTIVE_USERS_COUNT_V1 = "/api/v1/admin/analytics/users/active"  # GET -> Gets count of active users over the given time period.
GET_ENGAGED_USERS_COUNT_V1 = "/api/v1/admin/analytics/users/engaged"  # GET -> Gets the count of engaged users in the time period.
GET_NEW_USERS_COUNT_V1 = "/api/v1/admin/analytics/users/new"  # GET -> Gets the count of new users over the time period.
GET_NEW_ENGAGED_USERS_COUNT_V1 = "/api/v1/admin/analytics/users/new-engaged"  # GET -> Gets the count of new users who engaged with the bot in the time period.
GET_RETENTION_RATE_V1 = "/api/v1/admin/analytics/users/retention-rate"  # GET -> Gets the count of users that return to using the chatbot in the given time frame.

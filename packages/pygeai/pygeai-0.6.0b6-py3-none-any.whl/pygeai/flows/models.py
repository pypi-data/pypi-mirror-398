from enum import Enum

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from typing import List, Optional


class ActiveDataPoint(BaseModel):
    date_time: int
    value: int


class ActiveMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: List[ActiveDataPoint]
    metric_description: str
    metric_name: str


class AgentWebhook(BaseModel):
    description: str
    headers: Dict[str, str]
    id: str
    url: str


class Aggregate(BaseModel):
    schedule_interval: int


class AnalyticsChatbotRequest(BaseModel):
    entities: Dict[str, str]
    entities_text: str
    event: str
    intent: str
    query: str
    request_id: str
    selected: bool


class GeoLocation(BaseModel):
    latitude: float
    longitude: float


class UserInfo(BaseModel):
    avatar: Optional[str]
    country: Optional[str]
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone_number: Optional[str]
    username: Optional[str]


class AnalyticsEvent(BaseModel):
    action: str
    category: str
    chat_bot_id: str
    client_id: str
    conversation_id: str
    flow: str
    label: str
    request: 'ChatbotRequest'
    request_id: str
    response: 'ChatbotResponse'
    timestamp: Optional[str]
    user_info: Optional[UserInfo]


class ApiError(BaseModel):
    args: Dict[str, str]
    code: str
    message: str
    message_key: str


class ApiKey(BaseModel):
    host: str
    key: str
    key_name: str
    type: str


class AverageSentMessageMetrics(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_description: str
    metric_name: str
    sent_messages: float


class B2ChatConfig(BaseModel):
    endpoint: str
    id: str
    integration_enabled: bool
    password: str
    username: str
    webhook: str


class BatchFAQResult(BaseModel):
    failed: bool
    id: str
    message: str


class BatchFAQResponse(BaseModel):
    results: List[BatchFAQResult]


class BillingConfiguration(BaseModel):
    bot_id: str
    bundle_session_price: float
    end_period: str
    extra_session_price: float
    id: str
    max_conversation_duration_per_session: int
    max_conversations_per_session: int
    open_billing: bool
    sessions_bundle: int
    start_period: str


class BillingRequest(BaseModel):
    end_period: str
    organization_id: str
    start_period: str


class BotDetail(BaseModel):
    id: str
    name: str
    status: str


class BotBillDetail(BaseModel):
    bot: BotDetail
    free_sessions: int
    total_sessions: int


class BotSnapshot(BaseModel):
    auto: bool
    bot_full_configuration: Dict[str, Any]
    description: str
    id: str
    name: str
    snapshot_date: str
    username: str


class Boundaries(BaseModel):
    height: float
    width: float


class BillingRuleName(str, Enum):
    BY_DURATION = "BY_DURATION"
    BY_MESSAGES = "BY_MESSAGES"
    BILLABLE_FIRST_3_BY_DAY = "BILLABLE_FIRST_3_BY_DAY"


class ByDurationRule(BaseModel):
    description: str
    duration_minutes: int
    enabled: bool
    name: BillingRuleName


class ByFirstThreeBillableRule(BaseModel):
    description: str
    enabled: bool
    name: BillingRuleName


class ByMessagesRule(BaseModel):
    description: str
    enabled: bool
    messages_limit: int
    name: BillingRuleName


class Chain(BaseModel):
    type: str


class ChatbotRequest(BaseModel):
    channel: str
    channel_id: str
    client_id: str
    context_extra_data: Dict[str, Any] = {}
    entities: Dict[str, Any] = {}
    event: str
    geo_location: Optional[GeoLocation]
    language: Optional[str]
    locale: Optional[str]
    platform: Optional[str]
    query: str
    request_extra_data: Dict[str, Any] = {}
    request_id: str
    session_id: str
    timestamp: Optional[str]
    user_info: Optional[UserInfo]


class ChatbotResponse(BaseModel):
    chatbot_request: ChatbotRequest
    chatbot_responses_history: List[Any] = []
    disable_text_interaction: bool
    extra_data: Dict[str, Any] = {}
    file_support_enabled: bool
    responses: List[Any] = []
    timestamp: str
    user_info: Optional[UserInfo]


class Chunks(BaseModel):
    chunk_overlap: int
    chunk_size: int


class CommonEntity(BaseModel):
    id: str
    set: str
    text: str


class CompletedFlowData(BaseModel):
    completed_flow_count: int
    total_flow_count: int


class CompletedFlowMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: CompletedFlowData
    metric_description: str
    metric_name: str


class Content(BaseModel):
    text: str


class Context(BaseModel):
    channel: str
    channel_id: str
    check_serializable: bool
    context_values: Dict[str, Any] = {}
    conversation_id: str
    expired: bool
    extra_data: Dict[str, Any] = {}
    flow: str
    force_prompt: bool
    locale: str
    platform: str
    session_id: str
    user_info: Optional[UserInfo]


class ContextSettings(BaseModel):
    auto_snapshot_max_count: int
    auto_snapshot_on_flow_updates_enabled: bool
    check_serializable: bool
    file_support_enabled: bool
    file_support_force_references: bool
    max_inactivity_time: int
    max_response_history: int
    revision_enabled: bool
    show_logs: bool
    store_entities_on_context: bool
    store_user_info_on_context: bool
    upload_max_file_count: int
    upload_max_file_size: int
    use_locale_from_request: bool


class ContextValue(BaseModel):
    global_: bool = Field(..., alias='global')
    lifespan: int
    time: int
    value: Any


class ContextVariable(BaseModel):
    description: str
    example: str
    id: str
    is_constant: bool
    is_protected: bool
    label: str
    type: str
    value: Any


class CreateApiKeyRequest(BaseModel):
    key_name: str
    host: str
    type: str


class CustomResolver(BaseModel):
    resolver: str
    entities: Dict[str, Any] = {}


class DataPageBotSnapshot(BaseModel):
    content: List[Any] = []
    has_more: bool
    page: int
    size: int
    total: int


class DataPageLOVRecord(BaseModel):
    content: List[Any] = []
    has_more: bool
    page: int
    size: int
    total: int


class DataPageMapStringObject(BaseModel):
    content: List[Any] = []
    has_more: bool
    page: int
    size: int
    total: int


class DataPagePNDataSource(BaseModel):
    content: List[Any] = []
    has_more: bool
    page: int
    size: int
    total: int


class DataPagePushNotification(BaseModel):
    content: List[Any] = []
    has_more: bool
    page: int
    size: int
    total: int


class DemoSettings(BaseModel):
    background: str
    show_branding: bool
    show_description: bool
    show_logs: bool
    style: str


class Embeddings(BaseModel):
    model_name: str
    provider: str


class EngagedData(BaseModel):
    active_user_count: int
    engaged_user_count: int


class EngagedMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: EngagedData
    metric_description: str
    metric_name: str


class Entity(BaseModel):
    data_details: List[Any]
    data_status: str
    editor: UserInfo
    entity_type: str
    id: str
    locale: str
    message_keys: Dict[str, Any]
    name: str
    values: List[Any]


class EntityMetadata(BaseModel):
    count_of_invalid_entities: int
    end_index: int
    entity: str
    group: str
    role: str
    start_index: int
    value: str


class EntityValue(BaseModel):
    duplicated: bool
    duplicated_synonyms: List[str]
    synonyms: List[str]
    value: str


class EventData(BaseModel):
    action: str
    category: str
    event_count: int
    label: str
    percentage: int


class EventMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_column_descriptions: Dict[str, Any]
    metric_data: List[EventData]
    metric_description: str
    metric_name: str


class ExtractedFAQ(BaseModel):
    answer: str
    question: str


class FallbackData(BaseModel):
    count: int
    id: int
    intent: str
    last_occurrence: int
    query: str
    resolved_with: str
    ticket_status: str
    updated_on: int


class FallbackFaq(BaseModel):
    answer: str
    editor: UserInfo
    id: str
    intent: str
    queries: List[str]
    questions: List[str]
    set: str
    update: bool


class FallbackIntent(BaseModel):
    data_details: List[Any]
    data_status: str
    description: str
    duplicated: bool
    editor: UserInfo
    flow_id: str
    friendly_name: str
    id: str
    locale: str
    message_keys: Dict[str, Any]
    metadata: 'IntentMetadata'
    model: str
    name: str
    personality: bool
    queries: List[str]
    training_phrases: List[str]


class FallbackQuery(BaseModel):
    queries: List[str]


class Faq(BaseModel):
    answer: str
    editor: UserInfo
    id: str
    questions: List[str]
    set: str
    update: bool


class File(BaseModel):
    absolute: bool
    absolute_file: 'File'
    absolute_path: str
    canonical_file: 'File'
    canonical_path: str
    directory: bool
    executable: bool
    file: bool
    free_space: int
    hidden: bool
    last_modified: int
    name: str
    parent: str
    parent_file: 'File'
    path: str
    readable: bool
    total_space: int
    usable_space: int
    writable: bool


class FileAttachment(BaseModel):
    external_url: str
    file_name: str
    id: str
    mime_type: str
    page_number: int
    url: str


class FingerPrintDto(BaseModel):
    trained_at: float
    version: str


class FluentLabDescriptor(BaseModel):
    allows_multi: bool
    app_description: str
    app_name: str
    app_version: str
    icon_path: str
    id: str
    settings_schema: Dict[str, Any]
    svg_content: str
    type: str


class Folder(BaseModel):
    id: str
    name: str


class FolderDto(BaseModel):
    id: str
    name: str


class Fork(BaseModel):
    content: Dict[str, Any]
    flow: str
    intent: 'Intent'
    resolver_name: str


class Fulfillment(BaseModel):
    name: str
    not_handled: bool
    prompt: bool
    prompting_context: List[str]
    results: Dict[str, Any]
    tool_call: bool


class FunnelMetric(BaseModel):
    children: List[Any]
    conversation_end_count: int
    conversation_end_percentage: float
    count: int
    entities_text: str
    fallback: bool
    flow: str
    intent: str
    percentage: float
    type: str


class IndexOptions(BaseModel):
    chunks: Chunks


class Integration(BaseModel):
    category: str
    enabled: bool
    id: str
    settings: Dict[str, Any]
    type: str


class IntentMetadata(BaseModel):
    count_of_duplicate_intent: Dict[str, int]
    count_of_invalid_intents: Dict[str, int]
    local_entities: List[str]


class Intent(BaseModel):
    data_details: List[str]
    data_status: str
    description: str
    duplicated: bool
    editor: UserInfo
    flow_id: str
    friendly_name: str
    id: str
    locale: str
    message_keys: Dict[str, List[Any]]
    metadata: IntentMetadata
    model: str
    name: str
    personality: bool
    training_phrases: List[str]
    data_messages_keys: Dict[str, Any]


class IntentDetectorConfig(BaseModel):
    enabled: bool
    fallback_intent: str
    name: str
    priority: int
    props: Dict[str, Any]
    type: str


class IntentDto(BaseModel):
    intents: List[Intent]
    metadata: IntentMetadata


class InteractionsMetric(BaseModel):
    intents: List[Any]
    message_description_key: str
    message_title_key: str
    metric_description: str
    metric_name: str


class LLMManagerRequest(BaseModel):
    model: str
    text: str
    vendor: str


class LOVRecord(BaseModel):
    description: str
    id: str


class Label(BaseModel):
    id: str
    key: str
    locale: str
    text: str


class LabelDto(BaseModel):
    key: str
    locale: str
    value: str


class LangflowFlow(BaseModel):
    data: Dict[str, Any]
    description: str
    id: str
    name: str
    validation: Dict[str, Any]


class LlamaIndexDocument(BaseModel):
    exists_in_file_storage: bool
    file_name: str
    id: str
    tags: List[str]
    text: str
    updated: str
    url: str
    exits_in_file_storage: bool


class LLM(BaseModel):
    cache: bool
    frequency_penalty: int
    max_tokens: int
    model_name: str
    n: int
    presence_penalty: int
    provider: str
    stream: bool
    temperature: int
    top_p: int
    verbose: bool


class MessageInfo(BaseModel):
    count: int
    intent_label: str


class MessageMetrics(BaseModel):
    intents: List[Any]
    message_description_key: str
    message_title_key: str
    metric_description: str
    metric_name: str


class Metadata(BaseModel):
    boundaries: Boundaries
    bounget_boundaries: Boundaries
    gotos: List[Any]


class Metadatum(BaseModel):
    key: str
    type: str
    value: str


class Model(BaseModel):
    id: str
    locale: str


class ModelConfig(BaseModel):
    model: str
    threshold: float


class MostUsedFlowData(BaseModel):
    complete_flow_count: int
    flow: str
    incomplete_flow_count: int
    label: str
    last_occurrence: int
    total_interactions: int


class MostUsedFlowMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: List[MostUsedFlowData]
    metric_description: str
    metric_name: str


class MostUsedIntentData(BaseModel):
    intent: str
    last_occurrence: int
    queries: int
    total_matches: int


class MostUsedIntentMetrics(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: List[MostUsedIntentData]
    metric_description: str
    metric_name: str


class NLUPipeline(BaseModel):
    fallback_intent: str
    id: str
    intent_detectors: List[Any]
    nlupipeline_configuration_defined: bool


class NLUPipelineContext(BaseModel):
    intents_by_intent_detector: Dict[str, Any]
    intents_by_priority_group: Dict[str, Any]
    last_executed_priority_group: int
    optimal_intents_by_priority_group: Dict[str, Any]


class NewEngagedData(BaseModel):
    new_engaged_user_count: int
    new_user_count: int


class NewEngagedMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: NewEngagedData
    metric_description: str
    metric_name: str


class NewUserData(BaseModel):
    active_user_count: int
    new_user_count: int


class NewUserMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: NewUserData
    metric_description: str
    metric_name: str


class Organization(BaseModel):
    id: str
    name: str


class OrganizationBill(BaseModel):
    bill_date: str
    billing_configuration: BillingConfiguration
    bots: List[Any]
    extra_sessions: int
    free_sessions: int
    id: str
    organization: Organization
    total_extra_sessions_cost: float
    total_sessions: int
    total_sessions_cost: float


class PNDataSource(BaseModel):
    id: str
    uri: str
    name: str
    description: Optional[str]
    token: str
    schema: Optional[str]
    type: str  # Enum: [ API, FILE ]
    enabled: bool
    verified: bool


class PNStatistics(BaseModel):
    answered: int
    delivered: int
    errors: int
    ignored: int
    recipients: int
    sent: int


class Sort(BaseModel):
    empty: bool
    sorted: bool
    unsorted: bool


class Pageable(BaseModel):
    offset: int
    page_number: int
    page_size: int
    paged: bool
    sort: Sort
    unpaged: bool


class Page(BaseModel):
    content: List[dict]
    empty: bool
    first: bool
    last: bool
    number: int
    number_of_elements: int
    pageable: Pageable
    size: int
    sort: Sort
    total_elements: int
    total_pages: int


class ParameterPrompt(BaseModel):
    force_prompt: bool
    parameter: str
    resolver: str
    results: dict


class Personality(BaseModel):
    answers: List[str]
    data_details: List[str]
    data_status: str  # Enum Array [ 2 ]
    description: str
    editor: UserInfo
    flow_id: str
    friendly_name: str
    intent_name: str
    locale: str
    message_keys: dict
    model: str
    phrases: List[str]


class PersonalityMetadata(BaseModel):
    count_of_invalid_personalities: int


class PersonalityDto(BaseModel):
    metadata: PersonalityMetadata
    personalities: Page


class PipelineResolverDto(BaseModel):
    name: str
    set: str
    locale: str
    resolver_configs: List[dict]


class Plugin(BaseModel):
    max_token_send_limit: str
    model_id: str
    model_name: str
    plugin_description: str
    plugin_id: str
    plugin_name: str
    plugin_type: str
    provider_name: str
    streams: bool
    supported_categories: str
    supported_file_extensions: str
    supports_multimodal: bool
    temperature: float


class ProcessResult(BaseModel):
    created: int
    name: str
    reference: dict
    updated: int


class Profiling(BaseModel):
    name: str
    operator: str  # Enum Array [ 8 ]
    value: str


class Prompt(BaseModel):
    model: str
    prompt: str
    system: str
    temperature: float
    vendor: str


class PromptInjectionDetectionSettings(BaseModel):
    enabled_heuristic_detection: bool
    enabled_model_detection: bool
    heuristic_detection_threshold: float
    max_length_prompt: int
    model_detection_threshold: float


class PromptTemplate(BaseModel):
    id: str
    template: str


class PushNotificationStatus(str, Enum):
    DRAFT = "Draft"
    SETTLED = "Settled"
    SENT = "Sent"
    READY_TO_SEND = "ReadyToSend"
    TEMPLATE_CHANGED = "TemplateChanged"
    PREPARING_TO_SEND = "PreparingToSend"
    SENDING = "Sending"
    SCHEDULED = "Scheduled"
    ERROR = "Error"


class PushNotification(BaseModel):
    flow_name: str
    id: str
    name: str
    description: str
    channel: str
    datasource: str
    locale: str
    status: PushNotificationStatus
    created: str  # ISO 8601 datetime
    modified: str  # ISO 8601 datetime
    sent: Optional[str]  # ISO 8601 datetime
    template: str
    notes: Dict[str, str]
    event: str
    recipientname: str
    recipientnumber: str
    recipients: int


class QueryInfo(BaseModel):
    last_occurrence: int
    query: str
    total_matches: int


class QueryInfoMetrics(BaseModel):
    intent: str
    message_description_key: str
    message_title_key: str
    metric_data: List[QueryInfo]
    metric_description: str
    metric_name: str
    queries: int
    total_matches: int


class QuotasSettings(BaseModel):
    active_sessions: int
    session_queries_per_minute: int


class Response(BaseModel):
    content: str
    extra_data: Dict[str, str]
    id: str
    locale: str
    name: str
    platform: str
    prompt: bool
    template: str
    type: Literal["TEXT", "SSML", "RICH_MESSAGE", "ASSISTANT_TOOL"]


class RetentionRateData(BaseModel):
    retained_engaged_user_count: int
    total_engaged_user_count: int


class RetentionRateMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: RetentionRateData
    metric_description: str
    metric_name: str


class ModelStatus(BaseModel):
    approx_training_time: float
    entities_with_issues: bool
    id: str
    intent_with_issues: bool
    locale: str
    model: str
    model_file: str
    not_handled_error_list: List[str]
    personality_with_issues: bool
    status: Literal[
        "AWAITING_TRAINING", "TRAINED", "TRAINING", "ERROR_WHILE_TRAINING", "WITHOUT_MODEL", "UPLOADING_DATA"
    ]
    training_start: str


class TrainingServerStatusDto(BaseModel):
    fingerprint: FingerPrintDto
    model_file: str
    num_active_training_jobs: int
    trained_at_training_server: bool
    training_progress: float


class StatusResponseDto(BaseModel):
    model_status: ModelStatus
    server_status: TrainingServerStatusDto


class Template(BaseModel):
    description: str
    dynamic_component: bool
    id: str
    key: str
    locale: str
    platform: str
    type: List[int]
    value: List[Any]


class Timestamp(BaseModel):
    date: int
    day: int
    hours: int
    minutes: int
    month: int
    nanos: int
    seconds: int
    time: int
    timezone_offset: int
    year: int


class TotalEventData(BaseModel):
    date_time: int
    value: int


class TotalEventMetric(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_data: List[TotalEventData]
    metric_description: str
    metric_name: str


class TrainedModel(BaseModel):
    creation_time: str
    file_location: str
    id: str
    model_locale: str
    model_name: str
    user_info: UserInfo


class TrainingDataConfig(BaseModel):
    config_name: str
    editor: UserInfo
    id: str
    language: str
    pipeline: List[Dict[str, Any]]


class TrainingDataConfigDto(BaseModel):
    config_name: str
    id: str
    language: str
    pipeline: List[Dict[str, Any]]


class Segment(BaseModel):
    entity_type: str
    group: str
    role: str
    text: str


class TrainingPhrase(BaseModel):
    duplicated: bool
    segments: List[Segment]
    text: str


class TrainingResultDto(BaseModel):
    entities_with_issues: bool
    intent_with_issues: bool
    locale: str
    model_name: str
    not_handled_error_keys_list: List[str]
    not_handled_error_list: List[str]
    personality_with_issues: bool
    successful_training: bool


class AnalyticsTranscriptsResponse(BaseModel):
    content: str
    extra_data: Dict[str, Any]
    name: str
    prompt: bool
    template: str
    type: Literal["TEXT", "SSML", "RICH_MESSAGE", "ASSISTANT_TOOL"]


class TranscriptData(BaseModel):
    logs: List[Any]
    request: AnalyticsChatbotRequest
    responses: List[AnalyticsTranscriptsResponse]


class ConversationData(BaseModel):
    client_id: str
    conversation_id: str
    locale: str
    logs: List[str]
    platform: str
    query: str
    timestamp: int
    transcripts: List[TranscriptData]
    user_id: int
    user_info: UserInfo
    username: str


class TranscriptMetric(BaseModel):
    conversations: List[ConversationData]


class Transition(BaseModel):
    id: str
    condition: str
    next_state: str = Field(..., alias="next-state")
    next_flow: str = Field(..., alias="next-flow")
    event: str
    keywords: List[str]
    index: int


class URI(BaseModel):
    absolute: bool
    authority: str
    fragment: str
    host: str
    opaque: bool
    path: str
    port: Optional[int]
    query: str
    raw_authority: str
    raw_fragment: str
    raw_path: str
    raw_query: str
    raw_scheme_specific_part: str
    raw_user_info: str
    scheme: str
    scheme_specific_part: str
    user_info: str


class URL(BaseModel):
    authority: str
    content: Dict[str, Any]
    default_port: Optional[int]
    file: str
    host: str
    path: str
    port: Optional[int]
    protocol: str
    query: str
    ref: str
    user_info: str


class UnansweredMessageMetrics(BaseModel):
    message_description_key: str
    message_title_key: str
    metric_description: str
    metric_name: str
    total_message: int
    unanswered_message: int


class UpdateCommonEntityRequest(BaseModel):
    add_entities: List[CommonEntity]
    delete_entities: List[CommonEntity]


class PageConversationData(BaseModel):
    content: List[ConversationData]
    empty: bool
    first: bool
    last: bool
    number: int
    number_of_elements: int
    pageable: Pageable
    size: int
    sort: Sort
    total_elements: int
    total_pages: int


class UserConversation(BaseModel):
    conversations: PageConversationData


class UserInformation(BaseModel):
    avatar: str
    client_id: str
    count: int
    country: str
    first_seen: int
    id: int
    last_seen: int
    username: str


class ValidationFailure(BaseModel):
    id: str
    message: str
    validation_level: str  # ENUM: [WARNING, ERROR]


class Validator(BaseModel):
    entity: str
    entity_type: str = Field(..., alias="entity-type")
    intents: List[str]
    type: str


class Variable(BaseModel):
    key: str
    value: str


class Webhook(BaseModel):
    description: str
    headers: Dict[str, str]
    id: str
    url: str


class WhatsappB2CConfig(BaseModel):
    client: str
    endpoint: str
    id: str
    integration_enabled: bool
    push_notification_allowed: bool
    secret: str
    security_endpoint: str


class WhatsappConfig(BaseModel):
    appsecret: str
    endpoint: str
    id: str
    integration_enabled: bool
    jwt: str
    phone: str
    phoneid: str
    push_notification_allowed: bool
    verify: str
    wbai: str

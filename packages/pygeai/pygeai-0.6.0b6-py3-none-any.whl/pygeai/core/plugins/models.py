from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from uuid import UUID

from pygeai.core import CustomBaseModel


class PluginBase(CustomBaseModel):
    can_regenerate_answer: bool = Field(..., alias="canRegenerateAnswer")
    can_show_preview: bool = Field(..., alias="canShowPreview")
    full_conversation: bool = Field(..., alias="fullConversation")
    max_output_tokens: int = Field(..., alias="maxOutputTokens")
    must_trigger_initial_message: bool = Field(..., alias="mustTriggerInitialMessage")
    plugin_id: str = Field(..., alias="pluginId")
    plugin_name: str = Field(..., alias="pluginName")
    plugin_type: str = Field(..., alias="pluginType")
    share_scope: str = Field(..., alias="shareScope")
    streams: bool = Field(..., alias="streams")
    supports_raw_html: bool = Field(..., alias="supportsRawHtml")
    upload_files: bool = Field(..., alias="uploadFiles")
    upload_max_file_count: int = Field(..., alias="uploadMaxFileCount")
    upload_max_file_size: int = Field(..., alias="uploadMaxFileSize")
    plugin_description: Optional[str] = Field(None, alias="pluginDescription")
    temperature: Optional[float] = Field(None, alias="temperature")

    class Config:
        populate_by_name = True

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class DataAnalystPlugin(PluginBase):
    model_id: UUID = Field(..., alias="modelId")
    model_name: str = Field(..., alias="modelName")
    provider_name: str = Field(..., alias="providerName")


class TextPromptAssistantPlugin(PluginBase):
    input_moderation: bool = Field(..., alias="inputModeration")
    llm_output: bool = Field(..., alias="llmOutput")
    max_token_send_limit: int = Field(..., alias="maxTokenSendLimit")
    model_id: UUID = Field(..., alias="modelId")
    model_name: str = Field(..., alias="modelName")
    prompt_injection: bool = Field(..., alias="promptInjection")
    provider_name: str = Field(..., alias="providerName")
    supported_categories: str = Field(..., alias="supportedCategories")
    supported_file_extensions: str = Field(..., alias="supportedFileExtensions")
    supports_multimodal: bool = Field(..., alias="supportsMultimodal")
    supports_function_calling: Optional[bool] = Field(None, alias="supportsFunctionCalling")
    supports_tool_calling: Optional[bool] = Field(None, alias="supportsToolCalling")
    plugin_icon: Optional[str] = Field(None, alias="pluginIcon")


class RAGPlugin(CustomBaseModel):
    pass


class AgentPlugin(CustomBaseModel):
    max_token_send_limit: Optional[int] = Field(None, alias="maxTokenSendLimit")
    model_id: Optional[UUID] = Field(None, alias="modelId")
    model_name: Optional[str] = Field(None, alias="modelName")
    provider_name: Optional[str] = Field(None, alias="providerName")
    supported_categories: Optional[str] = Field(None, alias="supportedCategories")
    supported_file_extensions: Optional[str] = Field(None, alias="supportedFileExtensions")
    supports_function_calling: Optional[bool] = Field(None, alias="supportsFunctionCalling")
    supports_multimodal: Optional[bool] = Field(None, alias="supportsMultimodal")
    supports_tool_calling: Optional[bool] = Field(None, alias="supportsToolCalling")
    plugin_icon: Optional[str] = Field(None, alias="pluginIcon")


class PluginsResponse(CustomBaseModel):
    plugins: List[PluginBase] = Field(..., alias="plugins")

    class Config:
        populate_by_name = True

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


from datetime import datetime
from typing import Optional, Literal, Dict, List

from pydantic import Field, field_validator

from pygeai.core import CustomBaseModel
from pygeai.core.models import ChatVariableList, Assistant, LlmSettings


class DocumentMetadata(CustomBaseModel):
    """
    Represents metadata for a document in key-value format.
    """
    key: str = Field(..., alias="key", description="The key of the metadata")
    value: str = Field(..., alias="value", description="The value of the metadata")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class Document(CustomBaseModel):
    """
    Represents a document with associated metadata and properties.
    """
    id: str = Field(..., alias="id", description="Unique identifier of the document")
    chunks: str = Field(..., alias="chunks", description="Content chunks of the document")
    name: Optional[str] = Field(None, alias="name", description="Name of the document")
    extension: str = Field(..., alias="extension", description="File extension of the document")
    index_status: str = Field(..., alias="indexStatus", description="Indexing status of the document")
    metadata: Optional[List[DocumentMetadata]] = Field([], alias="metadata", description="List of metadata associated with the document")
    timestamp: Optional[datetime] = Field(None, alias="timestamp", description="Timestamp of the document")
    url: str = Field(..., alias="url", description="URL of the document")

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value):
        if isinstance(value, list):
            return [DocumentMetadata.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "id": self.id,
            "chunks": self.chunks,
            "name": self.name,
            "extension": self.extension,
            "indexStatus": self.index_status,
            "metadata": [meta.to_dict() for meta in self.metadata] if self.metadata else None,
            "timestamp": self.timestamp,
            "url": self.url
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class Search(CustomBaseModel):
    """
    Represents search configuration for querying documents.
    """
    k: int = Field(..., alias="k", description="Number of results to return")
    type: Literal["similarity", "mmr"] = Field("similarity", alias="type", description="Type of search algorithm to use")
    fetch_k: Optional[float] = Field(None, alias="fetchK", description="Number of documents to fetch for MMR search")
    lambda_: Optional[float] = Field(None, alias="lambda", description="Lambda parameter for MMR search")
    prompt: str = Field(..., alias="prompt", description="Search prompt or query")
    return_source_documents: bool = Field(..., alias="returnSourceDocuments", description="Whether to return source documents")
    score_threshold: float = Field(..., alias="scoreThreshold", description="Score threshold for search results")
    template: str = Field(..., alias="template", description="Template for formatting search results")

    def to_dict(self):
        result = {
            "k": self.k,
            "type": self.type,
            "fetchK": self.fetch_k,
            "lambda": self.lambda_,
            "prompt": self.prompt,
            "returnSourceDocuments": self.return_source_documents,
            "scoreThreshold": self.score_threshold,
            "template": self.template
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class RetrieverOptions(CustomBaseModel):
    """
    Represents options for the retriever used in search.
    """
    type: Literal["vectorStore", "multiQuery", "selfQuery", "hyde", "contextualCompression"] = Field(..., alias="type", description="Type of retriever to use")
    search_type: Optional[str] = Field("similarity", alias="searchType", description="Search type for Azure AISearch")
    step: Optional[Literal["all", "documents"]] = Field("all", alias="step", description="Step for retrieval process")
    prompt: Optional[str] = Field(None, alias="prompt", description="Custom prompt for retriever, if applicable")

    def to_dict(self):
        result = {
            "type": self.type,
            "searchType": self.search_type,
            "step": self.step,
            "prompt": self.prompt
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ChainOptions(CustomBaseModel):
    """
    Represents options for the processing chain.
    """
    type: str = Field(..., alias="type", description="Type of processing chain")

    def to_dict(self):
        return {"type": self.type}

    def __str__(self):
        return str(self.to_dict())


class EmbeddingsOptions(CustomBaseModel):
    """
    Represents configuration for embeddings.
    """
    dimensions: int = Field(..., alias="dimensions", description="Number of dimensions for embeddings")
    model_name: str = Field(..., alias="modelName", description="Name of the embedding model")
    provider: str = Field(..., alias="provider", description="Provider of the embedding model")
    use_proxy: Optional[bool] = Field(False, alias="useProxy", description="Whether to use a proxy for embedding requests")

    def to_dict(self):
        result = {
            "dimensions": self.dimensions,
            "modelName": self.model_name,
            "provider": self.provider,
            "useProxy": self.use_proxy
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class IngestionOptions(CustomBaseModel):
    """
    Represents configuration for document ingestion.
    """
    geai_options: Dict = Field(..., alias="geaiOptions", description="GEAI-specific ingestion options")
    llama_parse_options: Dict = Field(..., alias="llamaParseOptions", description="LlamaParse-specific ingestion options")
    provider: str = Field(..., alias="provider", description="Provider for ingestion")

    def to_dict(self):
        result = {
            "geaiOptions": self.geai_options,
            "llamaParseOptions": self.llama_parse_options,
            "provider": self.provider
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class SearchOptions(CustomBaseModel):
    """
    Represents comprehensive search options for RAG.
    """
    history_count: int = Field(..., alias="historyCount", description="Number of history items to consider")
    llm: LlmSettings = Field(..., alias="llm", description="LLM settings for search")
    search: Search = Field(..., alias="search", description="Search configuration")
    retriever: RetrieverOptions = Field(..., alias="retriever", description="Retriever configuration")
    chain: Optional[ChainOptions] = Field(None, alias="chain", description="Chain configuration")
    embeddings: Optional[EmbeddingsOptions] = Field(None, alias="embeddings", description="Embeddings configuration")
    ingestion: Optional[IngestionOptions] = Field(None, alias="ingestion", description="Ingestion configuration")
    options: Optional[Dict] = Field(None, alias="options", description="Additional options")
    rerank: Optional[Dict] = Field(None, alias="rerank", description="Rerank configuration")
    variables: Optional[ChatVariableList] = Field(None, alias="variables", description="Variables for search")
    vector_store: Optional[Dict] = Field(None, alias="vectorStore", description="Vector store configuration")

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value):
        if isinstance(value, dict):
            return Search.model_validate(value)
        return value

    @field_validator("retriever", mode="before")
    @classmethod
    def normalize_retriever(cls, value):
        if isinstance(value, dict):
            return RetrieverOptions.model_validate(value)
        return value

    @field_validator("chain", mode="before")
    @classmethod
    def normalize_chain(cls, value):
        if isinstance(value, dict):
            return ChainOptions.model_validate(value)
        return value

    @field_validator("embeddings", mode="before")
    @classmethod
    def normalize_embeddings(cls, value):
        if isinstance(value, dict):
            return EmbeddingsOptions.model_validate(value)
        return value

    @field_validator("ingestion", mode="before")
    @classmethod
    def normalize_ingestion(cls, value):
        if isinstance(value, dict):
            return IngestionOptions.model_validate(value)
        return value

    def to_dict(self):
        result = {
            "historyCount": self.history_count,
            "llm": self.llm.to_dict() if self.llm else None,
            "search": self.search.to_dict() if self.search else None,
            "retriever": self.retriever.to_dict() if self.retriever else None,
            "chain": self.chain.to_dict() if self.chain else None,
            "embeddings": self.embeddings.to_dict() if self.embeddings else None,
            "ingestion": self.ingestion.to_dict() if self.ingestion else None,
            "options": self.options,
            "rerank": self.rerank,
            "variables": self.variables.to_list() if self.variables else None,
            "vectorStore": self.vector_store
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ChildOptions(CustomBaseModel):
    """
    Represents options for child document processing.
    """
    chunk_size: float = Field(..., alias="chunkSize", description="Size of chunks for child documents")
    chunk_overlap: float = Field(..., alias="chunkOverlap", description="Overlap between chunks for child documents")
    content_processing: Optional[Literal["", "clean"]] = Field("", alias="contentProcessing", description="Content processing mode for child documents")

    def to_dict(self):
        result = {
            "chunkSize": self.chunk_size,
            "chunkOverlap": self.chunk_overlap,
            "contentProcessing": self.content_processing
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ChildDocumentOptions(CustomBaseModel):
    """
    Represents options for child document retrieval.
    """
    child_k: float = Field(..., alias="childK", description="Number of child documents to retrieve")
    child: ChildOptions = Field(..., alias="child", description="Child document processing options")

    @field_validator("child", mode="before")
    @classmethod
    def normalize_child(cls, value):
        if isinstance(value, dict):
            return ChildOptions.model_validate(value)
        return value

    def to_dict(self):
        result = {
            "childK": self.child_k,
            "child": self.child.to_dict() if self.child else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ChunkOptions(CustomBaseModel):
    """
    Represents chunking options for document processing.
    """
    chunk_overlap: int = Field(..., alias="chunkOverlap", description="Overlap between chunks")
    chunk_size: int = Field(..., alias="chunkSize", description="Size of each chunk")

    def to_dict(self):
        result = {
            "chunkOverlap": self.chunk_overlap,
            "chunkSize": self.chunk_size
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class IndexOptions(CustomBaseModel):
    """
    Represents indexing options for documents.
    """
    chunks: ChunkOptions = Field(..., alias="chunks", description="Chunking configuration for indexing")
    use_parent_document: Optional[bool] = Field(False, alias="useParentDocument", description="Whether to use parent document for indexing")
    child_document: Optional[ChildDocumentOptions] = Field(None, alias="childDocument", description="Child document options if use_parent_document is True")

    @field_validator("chunks", mode="before")
    @classmethod
    def normalize_chunks(cls, value):
        if isinstance(value, dict):
            return ChunkOptions.model_validate(value)
        return value

    @field_validator("child_document", mode="before")
    @classmethod
    def normalize_child_document(cls, value):
        if isinstance(value, dict):
            return ChildDocumentOptions.model_validate(value)
        return value

    def to_dict(self):
        result = {
            "chunks": self.chunks.to_dict() if self.chunks else None,
            "useParentDocument": self.use_parent_document,
            "childDocument": self.child_document.to_dict() if self.child_document else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class RAGAssistant(Assistant):
    """
    Represents a RAG (Retrieval-Augmented Generation) assistant configuration.
    """
    template: Optional[str] = Field(None, alias="template", description="Template for RAG assistant responses")
    search_options: Optional[SearchOptions] = Field(None, alias="searchOptions", description="Search options for RAG")
    index_options: Optional[IndexOptions] = Field(None, alias="indexOptions", description="Indexing options for RAG")

    @field_validator("search_options", mode="before")
    @classmethod
    def normalize_search_options(cls, value):
        if isinstance(value, dict):
            return SearchOptions.model_validate(value)
        return value

    @field_validator("index_options", mode="before")
    @classmethod
    def normalize_index_options(cls, value):
        if isinstance(value, dict):
            return IndexOptions.model_validate(value)
        return value

    def to_dict(self):
        assistant = super().to_dict()
        result = {
            "template": self.template,
            "searchOptions": self.search_options.to_dict() if self.search_options else None,
            "indexOptions": self.index_options.to_dict() if self.index_options else None
        }
        assistant.update({k: v for k, v in result.items() if v is not None})
        return assistant

    def __str__(self):
        return str(self.to_dict())


class UploadDocument(CustomBaseModel):
    """
    Represents a document to be uploaded.
    """
    path: str = Field(..., alias="path", description="Path to the document file")
    upload_type: Literal["binary", "multipart"] = Field("multipart", alias="uploadType", description="Type of upload method")
    metadata: Optional[dict] = Field(None, alias="metadata", description="Metadata associated with the document")
    content_type: str = Field(..., alias="contentType", description="Content type of the document")

    def to_dict(self):
        result = {
            "path": self.path,
            "uploadType": self.upload_type,
            "metadata": self.metadata,
            "contentType": self.content_type
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class UploadType:
    BINARY = "binary"
    MULTIPART = "multipart"
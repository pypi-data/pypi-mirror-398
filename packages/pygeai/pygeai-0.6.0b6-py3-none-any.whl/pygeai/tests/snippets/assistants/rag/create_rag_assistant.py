from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import WelcomeData, LlmSettings
from pygeai.assistant.rag.models import Search, RetrieverOptions, SearchOptions, ChunkOptions, IndexOptions, \
    RAGAssistant

manager = AssistantManager()

llm_options = LlmSettings(
    cache=False,
    temperature=0.1,
    max_tokens=999,
    model_name="gpt-3.5-turbo-16k",
    n=1,
    presence_penalty=0,
    frequency_penalty=0,
    provider="OpenAI",
    stream=False,
    top_p=1.0,
    type=None,
    verbose=True
)

retriever_options = RetrieverOptions(
    type="vectorStore"
)

search_options = SearchOptions(
    history_count=2,
    llm=llm_options,
    search=Search(
        k=5,
        return_source_documents=False,
        score_threshold=0,
        prompt="Use {context} and {question}",
        template=""
    ),
    retriever=retriever_options
)

chunk_options = ChunkOptions(
    chunk_size=999,
    chunk_overlap=0
)

index_options = IndexOptions(
    chunks=chunk_options
)

welcome_data = WelcomeData(
    title="Test Profile Welcome Data",
    description="Test Profile with WelcomeData",
    features=[],
    examples_prompt=[]
)

rag_assistant = RAGAssistant(
    name="TestRAG3",
    description="Test Profile with WelcomeData",
    search_options=search_options,
    index_options=index_options,
    welcome_data=welcome_data
)

response = manager.create_assistant(rag_assistant)
print(f"response: {response}")
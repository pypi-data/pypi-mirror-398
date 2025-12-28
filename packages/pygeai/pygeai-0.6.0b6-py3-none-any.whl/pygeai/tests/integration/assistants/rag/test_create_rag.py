from unittest import TestCase
import uuid
from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import WelcomeData, LlmSettings
from pygeai.assistant.rag.models import (
    Search,
    RetrieverOptions,
    SearchOptions,
    ChunkOptions,
    IndexOptions,
    RAGAssistant,
)


class TestAssistantCreateRagIntegration(TestCase):

    def setUp(self):
        """
        Set up the test environment.
        """
        self.assistant_manager = AssistantManager()

        self.new_rag = self.__load_rag()
        self.created_rag: RAGAssistant = None


    def tearDown(self):
        """
        Clean up after each test if necessary.
        This can be used to delete the created tool
        """
        if isinstance(self.created_rag, RAGAssistant):
            self.assistant_manager.delete_assistant(assistant_name=self.created_rag.name)            


    def __load_rag(self):
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
            verbose=True,
        )

        retriever_options = RetrieverOptions(type="vectorStore")

        search_options = SearchOptions(
            history_count=2,
            llm=llm_options,
            search=Search(
                k=5,
                return_source_documents=False,
                score_threshold=0,
                prompt="Use {context} and {question}",
                template="",
            ),
            retriever=retriever_options,
        )

        chunk_options = ChunkOptions(chunk_size=999, chunk_overlap=0)

        index_options = IndexOptions(chunks=chunk_options)

        welcome_data = WelcomeData(
            title="Test Profile Welcome Data",
            description="Test Profile with WelcomeData",
            features=[],
            examples_prompt=[],
        )

        return RAGAssistant(
            name=str(uuid.uuid4()),
            description="Test Profile with WelcomeData",
            search_options=search_options,
            index_options=index_options,
            welcome_data=welcome_data,
        )


    def test_create_rag_assistant(self):
        rag_assistant = self.__load_rag()
        self.created_rag = self.assistant_manager.create_assistant(rag_assistant)

        self.assertIsInstance(self.created_rag, RAGAssistant, "Failed to create RAG assistant")

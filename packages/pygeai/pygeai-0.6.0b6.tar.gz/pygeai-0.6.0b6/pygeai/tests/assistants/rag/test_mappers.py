import unittest
from pygeai.assistant.rag.mappers import RAGAssistantMapper
from pygeai.assistant.rag.models import RAGAssistant, SearchOptions, Search, RetrieverOptions, EmbeddingsOptions, \
    IngestionOptions, IndexOptions, ChunkOptions, ChatVariableList, ChainOptions
from pygeai.core.models import ChatVariable


class TestRAGAssistantMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.rag.test_mappers.TestRAGAssistantMapper
    """

    def setUp(self):
        self.response_data = {
            'description': 'Test Profile with WelcomeData',
            'indexOptions': {
                'chunks': {
                    'chunkOverlap': 100,
                    'chunkSize': 999
                }
            },
            'name': 'TestRAG2',
            'searchOptions': {
                'chain': {'type': 'stuff'},
                'embeddings': {
                    'dimensions': 1536,
                    'modelName': 'text-embedding-3-small',
                    'provider': 'openai',
                    'useProxy': True
                },
                'historyCount': 2,
                'ingestion': {
                    'geaiOptions': {},
                    'llamaParseOptions': {},
                    'provider': 'geai'
                },
                'llm': {
                    'cache': False,
                    'frequencyPenalty': 0,
                    'maxTokens': 999,
                    'modelName': 'gpt-3.5-turbo-16k',
                    'n': 1,
                    'presencePenalty': 0,
                    'provider': 'openai',
                    'stream': False,
                    'temperature': 0.1,
                    'topP': 1,
                    'verbose': False
                },
                'options': {},
                'rerank': {},
                'retriever': {
                    'searchType': 'similarity',
                    'step': 'all',
                    'type': 'vectorStore'
                },
                'search': {
                    'chunkDocument': {},
                    'fetchK': 0,
                    'k': 5,
                    'lambda': 0,
                    'prompt': 'Use {context} and {question}',
                    'returnSourceDocuments': False,
                    'scoreThreshold': 0.0,
                    'template': 'Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.\r\n\r\nChat History:\r\n{chat_history}\r\nFollow-Up Input: {question}\r\nStandalone question:',
                    'type': 'similarity'
                },
                'variables': [
                    {'key': 'context'},
                    {'key': 'question'},
                    {'key': 'chat_history'},
                    {'key': 'question'}
                ],
                'vectorStore': {}
            },
            'status': 1,
            'welcomeData': {
                'description': 'Test Profile with WelcomeData',
                'title': 'Test Profile Welcome Data'
            }
        }

    def test_map_to_rag_assistant(self):
        result = RAGAssistantMapper.map_to_rag_assistant(self.response_data)

        self.assertIsInstance(result, RAGAssistant)
        self.assertEqual(result.name, 'TestRAG2')
        self.assertEqual(result.type, 'rag')
        self.assertEqual(result.status, 1)
        self.assertEqual(result.description, 'Test Profile with WelcomeData')
        self.assertIsNone(result.prompt) 
        self.assertIsNone(result.template) 
        self.assertIsNotNone(result.llm_settings)
        self.assertIsNotNone(result.welcome_data)
        self.assertIsNotNone(result.search_options)
        self.assertIsNotNone(result.index_options)

    def test_map_to_search_options(self):
        search_options_data = self.response_data['searchOptions']
        result = RAGAssistantMapper.map_to_search_options(search_options_data)

        self.assertIsInstance(result, SearchOptions)
        self.assertEqual(result.history_count, 2)
        self.assertIsNotNone(result.llm)
        self.assertEqual(result.llm.model_name, 'gpt-3.5-turbo-16k')
        self.assertEqual(result.llm.provider_name, 'openai')
        self.assertEqual(result.llm.temperature, 0.1)
        self.assertIsInstance(result.search, Search)
        self.assertIsInstance(result.retriever, RetrieverOptions)
        self.assertEqual(result.chain, ChainOptions(type="stuff"))
        self.assertIsInstance(result.embeddings, EmbeddingsOptions)
        self.assertIsInstance(result.ingestion, IngestionOptions)
        self.assertEqual(result.options, {})
        self.assertEqual(result.rerank, {})
        self.assertIsInstance(result.variables, ChatVariableList)
        self.assertEqual(result.vector_store, None)

    def test_map_to_search(self):
        search_data = self.response_data['searchOptions']['search']
        result = RAGAssistantMapper.map_to_search(search_data)

        self.assertIsInstance(result, Search)
        self.assertEqual(result.k, 5)
        self.assertEqual(result.type, 'similarity')
        self.assertEqual(result.fetch_k, 0)
        self.assertEqual(result.lambda_, 0)
        self.assertEqual(result.prompt, 'Use {context} and {question}')
        self.assertFalse(result.return_source_documents)
        self.assertEqual(result.score_threshold, 0.0)
        self.assertEqual(result.template, 'Given the following conversation and a follow-up question, rephrase the follow-up question to be a standalone question.\r\n\r\nChat History:\r\n{chat_history}\r\nFollow-Up Input: {question}\r\nStandalone question:')

    def test_map_to_retriever_options(self):
        retriever_data = self.response_data['searchOptions']['retriever']
        result = RAGAssistantMapper.map_to_retriever_options(retriever_data)

        self.assertIsInstance(result, RetrieverOptions)
        self.assertEqual(result.type, 'vectorStore')
        self.assertEqual(result.search_type, 'similarity')
        self.assertEqual(result.step, 'all')
        self.assertIsNone(result.prompt)

    def test_map_to_index_options(self):
        index_options_data = self.response_data['indexOptions']
        result = RAGAssistantMapper.map_to_index_options(index_options_data)

        self.assertIsInstance(result, IndexOptions)
        self.assertIsInstance(result.chunks, ChunkOptions)
        self.assertFalse(result.use_parent_document)
        self.assertIsNone(result.child_document)

    def test_map_to_chunk_options(self):
        chunk_data = self.response_data['indexOptions']['chunks']
        result = RAGAssistantMapper.map_to_chunk_options(chunk_data)

        self.assertIsInstance(result, ChunkOptions)
        self.assertEqual(result.chunk_overlap, 100)
        self.assertEqual(result.chunk_size, 999)

    def test_map_to_embeddings(self):
        embeddings_data = self.response_data['searchOptions']['embeddings']
        result = RAGAssistantMapper.map_to_embeddings(embeddings_data)

        self.assertIsInstance(result, EmbeddingsOptions)
        self.assertEqual(result.dimensions, 1536)
        self.assertEqual(result.model_name, 'text-embedding-3-small')
        self.assertEqual(result.provider, 'openai')
        self.assertTrue(result.use_proxy)

    def test_map_to_ingestion(self):
        ingestion_data = self.response_data['searchOptions']['ingestion']
        result = RAGAssistantMapper.map_to_ingestion(ingestion_data)

        self.assertIsInstance(result, IngestionOptions)
        self.assertEqual(result.geai_options, {})
        self.assertEqual(result.llama_parse_options, {})
        self.assertEqual(result.provider, 'geai')

    def test_map_to_variable_list(self):
        variables_data = self.response_data['searchOptions']['variables']
        result = RAGAssistantMapper.map_to_variable_list(variables_data)

        self.assertIsInstance(result, ChatVariableList)
        self.assertEqual(len(result.variables), 4)
        self.assertIsInstance(result.variables[0], ChatVariable)
        self.assertEqual(result.variables[0].key, 'key')
        self.assertEqual(result.variables[0].value, 'context')
        self.assertEqual(result.variables[1].value, 'question')
        self.assertEqual(result.variables[2].value, 'chat_history')
        self.assertEqual(result.variables[3].value, 'question')

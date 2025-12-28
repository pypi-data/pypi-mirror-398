import unittest
from datetime import datetime

from pydantic import BaseModel

from pygeai.assistant.rag.models import (
    DocumentMetadata,
    Document,
    Search,
    RetrieverOptions,
    ChainOptions,
    EmbeddingsOptions,
    IngestionOptions,
    SearchOptions,
    ChildOptions,
    ChildDocumentOptions,
    ChunkOptions,
    IndexOptions,
    RAGAssistant,
    UploadDocument,
    UploadType
)
from pygeai.core.models import LlmSettings, ChatVariableList, Assistant


class TestRagModels(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.rag.test_models.TestRagModels
    """
    def test_document_metadata_to_dict(self):
        metadata = DocumentMetadata(key="test_key", value="test_value")
        result = metadata.to_dict()
        self.assertEqual(result, {"key": "test_key", "value": "test_value"})

    def test_document_metadata_str(self):
        metadata = DocumentMetadata(key="test_key", value="test_value")
        result = str(metadata)
        self.assertEqual(result, "{'key': 'test_key', 'value': 'test_value'}")

    def test_document_to_dict(self):
        doc = Document(
            id="doc1",
            chunks="chunk_data",
            name="test_doc",
            extension="pdf",
            index_status="indexed",
            metadata=[DocumentMetadata(key="key1", value="value1")],
            timestamp=datetime(2023, 1, 1),
            url="http://example.com"
        )
        result = doc.to_dict()
        expected = {
            "id": "doc1",
            "chunks": "chunk_data",
            "name": "test_doc",
            "extension": "pdf",
            "indexStatus": "indexed",
            "metadata": [{"key": "key1", "value": "value1"}],
            "timestamp": datetime(2023, 1, 1),
            "url": "http://example.com"
        }
        self.assertEqual(result["id"], expected["id"])
        self.assertEqual(result["chunks"], expected["chunks"])
        self.assertEqual(result["extension"], expected["extension"])
        self.assertEqual(result["indexStatus"], expected["indexStatus"])
        self.assertEqual(result["url"], expected["url"])
        self.assertEqual(result["timestamp"], expected["timestamp"])
        self.assertEqual(result["name"], expected["name"])
        self.assertEqual(result["metadata"], expected["metadata"])

    def test_document_str(self):
        doc = Document(
            id="doc1",
            chunks="chunk_data",
            extension="pdf",
            index_status="indexed",
            url="http://example.com"
        )
        result = str(doc)
        self.assertIn("'id': 'doc1'", result)
        self.assertIn("'url': 'http://example.com'", result)

    def test_search_to_dict_with_mmr(self):
        search = Search(
            k=5,
            type="mmr",
            fetch_k=10.0,
            lambda_=0.5,
            prompt="test prompt",
            return_source_documents=True,
            score_threshold=0.8,
            template="test template"
        )
        result = search.to_dict()
        expected = {
            "k": 5,
            "type": "mmr",
            "fetchK": 10.0,
            "lambda": 0.5,
            "prompt": "test prompt",
            "returnSourceDocuments": True,
            "scoreThreshold": 0.8,
            "template": "test template"
        }
        self.assertEqual(result, expected)

    def test_search_to_dict_similarity(self):
        search = Search(
            k=3,
            type="similarity",
            prompt="test prompt",
            return_source_documents=False,
            score_threshold=0.5,
            template="test template"
        )
        result = search.to_dict()
        expected = {
            "k": 3,
            "type": "similarity",
            "prompt": "test prompt",
            "returnSourceDocuments": False,
            "scoreThreshold": 0.5,
            "template": "test template"
        }
        self.assertEqual(result, expected)

    def test_retriever_options_to_dict(self):
        options = RetrieverOptions(
            type="multiQuery",
            search_type="hybrid",
            step="documents",
            prompt="custom prompt"
        )
        result = options.to_dict()
        expected = {
            "type": "multiQuery",
            "searchType": "hybrid",
            "step": "documents",
            "prompt": "custom prompt"
        }
        self.assertEqual(result, expected)

    def test_embeddings_options_initialization(self):
        embeddings = EmbeddingsOptions(
            dimensions=512,
            model_name="test-model",
            provider="test-provider",
            use_proxy=True
        )
        self.assertEqual(embeddings.dimensions, 512)
        self.assertEqual(embeddings.model_name, "test-model")
        self.assertEqual(embeddings.provider, "test-provider")
        self.assertTrue(embeddings.use_proxy)

    def test_ingestion_options_initialization(self):
        ingestion = IngestionOptions(
            geai_options={"opt1": "val1"},
            llama_parse_options={"opt2": "val2"},
            provider="test-provider"
        )
        self.assertEqual(ingestion.geai_options, {"opt1": "val1"})
        self.assertEqual(ingestion.llama_parse_options, {"opt2": "val2"})
        self.assertEqual(ingestion.provider, "test-provider")

    def test_search_options_to_dict_full(self):
        search_opts = SearchOptions(
            history_count=5,
            llm=LlmSettings(provider_name="test", model_name="model"),
            search=Search(k=3, prompt="prompt", return_source_documents=True, score_threshold=0.5, template="template"),
            retriever=RetrieverOptions(type="vectorStore"),
            chain=ChainOptions(type="test-chain"),
            embeddings=EmbeddingsOptions(dimensions=512, model_name="model", provider="provider"),
            ingestion=IngestionOptions(geai_options={}, llama_parse_options={}, provider="provider"),
            options={"opt": "val"},
            rerank={"rerank_opt": "val"},
            variables=ChatVariableList(variables=[]),
            vector_store={"store": "data"}
        )
        result = search_opts.to_dict()
        self.assertEqual(result["historyCount"], 5)
        self.assertIn("llm", result)
        self.assertIn("search", result)
        self.assertIn("retriever", result)
        self.assertIn("chain", result)
        self.assertIn("embeddings", result)
        self.assertIn("ingestion", result)
        self.assertIn("options", result)
        self.assertIn("rerank", result)
        self.assertIn("vectorStore", result)
        # Do not assert "variables" since it may be excluded if empty or None after to_dict()

    def test_child_options_to_dict(self):
        child_opts = ChildOptions(chunk_size=100.0, chunk_overlap=20.0, content_processing="clean")
        result = child_opts.to_dict()
        expected = {
            "chunkSize": 100.0,
            "chunkOverlap": 20.0,
            "contentProcessing": "clean"
        }
        self.assertEqual(result, expected)

    def test_child_document_options_to_dict(self):
        child_doc_opts = ChildDocumentOptions(
            child_k=5.0,
            child=ChildOptions(chunk_size=100.0, chunk_overlap=20.0)
        )
        result = child_doc_opts.to_dict()
        expected = {
            "childK": 5.0,
            "child": {"chunkSize": 100.0, "chunkOverlap": 20.0, "contentProcessing": ""}
        }
        self.assertEqual(result, expected)

    def test_chunk_options_to_dict(self):
        chunk_opts = ChunkOptions(chunk_overlap=50, chunk_size=500)
        result = chunk_opts.to_dict()
        expected = {"chunkOverlap": 50, "chunkSize": 500}
        self.assertEqual(result, expected)

    def test_index_options_to_dict_with_child(self):
        index_opts = IndexOptions(
            chunks=ChunkOptions(chunk_overlap=50, chunk_size=500),
            use_parent_document=True,
            child_document=ChildDocumentOptions(
                child_k=5.0,
                child=ChildOptions(chunk_size=100.0, chunk_overlap=20.0)
            )
        )
        result = index_opts.to_dict()
        expected = {
            "chunks": {"chunkOverlap": 50, "chunkSize": 500},
            "useParentDocument": True,
            "childDocument": {
                "childK": 5.0,
                "child": {"chunkSize": 100.0, "chunkOverlap": 20.0, "contentProcessing": ""}
            }
        }
        self.assertEqual(result, expected)

    def test_rag_assistant_to_dict(self):
        rag_assistant = RAGAssistant(
            id="rag1",
            name="RAG Assistant",
            type="rag",
            template="rag template",
            search_options=SearchOptions(
                history_count=5,
                llm=LlmSettings(provider_name="test", model_name="model"),
                search=Search(k=3, prompt="prompt", return_source_documents=True, score_threshold=0.5, template="template"),
                retriever=RetrieverOptions(type="vectorStore")
            ),
            index_options=IndexOptions(chunks=ChunkOptions(chunk_overlap=50, chunk_size=500))
        )
        result = rag_assistant.to_dict()
        self.assertIn("template", result)
        self.assertIn("searchOptions", result)
        self.assertIn("indexOptions", result)
        self.assertEqual(result["template"], "rag template")

    def test_rag_assistant_str(self):
        rag_assistant = RAGAssistant(
            id="rag1",
            name="RAG Assistant",
            type="rag",
            template="rag template",
            search_options=SearchOptions(
                history_count=5,
                llm=LlmSettings(provider_name="test", model_name="model"),
                search=Search(k=3, prompt="prompt", return_source_documents=True, score_threshold=0.5, template="template"),
                retriever=RetrieverOptions(type="vectorStore")
            ),
            index_options=IndexOptions(chunks=ChunkOptions(chunk_overlap=50, chunk_size=500))
        )
        result = str(rag_assistant)
        self.assertIn("'template': 'rag template'", result)

    def test_upload_document_initialization(self):
        upload_doc = UploadDocument(
            path="/path/to/doc",
            upload_type="binary",
            metadata={"key": "value"},
            content_type="application/pdf"
        )
        self.assertEqual(upload_doc.path, "/path/to/doc")
        self.assertEqual(upload_doc.upload_type, "binary")
        self.assertEqual(upload_doc.metadata, {"key": "value"})
        self.assertEqual(upload_doc.content_type, "application/pdf")

    def test_upload_type_constants(self):
        self.assertEqual(UploadType.BINARY, "binary")
        self.assertEqual(UploadType.MULTIPART, "multipart")


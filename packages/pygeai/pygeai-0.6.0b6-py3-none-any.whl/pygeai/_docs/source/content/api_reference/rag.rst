RAG Assistant
=============

This section describes how to interact with the Retrieval-Augmented Generation (RAG) Assistant in Globant Enterprise AI (GEAI) using the Command Line Interface (CLI), Low-Level Service Layer, and High-Level Service Layer. The RAG Assistant enables document retrieval and query execution with configurable search and indexing options.

Create RAG Assistant
--------------------

Creates a new RAG Assistant with configurable options for search, indexing, and welcome data. A name is required, while description, template, search options, index options, and welcome data are optional.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag create-assistant \
      -n "MyRAGAssistant" \
      -d "RAG Assistant for document retrieval" \
      --template "default_rag_template" \
      --history-count 5 \
      --model-name "gpt-4" \
      --temperature 0.7 \
      --chunk-size 512 \
      --chunk-overlap 50 \
      --wd-title "Welcome to My Assistant" \
      --wd-description "This assistant helps retrieve and summarize documents."

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``-d, --description``: Description of the assistant's purpose.
* ``--template, --tpl``: Name of an existing RAG template (optional).
* ``--history-count, --hc``: Number of historical interactions to include.
* ``--model-name, -m``: LLM model name (e.g., "gpt-4").
* ``--temperature, --temp, -t``: Sampling temperature for LLM responses.
* ``--chunk-size``: Size of each document chunk.
* ``--chunk-overlap``: Overlap size between chunks.
* ``--wd-title``: Title for welcome data.
* ``--wd-description``: Description for welcome data.

Additional flags for search, index, and welcome data are available; refer to ``geai rag create-assistant -h``.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.assistant.rag.clients import RAGAssistantClient

    name = "MyRAGAssistant"
    description = "RAG Assistant for document retrieval"
    template = "default_rag_template"
    search_options = {
        "history_count": 5,
        "llm": {
            "modelName": "gpt-4",
            "temperature": 0.7,
            "maxTokens": 1000
        },
        "search": {
            "k": 10,
            "type": "similarity"
        }
    }
    index_options = {
        "chunks": {
            "chunk_size": 512,
            "chunkOverlap": 50
        }
    }
    welcome_data = {
        "title": "Welcome to My Assistant",
        "description": "This assistant helps retrieve and summarize documents."
    }

    client = RAGAssistantClient()
    new_assistant = client.create_assistant(
        name=name,
        description=description,
        template=template,
        search_options=search_options,
        index_options=index_options,
        welcome_data=welcome_data
    )
    print(new_assistant)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``description``: Optional description of the assistant's purpose.
* ``template``: Optional name of an existing RAG template.
* ``search_options``: Dictionary configuring search behavior (e.g., LLM settings, search type).
* ``index_options``: Dictionary configuring document indexing (e.g., chunk size, overlap).
* ``welcome_data``: Dictionary configuring the welcome message.

**Returns**:
A dictionary containing the API response with details of the created assistant.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.assistant.managers import AssistantManager
    from pygeai.assistant.rag.models import RAGAssistant, SearchOptions, IndexOptions, WelcomeData

    manager = AssistantManager()

    search_options = SearchOptions(
        history_count=5,
        llm={
            "modelName": "gpt-4",
            "temperature": 0.7,
            "maxTokens": 1000
        },
        search={
            "k": 10,
            "type": "similarity"
        }
    )
    index_options = IndexOptions(
        chunks={
            "chunk_size": 512,
            "chunkOverlap": 50
        }
    )
    welcome_data = WelcomeData(
        title="Welcome to My Assistant",
        description="This assistant helps retrieve and summarize documents."
    )

    assistant = RAGAssistant(
        name="MyRAGAssistant",
        description="RAG Assistant for document retrieval",
        template="default_rag_template",
        search_options=search_options,
        index_options=index_options,
        welcome_data=welcome_data
    )

    created_assistant = manager.create_assistant(assistant)
    print(created_assistant)

**Components**:

* ``RAGAssistant``: Model defining the assistant's properties.
* ``SearchOptions``: Configures search behavior (e.g., LLM settings, retrieval parameters).
* ``IndexOptions``: Configures document indexing (e.g., chunking).
* ``WelcomeData``: Configures the assistant's welcome message.
* ``AssistantManager``: Manages creation and response mapping.

**Returns**:
A ``RAGAssistant`` instance representing the created assistant, or an error response if creation fails.

Update RAG Assistant
--------------------

Updates an existing RAG Assistant’s status, description, template, search options, or welcome data. The assistant name and status are required.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag update-assistant \
      -n "MyRAGAssistant" \
      --status 1 \
      -d "Updated RAG Assistant description"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``--status``: (Required) Status (1 for enabled, 0 for disabled).
* ``-d, --description``: Updated description.
* ``--template, --tpl``: Updated template name.
* Additional flags for search options and welcome data (see ``geai rag update-assistant -h``).

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    updated_assistant = client.update_assistant(
        name="MyRAGAssistant",
        status=1,
        description="Updated RAG Assistant description",
        search_options={
            "history_count": 10,
            "llm": {"modelName": "gpt-4", "temperature": 0.8}
        }
    )
    print(updated_assistant)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``status``: (Required) Status (1 for enabled, 0 for disabled).
* ``description``: Optional updated description.
* ``template``: Optional updated template name.
* ``search_options``: Optional updated search configuration.
* ``welcome_data``: Optional updated welcome message configuration.

**Returns**:
A dictionary containing the API response with details of the updated assistant.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    assistant = RAGAssistant(
        name="MyRAGAssistant",
        status=1,
        description="Updated RAG Assistant description",
        search_options=SearchOptions(
            history_count=10,
            llm={"modelName": "gpt-4", "temperature": 0.8}
        )
    )
    updated_assistant = manager.update_assistant(assistant)
    print(updated_assistant)

**Components**:

* ``RAGAssistant``: Model with updated properties.
* ``AssistantManager``: Manages update and response mapping.

**Returns**:
A ``RAGAssistant`` instance with updated details, or an error response.

Delete RAG Assistant
--------------------

Deletes an existing RAG Assistant by name.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag delete-assistant -n "MyRAGAssistant"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    result = client.delete_assistant(name="MyRAGAssistant")
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.

**Returns**:
A dictionary containing the API response indicating deletion success or failure.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    result = manager.delete_assistant(assistant_name="MyRAGAssistant")
    print(result)

**Parameters**:

* ``assistant_name``: (Required) Name of the RAG Assistant.

**Returns**:
An ``EmptyResponse`` indicating success, or an error response.

List RAG Assistants
-------------------

Retrieves all RAG Assistants in a project.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag list-assistants

**Flags**:
None.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    assistants = client.get_assistants_from_project()
    print(assistants)

**Parameters**:
None.

**Returns**:
A dictionary containing a list of RAG Assistants in the project.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    assistant = manager.get_assistant_data(assistant_name="MyRAGAssistant")
    print(assistant)

**Note**: The high-level manager retrieves a specific assistant by name. To list all assistants, use the low-level client or CLI.

**Returns**:
A ``RAGAssistant`` instance for the specified assistant, or an error response.

Get RAG Assistant
-----------------

Retrieves details of a specific RAG Assistant by name.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag get-assistant -n "MyRAGAssistant"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    assistant_data = client.get_assistant_data(name="MyRAGAssistant")
    print(assistant_data)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.

**Returns**:
A dictionary containing the assistant’s details.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    assistant = manager.get_assistant_data(assistant_name="MyRAGAssistant")
    print(assistant)

**Parameters**:

* ``assistant_name``: (Required) Name of the RAG Assistant.

**Returns**:
A ``RAGAssistant`` instance with the assistant’s details, or an error response.

Upload Document
---------------

Uploads a document to a RAG Assistant for indexing and retrieval.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag upload-document \
      -n "MyRAGAssistant" \
      -f "/path/to/document.pdf" \
      --content-type "application/pdf" \
      --upload-type "multipart"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``-f, --file-path``: (Required) Path to the document file.
* ``--content-type, --ct``: MIME type of the document (e.g., "application/pdf").
* ``--upload-type, -t``: Upload method ("multipart" or "binary", defaults to "multipart").
* ``--metadata, -m``: Optional metadata (JSON or file path, for multipart uploads).

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    result = client.upload_document(
        name="MyRAGAssistant",
        file_path="/path/to/document.pdf",
        content_type="application/pdf",
        upload_type="multipart",
        metadata={"author": "John Doe"}
    )
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``file_path``: (Required) Path to the document file.
* ``content_type``: MIME type (e.g., "application/pdf").
* ``upload_type``: "multipart" or "binary" (defaults to "multipart").
* ``metadata``: Optional metadata dictionary or file path (for multipart).

**Returns**:
A dictionary containing the API response with details of the uploaded document.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.assistant.rag.models import RAGAssistant, UploadDocument

    manager = AssistantManager()
    assistant = RAGAssistant(name="MyRAGAssistant")
    document = UploadDocument(
        path="/path/to/document.pdf",
        content_type="application/pdf",
        upload_type="multipart",
        metadata={"author": "John Doe"}
    )
    result = manager.upload_document(assistant, document)
    print(result)

**Components**:

* ``RAGAssistant``: Specifies the target assistant.
* ``UploadDocument``: Defines the document properties.
* ``AssistantManager``: Manages upload and response mapping.

**Returns**:
A ``Document`` instance representing the uploaded document, or an error response.

Retrieve Document
-----------------

Retrieves a specific document from a RAG Assistant by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag get-document -n "MyRAGAssistant" --document-id "doc123"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``--document-id, --id``: (Required) Document ID.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    document = client.retrieve_document(name="MyRAGAssistant", document_id="doc123")
    print(document)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``document_id``: (Required) Document ID.

**Returns**:
A dictionary containing the document’s details.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    document = manager.get_document(name="MyRAGAssistant", document_id="doc123")
    print(document)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``document_id``: (Required) Document ID.

**Returns**:
A ``Document`` instance with the document’s details, or an error response.

List Documents
--------------

Lists documents associated with a RAG Assistant, with optional pagination.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag list-documents -n "MyRAGAssistant" --skip 0 --count 10

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``--skip, -s``: Number of documents to skip (default: 0).
* ``--count, -c``: Number of documents to return (default: 10).

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    documents = client.get_documents(name="MyRAGAssistant", skip=0, count=10)
    print(documents)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``skip``: Number of documents to skip (default: 0).
* ``count``: Number of documents to return (default: 10).

**Returns**:
A dictionary containing a list of documents.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    documents = manager.get_document_list(name="MyRAGAssistant", skip=0, count=10)
    print(documents)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``skip``: Number of documents to skip (default: 0).
* ``count``: Number of documents to return (default: 10).

**Returns**:
A ``DocumentListResponse`` containing the list of documents, or an error response.

Delete Document
---------------

Deletes a specific document from a RAG Assistant by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag delete-document -n "MyRAGAssistant" --document-id "doc123"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``--document-id, --id``: (Required) Document ID.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    result = client.delete_document(name="MyRAGAssistant", document_id="doc123")
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``document_id``: (Required) Document ID.

**Returns**:
A dictionary indicating deletion success or failure.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    result = manager.delete_document(name="MyRAGAssistant", document_id="doc123")
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.
* ``document_id``: (Required) Document ID.

**Returns**:
An ``EmptyResponse`` indicating success, or an error response.

Delete All Documents
-------------------

Deletes all documents associated with a RAG Assistant.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag delete-all-documents -n "MyRAGAssistant"

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    result = client.delete_all_documents(name="MyRAGAssistant")
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.

**Returns**:
A dictionary indicating deletion success or failure.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    result = manager.delete_all_documents(name="MyRAGAssistant")
    print(result)

**Parameters**:

* ``name``: (Required) Name of the RAG Assistant.

**Returns**:
An ``EmptyResponse`` indicating success, or an error response.

Execute Query
-------------

Executes a query against the RAG Assistant’s indexed documents.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai rag execute-query -n "MyRAGAssistant" --query '{"query": "What is AI?"}'

**Flags**:

* ``-n, --name``: (Required) Name of the RAG Assistant.
* ``--query``: (Required) JSON query string.

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    client = RAGAssistantClient()
    query = {"query": "What is AI?"}
    result = client.execute_query(query=query)
    print(result)

**Parameters**:

* ``query``: (Required) Dictionary containing the query details.

**Returns**:
A dictionary containing the query results.

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    manager = AssistantManager()
    query = {"query": "What is AI?"}
    result = manager.execute_query(query=query)  # Note: Manager may not directly support execute_query; use client
    print(result)

**Note**: The high-level ``AssistantManager`` does not explicitly expose ``execute_query``. Use ``RAGAssistantClient`` for this functionality.

**Returns**:
A dictionary containing the query results, or an error response.

Notes
-----

* The CLI provides a user-friendly interface with flags for all configuration options.
* The Low-Level Client (``RAGAssistantClient``) offers fine-grained control over API calls, ideal for custom integrations.
* The High-Level Manager (``AssistantManager``) simplifies operations by handling response mapping and error processing, suitable for robust applications.
* Error handling in both low-level and high-level layers manages JSON decoding errors and API errors, returning structured responses.
* Search, index, and welcome data options are highly customizable for tailored assistant behavior.

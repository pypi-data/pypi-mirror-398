Embeddings
==========

The API Reference enables you to generate embeddings from various input types, including text and images. You can leverage different LLM providers and their respective models for this purpose.

* Generate embeddings: Generates embeddings for a given list of inputs using a specified LLM model.


Generate embeddings
~~~~~~~~~~~~~~

Generates embeddings from different input types using `PyGEA </pygeai>`_. It can interact with several LLM providers and their respective models for embedding generation.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_


Command line
^^^^^^^^^^^^

Use the following command to generate embeddings:

.. code-block:: shell

    geai emb generate \
     -i "<your_text_input>" \
     -i "<your_image_input>" \
     -m "<provider>/<model_name>"

Replace the placeholders with your desired values:

* `<your_text_input>`: The text you want to generate an embedding for. For example: `"Help me with Globant Enterprise AI."`
* `<your_image_input>`: The image data, encoded appropriately (e.g., base64). For example: `"image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAEElEQVR4nGK6HcwNCAAA//8DTgE8HuxwEQAAAABJRU5ErkJggg=="`
* `<provider>/<model_name>`: The provider and model to use for embedding generation. For example: `"awsbedrock/amazon.titan-embed-text-v1"`


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to generate embeddings using the low-level service layer:


.. code-block:: python

    from pygeai.core.embeddings.clients import EmbeddingsClient
    from pygeai.core.services.llm.model import Model
    from pygeai.core.services.llm.providers import Provider

    client = EmbeddingsClient()

    inputs = [
        "<your_text_input>",
        "<your_image_input>"
    ]

    embeddings = client.generate_embeddings(
        input_list=inputs,
        model=f"{Provider.<provider>}/{Model.<provider>.<model_name>}",
        encoding_format=None,
        dimensions=None,
        user=None,
        input_type=None,
        timeout=600,
        cache=False
    )

    print(embeddings)


Replace the placeholders with your desired values:

* `<your_text_input>`: Text you want to generate an embedding for. For example: `"Help me with Globant Enterprise AI"`
* `<your_image_input>`: Image data, encoded appropriately (e.g., base64). For example: `"image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAEElEQVR4nGK6HcwNCAAA//8DTgE8HuxwEQAAAABJRU5ErkJggg=="`
* `<provider>`: LLM provider. For example: `AWS_BEDROCK`
* `<model_name>`: Specific model from the provider. For example: `AMAZON_TITAN_EMBED_TEXT_V1`


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to generate embeddings using the high-level service layer:


.. code-block:: python

    from pygeai.core.embeddings.managers import EmbeddingsManager
    from pygeai.core.embeddings.models import EmbeddingConfiguration
    from pygeai.core.services.llm.model import Model
    from pygeai.core.services.llm.providers import Provider

    manager = EmbeddingsManager()

    inputs = [
        "<your_text_input>",
        "<your_image_input>"
    ]


    configuration = EmbeddingConfiguration(
        inputs=inputs,
        model=f"{Provider.<provider>}/{Model.<provider>.<model_name>}",
        encoding_format=None,
        dimensions=None,
        user=None,
        input_type=None,
        timeout=600,
        cache=False
    )

    embeddings = manager.generate_embeddings(configuration)
    print(embeddings)


Replace the placeholders with your desired values:

* `<your_text_input>`: Text you want to generate an embedding for. For example: `"Help me with Globant Enterprise AI"`
* `<your_image_input>`: Image data, encoded appropriately (e.g., base64). For example: `"image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAEElEQVR4nGK6HcwNCAAA//8DTgE8HuxwEQAAAABJRU5ErkJggg=="`
* `<provider>`: LLM provider. For example: `AWS_BEDROCK`
* `<model_name>`: Specific model from the provider. For example: `AMAZON_TITAN_EMBED_TEXT_V1`



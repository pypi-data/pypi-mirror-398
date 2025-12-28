API Reference
=============

This document provides a comprehensive overview of **API Reference**, outlining its structure and available functionalities.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    api_reference/chat
    api_reference/project
    api_reference/rag
    api_reference/embeddings


Authentication
--------------
To use the API, you need to authenticate each request using `API Tokens <https://wiki.genexus.com/enterprise-ai/wiki?564,API+Tokens>`_. These tokens are managed in `Globant Enterprise AI Backoffice <https://wiki.genexus.com/enterprise-ai/wiki?42,Globant+Enterprise+AI+Backoffice>`_.

The following properties are common to every interaction with **API Reference**:

==========================  ================================================================
Variable                        Description
==========================  ================================================================
`GEAI_API_BASE_URL`              `$BASE_URL`. The base URL for your Globant Enterprise AI installation (e.g., https://api.saia.ai or a custom value).
`GEAI_API_KEY`                   `$SAIA_APITOKEN`. An API token generated for each project or organization.
==========================  ================================================================

Interaction Levels
------------------
The API is designed with three levels of abstraction to cater to different use cases and developer preferences:

Command Line
~~~~~~~~~~~~
This level provides a straightforward way to interact with the `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using simple commands. It handles the communication with the REST API and presents the responses in an easy-to-understand format.

Low-Level Service Layer
~~~~~~~~~~~~~~~~~~~~~~~
This layer offers more granular control over API interactions. You work directly with client classes that handle the HTTP requests and responses. This layer returns data in JSON format, providing flexibility for further processing.

High-Level Service Layer
~~~~~~~~~~~~~~~~~~~~~~~~
This layer abstracts away the complexities of handling raw JSON data. It uses manager classes that map the JSON responses to Python objects, simplifying data manipulation and integration with your application logic.

Each item in this section has these three ways of implementing a function. The user can choose the one that adequate
better to their use case.

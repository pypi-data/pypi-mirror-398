Introduction
============

About SDKs
----------
An SDK (Software Development Kit) is a set of tools, libraries, documentation, code samples, processes and guides that
developers use to create software applications for a specific platform or service.
SDKs simplify the integration process by providing pre-built functionality and standardized methods for interfacing with APIs or systems.

- Tools: compilers, debuggers and other utilities
- Libraries: Collection of pre-written code that can be integrated into an application to extend its functionality.
- Documentation: Guides, API references, tutorials and best practices for using the SDK.
- Code samples: Snippets demonstrating how to use the SDK’s features
- Processes: Guidelines on how to develop, test and deploy applications using the SDK

The goal of `PyGEA </pygeai>`_ is to provide this set of resources in order to interact with `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_.

Requirements
------------
The SDK was designed to comply with the following requirements:

- Cross-platform: It runs on MacOS, Windows, Linux distributions and BSD variants.
- Easy to install: It offers ease of installation through pip or as an individual package.
- Easy to set up: It offers assistance during the setup process.
- Intuitive: Flags and options resemble those available in similar tools in order to provide a familiar interface to work with.
- Common use cases can be accomplished in a few steps.
- Native look for any Python developer, including naming conventions, style, etc.
- Comprehensive test suite to ensure reliability and consistency across releases.

Architecture
------------
The SDK is composed of libraries (libs), code samples, and documentation. The command-line utility interacts with the SDK to facilitate tasks. The geai-chat utility provides an interactive experience when dealing with the cli utility.
The lower level of the SDK handles interaction with the APIs available in Globant Enterprise AI.

Tools
-----
- geai-cli is the command-line utility through which you can interact with the SDK libraries.
- geai-chat is an interactive tool to perform common tasks with the Globant Enterprise AI in an automated manner.
- geai-dbg is a debugging tool that provides a detailed view of what the SDK is doing in order to find and fix any issues.

Libraries
---------

The user can import the different modules from the libraries in order to interact with GEAI services. The proposed structure for the libraries and tools is as follows

- pygeai: Meta-package that encapsulates all the components of the SDK.
    - pygeai-cli: Command-line tool to interact with the SDK.
    - pygeai-chat: Interactive version of the cli tool.
    - pygeai-dbg: Debugger to deal with potential issues in the SDK and have a detailed view of what it’s doing.
    - pygeai-core: To handle interaction with base components of Globant Enterprise AI. Also, to handle users, groups, permissions, API Tokens, etc.
    - pygeai-organization: To handle `Organizations <https://wiki.genexus.com/enterprise-ai/wiki?42,Globant+Enterprise+AI+Backoffice#Organization+Options>`_, `Projects <https://wiki.genexus.com/enterprise-ai/wiki?565,Projects>`_, etc.
    - pygeai-agent: To handle interactions with Agent Studio.
    - pygeai-assistant: To handle interaction with `Data Analyst Assistants <https://wiki.genexus.com/enterprise-ai/wiki?886,Data+Analyst+Assistant+2.0>`_, `RAG Assistants <https://wiki.genexus.com/enterprise-ai/wiki?44,RAG+Assistants+Introduction>`_, `Chat with Data Assistants <https://wiki.genexus.com/enterprise-ai/wiki?159,Chat+with+Data+Assistant>`_, `Chat with API Assistants <https://wiki.genexus.com/enterprise-ai/wiki?110,API+Assistant>`_, and `Chat Assistants <https://wiki.genexus.com/enterprise-ai/wiki?708,Chat+Assistant>`_.
    - pygeai-flows: To handle interactions with `Flows <https://wiki.genexus.com/enterprise-ai/wiki?321,Flows+in+Globant+Enterprise+AI>`_.

Samples
-------

Code samples should illustrate how to use each module at a high level, including additional references to appropriate documentation when deeper understanding is required.

Documentation
-------------

The following basic documents are available to help you get started:

- `Quickstart </docs/source/content/quickstart.rst>`_: A simple guide showing the process of installing, configuring and starting the SDK.
- `API reference </docs/source/content/api_reference.rst>`_: A detailed description of each module.

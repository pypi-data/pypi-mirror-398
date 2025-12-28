Quickstart
===========

This is a step-by-step guide to get you started with `PyGEA </pygeai>`_.


Installation
------------
Before you begin, ensure Python 3.8 or higher is installed. While a system-level installation is possible, using a virtual environment is recommended.

1.  Create a virtual environment:

.. code-block:: shell

    ~$ python3 -m venv venv

2.  Activate the virtual environment:

.. code-block:: shell

    ~$ source venv/bin/activate
    (venv) ~$


3. Install the SDK:

.. code-block:: shell

    (venv) ~$ pip install pygeai

This installs the **PyGEA** command-line tool and the necessary libraries.


Command line utility
--------------------

The SDK installation includes the PyGEA command-line tool. You can use it to interact with the `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_.

* Check the installed version:

.. code-block:: shell

    (venv) ~$ geai version
    - Globant Enterprise AI: GEAI cli utility. Version: 0.1.44


* Verify if you are running the latest version:

.. code-block:: shell

    (venv) ~$ geai check-updates
    There's a new version available: 0.1.44. You have 0.1.42 installed.


* Access the help command for information on commands and subcommands:

.. code-block:: shell

    (venv) ~$ geai help
    GEAI CLI
    --------

    NAME
        geai - Command Line Interface for Globant Enterprise AI

    SYNOPSIS
        geai <command> [<subcommand>] [--option] [option-arg]

    DESCRIPTION
        geai is a cli utility that interacts with the PyGEAI SDK to handle common tasks in Globant Enterprise AI,
        such as creating organizations and projects, defining assistants, managing workflows, etc.

        The available subcommands are as follows:
        help or h			Display help text
        version or v		Display version text
        check-updates or cu		Search for available updates

        configure or config or c		Setup the environment variables required to interact with GEAI
            --key or -k		Set GEAI API KEY
            --url or -u		Set GEAI API BASE URL
            --alias or -a		Set alias for settings section
        organization or org		Invoke organization endpoints to handle project parameters
        assistant or ast		Invoke assistant endpoints to handle assistant parameters
        rag			Invoke rag assistant endpoints to handle RAG assistant parameters
        chat			Invoke chat endpoints to handle chat with assistants parameters
        admin or adm		Invoke admin endpoints designed for internal use
        llm			Invoke llm endpoints for provider's and model retrieval
        files			Invoke files endpoints for file handling
    ...

* Get help for a specific subcommand:

.. code-block:: shell

    (venv) ~$ geai org help
    GEAI CLI - ORGANIZATION
    -----------------------
    ...

.. code-block:: shell

    (venv) ~$ geai ast help
    GEAI CLI - ASSISTANT
    --------------------
    ...

Initial configuration
---------------------

The configure command helps you set the BASE_URL and API_KEY for your Globant Enterprise AI instance. You can configure multiple settings using aliases. The default alias is 'default'.

1. Set up a new pair under the 'test' alias:

.. code-block:: shell

    (venv) ~$ geai configure
    # Configuring GEAI credentials...

2. When prompted to select an alias, enter:

.. code-block:: shell
    -> Select an alias (Leave empty to use 'default'): test

3. Enter your GEAI_API_KEY (SAIA_PROJECT_APITOKEN):

.. code-block:: shell
    -> Insert your GEAI_API_KEY (Leave empty to keep current value): yourapikeygoeshere_...
    GEAI API KEY for alias 'test' saved successfully!

4. Enter your GEAI API BASE URL ($BASE_URL for example, https://api.saia.ai or the value provided to you):

.. code-block:: shell

   -> Insert your GEAI API BASE URL (Leave empty to keep current value): https://api.saia.ai
    GEAI API BASE URL for alias 'test' saved successfully!

That's it! You now have everything you need to start using the SDK. You can use it via the geai utility, the low level
service layer or the managers that provide high level abstractions.






Code samples
============

In this section, you can find several snippets of code that show how to use the Python SDK to interact with GEAI.
They're presented in the form of simple functions, but they can be used separately or combined into more complex programs.

Organization API
----------------

1. Getting Assistant List
~~~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves a list of assistants based on the specified level of detail.

.. code-block:: python

    def display_assistant_list():
        """
        Retrieves and displays the assistant list with summary or full details.
        """
        client = OrganizationClient()
        assistant_list = client.get_assistant_list(detail="full")  # Can change detail to "summary"
        print(assistant_list)

2. Getting Project List
~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves the list of projects, optionally filtered by project name and detail level.

.. code-block:: python

    def display_project_list():
        """
        Retrieves and displays the project list with optional filters.
        """
        client = OrganizationClient()
        project_list = client.get_project_list(detail="full", name="ProjectName")  # Change filters as needed
        print(project_list)

3. Getting Project Details
~~~~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves detailed information about a specific project using its ID.

.. code-block:: python

    def display_project_data(project_id: str):
        """
        Retrieves and displays project details by project ID.
        """
        client = OrganizationClient()
        project_data = client.get_project_data(project_id=project_id)
        print(project_data)

4. Creating a New Project
~~~~~~~~~~~~~~~~~~~~~~~~~

This method creates a new project with the provided name, email, and optional description and usage limit.

.. code-block:: python

    def create_new_project(name: str, email: str, description: str = None, usage_limit: dict = None):
        """
        Creates a new project with the specified parameters.
        """
        client = OrganizationClient()
        new_project = client.create_project(name=name, email=email, description=description, usage_limit=usage_limit)
        print(new_project)

5. Updating an Existing Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method updates an existing project's name and/or description.

.. code-block:: python

    def update_project_data(project_id: str, name: str, description: str = None):
        """
        Updates an existing project with the provided name and description.
        """
        client = OrganizationClient()
        updated_project = client.update_project(project_id=project_id, name=name, description=description)
        print(updated_project)

6. Deleting a Project
~~~~~~~~~~~~~~~~~~~~~

This method deletes an existing project using its unique project ID.

.. code-block:: python

    def delete_project_data(project_id: str):
        """
        Deletes the specified project using its project ID.
        """
        client = OrganizationClient()
        delete_response = client.delete_project(project_id=project_id)
        print(delete_response)

7. Getting Project Tokens
~~~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves the tokens associated with a specific project.

.. code-block:: python

    def display_project_tokens(project_id: str):
        """
        Retrieves and displays tokens for a specific project.
        """
        client = OrganizationClient()
        tokens = client.get_project_tokens(project_id=project_id)
        print(tokens)

8. Exporting Request Data
~~~~~~~~~~~~~~~~~~~~~~~~~

This method exports request data based on assistant name, status, and pagination parameters.

.. code-block:: python

    def export_request_data(assistant_name: str = None, status: str = None, skip: int = 0, count: int = 0):
        """
        Exports request data based on filters such as assistant name and status.
        """
        client = OrganizationClient()
        request_data = client.export_request_data(assistant_name=assistant_name, status=status, skip=skip, count=count)
        print(request_data)

Assistant API
-------------

1. Getting Assistant Data
~~~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves assistant information using its ID.

.. code-block:: python

    def display_assistant_data(assistant_id: str, detail: str = "summary"):
        """
        Retrieves and displays assistant data based on assistant ID.
        """
        client = AssistantClient()
        assistant_data = client.get_assistant_data(assistant_id=assistant_id, detail=detail)
        print(assistant_data)

2. Creating a New Assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method creates a new assistant with the given configuration.

.. code-block:: python

    def create_new_assistant(assistant_type: str, name: str, prompt: str, description: str = None, llm_settings: dict = None, welcome_data: dict = None):
        """
        Creates a new assistant with the provided details.
        """
        client = AssistantClient()
        new_assistant = client.create_assistant(
            assistant_type=assistant_type,
            name=name,
            prompt=prompt,
            description=description,
            llm_settings=llm_settings,
            welcome_data=welcome_data
        )
        print(new_assistant)

3. Updating an Existing Assistant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This method updates an existing assistant with new details.

.. code-block:: python

    def update_assistant_data(assistant_id: str, status: int, action: str, revision_id: str = None, name: str = None, prompt: str = None, description: str = None, llm_settings: dict = None, welcome_data: dict = None):
        """
        Updates an assistant with the provided parameters.
        """
        client = AssistantClient()
        updated_assistant = client.update_assistant(
            assistant_id=assistant_id,
            status=status,
            action=action,
            revision_id=revision_id,
            name=name,
            prompt=prompt,
            description=description,
            llm_settings=llm_settings,
            welcome_data=welcome_data
        )
        print(updated_assistant)

4. Deleting an Assistant
~~~~~~~~~~~~~~~~~~~~~~~~

This method deletes an assistant by its ID.

.. code-block:: python

    def delete_assistant_data(assistant_id: str):
        """
        Deletes the assistant with the given ID.
        """
        client = AssistantClient()
        delete_response = client.delete_assistant(assistant_id=assistant_id)
        print(delete_response)

5. Sending a Chat Request
~~~~~~~~~~~~~~~~~~~~~~~~~

This method sends a chat request to the specified assistant.

.. code-block:: python

    def send_assistant_chat_request(assistant_name: str, messages: list, revision: int, revision_name: str):
        """
        Sends a chat request to the specified assistant.
        """
        client = AssistantClient()
        chat_response = client.send_chat_request(
            assistant_name=assistant_name,
            messages=messages,
            revision=revision,
            revision_name=revision_name
        )
        print(chat_response)

6. Getting Request Status
~~~~~~~~~~~~~~~~~~~~~~~~~

This method retrieves the status of a request using its unique ID.

.. code-block:: python

    def display_request_status(request_id: str):
        """
        Retrieves and displays the status of a specific request.
        """
        client = AssistantClient()
        request_status = client.get_request_status(request_id=request_id)
        print(request_status)

7. Canceling a Request
~~~~~~~~~~~~~~~~~~~~~~

This method cancels a request using its request ID.

.. code-block:: python

    def cancel_assistant_request(request_id: str):
        """
        Cancels the request with the specified ID.
        """
        client = AssistantClient()
        cancel_response = client.cancel_request(request_id=request_id)
        print(cancel_response)

Chat API
--------

1. Basic Chat Request
~~~~~~~~~~~~~~~~~~~~~
This snippet demonstrates how to initiate a simple chat request using the chat_completion method.

.. code-block:: python

    def initiate_chat(model: str, messages: list):
        """
        Initiates a simple chat request.
        """
        client = ChatClient()
        chat_response = client.chat_completion(
            model=model,
            messages=messages,
        )
        print(chat_response)

2. Generating Chat Completion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This snippet shows how to generate a chat completion by passing a model, messages, and additional parameters like temperature, max tokens, etc.

.. code-block:: python

    def generate_chat_completion(model: str, messages: list, temperature: int = None, max_tokens: int = None):
        """
        Generates a chat completion with the specified parameters.
        """
        client = ChatClient()
        completion_response = client.chat_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        print(completion_response)

3. Using Thread ID for Continuity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates how to include a thread_id to maintain continuity in the conversation.

.. code-block:: python

    def generate_chat_with_thread_id(model: str, messages: list, thread_id: str):
        """
        Generates a chat completion with thread ID for maintaining conversation continuity.
        """
        client = ChatClient()
        completion_response = client.chat_completion(
            model=model,
            messages=messages,
            thread_id=thread_id
        )
        print(completion_response)

4. Streaming Chat Completion Response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This snippet shows how to enable streaming for the chat completion, meaning the response will be streamed instead of receiving all at once.

.. code-block:: python

    def generate_streaming_chat(model: str, messages: list):
        """
        Generates a streaming chat completion.
        """
        client = ChatClient()
        streaming_response = client.chat_completion(
            model=model,
            messages=messages,
            stream=True
        )
        print(streaming_response)

5. Customizing Chat Completion with Penalties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example demonstrates how to use both frequency_penalty and presence_penalty to fine-tune the chat completion response.

.. code-block:: python

    def generate_chat_with_penalties(model: str, messages: list, frequency_penalty: float, presence_penalty: float):
        """
        Generates a chat completion with custom penalties.
        """
        client = ChatClient()
        completion_response = client.chat_completion(
            model=model,
            messages=messages,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        print(completion_response)

6. Advanced Chat Completion with All Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This snippet demonstrates how to provide a fully customized chat completion request, including model, messages, stream, temperature, max tokens, and penalties.

.. code-block:: python

    def generate_advanced_chat_completion(model: str, messages: list, stream: bool, temperature: int, max_tokens: int, thread_id: str, frequency_penalty: float, presence_penalty: float):
        """
        Generates a highly customized chat completion.
        """
        client = ChatClient()
        advanced_response = client.chat_completion(
            model=model,
            messages=messages,
            stream=stream,
            temperature=temperature,
            max_tokens=max_tokens,
            thread_id=thread_id,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        print(advanced_response)

Example Usage:
--------------

For all of the above snippets, you would use the ChatClient methods as shown. Here is an example of how you could call one of the above functions:

.. code-block:: python

    messages = [{"role": "user", "content": "Hello, how are you?"}]
    model = "saia:text:myAssistant|bot123"
    temperature = 0.7
    max_tokens = 100
    generate_chat_completion(model, messages, temperature, max_tokens)


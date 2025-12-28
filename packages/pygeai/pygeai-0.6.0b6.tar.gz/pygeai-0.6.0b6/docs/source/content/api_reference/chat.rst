Chat
====

Chat Completion
~~~~~~~~~~~~~~~

The GEAI SDK provides functionality to interact with the Globant Enterprise AI chat system, allowing users to generate chat completions using specified models and parameters. This can be achieved through the command line interface, the low-level service layer (ChatClient), or the high-level service layer (ChatManager). The `stream` parameter, which enables streaming responses, is supported in the command line and low-level service layer but not in the high-level service layer.

Command Line
^^^^^^^^^^^^

The `geai chat completion` command generates a chat completion based on the provided model and messages. Various flags allow customization of the response, such as streaming, temperature, and maximum tokens.

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Hi, welcome to Globant Enterprise AI!!"}]' \
      --temperature 0.7 \
      --max-tokens 1000 \
      --stream 1

To use a different API key alias for authentication:

.. code-block:: shell

    geai --alias admin chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "What is Globant Enterprise AI?"}]' \
      --temperature 0.5 \
      --max-tokens 500

For a non-streaming response with additional parameters like frequency and presence penalties:

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Can you explain AI solutions offered by Globant?"}]' \
      --temperature 0.6 \
      --max-tokens 800 \
      --frequency-penalty 0.1 \
      --presence-penalty 0.2 \
      --stream 0

Using tools and tool choice to fetch weather data:

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --messages '[{"role": "user", "content": "Please get the current weather for San Francisco."}]' \
      --temperature 0.6 \
      --max-tokens 800 \
      --tools '[{"name": "get_weather", "description": "Fetches the current weather for a given location", "parameters": {"type": "object", "properties": {"location": {"type": "string", "description": "City name"}}, "required": ["location"]}, "strict": true}]' \
      --tool-choice '{"type": "function", "function": {"name": "get_weather"}}' \
      --stream 1

Low Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatClient` class provides a low-level interface to generate chat completions. It supports both streaming and non-streaming responses and allows fine-grained control over parameters.

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=[{"role": "user", "content": "What is Globant Enterprise AI?"}],
        temperature=0.5,
        max_tokens=500,
        stream=False
    )
    print(response)

Streaming response with tools:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    llm_settings = {
        "temperature": 0.6,
        "max_tokens": 800,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.2
    }

    messages = [{"role": "user", "content": "Please get the current weather for San Francisco."}]

    tools = [
        {
            "name": "get_weather",
            "description": "Fetches the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string", "description": "City name"}},
                "required": ["location"]
            },
            "strict": True
        }
    ]

    tool_choice = {"type": "function", "function": {"name": "get_weather"}}

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        stream=True,
        tools=tools,
        tool_choice=tool_choice,
        **llm_settings
    )

    for chunk in response:
        print(chunk, end="")

Using variables and thread ID:

.. code-block:: python

    from pygeai.chat.clients import ChatClient

    client = ChatClient()

    response = client.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for Globant Enterprise AI."},
            {"role": "user", "content": "What AI solutions does Globant offer?"}
        ],
        temperature=0.8,
        max_tokens=2000,
        presence_penalty=0.1,
        thread_id="thread_123e4567-e89b-12d3-a456-426614174000",
        variables=[{"key": "user_region", "value": "North America"}, {"key": "industry", "value": "Technology"}],
        stream=False
    )
    print(response)

High Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

The `ChatManager` class provides a high-level interface for generating chat completions. It does not support streaming responses but simplifies the process by using structured models like `ChatMessageList` and `LlmSettings`.

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.5,
        max_tokens=500,
        frequency_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Can you explain what Globant Enterprise AI does?")]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings
    )
    print(response)

Using tools to check weather and send an email:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.7,
        max_tokens=1000,
        frequency_penalty=0.3,
        presence_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Can you check the weather for New York and send an email summary?")]
    )

    tools = ChatToolList(
        variables=[
            ChatTool(
                name="get_weather",
                description="Fetches the current weather for a given location",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"]
                },
                strict=True
            ),
            ChatTool(
                name="send_email",
                description="Sends an email to a recipient with a subject and body",
                parameters={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Email address"},
                        "subject": {"type": "string", "description": "Email subject"},
                        "body": {"type": "string", "description": "Email content"}
                    },
                    "required": ["recipient", "subject", "body"]
                },
                strict=False
            )
        ]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        tools=tools
    )
    print(response)

With variables and thread ID:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatVariable, ChatVariableList

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.8,
        max_tokens=2000,
        presence_penalty=0.1
    )

    messages = ChatMessageList(
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant for Globant Enterprise AI."),
            ChatMessage(role="user", content="What AI solutions does Globant offer?")
        ]
    )

    variables = ChatVariableList(
        variables=[
            ChatVariable(key="user_region", value="North America"),
            ChatVariable(key="industry", value="Technology")
        ]
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        thread_id="thread_123e4567-e89b-12d3-a456-426614174000",
        variables=variables
    )
    print(response)

With tool choice:

.. code-block:: python

    from pygeai.chat.managers import ChatManager
    from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList, ToolChoice, ToolChoiceObject, ToolChoiceFunction

    manager = ChatManager()

    llm_settings = LlmSettings(
        temperature=0.6,
        max_tokens=800,
        frequency_penalty=0.1,
        presence_penalty=0.2
    )

    messages = ChatMessageList(
        messages=[ChatMessage(role="user", content="Please get the current weather for San Francisco.")]
    )

    tools = ChatToolList(
        variables=[
            ChatTool(
                name="get_weather",
                description="Fetches the current weather for a given location",
                parameters={
                    "type": "object",
                    "properties": {"location": {"type": "string", "description": "City name"}},
                    "required": ["location"]
                },
                strict=True
            ),
            ChatTool(
                name="send_notification",
                description="Sends a notification with a message",
                parameters={
                    "type": "object",
                    "properties": {"message": {"type": "string", "description": "Notification content"}},
                    "required": ["message"]
                },
                strict=False
            )
        ]
    )

    tool_choice = ToolChoice(
        value=ToolChoiceObject(
            function=ToolChoiceFunction(name="get_weather")
        )
    )

    response = manager.chat_completion(
        model="saia:assistant:Welcome data Assistant 3",
        messages=messages,
        llm_settings=llm_settings,
        tool_choice=tool_choice,
        tools=tools
    )
    print(response)
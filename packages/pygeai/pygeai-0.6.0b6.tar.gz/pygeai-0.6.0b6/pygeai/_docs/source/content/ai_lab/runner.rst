Runner
======

The `Runner` class in the PyGEAI SDK's `lab` module provides a straightforward, asynchronous interface for executing AI agent tasks within the Globant Enterprise AI Lab's runtime environment. It enables developers to run agents with flexible input formats and customizable language model (LLM) settings, facilitating both testing and production use cases. The `Runner` class abstracts the complexity of chat completion requests, handling message processing and LLM configuration to deliver a `ProviderResponse` object containing the agent’s response and metadata.

Overview
-------

The `Runner` class is designed to execute agent tasks by invoking the Lab’s chat completion API. It supports multiple input types—strings, `ChatMessage`, or `ChatMessageList`—allowing developers to interact with agents in various contexts, from simple text inputs to structured conversation histories. The class also accepts optional LLM settings to fine-tune the agent's behavior, such as temperature, token limits, and penalties, ensuring precise control over task execution.

The `Runner` is particularly useful for:

- **Testing Agents**: Validate agent behavior during development by running tasks with different inputs and configurations.
- **Production Execution**: Integrate agent execution into applications, leveraging the Lab’s runtime for scalable task processing.
- **Flexible Input Handling**: Support diverse use cases by accepting raw text, single messages, or multi-message conversation contexts.

Key Features
------------

- **Asynchronous Execution**: Uses `asyncio` for non-blocking task execution, suitable for high-performance applications.
- **Flexible Input Types**:
  - **String**: Simple text input, automatically converted to a user message.
  - **ChatMessage**: A single message with a specified role (e.g., "user") and content.
  - **ChatMessageList**: A list of messages, enabling conversation history or system prompts.
- **Customizable LLM Settings**: Accepts `LlmSettings` or dictionary-based configurations to adjust parameters like temperature, max tokens, and penalties.
- **Error Handling**: Raises `WrongArgumentError` for invalid input types, ensuring robust validation.
- **Integration with AILabManager**: Works seamlessly with agents created and managed via the `AILabManager` class.

Usage
-----

The `Runner` class is invoked via its asynchronous `run` method, which takes an `Agent` instance, user input, and optional LLM settings. The method returns a `ProviderResponse` object containing the agent’s response, usage details, and metadata. Below are examples demonstrating its usage with different input types, based on a scenario where an agent translates text into ancient French.

### Example: Creating and Running an Agent

First, an agent is created using the `AILabManager` to translate modern text into ancient French. The agent is then executed using the `Runner` class with various input formats.

.. code-block:: python

    import asyncio
    from pygeai.lab.runners import Runner
    from pygeai.lab.managers import AILabManager
    from pygeai.lab.models import Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList
    from pygeai.core.models import ChatMessageList, ChatMessage, LlmSettings

    manager = AILabManager()
    project_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # Track created entities for rollback
    created_entities = {"agent_id": None}

    def rollback():
        """Deletes created entities to clean up."""
        print("\n=== Initiating Rollback ===")
        if created_entities["agent_id"]:
            print(f"Deleting agent {created_entities['agent_id']}...")
            result = manager.delete_agent(project_id=project_id, agent_id=created_entities["agent_id"])
            print(f"Rollback: {result}")
        print("Rollback complete.")

    def create_translation_agent():
        """Creates and publishes an agent for translating text into ancient French."""
        print("\n=== Agent Creation Flow ===")
        print("Creating agent 'AncientFrenchTranslator' as draft...")
        agent = Agent(
            name="AncientFrenchTranslatorTest",
            access_scope="private",
            public_name="ancient_french_translator_test",
            job_description="Translates modern text into ancient French",
            avatar_image="https://example.com/ancient_french_avatar.png",
            description="An agent for translating text into ancient French",
            agent_data=AgentData(
                prompt=Prompt(
                    instructions="Translate the provided text into ancient French, using vocabulary and grammar consistent with medieval French (circa 12th-14th century). Ensure the tone is formal and historically appropriate.",
                    inputs=["text"],
                    outputs=[
                        PromptOutput(key="translated_text", description="Text translated into ancient French")
                    ],
                    examples=[
                        PromptExample(
                            input_data="Text: Hello, how are you today?",
                            output='{"translated_text": "Salvete, comment estes-vous or?"}'
                        ),
                        PromptExample(
                            input_data="Text: I am going to the market.",
                            output='{"translated_text": "Je vais au marchié."}'
                        )
                    ]
                ),
                llm_config=LlmConfig(
                    max_tokens=1000,
                    timeout=60,
                    sampling=Sampling(temperature=0.6, top_k=50, top_p=0.95)
                ),
                models=ModelList(models=[
                    Model(name="gpt-4-turbo"),
                    Model(name="mistral-7b")
                ]),
                resource_pools=None
            ),
            is_draft=True,
            revision=1,
            status="pending"
        )

        # Create, update, and publish the agent
        create_agent_result = manager.create_agent(project_id=project_id, agent=agent, automatic_publish=False)
        if isinstance(create_agent_result, Agent):
            created_entities["agent_id"] = create_agent_result.id
            agent = create_agent_result
            agent.description = "Specialized agent for accurate ancient French translations"
            manager.update_agent(project_id=project_id, agent=agent, automatic_publish=False)
            manager.publish_agent_revision(project_id=project_id, agent_id=created_entities["agent_id"], revision="1")
            return manager.get_agent(project_id=project_id, agent_id=created_entities["agent_id"])
        else:
            rollback()
            raise Exception("Agent creation failed")

    async def test_translation_agent(agent):
        """Tests the ancient French translation agent with different input types."""
        print("\n=== Testing Ancient French Translation Agent ===")

        # Test 1: String Input
        print("Test 1: Translating a string input...")
        user_input = "Good morning, my friend!"
        try:
            response = await Runner.run(
                agent=agent,
                user_input=user_input,
                llm_settings={
                    "temperature": 0.6,
                    "max_tokens": 200,
                    "frequency_penalty": 0.1,
                    "presence_penalty": 0.2
                }
            )
            print(f"Input: {user_input}")
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error in Test 1: {e}")

        # Test 2: ChatMessage Input
        print("\nTest 2: Translating a ChatMessage input...")
        chat_message = ChatMessage(
            role="user",
            content="I am traveling to a distant land."
        )
        try:
            response = await Runner.run(
                agent=agent,
                user_input=chat_message,
                llm_settings=LlmSettings(
                    temperature=0.7,
                    max_tokens=300,
                    frequency_penalty=0.0,
                    presence_penalty=0.0
                )
            )
            print(f"Input: {chat_message.content}")
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error in Test 2: {e}")

        # Test 3: ChatMessageList Input
        print("\nTest 3: Translating a ChatMessageList input...")
        chat_message_list = ChatMessageList(messages=[
            ChatMessage(role="system", content="Translate the following into ancient French with a formal tone."),
            ChatMessage(role="user", content="The sun rises slowly over the hills.")
        ])
        try:
            response = await Runner.run(
                agent=agent,
                user_input=chat_message_list
                # Using default LLM settings
            )
            print(f"Input: System: {chat_message_list.messages[0].content}\nUser: {chat_message_list.messages[1].content}")
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error in Test 3: {e}")

    async def main():
        try:
            agent = create_translation_agent()
            await test_translation_agent(agent)
            print("\n=== Translation Agent Testing Completed Successfully ===")
            rollback()
        except Exception as e:
            rollback()
            print(f"\n# Critical error: {e}")

    if __name__ == "__main__":
        asyncio.run(main())

### Output Explanation

The `run` method returns a `ProviderResponse` object, which includes:

- **choices**: A list of `Choice` objects, each containing a `ChatMessage` with the agent’s response (e.g., translated text).
- **usage**: A `UsageDetails` object detailing token counts, costs, and currency.
- **model**: The LLM model used (e.g., `gpt-4-turbo-2024-04-09`).
- **created**: A timestamp for when the response was generated.
- **id**: A unique identifier for the chat completion request (optional).
- **system_fingerprint**: A unique identifier for the system configuration (optional).
- **service_tier**: The service tier used for the request (optional).
- **object**: A string indicating the response type, typically `chat.completion` (optional).

For example, in the string input test (`"Good morning, my friend!"`):

- The response includes a `ChatMessage` with content: `"Salut, amis mien! Bon matin à vous!"`.
- Usage details show `completion_tokens=15`, `prompt_tokens=312`, and `total_cost=0.00357` USD.
- Metadata includes `model='gpt-4-turbo-2024-04-09'`, `created=1745598637`, and `id='chatcmpl-BQGEfS8w0z3ly6OZfRKZbN1VxQyFs'`.

### Input Flexibility

The `Runner` class’s ability to handle multiple input types is a key strength, enabling developers to tailor interactions to specific use cases:

- **String Input**: Ideal for quick tests or simple interactions. The input is automatically wrapped as a `ChatMessage` with the "user" role.
- **ChatMessage Input**: Allows specification of the message role (e.g., "user", "system") and content, useful for structured single-message interactions.
- **ChatMessageList Input**: Supports conversation history or multi-message contexts, such as including a system prompt followed by user input, enabling complex dialogues.

This flexibility ensures the `Runner` can accommodate both lightweight prototyping and sophisticated conversational workflows.

### LLM Settings Customization

The `llm_settings` parameter accepts either a dictionary or an `LlmSettings` object, allowing developers to fine-tune the agent’s behavior. Key parameters include:

- `temperature`: Controls randomness (e.g., 0.6 for balanced outputs).
- `max_tokens`: Limits the response length (e.g., 200 or 300 tokens).
- `frequency_penalty` and `presence_penalty`: Adjusts token repetition tendencies.

If no `llm_settings` are provided, the `Runner` applies default settings (`temperature=0.6`, `max_tokens=800`, `frequency_penalty=0.1`, `presence_penalty=0.2`).

Error Handling
--------------

The `Runner` class validates input types and raises a `WrongArgumentError` if the `user_input` is not a string, `ChatMessage`, or `ChatMessageList`. Developers should handle exceptions to ensure robust execution, as shown in the example’s try-except blocks.

Integration with AILabManager
----------------------------

The `Runner` integrates seamlessly with the `AILabManager` class, which is used to create, manage, and retrieve agents. In the example, the `AILabManager` creates and publishes the agent, which is then passed to the `Runner` for execution. This workflow ensures agents are properly configured before runtime execution.

Best Practices
--------------

- **Input Validation**: Always validate input types before passing to `Runner.run` to avoid `WrongArgumentError`.
- **Asynchronous Execution**: Use `await` in async functions or `asyncio.run` for top-level execution to handle the `Runner`’s asynchronous nature.
- **Rollback Mechanism**: Implement rollback logic (as shown in the example) to clean up created entities during testing or error scenarios.
- **LLM Tuning**: Experiment with `llm_settings` to optimize agent responses for specific tasks, balancing creativity and precision.
- **Testing with Multiple Inputs**: Test agents with all supported input types to ensure robustness across use cases.
- **Response Processing**: Extract the agent’s response from the `ProviderResponse` object’s `choices` list (e.g., `response.choices[0].message.content`) for further processing.

The `Runner` class is a powerful tool for executing AI agents within the Globant Enterprise AI Lab, offering flexibility, ease of use, and seamless integration with the broader PyGEAI SDK ecosystem.

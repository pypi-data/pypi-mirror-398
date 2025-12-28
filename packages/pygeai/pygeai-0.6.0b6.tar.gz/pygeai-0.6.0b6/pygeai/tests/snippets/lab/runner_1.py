import asyncio

from pygeai.lab.runners import Runner
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList
)
from pygeai.core.models import ChatMessageList, ChatMessage, LlmSettings

manager = AILabManager()
project_id = "2ca6883f-6778-40bb-bcc1-85451fb11107"

# Track created entities for rollback
created_entities = {
    "agent_id": None
}


def rollback():
    """
    Deletes created entities to clean up after execution or in case of errors.
    """
    print("\n=== Initiating Rollback ===")
    if created_entities["agent_id"]:
        print(f"Deleting agent {created_entities['agent_id']}...")
        result = manager.delete_agent(project_id=project_id, agent_id=created_entities["agent_id"])
        print(f"Rollback: {result}")
    print("Rollback complete.")


def create_translation_agent():
    """
    Creates and publishes an agent for translating text into ancient French.

    :return: Agent - The created and published agent.
    """
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
                Model(name="gpt-4-turbo"),  # Assuming a model capable of handling historical language
                Model(name="mistral-7b")
            ]),
            resource_pools=None  # No tools or resource pools needed for this example
        ),
        is_draft=True,
        revision=1,
        status="pending"
    )

    # Create the agent
    create_agent_result = manager.create_agent(project_id=project_id, agent=agent, automatic_publish=False)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created Agent: {create_agent_result.name}, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print("Error: Agent creation failed:", create_agent_result)
        rollback()
        raise Exception("Agent creation failed")

    # Update the agent with additional details
    print("Updating agent with refined description...")
    agent = create_agent_result
    agent.description = "Specialized agent for accurate ancient French translations"
    agent.job_description = "Translates modern text into historically accurate ancient French"

    update_agent_result = manager.update_agent(project_id=project_id, agent=agent, automatic_publish=False)
    if isinstance(update_agent_result, Agent):
        print(f"Success: Updated Agent: {update_agent_result.description}")
    else:
        print("Error: Agent update failed:", update_agent_result)
        rollback()
        raise Exception("Agent update failed")

    # Publish the agent
    print("Publishing agent revision '1'...")
    publish_agent_result = manager.publish_agent_revision(project_id=project_id, agent_id=created_entities["agent_id"],
                                                          revision="1")
    if isinstance(publish_agent_result, Agent):
        print(f"Success: Published Agent Revision: {publish_agent_result.name}")
    else:
        print("Error: Agent publish failed:", publish_agent_result)
        rollback()
        raise Exception("Agent publish failed")

    # Retrieve the latest agent version
    print("Retrieving latest agent version...")
    latest_agent = manager.get_agent(project_id=project_id, agent_id=created_entities["agent_id"])
    if isinstance(latest_agent, Agent):
        print(f"Success: Latest Agent: {latest_agent.name}, Description: {latest_agent.description}")
    else:
        print("Error: Agent retrieval failed:", latest_agent.errors)
        rollback()
        raise Exception("Agent retrieval failed")

    return latest_agent


async def test_translation_agent(agent):
    """
    Tests the ancient French translation agent using the Runner class.

    :param agent: Agent - The agent to test.
    """
    print("\n=== Testing Ancient French Translation Agent ===")

    # Test case 1: Simple string input
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

    # Test case 2: ChatMessage input
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

    # Test case 3: ChatMessageList input
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
        print(f"Input: _System: {chat_message_list.messages[0].content}\nUser: {chat_message_list.messages[1].content}")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error in Test 3: {e}")


async def main():
    try:
        # Create and publish the translation agent
        agent = create_translation_agent()

        # Test the agent with different input types
        await test_translation_agent(agent)

        print("\n=== Translation Agent Testing Completed Successfully ===")

        rollback()
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
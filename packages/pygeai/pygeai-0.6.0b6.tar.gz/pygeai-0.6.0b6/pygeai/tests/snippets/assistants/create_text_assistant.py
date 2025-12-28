from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import TextAssistant, LlmSettings, WelcomeData, WelcomeDataFeature, \
    WelcomeDataExamplePrompt, GuardrailSettings
from pygeai.core.services.llm.model import Model
from pygeai.core.services.llm.providers import Provider


manager = AssistantManager()

guardrail_settings = GuardrailSettings(
    llm_output=True,
    input_moderation=True,
    prompt_injection=True
)

llm_settings = LlmSettings(
    provider_name=Provider.OPENAI,
    model_name=Model.OpenAI.GPT_4,
    temperature=0.7,
    max_tokens=1000,
    upload_files=False,
    guardrail_settings=guardrail_settings
)

welcome_data = WelcomeData(
    title="AI Assistant",
    description="An AI-powered assistant to help with various tasks.",
    features=[
        WelcomeDataFeature(title="Feature 1", description="Description of feature 1"),
        WelcomeDataFeature(title="Feature 2", description="Description of feature 2")
    ],
    examples_prompt=[
        WelcomeDataExamplePrompt(title="Example 1", description="This is an example", prompt_text="How can I help you today?"),
        WelcomeDataExamplePrompt(title="Example 2", description="Another example", prompt_text="Tell me a joke.")
    ]
)

assistant = TextAssistant(
    name="ChatBot",
    description="A chatbot assistant for customer support",
    prompt="Hello! How can I assist you today?",
    llm_settings=llm_settings,
    welcome_data=welcome_data
)


try:
    response = manager.create_assistant(assistant)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

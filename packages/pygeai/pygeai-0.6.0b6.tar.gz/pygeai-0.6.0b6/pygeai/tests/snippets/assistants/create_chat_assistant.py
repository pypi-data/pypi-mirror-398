from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import LlmSettings, WelcomeData, WelcomeDataFeature, \
    WelcomeDataExamplePrompt, GuardrailSettings, ChatAssistant

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
    title="Assistant with WelcomeData",
    description="It is to test WelcomeData",
    features=[
        WelcomeDataFeature(title="First Feature", description="First Feature Description"),
        WelcomeDataFeature(title="Second Feature", description="Second Feature Description")
    ],
    examples_prompt=[
        WelcomeDataExamplePrompt(
            title="First Prompt Example",
            description="First Prompt Example Description",
            prompt_text="You are an assistant specialized in translating"
        )
    ]
)

assistant = ChatAssistant(
    name="Welcome data Assistant 5",
    description="A chatbot assistant for customer support",
    prompt="Translate to French",
    llm_settings=llm_settings,
    welcome_data=welcome_data
)

try:
    response = manager.create_assistant(assistant)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

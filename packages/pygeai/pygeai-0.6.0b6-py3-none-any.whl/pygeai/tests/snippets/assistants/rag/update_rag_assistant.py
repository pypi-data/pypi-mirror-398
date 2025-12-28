from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import WelcomeDataFeature, WelcomeDataExamplePrompt, WelcomeData
from pygeai.assistant.rag.models import RAGAssistant


features = [
    WelcomeDataFeature(
        title="Updated weather conditions",
        description="Get the state of the weather in any country"
    ),
    WelcomeDataFeature(
        title="Rain probability updated",
        description="Get the rain probability in any location"
    )
]

examples_prompt = [
    WelcomeDataExamplePrompt(
        title="First Prompt Example",
        description="First Prompt Example Description",
        prompt_text="You are an assistant specializing in..."
    )
]

welcome_data = WelcomeData(
    title="Welcome to RAG Update",
    description="It is a RAG created with WelcomeData via API",
    features=features,
    examples_prompt=examples_prompt
)

rag_assistant = RAGAssistant(
    name="Test-Profile-WelcomeData-2",
    status=1,
    description="Updated RAGAssistant profile with welcome data",
    template="",
    welcome_data=welcome_data,
    search_options=None,
    index_options=None
)

manager = AssistantManager()

updated_assistant = manager.update_assistant(assistant=rag_assistant)

print(updated_assistant)



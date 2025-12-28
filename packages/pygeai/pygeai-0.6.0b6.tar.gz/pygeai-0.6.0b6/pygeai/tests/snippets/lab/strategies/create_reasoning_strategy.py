from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ReasoningStrategy, LocalizedDescription

manager = AILabManager()
strategy = ReasoningStrategy(
    name="RSName3",
    system_prompt="Let's think step by step.",
    access_scope="private",
    type="addendum",
    localized_descriptions=[
        LocalizedDescription(language="spanish", description="RSName spanish description"),
        LocalizedDescription(language="english", description="RSName english description"),
        LocalizedDescription(language="japanese", description="RSName japanese description")
    ]
)

result = manager.create_reasoning_strategy(
    strategy=strategy,
    automatic_publish=True
)

print(f"Created: {result.name}, ID: {result.id}")

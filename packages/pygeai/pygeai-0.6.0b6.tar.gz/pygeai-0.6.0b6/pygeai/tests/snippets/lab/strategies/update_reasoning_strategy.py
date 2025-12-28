from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ReasoningStrategy, LocalizedDescription

strategy = ReasoningStrategy(
    id="2b757122-3e36-499d-909e-87074c3afc94",
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

manager = AILabManager()
strategy.system_prompt = "Updated step-by-step thinking."

result = manager.update_reasoning_strategy(
    strategy=strategy,
    automatic_publish=False,
    upsert=False
)

print(f"Updated: {result.name}, Prompt: {result.system_prompt}")

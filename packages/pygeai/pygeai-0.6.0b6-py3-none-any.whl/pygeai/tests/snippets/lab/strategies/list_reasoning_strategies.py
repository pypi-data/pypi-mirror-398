from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, ReasoningStrategyList

manager = AILabManager()
filter_settings = FilterSettings(
    # name="RSName2",
    start="0",
    count="100",
    allow_external=True,
    access_scope="private"
)

result = manager.list_reasoning_strategies(filter_settings)
print(f"Found {len(result.strategies)} strategies:")
for strategy in result.strategies:
    print(f"Name: {strategy.name}, ID: {strategy.id}")

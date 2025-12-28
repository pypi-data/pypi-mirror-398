from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ReasoningStrategy

manager = AILabManager()

result = manager.get_reasoning_strategy(
    reasoning_strategy_id="2b757122-3e36-499d-909e-87074c3afc94"
)

print(f"Retrieved: {result.name}, ID: {result.id}")

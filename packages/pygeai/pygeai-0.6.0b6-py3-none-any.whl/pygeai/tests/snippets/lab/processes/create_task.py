from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Task

manager = AILabManager()
task = Task(name="basic-task-4", description="Basic task for process", title_template="Basic Task")
result = manager.create_task(task=task, automatic_publish=True)

print(f"Created task: {result.name}, ID: {result.id}")

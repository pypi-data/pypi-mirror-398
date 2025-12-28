from pygeai.assistant.managers import AssistantManager
from pygeai.organization.managers import OrganizationManager

manager = AssistantManager()


response = manager.delete_assistant(assistant_name="Test-Profile-WelcomeData-9")
print(f"response: {response}")

from pygeai.assistant.managers import AssistantManager
from pygeai.organization.managers import OrganizationManager

manager = AssistantManager()


response = manager.get_assistant_data(assistant_name="Test-Profile-WelcomeData-2")
print(f"response: {response}")

from pygeai.assistant.managers import AssistantManager
from pygeai.organization.managers import OrganizationManager

manager = AssistantManager()

response = manager.get_document_list(name="Test-Profile-WelcomeData-4")
print(response)
from pygeai.assistant.managers import AssistantManager
from pygeai.organization.managers import OrganizationManager

manager = AssistantManager()

response = manager.get_request_status("2a7c857c-175a-4f40-b219-6a2afff97d7a")
print(f"response: {response}")

from pygeai.assistant.managers import AssistantManager


manager = AssistantManager()

response = manager.delete_all_documents(name="Test-Profile-WelcomeData-3")
print(response)
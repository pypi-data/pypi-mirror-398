from pygeai.assistant.managers import AssistantManager


manager = AssistantManager()

response = manager.cancel_request("2a7c857c-175a-4f40-b219-6a2afff97d7a")
print(f"response: {response}")

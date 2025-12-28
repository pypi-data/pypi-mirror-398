from pygeai.assistant.managers import AssistantManager


manager = AssistantManager()


response = manager.get_assistant_data(assistant_id="3372b866-36b3-4541-8897-d371dab99f10")
print(f"response: {response}")

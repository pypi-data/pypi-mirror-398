from pygeai.assistant.data_analyst.clients import DataAnalystAssistantClient

client = DataAnalystAssistantClient()
try:
    status = client.get_status(assistant_id="bab64d47-6416-4f26-a0f4-765db7416652")
    print(status)
except ValueError as e:
    print(f"Error: {e}")


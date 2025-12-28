from pygeai.assistant.data_analyst.clients import DataAnalystAssistantClient

client = DataAnalystAssistantClient()

result = client.extend_dataset(
    assistant_id="bab64d47-6416-4f26-a0f4-765db7416652",
    file_paths=["./magic_burgers_sales_data.csv"]
)
print(result)
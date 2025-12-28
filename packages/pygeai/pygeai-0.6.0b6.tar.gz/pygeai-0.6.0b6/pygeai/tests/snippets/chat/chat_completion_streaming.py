from pygeai.chat.clients import ChatClient

client = ChatClient()

llm_settings = {
    "temperature": 0.6,
    "max_tokens": 800,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.2
}

messages = [
    {
        "role": "user",
        "content": "Please get the current weather for San Francisco."
    }
]

tools = [
    {
        "name": "get_weather",
        "description": "Fetches the current weather for a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"]
        },
        "strict": True
    },
    {
        "name": "send_notification",
        "description": "Sends a notification with a message",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Notification content"}
            },
            "required": ["message"]
        },
        "strict": False
    }
]

tool_choice = {
    "type": "function",
    "function": {
        "name": "get_weather"
    }
}

response = client.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    stream=True,
    tools=tools,
    tool_choice=tool_choice,
    **llm_settings
)

for chunk in response:
    print(chunk, end="")

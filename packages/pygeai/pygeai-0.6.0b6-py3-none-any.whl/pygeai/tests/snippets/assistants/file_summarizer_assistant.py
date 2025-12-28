from uuid import uuid4
from pygeai.chat.managers import ChatManager
from pygeai.core.files.responses import UploadFileResponse
from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import UploadFile
from pygeai.core.models import ChatMessageList, ChatMessage, LlmSettings
from pygeai.assistant.managers import AssistantManager
from pygeai.core.services.llm.model import Model
from pygeai.core.services.llm.providers import Provider
from pygeai.core.models import WelcomeData, WelcomeDataFeature, WelcomeDataExamplePrompt, GuardrailSettings, ChatAssistant

project_id = "2ca6883f-6778-40bb-bcc1-85451fb11107"

file_manager = FileManager(
    organization_id="4aa15b61-d3c7-4a5c-99b8-052d18a04ff2",
    project_id=project_id
)
chat_manager = ChatManager()
assistant_manager = AssistantManager()

created_entities = {
    "assistant_id": None,
    "file_id": None
}


def rollback():
    print("\n=== Initiating Rollback ===")
    if created_entities["assistant_id"]:
        print(f"Deleting assistant {created_entities['assistant_id']}...")
        result = assistant_manager.delete_assistant(assistant_id=created_entities["assistant_id"])
        print(f"Rollback: {result}")
    if created_entities["file_id"]:
        print(f"Deleting file {created_entities['file_id']}...")
        result = file_manager.delete_file(file_id=created_entities["file_id"])
        print(f"Rollback: {result}")
    print("Rollback complete.")


def main():
    # File Upload Flow
    print("\n=== File Upload Flow ===")
    print("Uploading file 'test.txt'...")
    file_to_upload = UploadFile(
        name="test.txt",
        path="./test.txt",
        folder="summaries"
    )
    upload_result = file_manager.upload_file(file=file_to_upload)
    if isinstance(upload_result, UploadFileResponse) and upload_result.success:
        print(f"Success: Uploaded File: test.txt, ID: {upload_result.id}")
        created_entities["file_id"] = upload_result.id
    else:
        print("Error: File upload failed:", upload_result)
        rollback()
        exit()

    # Retrieve File Metadata
    print("Retrieving file metadata...")
    file_data = file_manager.get_file_data(file_id=created_entities["file_id"])
    if hasattr(file_data, "name"):
        file_name = file_data.name
        print(f"Success: Retrieved File Name: {file_name}")
    else:
        print("Error: File retrieval failed:", file_data)
        rollback()
        exit()

    # Assistant Flow
    print("\n=== Assistant Flow ===")
    print("Creating assistant 'FileSummaryAssistant'...")
    assistant_id = str(uuid4())
    guardrail_settings = GuardrailSettings(
        llm_output=True,
        input_moderation=True,
        prompt_injection=True
    )
    llm_settings = LlmSettings(
        provider_name=Provider.OPENAI,
        model_name=Model.OpenAI.GPT_4,
        temperature=0.7,
        max_tokens=1000,
        upload_files=True,
        guardrail_settings=guardrail_settings
    )
    welcome_data = WelcomeData(
        title="File Summary Assistant",
        description="An assistant for summarizing files",
        features=[
            WelcomeDataFeature(title="File Summarization", description="Summarizes content from uploaded text files"),
            WelcomeDataFeature(title="Quick Processing", description="Generates concise summaries in under 50 words")
        ],
        examples_prompt=[
            WelcomeDataExamplePrompt(
                title="Summarize File",
                description="Summarize the content of an uploaded file",
                prompt_text=f"Summarize the content of the file {{file:{file_name}}} in 50 words or less."
            )
        ]
    )
    assistant = ChatAssistant(
        id=assistant_id,
        name="FileSummaryAssistant2",
        description="An assistant for summarizing text file content",
        prompt="Read the provided text file by its ID and generate a concise summary in 50 words or less.",
        llm_settings=llm_settings,
        welcome_data=welcome_data
    )
    create_assistant_result = assistant_manager.create_assistant(assistant)
    create_assistant_result = create_assistant_result.assistant if hasattr(create_assistant_result, "assistant") else create_assistant_result
    if isinstance(create_assistant_result, ChatAssistant):
        print(f"Success: Created Assistant: {create_assistant_result.name}, ID: {create_assistant_result.id}")
        created_entities["assistant_id"] = create_assistant_result.id
    else:
        print("Error: Assistant creation failed:", create_assistant_result)
        rollback()
        exit()

    # Chat Completion Flow
    print("\n=== Chat Completion Flow ===")
    print(f"Asking assistant about the uploaded file '{file_name}'...")
    messages = ChatMessageList(messages=[
        ChatMessage(
            role="user",
            content=f"Please summarize the content of the {{file:{file_name}}} ({file_name}) in 50 words or less."
        )
    ])
    chat_response = chat_manager.chat_completion(
        model=f"saia:assistant:{assistant.name}",
        messages=messages,
        llm_settings=llm_settings
    )
    if hasattr(chat_response, "choices") and chat_response.choices:
        print(f"Success: Chat Response: {chat_response.choices[0].message.content}")
    else:
        print("Error: Chat completion failed:", chat_response)
        rollback()
        exit()

    print("\n=== Process Completed Successfully ===")


if __name__ == "__main__":
    try:
        main()
        rollback()
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")
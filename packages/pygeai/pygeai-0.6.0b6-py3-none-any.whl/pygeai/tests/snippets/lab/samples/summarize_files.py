import logging
import os
from uuid import uuid4

from dotenv import load_dotenv
from pydantic_settings import SettingsConfigDict
from pygeai.chat.managers import ChatManager
from pygeai.core.files.responses import UploadFileResponse
from pygeai.lab.managers import AILabManager
from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import UploadFile
from pygeai.core.models import ChatMessageList, ChatMessage, LlmSettings
from pygeai.lab.models import Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList

logger = logging.getLogger(__name__)

project_id = "2ca6883f-6778-40bb-bcc1-85451fb11107"
organization_id = "4aa15b61-d3c7-4a5c-99b8-052d18a04ff2"

lab_manager = AILabManager()
file_manager = FileManager(organization_id=organization_id, project_id=project_id)
chat_manager = ChatManager()

created_entities = {
    "agent_id": None,
    "file_id": None
}


def rollback():
    print("\n=== Initiating Rollback ===")
    if created_entities["agent_id"]:
        print(f"Deleting agent {created_entities['agent_id']}...")
        result = lab_manager.delete_agent(agent_id=created_entities["agent_id"])
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
        path="test.txt",
        #folder="summaries"
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

    # Agent Flow
    print("\n=== Agent Flow ===")
    print("Creating agent 'FileSummaryAgent' as draft...")
    agent_id = str(uuid4())
    agent = Agent(
        id=agent_id,
        name="FileSummaryAgent2",
        access_scope="private",
        job_description="Reads and summarizes content from text files",
        description="An agent designed to process and summarize file content",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Read the provided text file by its ID and generate a concise summary.",
                context="You are a helpful agent that can read and summarize text files.",
                inputs=["file_id"],
                outputs=[
                    PromptOutput(key="summary", description="Summary of the file content")
                ],
                examples=[
                    PromptExample(
                        input_data=f"File ID: {created_entities['file_id']}",
                        output='{"summary": "Summary of test.txt content."}'
                    )
                ]
            ),
            llm_config=LlmConfig(
                max_tokens=2000,
                timeout=60,
                sampling=Sampling(temperature=0.8)
            ),
            models=ModelList(models=[
                Model(name="gpt-4o-mini")
            ])
        ),
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_agent_result = lab_manager.create_agent(agent=agent, automatic_publish=False)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created Agent: {create_agent_result.name}, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print("Error: Agent creation failed:", create_agent_result)
        rollback()
        exit()

    print("Publishing agent revision '1'...")
    publish_agent_result = lab_manager.publish_agent_revision(agent_id=created_entities["agent_id"], revision="1")
    if isinstance(publish_agent_result, Agent):
        print(f"Success: Published Agent Revision: {publish_agent_result.name}")
    else:
        print("Error: Agent publish failed:", publish_agent_result)
        rollback()
        exit()

    # Chat Completion Flow
    print("\n=== Chat Completion Flow ===")
    print(f"Asking agent about the uploaded file '{file_name}'...")
    messages = ChatMessageList(messages=[
        ChatMessage(
            role="user",
            content=f"Please summarize the content of the {{file:{file_name}}} ({file_name}) in 50 words or less."
        )
    ])
    llm_settings = LlmSettings(
        temperature=0.7,
        max_tokens=500
    )
    chat_response = chat_manager.chat_completion(
        model=f"saia:agent:{agent.name}",
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
        #rollback()
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")
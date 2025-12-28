from pygeai.assistant.managers import AssistantManager
from pygeai.assistant.rag.models import UploadDocument, RAGAssistant, UploadType

manager = AssistantManager()

assistant = RAGAssistant(
    name="Test-Profile-WelcomeData-4"
)

document = UploadDocument(
    path="test.txt",
    upload_type=UploadType.MULTIPART,
    metadata={'type': 'test', 'year': 2025},
    content_type="text/plain"
)

response = manager.upload_document(assistant=assistant, document=document)

print(response)
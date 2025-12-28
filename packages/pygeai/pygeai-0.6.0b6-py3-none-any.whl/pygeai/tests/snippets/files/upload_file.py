from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import UploadFile

file = UploadFile(
    path="test.txt",
    name="TestyFile",
    folder="TestyTestTemp"
)

file_manager = FileManager()

response = file_manager.upload_file(file)
print(response)

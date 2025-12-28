from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import File

file = File(id="7fe2393d-8f86-4020-a51f-bc14ab957e1e")

file_manager = FileManager()

response = file_manager.delete_file(file_id=file.id)
print(response)

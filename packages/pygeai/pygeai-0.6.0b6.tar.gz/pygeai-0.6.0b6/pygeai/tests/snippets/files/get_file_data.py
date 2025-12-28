from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import File

file = File(id="9984b837-fe88-4014-ad14-91e1596c8ead")

file_manager = FileManager()

response = file_manager.get_file_data(file_id=file.id)
print(response)

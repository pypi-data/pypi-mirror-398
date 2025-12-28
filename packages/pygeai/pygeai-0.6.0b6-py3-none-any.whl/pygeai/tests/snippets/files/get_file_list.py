from pygeai.core.files.managers import FileManager

file_manager = FileManager()

response = file_manager.get_file_list()
print(response)

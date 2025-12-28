from pygeai.core.files.models import FileList, File
from pygeai.core.files.responses import UploadFileResponse


class FileResponseMapper:

    @classmethod
    def map_to_upload_file_response(cls, data: dict) -> UploadFileResponse:
        return UploadFileResponse(
            id=data.get('dataFileId'),
            url=data.get('dataFileUrl'),
            success=data.get('success')
        )

    @classmethod
    def map_to_file_list_response(cls, data: dict) -> FileList:
        file_list = cls.map_to_file_list(data)

        return FileList(
            files=file_list
        )

    @classmethod
    def map_to_file_list(cls, data: dict) -> list[File]:
        file_list = list()
        files = data.get('dataFiles')
        if files is not None and any(files):
            for file_data in files:
                file = cls.map_to_file(file_data)
                file_list.append(file)

        return file_list

    @classmethod
    def map_to_file(cls, data: dict) -> File:
        return File(
            id=data.get('DataFileId') or data.get('dataFileId'),
            name=data.get('DataFileName') or data.get('dataFileName'),
            extension=data.get('DataFileExtension') or data.get('dataFileExtension'),
            purpose=data.get('DataFilePurpose') or data.get('dataFilePurpose'),
            size=data.get('DataFileSize') or data.get('dataFileSize'),
            url=data.get('DataFileUrl') or data.get('dataFileUrl')

        )
import unittest

from pygeai.core.files.mappers import FileResponseMapper
from pygeai.core.files.models import FileList, File
from pygeai.core.files.responses import UploadFileResponse


class TestFileResponseMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.files.test_mappers.TestFileResponseMapper
    """

    def test_map_to_upload_file_response(self):
        data = {
            'dataFileId': 'file-123',
            'dataFileUrl': 'https://example.com/file.txt',
            'success': True
        }
        
        result = FileResponseMapper.map_to_upload_file_response(data)
        
        self.assertIsInstance(result, UploadFileResponse)
        self.assertEqual(result.id, 'file-123')
        self.assertEqual(result.url, 'https://example.com/file.txt')
        self.assertTrue(result.success)

    def test_map_to_upload_file_response_missing_fields(self):
        data = {}
        
        result = FileResponseMapper.map_to_upload_file_response(data)
        
        self.assertIsNone(result.id)
        self.assertIsNone(result.url)
        self.assertIsNone(result.success)

    def test_map_to_file_list_response(self):
        data = {
            'dataFiles': [
                {
                    'dataFileId': 'file-1',
                    'dataFileName': 'test1.txt',
                    'dataFileExtension': 'txt',
                    'dataFilePurpose': 'testing',
                    'dataFileSize': 1024,
                    'dataFileUrl': 'https://example.com/file1.txt'
                },
                {
                    'dataFileId': 'file-2',
                    'dataFileName': 'test2.pdf',
                    'dataFileExtension': 'pdf',
                    'dataFilePurpose': 'document',
                    'dataFileSize': 2048,
                    'dataFileUrl': 'https://example.com/file2.pdf'
                }
            ]
        }
        
        result = FileResponseMapper.map_to_file_list_response(data)
        
        self.assertIsInstance(result, FileList)
        self.assertEqual(len(result.files), 2)
        self.assertEqual(result.files[0].id, 'file-1')
        self.assertEqual(result.files[1].id, 'file-2')

    def test_map_to_file_list_empty(self):
        data = {'dataFiles': []}
        
        result = FileResponseMapper.map_to_file_list(data)
        
        self.assertEqual(result, [])

    def test_map_to_file_list_none(self):
        data = {}
        
        result = FileResponseMapper.map_to_file_list(data)
        
        self.assertEqual(result, [])

    def test_map_to_file_lowercase_keys(self):
        data = {
            'dataFileId': 'file-1',
            'dataFileName': 'test.txt',
            'dataFileExtension': 'txt',
            'dataFilePurpose': 'testing',
            'dataFileSize': 1024,
            'dataFileUrl': 'https://example.com/file.txt'
        }
        
        result = FileResponseMapper.map_to_file(data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.id, 'file-1')
        self.assertEqual(result.name, 'test.txt')
        self.assertEqual(result.extension, 'txt')
        self.assertEqual(result.purpose, 'testing')
        self.assertEqual(result.size, 1024)
        self.assertEqual(result.url, 'https://example.com/file.txt')

    def test_map_to_file_uppercase_keys(self):
        data = {
            'DataFileId': 'file-2',
            'DataFileName': 'document.pdf',
            'DataFileExtension': 'pdf',
            'DataFilePurpose': 'documentation',
            'DataFileSize': 2048,
            'DataFileUrl': 'https://example.com/doc.pdf'
        }
        
        result = FileResponseMapper.map_to_file(data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.id, 'file-2')
        self.assertEqual(result.name, 'document.pdf')
        self.assertEqual(result.extension, 'pdf')
        self.assertEqual(result.purpose, 'documentation')
        self.assertEqual(result.size, 2048)
        self.assertEqual(result.url, 'https://example.com/doc.pdf')

    def test_map_to_file_mixed_keys(self):
        data = {
            'DataFileId': 'file-3',
            'dataFileName': 'mixed.csv',
            'DataFileExtension': 'csv',
            'dataFilePurpose': 'data',
            'DataFileSize': 512,
            'dataFileUrl': 'https://example.com/data.csv'
        }
        
        result = FileResponseMapper.map_to_file(data)
        
        self.assertEqual(result.id, 'file-3')
        self.assertEqual(result.name, 'mixed.csv')
        self.assertEqual(result.extension, 'csv')


if __name__ == '__main__':
    unittest.main()

import json
from pathlib import Path

from pygeai import logger
from pygeai.core.common.exceptions import InvalidPathException, InvalidJSONException


class JSONLoader:

    @classmethod
    def load_data(cls, file_path: str):
        data = {}
        file = Path(file_path)
        if not file.exists():
            raise InvalidPathException(f"File {file_path} doesn't exist")

        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"The file doesn't contain a valid JSON: {e}")
                raise InvalidJSONException(f"File {file_path} doesn't contain valid JSON.")

        return data

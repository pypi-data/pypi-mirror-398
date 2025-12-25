import json
import logging
from json import JSONDecodeError
from typing import Any

logger = logging.getLogger(__name__)


def json_document_read_handler(path: str) -> str | list[dict[str, Any]] | None:
    """Processes and extracts text from a JSON document format file [*.json].

    :param path: Path to the document file
    :return: A string containing all extracted text or None if the file cannot be read
    """
    # List of encodings to try
    encodings = ["utf-8", "latin-1", "windows-1252", "iso-8859-1", "cp1252"]

    # Try different encodings
    for encoding in encodings:
        try:
            with open(path, encoding=encoding) as file:
                content = file.read()
                try:
                    data = json.loads(content)
                except JSONDecodeError as e:
                    logger.info(f"Invalid JSON file: {path}. Error: {e}")
                    return content
                if isinstance(data, dict):
                    return [data]
                if isinstance(data, list):
                    return data
                return str(data)
        except UnicodeDecodeError:
            continue  # Try the next encoding

    # If all encodings fail, raise an error
    raise ValueError(
        f"Could not decode file {path} with any of the attempted encodings: {encodings}"
    )

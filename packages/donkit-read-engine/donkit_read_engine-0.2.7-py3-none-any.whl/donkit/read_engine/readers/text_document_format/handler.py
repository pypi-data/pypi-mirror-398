def text_document_read_handler(path: str) -> str:
    """Processes and extracts text from a text document format file [TXT / CSV / ...].

    :param path: Path to the document file
    :return: A string containing all extracted text or None if the file cannot be read
    """
    # List of encodings to try
    encodings = ["utf-8", "latin-1", "windows-1252", "iso-8859-1", "cp1252"]

    # Try different encodings
    for encoding in encodings:
        try:
            with open(path, encoding=encoding) as file:
                # Read all lines from the file and store them in a list
                lines: list[str] = file.readlines()
                # Join all lines into a single string and return
                return " ".join([" ".join(line.split()) for line in lines])
        except UnicodeDecodeError:
            continue  # Try the next encoding

    # If all encodings fail, raise an error
    raise ValueError(
        f"Could not decode file {path} with any of the attempted encodings: {encodings}"
    )

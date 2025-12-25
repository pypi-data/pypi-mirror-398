import pandas as pd


def sheet_read_handler(path: str) -> str:
    """Processes and extracts text from all sheets in an Excel file [XLS/XLSX].

    :param path: Path to the document file
    :return: A string containing all extracted text from the first 300 rows of each sheet
    """
    # Read all sheets of the Excel file into a dictionary where keys are sheet names
    # and values are DataFrames. By default, it reads all rows unless limited.
    xls = pd.ExcelFile(path)
    formatted_texts: list[str] = []  # List to store extracted text from all sheets

    # Iterate through each sheet in the Excel file
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
        df = df.fillna("").map(str.strip)  # Remove NaN values and surrounding spaces

        formatted_texts.append("<sheet>")
        formatted_texts.append(f"# {sheet_name}\n")  # Sheet header

        # Check whether the table has column headers
        if not df.empty:
            formatted_texts.append(
                "| " + " | ".join(str(col) for col in df.columns) + " |"
            )  # Column headers
            formatted_texts.append(
                "| " + " | ".join(["---"] * len(df.columns)) + " |"
            )  # Separators

            # Append rows while filtering out empty values
            for _, row in df.iterrows():
                row_values = [
                    str(cell) if cell else " " for cell in row
                ]  # Replace empty cells with a space
                formatted_texts.append("| " + " | ".join(row_values) + " |")

        formatted_texts.append("\n")  # Separate sheets

    return "\n".join(formatted_texts)

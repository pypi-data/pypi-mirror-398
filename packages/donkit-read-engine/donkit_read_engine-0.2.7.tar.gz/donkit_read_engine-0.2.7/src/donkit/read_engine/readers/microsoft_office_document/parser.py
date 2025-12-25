import io
from typing import IO, Any

from docx import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.oxml.text.run import CT_R
from docx.table import Table
from docx.text.paragraph import Paragraph
from loguru import logger


class DocumentParser:
    def __init__(self, document: DocxDocument):
        """Initialize the DocumentParser with a given .docx document."""
        self.document = document  # Store the document to be parsed
        # Approximate number of lines per A4 page
        self.lines_per_page = 40
        # Current page
        self.current_page = 1
        # Line counter for the current page
        self.lines_on_page = 0
        # Maximum line length in characters
        self.max_line_length = 80

    def parse(self) -> list[dict[str, Any]]:
        """
        Parses a document and returns a list of elements (paragraphs, tables, images) with a page reference.

        Returns:
        List of dictionaries containing document elements
        """
        result: list[dict[str, Any]] = []
        self.current_page = 1
        self.lines_on_page = 0

        for element in self.document.element.body.iterchildren():
            # Check for page breaks
            if self._is_page_break(element):
                self.current_page += 1
                self.lines_on_page = 0
                continue

            if isinstance(element, CT_P):  # Paragraph element
                parsed_paragraph = self.parse_paragraph(
                    Paragraph(element, self.document)
                )
                if not parsed_paragraph:
                    continue

                if isinstance(parsed_paragraph, list):
                    # Process a list of elements
                    for item in parsed_paragraph:
                        if isinstance(item, dict):
                            item["page"] = self.current_page
                            # Estimate how many lines the element occupies
                            content = item.get("content", "")
                            if isinstance(content, str):
                                self._count_lines(content)
                            result.append(item)
                else:
                    # Process a single element
                    parsed_paragraph["page"] = self.current_page
                    # Estimate how many lines the element occupies
                    content = parsed_paragraph.get("content", "")
                    if isinstance(content, str):
                        self._count_lines(content)
                    result.append(parsed_paragraph)

            elif isinstance(element, CT_Tbl):  # Table element
                parsed_table = self.parse_table(Table(element, self.document))
                if parsed_table:
                    parsed_table["page"] = self.current_page
                    # Tables generally take more space
                    rows = len(parsed_table.get("content", []))
                    self.lines_on_page += rows * 2  # Rough estimate
                    self._check_page_overflow()
                    result.append(parsed_table)

        # Return parsed results including page information
        return result

    def _is_page_break(self, element) -> bool:
        """Checks if an element is a page break."""
        return isinstance(element, CT_P) and element.xpath('.//w:br[@w:type="page"]')

    def _count_lines(self, text: str) -> None:
        """
        Counts the number of lines in the text and updates the line counter per page.
        If the line limit per page is reached, increments the page number.
        """
        if not text:
            return

        # Count lines considering line breaks
        lines = text.count("\n") + 1

        # Add lines for long text without explicit breaks
        if "\n" not in text:
            lines += len(text) // self.max_line_length

        self.lines_on_page += lines
        self._check_page_overflow()

    def _check_page_overflow(self) -> None:
        """Checks if the number of lines per page has been exceeded."""
        if self.lines_on_page >= self.lines_per_page:
            self.current_page += 1
            self.lines_on_page = self.lines_on_page % self.lines_per_page

    def parse_paragraph(
        self, paragraph: Paragraph
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """
        Parses a paragraph element.
        Checks whether it contains graphics (images or hyperlinks).
        If it does, it processes them separately.
        Otherwise, it extracts and returns the paragraph text.
        """
        if paragraph._element.xpath(
            ".//a:graphic"
        ):  # Paragraph contains a graphic element
            return self._parse_child_paragraph(paragraph._element)
        else:
            text = self.get_element_text(paragraph._element)
            if text:
                style_id = paragraph.style.style_id if paragraph.style else "Normal"
                # Determine whether this is a heading
                if style_id.startswith("Heading"):
                    heading_level = (
                        int(style_id.replace("Heading", ""))
                        if style_id != "Heading"
                        else 1
                    )
                    # Format the heading similar to markdown
                    formatted_text = f"{'#' * heading_level} {text}"
                    return {
                        "type": "Text",
                        "content": formatted_text,
                        "style_id": style_id,
                    }
                else:
                    return {"type": "Text", "content": text, "style_id": style_id}
            return None

    def get_element_text(self, element) -> str:
        """
        Extracts all text from the specified XML element.
        If the element contains text blocks (<w:t>), concatenates them and returns the result.
        """
        try:
            children = element.xpath(
                ".//w:t"
            )  # Locate all text nodes inside the target element
        except Exception as e:
            logger.error(f"Error parsing element: {e}")
            children = (
                element.iterchildren()
            )  # Fallback: iterate children if XPath fails
        return "".join(c.text for c in children if c.text).strip()

    def _parse_child_paragraph(self, element) -> list[dict[str, Any]]:
        """
        Parses a child paragraph containing either graphics or text.
        Processes each child element within the paragraph, extracting the text or graphic content.
        """
        data = []
        for child in element.iterchildren():
            if isinstance(child, CT_R) and child.xpath(".//a:graphic"):
                part = self._parse_graphic(child)
            else:
                text = self.get_element_text(child)
                if text:
                    part = {"type": "Text", "content": text}
                else:
                    continue

            if part is None:
                continue
            data.append(part)
        return data

    def _parse_graphic(self, element) -> dict[str, Any]:
        """
        Parses a graphic element within a paragraph.
        Extracts image data and returns it as part of the document's content.
        """
        try:
            rid = element.xpath(".//a:blip/@*")[0]
            image_bytes: IO[bytes] = io.BytesIO(
                self.document.part.rels[rid]._target.blob
            )
            return {"type": "Image", "content": image_bytes}
        except Exception as e:
            logger.error(f"Error parsing graphic: {e}")
            return None

    def parse_table(self, table: Table, strip=True) -> dict[str, Any]:
        """
        Parses a table element and returns its data along with merged cells.
        The `strip` argument determines whether leading/trailing spaces should be removed from the cell's contents.
        """
        content = [
            [cell.text.strip() if strip else cell.text for cell in row.cells]
            for row in table.rows
        ]

        merged_cells = {}
        for x, row in enumerate(table.rows):
            for y, cell in enumerate(row.cells):
                try:
                    if (
                        hasattr(cell, "_tc")
                        and cell._tc is not None
                        and (cell._tc.vMerge or cell._tc.grid_span != 1)
                    ):
                        tc = (
                            cell._tc.top,
                            cell._tc.bottom,
                            cell._tc.left,
                            cell._tc.right,
                        )
                        merged_cells["_".join(map(str, tc))] = cell.text
                except Exception as e:
                    logger.error(f"Error processing cell at ({x}, {y}): {e}")

        return {"type": "Table", "content": content, "merged_cells": merged_cells}

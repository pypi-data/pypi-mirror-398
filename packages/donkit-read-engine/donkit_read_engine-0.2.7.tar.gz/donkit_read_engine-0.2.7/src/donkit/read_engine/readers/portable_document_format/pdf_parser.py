import os
import threading
from collections import defaultdict

import fitz  # PyMuPDF
from loguru import logger

# Optional unstructured.io support
try:
    from unstructured.partition.pdf import partition_pdf

    HAS_UNSTRUCTURED = True
    print("unstructured available")
except Exception:
    HAS_UNSTRUCTURED = False


class StructuredPDFProcessor:
    """Simple PDF text processor using PyMuPDF.

    Extracts only text content while preserving hierarchical structure
    (headings, paragraphs, lists).
    """

    def __init__(self):
        """Initialize the PDF processor."""
        pass

    def process_pdf(self, pdf_path: str) -> list[dict[str, str | int]]:
        """Process a PDF file and extract structured content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of dictionaries with extracted content and page numbers
        """
        logger.debug(f"Processing PDF file: {pdf_path}")

        raw_results = []
        threads = []
        lock = threading.Lock()

        try:
            # Open PDF document to get page count
            document = fitz.open(pdf_path)
            page_count = len(document)
            document.close()

            # Threading for parallel processing
            def process_page_thread(page_num: int):
                page_content = self._process_page(pdf_path, page_num)
                with lock:
                    raw_results.extend(page_content)

            # Start a thread for each page with a semaphore to limit concurrency
            semaphore = threading.Semaphore(4)  # Limit to 4 concurrent threads

            for page_num in range(page_count):
                thread = threading.Thread(
                    target=lambda p=page_num: self._thread_wrapper(
                        process_page_thread, semaphore, p
                    )
                )
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Group all text by page
            page_text: dict[int, list[str]] = defaultdict(list)
            result = []

            # Collect text per page first
            for item in raw_results:
                page_num = item.get("page", 1)
                item_type = item.get("type", "")

                if item_type == "Text":
                    page_text[page_num].append(item.get("content", ""))
                elif item_type == "Image" or item_type == "Error":
                    result.append(item)

            # Add merged text for every page
            for page_num, texts in sorted(page_text.items()):
                result.append(
                    {"page": page_num, "type": "Text", "content": "\n\n".join(texts)}
                )

            # Sort result by page and type (text first, then images)
            result.sort(
                key=lambda x: (
                    x.get("page", 0),
                    0 if x.get("type", "") == "Text" else 1,
                    x.get("image_index", 0),
                )
            )

            return result

        except Exception as e:
            logger.exception(f"Error processing PDF: {e}")
            return [
                {
                    "page": 1,
                    "type": "Error",
                    "content": f"Error processing PDF: {e!s}",
                }
            ]

    def _thread_wrapper(self, func, semaphore, *args, **kwargs):
        """Helper to run a function with semaphore protection."""
        with semaphore:
            return func(*args, **kwargs)

    def _process_page(self, pdf_path: str, page_num: int) -> list[dict[str, str | int]]:
        """Process a single PDF page and extract text only.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-based)

        Returns:
            List of dictionaries with extracted content
        """
        result = []

        try:
            # Extract text only
            text_content = self._extract_text(pdf_path, page_num)

            # Add text content to result
            if text_content:
                result.append(
                    {
                        "page": page_num + 1,  # Convert to 1-based page numbers
                        "type": "Text",
                        "content": text_content.strip(),
                    }
                )

        except Exception as e:
            logger.error(f"Error processing page {page_num + 1}: {e}")
            result.append(
                {
                    "page": page_num + 1,
                    "type": "Error",
                    "content": f"Error processing page: {e!s}",
                }
            )

        return result

    def _extract_text(self, pdf_path: str, page_num: int) -> str:
        """Extract structured text from a PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-based)

        Returns:
            Extracted text with preserved structure
        """
        document = fitz.open(pdf_path)
        page = document[page_num]

        # Extract text while keeping formatting hints
        text_blocks = []

        # Approximate heading detection via font size
        blocks = page.get_text("dict")["blocks"]

        # Determine the most common font size representing body text
        font_sizes = []
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font_sizes.append(span["size"])

        # Use the most common size as baseline
        body_font_size = 11.0  # default fallback value
        if font_sizes:
            # Simple mode calculation
            sizes_count = {}
            for size in font_sizes:
                sizes_count[size] = sizes_count.get(size, 0) + 1
            most_common = max(sizes_count.items(), key=lambda x: x[1])
            body_font_size = most_common[0]

        # Process text blocks
        for block in blocks:
            if "lines" not in block:
                continue

            block_text = ""
            is_heading = False
            is_list_item = False

            for line in block["lines"]:
                line_text = ""
                line_is_heading = False

                # Detect list items
                first_span = line["spans"][0] if line["spans"] else None
                if first_span and first_span["text"].strip():
                    first_char = first_span["text"].strip()[0]
                    if first_char in ["•", "·", "-", "*"] or (
                        first_char.isdigit()
                        and len(first_span["text"].strip()) > 1
                        and first_span["text"].strip()[1] in [".", ")"]
                    ):
                        is_list_item = True

                for span in line["spans"]:
                    # Check for headings (font noticeably larger than baseline)
                    if (
                        span["size"] > body_font_size * 1.2
                        and len(span["text"].strip()) > 0
                    ):
                        line_is_heading = True
                    line_text += span["text"]

                if line_text.strip():
                    if line_is_heading:
                        is_heading = True
                    block_text += line_text.strip() + " "

            block_text = block_text.strip()
            if block_text:
                if is_heading:
                    # Mark block as a heading based on font size
                    if block["lines"][0]["spans"][0]["size"] > body_font_size * 1.5:
                        text_blocks.append(f"# {block_text}\n\n")
                    else:
                        text_blocks.append(f"## {block_text}\n\n")
                elif is_list_item:
                    # Preserve list formatting
                    if block_text[0].isdigit():
                        # Numbered list
                        text_blocks.append(f"{block_text}\n")
                    else:
                        # Bulleted list
                        text_blocks.append(f"{block_text}\n")
                else:
                    text_blocks.append(f"{block_text}\n\n")

        document.close()

        return "".join(text_blocks)


def parse_pdf(pdf_path: str) -> list[dict[str, str | int]]:
    """Analyze a PDF file and extract text content for RAG.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries with extracted content and page numbers
    """
    try:
        processor = StructuredPDFProcessor()
        return processor.process_pdf(pdf_path)
    except Exception as e:
        logger.exception(f"Error parsing PDF: {e}")
        return [{"page": 1, "type": "Error", "content": f"Error parsing PDF: {e!s}"}]


def parse_pdf_unstructured(pdf_path: str) -> list[dict[str, str | int]]:
    """Parse PDF with unstructured.io if available.

    Falls back to simple list of text chunks per page using element metadata.
    """
    if not HAS_UNSTRUCTURED:
        raise RuntimeError("unstructured not available")

    try:
        # Read strategy and OCR languages from environment (set via CLI in read_engine.py)
        # Tesseract uses language codes like "rus" for Russian, not "ru". Combine with '+'.
        strategy = os.getenv("UNSTRUCTURED_STRATEGY", "hi_res")
        languages_str = os.getenv("UNSTRUCTURED_OCR_LANG", "rus+eng")

        # Convert "rus+eng" to ["rus", "eng"] - unstructured expects a list
        languages = (
            languages_str.split("+") if "+" in languages_str else [languages_str]
        )

        # Call unstructured with correct parameter name `languages` for OCR
        elements = partition_pdf(
            filename=pdf_path,
            infer_table_structure=True,
            include_metadata=True,
            strategy=strategy,
            languages=languages,
        )

        # Group text by page
        pages: dict[int, list[str]] = defaultdict(list)
        results: list[dict[str, str | int]] = []

        for el in elements:
            # Some elements might not have metadata/page number
            meta = getattr(el, "metadata", None)
            page_num = getattr(meta, "page_number", None) or 1
            text = str(getattr(el, "text", "") or "").strip()
            if not text:
                continue
            pages[int(page_num)].append(text)

        for page_num in sorted(pages.keys()):
            content = "\n\n".join(pages[page_num]).strip()
            if content:
                results.append({"page": page_num, "type": "Text", "content": content})

        if not results:
            return [
                {
                    "page": 1,
                    "type": "Error",
                    "content": "No content extracted by unstructured",
                }
            ]

        return results
    except UnicodeDecodeError as e:
        # Common issue with Tesseract OCR output encoding - log without full traceback
        logger.error(
            f"Unicode decode error in unstructured/Tesseract OCR: {e}. "
            "Falling back to alternative PDF parser."
        )
        return [{"page": 1, "type": "Error", "content": f"OCR encoding error: {e!s}"}]
    except Exception as e:
        logger.exception(f"Error parsing PDF with unstructured: {e}")
        return [{"page": 1, "type": "Error", "content": f"unstructured failed: {e!s}"}]


def simple_pdf_read_handler(path: str) -> list[dict[str, str | int]]:
    """Simple PDF text parser without LLM or OCR.

    Uses `StructuredPDFProcessor` for basic text extraction.
    Falls back to unstructured.io if available.
    """
    try:
        result = parse_pdf_unstructured(path)
        if result and isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict) and result[0].get("type") == "Error":
                result = None
    except Exception:
        result = None
    if result is None:
        processor = StructuredPDFProcessor()
        result = processor.process_pdf(path)
    return result

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any
from typing import Literal

from donkit.read_engine.readers.static_visual_format.models import (
    get_image_analysis_service,
)
from dotenv import find_dotenv, load_dotenv
from loguru import logger

from .readers.portable_document_format.handler import LlmPDFReader
from .readers.portable_document_format.pdf_parser import simple_pdf_read_handler
from .readers.json_document_format.handler import json_document_read_handler
from .readers.microsoft_office_sheet.handler import sheet_read_handler
from .readers.microsoft_office_document.handler import (
    document_read_handler,
    LlmDocumentReader,
)
from .readers.microsoft_office_presentation.handler import (
    apresentation_read_handler,
)
from .readers.text_document_format.handler import text_document_read_handler
from .readers.static_visual_format.handler import image_read_handler

try:
    from donkit.llm import LLMModelAbstract
except ImportError:
    LLMModelAbstract = None  # type: ignore[misc, assignment]

# Load .env file with explicit search (important for Windows)
# Try multiple locations in priority order
_env_loaded = False
for _fname in (".env.local", ".env"):
    # 1. Try current working directory
    _cwd_path = Path.cwd() / _fname
    if _cwd_path.exists():
        load_dotenv(_cwd_path, override=False)
        _env_loaded = True
    # 2. Try parent directories (walk up to 3 levels)
    _parent = Path.cwd()
    for _ in range(3):
        _parent = _parent.parent
        _parent_env = _parent / _fname
        if _parent_env.exists():
            load_dotenv(_parent_env, override=False)
            _env_loaded = True
            break
    # 3. Fallback to find_dotenv
    if not _env_loaded:
        _found = find_dotenv(filename=_fname, usecwd=True)
        if _found:
            load_dotenv(_found, override=False)
            _env_loaded = True

if not _env_loaded:
    logger.warning(
        "⚠️ No .env file found in current or parent directories. "
        "LLM-based PDF processing may not be available. "
        f"Current directory: {Path.cwd()}"
    )
    logger.remove()
    logger.configure(handlers=[{"sink": sys.stderr, "level": "DEBUG"}])
else:
    logger.remove()
    logger.configure(
        handlers=[{"sink": sys.stderr, "level": os.getenv("RAGOPS_LOG_LEVEL", "ERROR")}]
    )


class DonkitReader:
    """Main document reader orchestrator.

    Manages initialization of all services and delegates to specific readers.
    """

    def __init__(
        self,
        use_llm: bool = True,
        output_format: Literal["json", "text", "md"] = "json",
        progress_callback: Callable[[int, int, str | None], None] | None = None,
        llm_model: "LLMModelAbstract | None" = None,
    ) -> None:
        """Initialize DonkitReader with appropriate services based on environment.

        Args:
            use_llm: Whether to use LLM for PDF processing (default: True)
                     If False, will use simple PDF reader even if credentials are available
            progress_callback: Optional callback for progress reporting.
                               Signature: (current: int, total: int, message: str | None) -> None
            llm_model: Optional LLM model instance to use for image analysis.
                       If provided, uses this model instead of creating one from env vars.
        """
        self.output_format = output_format
        self._progress_callback = progress_callback
        self._llm_model = llm_model
        self._image_service = (
            self._initialize_image_service(output_format) if use_llm else None
        )
        self._pdf_reader = self._initialize_pdf_reader() if use_llm else None
        self._document_reader = self._initialize_document_reader() if use_llm else None

        self.readers = {
            ".txt": text_document_read_handler,
            ".json": json_document_read_handler,
            ".csv": text_document_read_handler,
            ".xlsx": sheet_read_handler,
            ".xls": sheet_read_handler,
            ".png": image_read_handler,
            ".jpg": image_read_handler,
            ".jpeg": image_read_handler,
        }

    def _initialize_image_service(
        self,
        output_format: Literal["json", "text", "md"] = "json",
    ):
        """Initialize image analysis service based on available credentials and use_llm flag."""
        # If LLM model is provided, use it directly
        if self._llm_model:
            logger.info("📄 Image service available (using provided LLM model)")
            return get_image_analysis_service(
                output_format=output_format,
                llm_model=self._llm_model,
            )

        # Otherwise check for credentials in environment
        creds_keys = {
            "RAGOPS_OPENAI_API_KEY": os.getenv("RAGOPS_OPENAI_API_KEY"),
            "RAGOPS_VERTEX_CREDENTIALS": os.getenv("RAGOPS_VERTEX_CREDENTIALS"),
            "GOOGLE_APPLICATION_CREDENTIALS": os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS"
            ),
            "RAGOPS_AZURE_OPENAI_API_KEY": os.getenv("RAGOPS_AZURE_OPENAI_API_KEY"),
            "RAGOPS_DONKIT_API_KEY": os.getenv("RAGOPS_DONKIT_API_KEY"),
        }
        available_creds = [k for k, v in creds_keys.items() if v]

        if available_creds:
            logger.info(
                f"📄 Image service available (credentials: {', '.join(available_creds)})"
            )
            return get_image_analysis_service(output_format=output_format)
        else:
            logger.info("📄 No LLM credentials found, image analysis disabled")
            return None

    def _initialize_pdf_reader(self) -> LlmPDFReader | None:
        """Initialize PDF reader with image service if available."""
        if self._image_service:
            return LlmPDFReader(
                image_service=self._image_service,
                progress_callback=self._progress_callback,
            )
        return None

    def _initialize_document_reader(self) -> LlmDocumentReader | None:
        """Initialize document reader with image service if available."""
        if self._image_service:
            return LlmDocumentReader(image_service=self._image_service)
        return None

    async def _aread_pdf(
        self, path: str, output_path: str | None = None
    ) -> list[dict] | str:
        """Async: Read PDF using initialized PDF reader.

        Args:
            path: Path to PDF file
            output_path: Optional output path for batch processing

        Returns:
            List of dicts if output_path is None, otherwise output_path string
        """
        if self._pdf_reader:
            return await self._pdf_reader.aread(path, output_path=output_path)
        else:
            return await asyncio.to_thread(simple_pdf_read_handler, path)

    def _read_docx(self, path: str, output_path: str | None = None) -> list[dict] | str:
        """Read DOCX using initialized document reader.

        Args:
            path: Path to DOCX file
            output_path: Optional output path for batch processing

        Returns:
            List of dicts if output_path is None, otherwise output_path string
        """
        if self._document_reader:
            return self._document_reader.read(path, output_path=output_path)
        else:
            return document_read_handler(path)

    def read_document(
        self,
        file_path: str,
        output_dir: str | None = None,
    ) -> str:
        """Main method. Delegates to async aread_document to avoid sync LLM paths."""
        return asyncio.run(self.aread_document(file_path, output_dir))

    def __extract_content_sync(
        self, file_path: str, file_extension: str
    ) -> str | list[dict[str, Any]]:
        """Synchronous content extraction (runs in thread pool).
        Args:
            file_path: Path to the local file
            file_extension: File extension (including the dot)
        Returns:
            Content extracted from the document (either text or structured data)
        """
        try:
            if file_extension in self.readers:
                return self.readers[file_extension](file_path)
            else:
                msg = (
                    f"Unsupported file extension: {file_extension}"
                    f"Supported extensions: {list(self.readers.keys())}"
                )
                raise ValueError(msg)
        except Exception:
            raise

    @staticmethod
    def _process_output(
        content: str | list[dict[str, Any]],
        file_path: str,
        output_dir: str | None = None,
    ) -> str:
        """Process extracted content and always write a JSON file.

        Args:
            content: Extracted content (text or structured data)
            file_path: Original path to the file
            output_dir: Optional custom output directory
        """
        path = Path(file_path)
        file_name = path.stem

        # Determine output directory
        if output_dir is None:
            output_dir = str(path.parent / Path("processed"))
        else:
            output_dir = str(Path(output_dir))

        # Build the JSON payload with a consistent top-level shape: list of pages
        # output_format only affects how upstream produced each page's "content" (str or object).
        if isinstance(content, list):
            payload_content: list[dict[str, Any]] = content
        else:
            payload_content = [{"page": 1, "type": "Text", "content": content}]

        # Always write JSON with a top-level {"content": ...}
        output_file_name = f"{file_name}.json"
        processed_content = json.dumps(
            {"content": payload_content}, ensure_ascii=False, indent=2
        )

        output_path = Path(output_dir) / output_file_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(processed_content, encoding="utf-8")
        return output_path.as_posix()

    async def aread_document(
        self,
        file_path: str,
        output_dir: str | None = None,
    ) -> str:
        """Async: Main method to read a document and extract its content.

        Args:
            file_path: Path to the file
            output_dir: Optional custom output directory. If not provided,
                       creates 'processed/' subdirectory next to the source file.

        Returns:
            Path to the processed output file
        """
        try:
            # Get file extension to determine which reader to use
            file_extension = Path(file_path).suffix.lower()

            # For PDF/PPTX/DOCX with LLM and JSON output, use batch processing
            if file_extension in (".pdf", ".pptx", ".docx"):
                # Check if we have LLM reader for this file type
                has_llm_reader = (
                    file_extension in (".pdf", ".pptx") and self._pdf_reader
                ) or (file_extension == ".docx" and self._document_reader)
                if has_llm_reader:
                    # Prepare output path
                    path = Path(file_path)
                    file_name = path.stem
                    if output_dir is None:
                        output_dir_path = path.parent / Path("processed")
                    else:
                        output_dir_path = Path(output_dir)
                    output_dir_path.mkdir(parents=True, exist_ok=True)
                    output_file_path = output_dir_path / f"{file_name}.json"

                    # Process with batching directly to file
                    if file_extension == ".pdf":
                        result = await self._aread_pdf(
                            file_path, output_path=str(output_file_path)
                        )
                    elif file_extension == ".pptx":
                        result = await apresentation_read_handler(
                            file_path,
                            pdf_handler=self._aread_pdf,
                            output_path=str(output_file_path),
                        )
                    else:  # .docx
                        # DOCX uses sync handler for now - run in thread
                        result = await asyncio.to_thread(
                            self._read_docx,
                            file_path,
                            output_path=str(output_file_path),
                        )
                    return result if isinstance(result, str) else str(output_file_path)
            else:
                # Standard processing for other files (run in thread)
                content = await asyncio.to_thread(
                    self.__extract_content_sync, file_path, file_extension
                )
                # Process output based on requested format
                output_file_path = await asyncio.to_thread(
                    self._process_output, content, file_path, output_dir
                )
                return output_file_path
        except Exception:
            raise


def main() -> None:
    """CLI entry point for Donkit read engine.

    Usage:
        donkit-read-engine <file_path> [--output-type text|json|markdown]
    """
    parser = argparse.ArgumentParser(
        prog="donkit-read-engine",
        description="Read a document and export extracted content to text/json/markdown",
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        default="/Users/romanlosev/donkit/platform/ragops-agent/shared/read-engine/src/files",
        help="Path to a local file or directory to read (directory will be processed recursively)",
    )
    parser.add_argument(
        "--output-type",
        choices=["text", "json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--pdf-strategy",
        choices=["fast", "hi_res", "ocr_only", "auto"],
        default=None,
        help="unstructured parsing strategy (overrides UNSTRUCTURED_STRATEGY)",
    )
    parser.add_argument(
        "--ocr-lang",
        default=None,
        help="OCR languages for unstructured (e.g., 'rus+eng') (overrides UNSTRUCTURED_OCR_LANG)",
    )

    args = parser.parse_args()

    # Apply optional strategy settings for unstructured before constructing reader
    if args.pdf_strategy:
        os.environ["UNSTRUCTURED_STRATEGY"] = args.pdf_strategy
    if args.ocr_lang:
        os.environ["UNSTRUCTURED_OCR_LANG"] = args.ocr_lang

    reader = DonkitReader()
    input_path = Path(args.file_path)
    if input_path.is_dir():
        exts = set(reader.readers.keys())
        files: list[Path] = [
            f for f in input_path.rglob("*") if f.is_file() and f.suffix.lower() in exts
        ]
        for f in sorted(files):
            try:
                output_path = reader.read_document(f.as_posix(), args.output_type)  # type: ignore[arg-type]
                print(output_path)
            except Exception as e:
                print(f"ERROR processing {f}: {e}")
    else:
        output_path = reader.read_document(input_path.as_posix(), args.output_type)  # type: ignore[arg-type]
        print(output_path)


if __name__ == "__main__":
    main()

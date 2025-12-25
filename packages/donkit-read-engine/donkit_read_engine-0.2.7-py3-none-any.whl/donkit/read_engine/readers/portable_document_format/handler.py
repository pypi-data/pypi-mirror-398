import asyncio
import base64
import errno
import gc
import json
import os
import pathlib
import re
import shutil
import stat
import tempfile
import time
from collections.abc import Callable
from typing import Any

import fitz
from json_repair import repair_json
from loguru import logger
from pydantic import BaseModel

from ..static_visual_format.models import ImageAnalysisService


class PageContent(BaseModel):
    """Represents extracted content from a single PDF page."""

    page_num: int
    content: dict[str, Any] | str
    type: str = "Slide"


class PDFSplitter:
    """Splits PDF into individual pages."""

    @staticmethod
    def split(pdf_path: pathlib.Path, output_dir: pathlib.Path) -> None:
        """Split PDF into individual pages.

        Args:
            pdf_path: Path to PDF file
            output_dir: Directory to save page files
        """
        if output_dir.exists():
            safe_rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        document = fitz.open(pdf_path)
        try:
            for page_num in range(document.page_count):
                output_file = output_dir / f"page_{page_num + 1}.pdf"
                pdf_writer = fitz.open()
                try:
                    pdf_writer.insert_pdf(
                        document, from_page=page_num, to_page=page_num
                    )
                    pdf_writer.save(output_file)
                finally:
                    pdf_writer.close()
        finally:
            document.close()

    @staticmethod
    def get_sorted_pages(directory: pathlib.Path) -> list[str]:
        """Get sorted list of page files."""

        def extract_page_number(filename: str) -> int:
            match = re.search(r"page_(\d+)\.pdf", filename)
            return int(match.group(1)) if match else 0

        return sorted(os.listdir(directory), key=extract_page_number)


class PageProcessor:
    """Processes individual PDF pages."""

    def __init__(self, image_service: ImageAnalysisService):
        """Initialize page processor.

        Args:
            image_service: Image analysis service instance for LLM-based processing
        """
        self.image_service = image_service

    def process(self, page_path: str, page_num: int) -> PageContent:
        """[DEPRECATED] Sync processing is disabled. Use aprocess()."""
        raise NotImplementedError("Sync PDF processing is removed. Use aprocess().")

    async def aprocess(self, page_path: str, page_num: int) -> PageContent:
        """Async: Process a single PDF page.

        Args:
            page_path: Path to page PDF file
            page_num: Page number

        Returns:
            PageContent with extracted data

        Raises:
            RuntimeError: If page processing fails
        """
        try:
            # Convert page to image (quick sync operation - run in thread)
            encoded_image = self._page_to_image(page_path)

            # Analyze with LLM (async)
            raw_data = await self.image_service.aanalyze_image(encoded_image)

            # Parse model output (sync, quick)
            logger.debug(
                f"Parsing page {page_num}: raw_type={type(raw_data).__name__}, sample={(raw_data[:200] if isinstance(raw_data, str) else str(raw_data))[:200]}"
            )
            parsed_content = self._parse_output(raw_data, page_num)
            logger.debug(
                f"Parsed page {page_num}: parsed_type={type(parsed_content).__name__}"
            )

            return PageContent(page_num=page_num, content=parsed_content)
        except Exception as e:
            logger.error("Error processing page {}: {}", page_num, e, exc_info=True)
            raise RuntimeError(f"Failed to process page {page_num}: {e}") from e

    @staticmethod
    def _page_to_image(page_path: str) -> str:
        """Convert PDF page to base64-encoded image."""
        document = fitz.open(page_path)
        try:
            # fitz config.
            # included in function to ensure settings apply when called in thread pool
            fitz.TOOLS.set_aa_level(1)
            dpi = 85  # TODO: Ideally this should hook into a future "per document type" parsing mode. Lower dpi for sparse pages, high dpi for dense
            scale = dpi / 72
            mat = fitz.Matrix(scale, scale)

            page = document[0]
            pix = page.get_pixmap(colorspace=fitz.csGRAY, alpha=False, matrix=mat)
            png_bytes = pix.tobytes("png")

            # Base64 encode directly (no intermediate BytesIO)
            encoded_image = base64.b64encode(png_bytes).decode("ascii")
            return encoded_image
        finally:
            document.close()
            gc.collect()

    @staticmethod
    def _parse_output(raw_data: str | dict, page_num: int) -> dict[str, Any] | str:
        """Parse model output into structured format."""
        if isinstance(raw_data, dict):
            return raw_data

        if not isinstance(raw_data, str):
            logger.warning(
                f"Unexpected data type for page {page_num}: {type(raw_data)}"
            )
            raise ValueError("Unexpected data type from model")

        text = raw_data.strip()

        # Remove markdown fences
        if text.startswith("```json"):
            text = text[len("```json") :].strip()
        if text.startswith("```"):
            text = text[len("```") :].strip()
        if text.endswith("```"):
            text = text[:-3].strip()

        if not text:
            logger.warning(f"Empty content for page {page_num}")
            return ""

        # If output is not JSON-like (e.g., plain text or markdown), return as text
        if not (text.startswith("{") or text.startswith("[")):
            return text

        # JSON-like: attempt to repair and parse
        try:
            parsed = json.loads(repair_json(text))
            return parsed if isinstance(parsed, dict) else text
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed for page {page_num}: {e}")
            return text


class LlmPDFReader:
    """Main PDF reader with LLM-based image analysis."""

    def __init__(
        self,
        image_service: ImageAnalysisService,
        progress_interval: int = 1,
        progress_callback: Callable[[int, int, str | None], None] | None = None,
    ):
        """Initialize PDF reader.

        Args:
            image_service: Image analysis service instance (required for LLM-based processing)
            progress_interval: Log progress every N pages
            progress_callback: Optional callback for progress reporting.
                               Signature: (current: int, total: int, message: str | None) -> None
        """
        self.image_service = image_service
        self.progress_interval = progress_interval
        self.progress_callback = progress_callback
        self._splitter = PDFSplitter

    async def aread(
        self, pdf_path: str, output_path: str | None = None
    ) -> list[dict[str, Any]] | str:
        """Async: Read and process PDF file.

        Args:
            pdf_path: Path to PDF file
            output_path: Optional path to write results incrementally. If provided,
                        results are written in batches and path is returned.

        Returns:
            List of page dictionaries if output_path is None, otherwise path to output file

        Raises:
            RuntimeError: If processing fails
        """
        # Setup
        pdf_name = pathlib.Path(pdf_path).stem
        tmp_dir = self._create_temp_dir(pdf_name)

        try:
            # Split PDF (sync, fast operation - run in thread)
            await asyncio.to_thread(
                self._splitter.split, pathlib.Path(pdf_path), tmp_dir
            )
            page_files = self._splitter.get_sorted_pages(tmp_dir)
            # Process pages
            processor = PageProcessor(self.image_service)

            if output_path:
                # Process in batches and write to file
                await self._aprocess_all_pages_to_file(
                    tmp_dir, page_files, processor, output_path
                )
                return output_path
            else:
                # Process all pages in memory (legacy behavior)
                results = await self._aprocess_all_pages(tmp_dir, page_files, processor)
                return results

        except Exception as e:
            logger.error("Error processing PDF: {}", e, exc_info=True)
            raise

        finally:
            if tmp_dir.exists():
                safe_rmtree(tmp_dir)

    @staticmethod
    def _create_temp_dir(pdf_name: str) -> pathlib.Path:
        """Create temporary directory."""
        tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix=f"donkit_pdf_{pdf_name}_"))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        return tmp_dir

    def _process_all_pages(
        self, tmp_dir: pathlib.Path, page_files: list[str], processor: PageProcessor
    ) -> list[dict[str, Any]]:
        """[DEPRECATED] Sync processing is disabled. Use _aprocess_all_pages()."""
        raise NotImplementedError(
            "Sync PDF processing is removed. Use _aprocess_all_pages()."
        )

    async def _aprocess_all_pages(
        self, tmp_dir: pathlib.Path, page_files: list[str], processor: PageProcessor
    ) -> list[dict[str, Any]]:
        """Async: Process all pages in parallel using asyncio."""
        start_time = time.time()
        semaphore = asyncio.Semaphore(20)  # Limit concurrent LLM calls
        results = []
        lock = asyncio.Lock()

        async def process_one_page(page_num: int, page_file: str):
            """Process single page with semaphore."""
            async with semaphore:
                try:
                    page_path = tmp_dir / page_file
                    page_content = await processor.aprocess(str(page_path), page_num)

                    async with lock:
                        results.append(
                            {
                                "page": page_content.page_num,
                                "type": page_content.type,
                                "content": page_content.content,
                            }
                        )

                        # Progress logging and reporting
                        processed = len(results)
                        if processed % self.progress_interval == 0 or processed in [
                            1,
                            5,
                            15,
                            25,
                        ]:
                            elapsed = time.time() - start_time
                            avg_time = elapsed / processed
                            remaining = len(page_files) - processed
                            est_remaining = remaining * avg_time
                            msg = (
                                f"{processed}/{len(page_files)} pages "
                                f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                            )
                            # Report progress via callback if provided
                            if self.progress_callback:
                                self.progress_callback(processed, len(page_files), msg)

                        # Garbage collection
                        if processed % 5 == 0:
                            gc.collect()

                except Exception as e:
                    logger.error(f"Error processing page {page_num}: {e}")
                    async with lock:
                        results.append(
                            {
                                "page": page_num,
                                "type": "Error",
                                "content": f"Error processing page: {str(e)}",
                            }
                        )

        # Create tasks for all pages
        tasks = [
            process_one_page(page_num, page_file)
            for page_num, page_file in enumerate(page_files, start=1)
        ]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Sort results by page number
        results.sort(key=lambda x: x.get("page", 0))

        return results

    async def _aprocess_all_pages_to_file(
        self,
        tmp_dir: pathlib.Path,
        page_files: list[str],
        processor: PageProcessor,
        output_path: str,
        batch_size: int = 20,
        concurrency: int = 10,
    ) -> None:
        """Async: Process all pages in batches and write to file incrementally.

        Optimizations:
        - single file handle for streaming JSON array
        - single semaphore across all batches (bounded concurrency)
        - construct result dicts directly (avoid pydantic model_dump overhead)
        - reduced GC pressure and fewer syscalls
        """
        start_time = time.time()
        output_file = pathlib.Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Global semaphore to bound overall concurrency
        semaphore = asyncio.Semaphore(max(1, concurrency))

        # Start fresh and keep the file open for the whole operation
        f = open(output_file, "w", encoding="utf-8")
        try:
            f.write('{"content": [\n')

            total_processed = 0

            async def process_one_page(page_num: int, page_file: str) -> dict[str, Any]:
                """Process single page with semaphore and return final result dict."""
                async with semaphore:
                    page_path = tmp_dir / page_file
                    page_content = await processor.aprocess(str(page_path), page_num)
                    # Build final dict to avoid later conversions and conditionals
                    return {
                        "page": page_content.page_num,
                        "type": page_content.type,
                        "content": page_content.content,
                    }

            # Process in batches to control memory footprint of scheduled tasks
            for batch_start in range(0, len(page_files), batch_size):
                batch_end = min(batch_start + batch_size, len(page_files))
                batch_files = page_files[batch_start:batch_end]
                if not batch_files:
                    continue

                tasks: list[asyncio.Task[dict[str, Any]]] = [
                    asyncio.create_task(
                        process_one_page(batch_start + idx + 1, page_file)
                    )
                    for idx, page_file in enumerate(batch_files)
                ]

                batch_results: list[dict[str, Any]] = []
                first_exc: Exception | None = None
                for task in asyncio.as_completed(tasks):
                    try:
                        res = await task
                        batch_results.append(res)
                    except Exception as exc:
                        if first_exc is None:
                            first_exc = exc

                # Preserve order by page number
                batch_results.sort(key=lambda x: int(x.get("page", 0)))

                # Stream results to the file: serialize batch and write once
                serialized_batch = [
                    json.dumps(result, ensure_ascii=False, indent=2)
                    for result in batch_results
                ]
                if serialized_batch:
                    if total_processed > 0:
                        f.write(",\n")
                    logger.debug(
                        f"Writing batch pages {[r['page'] for r in batch_results]} to file"
                    )
                    # Items within the batch must be comma-separated for valid JSON
                    f.write(",\n".join(serialized_batch))

                # Progress updates (still per item to keep same UX)
                for _ in batch_results:
                    total_processed += 1
                    if (
                        total_processed % self.progress_interval == 0
                        or total_processed in [1, 5, 15, 25]
                    ):
                        elapsed = time.time() - start_time
                        avg_time = elapsed / max(total_processed, 1)
                        remaining = len(page_files) - total_processed
                        est_remaining = max(remaining * avg_time, 0)
                        msg = (
                            f"{total_processed}/{len(page_files)} pages "
                            f"({elapsed:.1f}s elapsed, ~{est_remaining:.1f}s remaining)"
                        )
                        if self.progress_callback:
                            self.progress_callback(
                                total_processed, len(page_files), msg
                            )

                if first_exc is not None:
                    raise first_exc

                # Occasional GC to release native resources from PDF/image ops
                if total_processed % 20 == 0:
                    gc.collect()
        finally:
            # Ensure JSON structure is closed even on exceptions
            try:
                f.write("\n]}")
            except Exception as e:
                logger.warning(f"Failed to finalize JSON output: {e}")
            finally:
                try:
                    f.close()
                except Exception:
                    pass


def safe_rmtree(path: pathlib.Path) -> None:
    """Safely remove directory tree with Windows-compatible error handling.

    On Windows, files might still be locked by the system. This function
    handles permission errors by trying to change file permissions before removal.

    Args:
        path: Path to directory to remove
    """
    import gc
    import platform

    # On Windows, force garbage collection and add small delay to release file handles
    if platform.system() == "Windows":
        gc.collect()
        time.sleep(0.1)  # 100ms delay for Windows to release file handles

    def handle_remove_error(func, filepath, exc_info):
        """Handle errors during directory removal on Windows."""
        # If permission error, try to change permissions and retry
        if exc_info[1].errno == errno.EACCES:
            try:
                os.chmod(filepath, stat.S_IWRITE)
                time.sleep(0.05)  # Small delay before retry
                func(filepath)
            except Exception as e:
                logger.warning(f"Could not remove {filepath}: {e}")
        else:
            logger.warning(f"Could not remove {filepath}: {exc_info[1]}")

    try:
        shutil.rmtree(path, onerror=handle_remove_error)
    except Exception as e:
        logger.warning(f"Failed to cleanup directory {path}: {e}")

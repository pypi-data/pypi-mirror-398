import glob
import os
import pathlib
import shutil
import subprocess
import sys
import asyncio
from typing import Callable, Awaitable

from dotenv import find_dotenv, load_dotenv
from loguru import logger


# Load .env file with explicit search (important for Windows)
load_dotenv(find_dotenv(usecwd=True), override=False)


logger.remove()
log_level = os.getenv("RAGOPS_LOG_LEVEL", os.getenv("LOG_LEVEL", "ERROR"))
logger.add(
    sys.stderr,
    level=log_level,
    enqueue=False,
    backtrace=False,
    diagnose=False,
)


def convert_pptx_to_pdf(pptx_path: str, tmp_dir: str) -> str:
    """Converts PPTX to PDF using LibreOffice."""
    try:
        command = (
            f'soffice --headless --convert-to pdf --outdir "{tmp_dir}" "{pptx_path}"'
        )
        logger.debug(f"Processing command: {command}")
    except Exception as e:
        logger.error(f"Error converting PPTX into PDF: {e}")
        raise Exception(f"To process PPTX you need to install LibreOffice: {e}")

    subprocess.call(command, shell=True)
    pdf_files = glob.glob(f"{tmp_dir}/*.pdf")
    if not pdf_files:
        raise FileNotFoundError(f"Files not found in : {tmp_dir}")

    output_pdf_path = pdf_files[0]
    logger.debug(f"PDF file created: {output_pdf_path}")

    return output_pdf_path


def presentation_read_handler(
    pptx_path: str, pdf_handler: Callable, output_path: str | None = None
) -> list[dict[str, str | int]] | str:
    """Extracts text and image placeholders from a PPTX file using OCR model after converting it to PDF.

    :param pptx_path: Path to the PPTX file to process.
    :param pdf_handler: Callable to handle PDF processing.
    :param output_path: Optional output path for batch processing.
    :return: List of dicts if output_path is None, otherwise output_path string.
    """
    # Create a temporary directory for PDF conversion and extraction
    tmp_dir = pathlib.Path(__file__).parent.joinpath("tmp")

    # Remove existing temp directory and recreate it
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # Define path for the temporary PDF file
    # output_pdf_path = f"{tmp_dir}/{pathlib.Path(pptx_path).name}.pdf"

    # Convert PPTX to PDF
    output_pdf_path = convert_pptx_to_pdf(pptx_path, str(tmp_dir))

    # Use the PDF handler to extract text and images from the converted PDF
    # Pass output_path if provided for batch processing
    if output_path:
        return pdf_handler(path=output_pdf_path, output_path=output_path)
    else:
        return pdf_handler(path=output_pdf_path)


async def apresentation_read_handler(
    pptx_path: str,
    pdf_handler: Callable[..., Awaitable[list[dict[str, str | int]] | str]],
    output_path: str | None = None,
) -> list[dict[str, str | int]] | str:
    """Async version: converts PPTX to PDF and awaits async pdf_handler.

    Args:
        pptx_path: Path to the PPTX file to process.
        pdf_handler: Async callable to handle PDF processing.
        output_path: Optional output path for batch processing.
    Returns:
        List of dicts if output_path is None, otherwise output_path string.
    """
    # Create temp dir
    tmp_dir = pathlib.Path(__file__).parent.joinpath("tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # Convert PPTX to PDF asynchronously
    command = f'soffice --headless --convert-to pdf --outdir "{tmp_dir}" "{pptx_path}"'
    logger.debug(f"Processing command: {command}")
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    rc = await proc.wait()
    if rc != 0:
        raise Exception(
            "To process PPTX you need to install LibreOffice or conversion failed"
        )

    pdf_files = glob.glob(f"{tmp_dir}/*.pdf")
    if not pdf_files:
        raise FileNotFoundError(f"Files not found in : {tmp_dir}")
    output_pdf_path = pdf_files[0]
    logger.debug(f"PDF file created: {output_pdf_path}")

    # Delegate to async pdf handler
    if output_path:
        return await pdf_handler(path=output_pdf_path, output_path=output_path)
    else:
        return await pdf_handler(path=output_pdf_path)

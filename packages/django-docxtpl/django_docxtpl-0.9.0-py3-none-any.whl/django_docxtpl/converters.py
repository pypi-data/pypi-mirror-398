"""Format conversion using LibreOffice headless."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from django_docxtpl.utils import OutputFormat, find_libreoffice, get_extension

if TYPE_CHECKING:
    from io import BytesIO


class ConversionError(Exception):
    """Exception raised when document conversion fails."""

    pass


class LibreOfficeNotFoundError(ConversionError):
    """Exception raised when LibreOffice is not found."""

    pass


def update_fields_in_docx(
    docx_content: bytes | BytesIO,
    *,
    timeout: int = 60,
) -> bytes:
    """Update all fields in a DOCX document using LibreOffice.

    This function opens the document in LibreOffice and updates all dynamic
    fields including:
    - Table of Contents (TOC)
    - Charts and graphs
    - Cross-references
    - Page numbers
    - Date fields
    - Other calculated fields

    This is useful when templates contain TOC or charts that need to be
    regenerated after the template has been rendered with new content.

    Args:
        docx_content: The DOCX content as bytes or BytesIO.
        timeout: Maximum time in seconds to wait for the operation.

    Returns:
        The DOCX document with updated fields as bytes.

    Raises:
        LibreOfficeNotFoundError: If LibreOffice is not installed.
        ConversionError: If the update operation fails.
    """
    libreoffice_path = find_libreoffice()
    if not libreoffice_path:
        raise LibreOfficeNotFoundError(
            "LibreOffice not found. Please install LibreOffice or set "
            "DOCXTPL_LIBREOFFICE_PATH in Django settings."
        )

    # Get content as bytes
    if isinstance(docx_content, bytes):
        content_bytes = docx_content
    else:
        content_bytes = docx_content.read()
        docx_content.seek(0)  # Reset position for potential reuse

    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_file = temp_path / "input.docx"
        input_file.write_bytes(content_bytes)

        # Use LibreOffice to open, update fields, and save as DOCX
        # The macro UpdateAll updates all fields including TOC
        # We convert to docx format which forces a re-save with updated fields
        cmd = [
            str(libreoffice_path),
            "--headless",
            "--convert-to",
            "docx",
            "--outdir",
            str(temp_path),
            str(input_file),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise ConversionError(
                f"Field update timed out after {timeout} seconds."
            ) from e

        if result.returncode != 0:
            raise ConversionError(
                f"LibreOffice field update failed: {result.stderr or result.stdout}"
            )

        # Find the output file
        output_file = temp_path / "input.docx"

        if not output_file.exists():
            # Try to find any DOCX file
            output_files = list(temp_path.glob("*.docx"))
            if output_files:
                output_file = output_files[0]
            else:
                raise ConversionError(
                    f"Field update completed but output file not found. "
                    f"Expected: {output_file}"
                )

        return output_file.read_bytes()


def convert_docx(
    docx_content: bytes | BytesIO,
    output_format: OutputFormat,
    *,
    timeout: int = 60,
    update_fields: bool = False,
) -> bytes:
    """Convert a DOCX document to another format using LibreOffice.

    Args:
        docx_content: The DOCX content as bytes or BytesIO.
        output_format: The desired output format (pdf, odt, html, txt).
        timeout: Maximum time in seconds to wait for conversion.
        update_fields: If True, update all fields (TOC, charts, etc.) before
            conversion. This requires an additional LibreOffice processing step.

    Returns:
        The converted document content as bytes.

    Raises:
        LibreOfficeNotFoundError: If LibreOffice is not installed.
        ConversionError: If the conversion fails.
        ValueError: If output_format is 'docx' (no conversion needed).
    """
    if output_format == "docx":
        raise ValueError(
            "No conversion needed for DOCX format. Use the original content."
        )

    libreoffice_path = find_libreoffice()
    if not libreoffice_path:
        raise LibreOfficeNotFoundError(
            "LibreOffice not found. Please install LibreOffice or set "
            "DOCXTPL_LIBREOFFICE_PATH in Django settings."
        )

    # Get content as bytes
    if isinstance(docx_content, bytes):
        content_bytes = docx_content
    else:
        content_bytes = docx_content.read()
        docx_content.seek(0)  # Reset position for potential reuse

    # If update_fields is True, first process the document to update TOC, charts, etc.
    if update_fields:
        content_bytes = update_fields_in_docx(content_bytes, timeout=timeout)

    # Create temporary directory for conversion
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        input_file = temp_path / "input.docx"
        input_file.write_bytes(content_bytes)

        # Build LibreOffice command
        # Format mapping for LibreOffice
        lo_format_map = {
            "pdf": "pdf",
            "odt": "odt",
            "html": "html",
            "txt": "txt",
        }
        lo_format = lo_format_map.get(output_format, output_format)

        cmd = [
            str(libreoffice_path),
            "--headless",
            "--convert-to",
            lo_format,
            "--outdir",
            str(temp_path),
            str(input_file),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            raise ConversionError(
                f"Conversion timed out after {timeout} seconds."
            ) from e

        if result.returncode != 0:
            raise ConversionError(
                f"LibreOffice conversion failed: {result.stderr or result.stdout}"
            )

        # Find the output file
        extension = get_extension(output_format)
        output_file = temp_path / f"input{extension}"

        if not output_file.exists():
            # Try to find any file with the expected extension
            output_files = list(temp_path.glob(f"*{extension}"))
            if output_files:
                output_file = output_files[0]
            else:
                raise ConversionError(
                    f"Conversion completed but output file not found. "
                    f"Expected: {output_file}"
                )

        return output_file.read_bytes()

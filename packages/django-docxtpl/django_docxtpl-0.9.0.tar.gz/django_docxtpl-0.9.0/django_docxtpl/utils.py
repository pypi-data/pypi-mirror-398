"""Utility functions for django-docxtpl."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from django.conf import settings

if TYPE_CHECKING:
    from docxtpl import DocxTemplate  # type: ignore[import-untyped]

# Supported output formats
OutputFormat = Literal["docx", "pdf", "odt", "html", "txt"]

# MIME types for each format
CONTENT_TYPES: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
    "odt": "application/vnd.oasis.opendocument.text",
    "html": "text/html",
    "txt": "text/plain",
}

# File extensions for each format
EXTENSIONS: dict[str, str] = {
    "docx": ".docx",
    "pdf": ".pdf",
    "odt": ".odt",
    "html": ".html",
    "txt": ".txt",
}

# Default paths to search for LibreOffice
LIBREOFFICE_PATHS = [
    # macOS
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    # Linux
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/usr/local/bin/soffice",
    # Windows (common paths)
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def get_content_type(output_format: OutputFormat) -> str:
    """Get the MIME content type for a given output format.

    Args:
        output_format: The output format (docx, pdf, odt, html, txt).

    Returns:
        The MIME content type string.

    Raises:
        ValueError: If the format is not supported.
    """
    if output_format not in CONTENT_TYPES:
        raise ValueError(
            f"Unsupported format: {output_format}. "
            f"Supported formats: {', '.join(CONTENT_TYPES.keys())}"
        )
    return CONTENT_TYPES[output_format]


def get_extension(output_format: OutputFormat) -> str:
    """Get the file extension for a given output format.

    Args:
        output_format: The output format (docx, pdf, odt, html, txt).

    Returns:
        The file extension including the dot (e.g., '.pdf').

    Raises:
        ValueError: If the format is not supported.
    """
    if output_format not in EXTENSIONS:
        raise ValueError(
            f"Unsupported format: {output_format}. "
            f"Supported formats: {', '.join(EXTENSIONS.keys())}"
        )
    return EXTENSIONS[output_format]


def get_filename_with_extension(filename: str, output_format: OutputFormat) -> str:
    """Add the correct extension to a filename based on the output format.

    If the filename already has the correct extension, it's returned as-is.
    If it has a different extension, the correct one is appended.

    Args:
        filename: The base filename (with or without extension).
        output_format: The desired output format.

    Returns:
        The filename with the correct extension.
    """
    extension = get_extension(output_format)
    if filename.lower().endswith(extension):
        return filename
    # Remove any existing extension from supported formats
    for ext in EXTENSIONS.values():
        if filename.lower().endswith(ext):
            filename = filename[: -len(ext)]
            break
    return f"{filename}{extension}"


def find_libreoffice() -> Path | None:
    """Find the LibreOffice executable.

    Searches in the following order:
    1. Django setting DOCXTPL_LIBREOFFICE_PATH
    2. System PATH (using shutil.which)
    3. Common installation locations

    Returns:
        Path to the LibreOffice executable, or None if not found.
    """
    # Check Django settings first
    custom_path = getattr(settings, "DOCXTPL_LIBREOFFICE_PATH", None)
    if custom_path:
        path = Path(custom_path)
        if path.exists() and path.is_file():
            return path

    # Check system PATH
    for cmd in ["soffice", "libreoffice"]:
        found = shutil.which(cmd)
        if found:
            return Path(found)

    # Check common installation paths
    for path_str in LIBREOFFICE_PATHS:
        path = Path(path_str)
        if path.exists() and path.is_file():
            return path

    return None


def get_template_dir() -> Path | None:
    """Get the configured template directory for DOCX templates.

    Returns:
        Path to the template directory, or None if not configured.
    """
    template_dir = getattr(settings, "DOCXTPL_TEMPLATE_DIR", None)
    if template_dir:
        return Path(template_dir)
    return None


# Type alias for context: dict or callable(DocxTemplate, tmp_dir) -> dict
ContextType = dict[str, Any] | Callable[["DocxTemplate", Path], dict[str, Any]]


def render_to_file(
    template: str | Path,
    context: ContextType,
    output_dir: str | Path,
    filename: str,
    output_format: OutputFormat = "docx",
    *,
    update_fields: bool = False,
    jinja_env: Any | None = None,
    autoescape: bool = False,
) -> Path:
    """Render a DOCX template and save to a file.

    This is useful for background tasks (Celery, Huey, RQ) where you need
    to generate a document and save it to disk without an HTTP response.

    Args:
        template: Path to the DOCX template file (absolute or relative to
                 DOCXTPL_TEMPLATE_DIR).
        context: Dictionary of context variables for template rendering, or
                a callable that receives the DocxTemplate instance and a Path
                to a temporary directory, and returns a context dictionary.
                Use a callable when you need to create objects that require
                the template instance (e.g., InlineImage) or temporary files.
        output_dir: Directory where the output file will be saved.
        filename: Output filename without extension.
        output_format: Desired output format (docx, pdf, odt, html, txt).
        update_fields: If True, update TOC, charts, and other dynamic fields.
        jinja_env: Optional Jinja2 Environment instance with custom filters,
                  globals, or other configuration. If not provided, docxtpl
                  will create a default Environment.
        autoescape: If True, enable Jinja2 autoescaping when rendering the
                   template. This escapes HTML/XML special characters in
                   context values. Default is False.

    Returns:
        Absolute path to the generated file.

    Raises:
        FileNotFoundError: If the template file doesn't exist.
        LibreOfficeNotFoundError: If LibreOffice is needed but not found.
        ConversionError: If the conversion fails.

    Example:
        from django_docxtpl.utils import render_to_file

        # Simple context dict
        output_path = render_to_file(
            template="reports/monthly.docx",
            context={"month": "December", "data": report_data},
            output_dir="/tmp/reports",
            filename="monthly_report",
            output_format="pdf",
            update_fields=True,
        )

        # Context with InlineImage (using callable)
        from docxtpl import InlineImage
        from docx.shared import Mm

        def build_context(docx, tmp_dir):
            return {
                "title": "Report",
                "chart": InlineImage(docx, "chart.png", width=Mm(150)),
            }

        output_path = render_to_file(
            template="reports/monthly.docx",
            context=build_context,
            output_dir="/tmp/reports",
            filename="monthly_report",
            output_format="pdf",
        )

        # Using custom Jinja2 filters
        from jinja2 import Environment

        def format_milers(value):
            return f"{value:,.0f}".replace(",", ".")

        jinja_env = Environment(autoescape=True)
        jinja_env.filters['milers'] = format_milers

        output_path = render_to_file(
            template="reports/monthly.docx",
            context={"value": 1234567},
            output_dir="/tmp/reports",
            filename="monthly_report",
            output_format="pdf",
            jinja_env=jinja_env,
        )
    """
    from io import BytesIO  # pylint: disable=import-outside-toplevel

    from docxtpl import DocxTemplate  # pylint: disable=import-outside-toplevel

    from django_docxtpl.converters import (  # pylint: disable=import-outside-toplevel
        convert_docx,
        update_fields_in_docx,
    )

    # Resolve template path
    template_path = Path(template)
    if not template_path.is_absolute():
        template_dir = get_template_dir()
        if template_dir:
            full_path = template_dir / template_path
            if full_path.exists():
                template_path = full_path
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template}")

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    import tempfile  # pylint: disable=import-outside-toplevel

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir_path = Path(tmp_dir)

        # Load the template
        doc = DocxTemplate(template_path)

        # Resolve context: if callable, call it with doc and tmp_dir
        if callable(context):
            resolved_context = context(doc, tmp_dir_path)
        else:
            resolved_context = context

        # Render the template with optional custom jinja_env and autoescape
        doc.render(resolved_context, jinja_env=jinja_env, autoescape=autoescape)

        # Save to BytesIO
        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)

    # Process the document
    if output_format == "docx":
        if update_fields:
            content = update_fields_in_docx(docx_buffer)
        else:
            content = docx_buffer.getvalue()
    else:
        content = convert_docx(docx_buffer, output_format, update_fields=update_fields)

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build full filename with extension
    full_filename = get_filename_with_extension(filename, output_format)
    file_path = output_path / full_filename

    # Write to file
    file_path.write_bytes(content)

    return file_path.resolve()

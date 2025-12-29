"""HttpResponse specialized for document generation."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

from django.http import HttpResponse
from docxtpl import DocxTemplate  # type: ignore[import-untyped]
from jinja2 import Environment

from django_docxtpl.converters import convert_docx, update_fields_in_docx
from django_docxtpl.utils import (
    OutputFormat,
    get_content_type,
    get_filename_with_extension,
    get_template_dir,
)

# Type alias for context: can be a dict or a callable that receives DocxTemplate
ContextType = dict[str, Any] | Callable[[DocxTemplate], dict[str, Any]]


class DocxTemplateResponse(HttpResponse):
    """HTTP response that renders a DOCX template and serves it as a document.

    This response class handles:
    - Loading DOCX templates from file paths or template directory
    - Rendering templates with Jinja2 context
    - Converting to different formats (PDF, ODT, etc.) via LibreOffice
    - Setting appropriate headers for file download

    Example:
        def my_view(request):
            return DocxTemplateResponse(
                request,
                template="invoice.docx",
                context={"customer": "John Doe", "total": 100},
                filename="invoice",
                output_format="pdf",
            )
    """

    def __init__(
        self,
        request: Any,
        template: str | Path,
        context: ContextType | None = None,
        filename: str = "document",
        output_format: OutputFormat = "docx",
        as_attachment: bool = True,
        update_fields: bool = False,
        jinja_env: Environment | None = None,
        autoescape: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the DocxTemplateResponse.

        Args:
            request: The HTTP request object.
            template: Path to the DOCX template file. Can be absolute or relative
                     to DOCXTPL_TEMPLATE_DIR setting.
            context: Dictionary of context variables for template rendering, or
                    a callable that receives the DocxTemplate instance and returns
                    a context dictionary. Use a callable when you need to create
                    objects that require the template instance (e.g., InlineImage).
            filename: Output filename without extension (extension added automatically).
            output_format: Desired output format (docx, pdf, odt, html, txt).
            as_attachment: If True, sets Content-Disposition to attachment.
            update_fields: If True, update all fields (TOC, charts, cross-references,
                          etc.) using LibreOffice before final output. Requires
                          LibreOffice even for DOCX output format.
            jinja_env: Custom Jinja2 Environment instance with filters, globals, etc.
                      Use this to add custom filters or configure Jinja2 behavior.
            autoescape: If True, enable Jinja2 autoescaping when rendering the
                       template. This escapes HTML/XML special characters in
                       context values. Default is False.
            **kwargs: Additional arguments passed to HttpResponse.
        """
        # Generate the document content
        content = self._render_document(
            template, context or {}, output_format, update_fields, jinja_env, autoescape
        )

        # Set content type
        content_type = get_content_type(output_format)

        # Initialize HttpResponse
        super().__init__(content=content, content_type=content_type, **kwargs)

        # Set filename with correct extension
        full_filename = get_filename_with_extension(filename, output_format)

        # Set Content-Disposition header
        disposition = "attachment" if as_attachment else "inline"
        self["Content-Disposition"] = f'{disposition}; filename="{full_filename}"'

    def _resolve_template_path(self, template: str | Path) -> Path:
        """Resolve the template path to an absolute path.

        Args:
            template: The template path (absolute or relative).

        Returns:
            Absolute path to the template file.

        Raises:
            FileNotFoundError: If the template file doesn't exist.
        """
        template_path = Path(template)

        # If absolute path, use it directly
        if template_path.is_absolute():
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
            return template_path

        # Try relative to template directory
        template_dir = get_template_dir()
        if template_dir:
            full_path = template_dir / template_path
            if full_path.exists():
                return full_path

        # Try as relative path from current directory
        if template_path.exists():
            return template_path.resolve()

        raise FileNotFoundError(
            f"Template not found: {template}. "
            f"Searched in: {template_dir or 'current directory'}"
        )

    def _render_document(
        self,
        template: str | Path,
        context: ContextType,
        output_format: OutputFormat,
        update_fields: bool = False,
        jinja_env: Environment | None = None,
        autoescape: bool = False,
    ) -> bytes:
        """Render the DOCX template and optionally convert to another format.

        Args:
            template: Path to the template file.
            context: Context dictionary for rendering, or a callable that
                    receives the DocxTemplate instance and returns a dict.
            output_format: Desired output format.
            update_fields: If True, update all fields (TOC, charts, etc.)
                          using LibreOffice.
            jinja_env: Custom Jinja2 Environment for template rendering.
            autoescape: If True, enable Jinja2 autoescaping when rendering.

        Returns:
            The rendered document as bytes.
        """
        template_path = self._resolve_template_path(template)

        # Load the template
        doc = DocxTemplate(template_path)

        # Resolve context: if callable, call it with the doc instance
        if callable(context):
            resolved_context = context(doc)
        else:
            resolved_context = context

        # Render the template with optional custom jinja_env and autoescape
        doc.render(resolved_context, jinja_env=jinja_env, autoescape=autoescape)

        # Save to BytesIO
        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)

        # If output format is DOCX and no field update needed, return directly
        if output_format == "docx" and not update_fields:
            return docx_buffer.getvalue()

        # If output format is DOCX but update_fields is True, process with LibreOffice
        if output_format == "docx" and update_fields:
            return update_fields_in_docx(docx_buffer)

        # Convert to requested format (with optional field update)
        return convert_docx(docx_buffer, output_format, update_fields=update_fields)

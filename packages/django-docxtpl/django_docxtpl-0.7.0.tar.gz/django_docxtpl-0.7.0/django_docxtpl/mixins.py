"""Mixins for Class-Based Views."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from django.http import HttpRequest, HttpResponse

from django_docxtpl.response import DocxTemplateResponse
from django_docxtpl.utils import OutputFormat

if TYPE_CHECKING:
    from docxtpl import DocxTemplate  # type: ignore[import-untyped]
    from jinja2 import Environment


class DocxTemplateResponseMixin:
    """Mixin for views that render DOCX templates.

    This mixin provides functionality to render DOCX templates and serve them
    as documents in various formats (DOCX, PDF, ODT, etc.).

    Attributes:
        template_name: Path to the DOCX template file.
        filename: Output filename without extension.
        output_format: Desired output format (docx, pdf, odt, html, txt).
        as_attachment: Whether to serve as attachment or inline.
        update_fields: Whether to update TOC, charts, and other fields.
        autoescape: Whether to enable Jinja2 autoescaping when rendering.

    Example:
        class InvoiceView(DocxTemplateResponseMixin, View):
            template_name = "invoices/template.docx"
            filename = "invoice"
            output_format = "pdf"

            def get_context_data(self):
                return {
                    "customer": "John Doe",
                    "items": [...],
                    "total": 100,
                }

            def get(self, request):
                return self.render_to_response()
    """

    template_name: str | Path | None = None
    filename: str = "document"
    output_format: OutputFormat = "docx"
    as_attachment: bool = True
    update_fields: bool = False
    autoescape: bool = False
    jinja_env: Environment | None = None
    request: HttpRequest  # Type hint for the request attribute from View

    def get_template_name(self) -> str | Path:
        """Return the template name to use for rendering.

        Override this method to dynamically determine the template.

        Returns:
            Path to the template file.

        Raises:
            ValueError: If template_name is not set.
        """
        if self.template_name is None:
            raise ValueError(
                f"{self.__class__.__name__} requires either a definition of "
                "'template_name' or an implementation of 'get_template_name()'"
            )
        return self.template_name

    def get_filename(self) -> str:
        """Return the filename for the generated document.

        Override this method to dynamically determine the filename.

        Returns:
            The filename without extension.
        """
        return self.filename

    def get_output_format(self) -> OutputFormat:
        """Return the output format for the document.

        Override this method to dynamically determine the format.

        Returns:
            The output format string.
        """
        return self.output_format

    def get_update_fields(self) -> bool:
        """Return whether to update fields (TOC, charts, etc.) in the document.

        Override this method to dynamically determine if fields should be updated.
        When True, LibreOffice will process the document to update:
        - Table of Contents (TOC)
        - Charts and graphs
        - Cross-references
        - Page numbers
        - Other calculated fields

        Note: This requires LibreOffice even for DOCX output format.

        Returns:
            True if fields should be updated, False otherwise.
        """
        return self.update_fields

    def get_jinja_env(self) -> Environment | None:
        """Return the Jinja2 Environment for template rendering.

        Override this method to dynamically provide a custom Jinja2 Environment
        with custom filters, globals, or other configurations.

        Returns:
            Jinja2 Environment instance or None to use the default.
        """
        return self.jinja_env

    def get_autoescape(self) -> bool:
        """Return whether to enable Jinja2 autoescaping when rendering.

        When True, HTML/XML special characters in context values will be
        automatically escaped. This is useful for preventing XSS when
        context values might contain user input.

        Override this method to dynamically determine if autoescaping
        should be enabled.

        Returns:
            True if autoescaping should be enabled, False otherwise.
        """
        return self.autoescape

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return the context dictionary for template rendering.

        Override this method to provide context variables when you don't need
        access to the DocxTemplate instance.

        Args:
            **kwargs: Additional context variables.

        Returns:
            Dictionary of context variables.
        """
        return kwargs

    def get_context_data_with_docx(
        self, docx: DocxTemplate, **kwargs: Any
    ) -> dict[str, Any] | None:
        """Return the context dictionary with access to the DocxTemplate instance.

        Override this method when you need to create objects that require the
        DocxTemplate instance, such as InlineImage, RichText, or Subdoc.

        If this method returns a non-None value, it takes precedence over
        get_context_data().

        Args:
            docx: The DocxTemplate instance being rendered.
            **kwargs: Additional context variables (typically URL kwargs).

        Returns:
            Dictionary of context variables, or None to fall back to
            get_context_data().

        Example:
            from docxtpl import InlineImage
            from docx.shared import Mm

            class MyDocumentView(DocxTemplateView):
                template_name = "document.docx"

                def get_context_data_with_docx(self, docx, **kwargs):
                    return {
                        "name": self.request.user.get_full_name(),
                        "logo": InlineImage(
                            docx,
                            image_descriptor="path/to/logo.png",
                            width=Mm(50)
                        ),
                    }
        """
        return None

    def _build_context_callable(
        self, **kwargs: Any
    ) -> Callable[[DocxTemplate], dict[str, Any]]:
        """Build a context callable that tries get_context_data_with_docx first.

        Returns:
            A callable that receives DocxTemplate and returns the context dict.
        """

        def context_builder(docx: DocxTemplate) -> dict[str, Any]:
            # Try get_context_data_with_docx first
            context = self.get_context_data_with_docx(docx, **kwargs)
            if context is not None:
                return context
            # Fall back to get_context_data
            return self.get_context_data(**kwargs)

        return context_builder

    def render_to_response(
        self, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> HttpResponse:
        """Render the template and return an HTTP response.

        Args:
            context: Optional context dictionary. If not provided,
                    a context builder is used that tries get_context_data_with_docx()
                    first, then falls back to get_context_data().
            **kwargs: Additional keyword arguments passed to the context methods.

        Returns:
            DocxTemplateResponse with the rendered document.
        """
        # If context is explicitly provided, use it directly
        if context is not None:
            final_context: dict[str, Any] | Any = context
        else:
            # Use a callable that will resolve context with access to DocxTemplate
            final_context = self._build_context_callable(**kwargs)

        return DocxTemplateResponse(
            request=self.request,
            template=self.get_template_name(),
            context=final_context,
            filename=self.get_filename(),
            output_format=self.get_output_format(),
            as_attachment=self.as_attachment,
            update_fields=self.get_update_fields(),
            jinja_env=self.get_jinja_env(),
            autoescape=self.get_autoescape(),
        )

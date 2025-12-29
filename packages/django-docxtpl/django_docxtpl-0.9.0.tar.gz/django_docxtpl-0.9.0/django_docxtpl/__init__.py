"""Django integration for docxtpl - generate documents from Word templates.

This package provides seamless integration between Django and docxtpl,
allowing you to generate documents from Word (.docx) templates with Jinja2
syntax and export them in multiple formats (DOCX, PDF, ODT, HTML, TXT).

Basic usage:
    from django_docxtpl import DocxTemplateResponse

    def my_view(request):
        return DocxTemplateResponse(
            request,
            template="my_template.docx",
            context={"name": "World"},
            filename="hello",
            output_format="pdf",
        )

Class-based view usage:
    from django_docxtpl import DocxTemplateView

    class MyDocumentView(DocxTemplateView):
        template_name = "my_template.docx"
        filename = "document"
        output_format = "pdf"

        def get_context_data(self, **kwargs):
            return {"name": "World"}
"""

from django_docxtpl.converters import (
    ConversionError,
    LibreOfficeNotFoundError,
    update_fields_in_docx,
)
from django_docxtpl.mixins import DocxTemplateResponseMixin
from django_docxtpl.response import ContextType, DocxTemplateResponse
from django_docxtpl.utils import OutputFormat, render_to_file
from django_docxtpl.views import DocxTemplateDetailView, DocxTemplateView

__version__ = "0.9.0"
__all__ = [
    # Response
    "DocxTemplateResponse",
    # Mixins
    "DocxTemplateResponseMixin",
    # Views
    "DocxTemplateView",
    "DocxTemplateDetailView",
    # Exceptions
    "ConversionError",
    "LibreOfficeNotFoundError",
    # Functions
    "update_fields_in_docx",
    "render_to_file",
    # Types
    "OutputFormat",
    "ContextType",
]

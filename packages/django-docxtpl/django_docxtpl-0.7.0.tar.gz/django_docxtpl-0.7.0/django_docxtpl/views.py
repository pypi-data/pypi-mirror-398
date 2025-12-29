"""Generic views for serving documents."""

from __future__ import annotations

from typing import Any

from django.http import HttpRequest, HttpResponse
from django.views import View

from django_docxtpl.mixins import DocxTemplateResponseMixin


class DocxTemplateView(DocxTemplateResponseMixin, View):
    """View that renders a DOCX template and serves it as a document.

    This is a ready-to-use view for serving documents. Simply set the
    template_name and override get_context_data() to provide context.

    Attributes:
        template_name: Path to the DOCX template file.
        filename: Output filename without extension.
        output_format: Desired output format (docx, pdf, odt, html, txt).
        as_attachment: Whether to serve as attachment or inline.
        update_fields: Whether to update TOC, charts, and other fields.
        autoescape: Whether to enable Jinja2 autoescaping when rendering.
        jinja_env: Custom Jinja2 Environment with filters, globals, etc.

    Example:
        # urls.py
        from django_docxtpl.views import DocxTemplateView

        class MyDocumentView(DocxTemplateView):
            template_name = "documents/report.docx"
            filename = "report"
            output_format = "pdf"

            def get_context_data(self, **kwargs):
                return {
                    "title": "Monthly Report",
                    "data": self.get_report_data(),
                }

        urlpatterns = [
            path("report/", MyDocumentView.as_view(), name="report"),
        ]
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET requests by rendering and returning the document.

        Args:
            request: The HTTP request.
            *args: Positional arguments from URL.
            **kwargs: Keyword arguments from URL.

        Returns:
            HttpResponse with the rendered document.
        """
        return self.render_to_response(**kwargs)


class DocxTemplateDetailView(DocxTemplateResponseMixin, View):
    """View for generating documents based on a single model instance.

    This view is similar to Django's DetailView but renders a DOCX template
    instead of an HTML template.

    Attributes:
        model: The model class to query.
        template_name: Path to the DOCX template file.
        filename: Output filename without extension.
        output_format: Desired output format (docx, pdf, odt, html, txt).
        as_attachment: Whether to serve as attachment or inline.
        update_fields: Whether to update TOC, charts, and other fields.
        autoescape: Whether to enable Jinja2 autoescaping when rendering.
        jinja_env: Custom Jinja2 Environment with filters, globals, etc.
        pk_url_kwarg: Name of the URL keyword argument containing the PK.
        slug_url_kwarg: Name of the URL keyword argument containing the slug.
        slug_field: Name of the model field to use for slug lookup.
        context_object_name: Name to use for the object in context.

    Example:
        class InvoiceDocumentView(DocxTemplateDetailView):
            model = Invoice
            template_name = "invoices/template.docx"
            filename = "invoice"
            output_format = "pdf"
            context_object_name = "invoice"

            def get_filename(self):
                return f"invoice_{self.object.number}"
    """

    model: Any = None  # Django Model class with Manager
    pk_url_kwarg: str = "pk"
    slug_url_kwarg: str = "slug"
    slug_field: str = "slug"
    context_object_name: str | None = None
    object: Any = None  # Will hold the retrieved object

    def get_object(self) -> Any:
        """Retrieve the object based on URL parameters.

        Returns:
            The model instance.

        Raises:
            ValueError: If model is not set.
            Http404: If object is not found.
        """
        from django.http import Http404

        if self.model is None:
            raise ValueError(
                f"{self.__class__.__name__} requires a definition of 'model'"
            )

        pk = self.kwargs.get(self.pk_url_kwarg)
        slug = self.kwargs.get(self.slug_url_kwarg)

        if pk is not None:
            obj = self.model.objects.filter(pk=pk).first()
        elif slug is not None:
            obj = self.model.objects.filter(**{self.slug_field: slug}).first()
        else:
            raise ValueError(
                f"Expected URL parameter '{self.pk_url_kwarg}' or "
                f"'{self.slug_url_kwarg}'"
            )

        if obj is None:
            raise Http404(f"{self.model.__name__} not found")

        return obj

    def get_context_object_name(self) -> str:
        """Return the name to use for the object in context.

        Returns:
            The context variable name.
        """
        if self.context_object_name:
            return self.context_object_name
        if self.model:
            return str(self.model.__name__).lower()
        return "object"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Return context with the object included.

        Returns:
            Context dictionary with the object.
        """
        context = super().get_context_data(**kwargs)
        context[self.get_context_object_name()] = self.object
        context["object"] = self.object
        return context

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Handle GET requests.

        Args:
            request: The HTTP request.
            *args: Positional arguments from URL.
            **kwargs: Keyword arguments from URL.

        Returns:
            HttpResponse with the rendered document.
        """
        self.object = self.get_object()
        return self.render_to_response(**kwargs)

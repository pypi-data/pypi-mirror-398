"""Tests for django_docxtpl.views module."""

from unittest.mock import MagicMock, patch

import pytest
from django.http import Http404
from django.test import RequestFactory

from django_docxtpl.views import DocxTemplateDetailView, DocxTemplateView


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """A simple GET request."""
    return request_factory.get("/")


class TestDocxTemplateView:
    """Tests for DocxTemplateView."""

    def test_get_returns_response(
        self, get_request, simple_docx_template, sample_context
    ):
        """Test GET request returns document response."""

        class TestView(DocxTemplateView):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                return {"name": "Test", "title": "Title"}

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {}

        response = view.get(get_request)

        assert response.status_code == 200
        assert response["Content-Type"] == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_get_with_custom_filename(self, get_request, simple_docx_template):
        """Test GET request with custom filename."""

        class TestView(DocxTemplateView):
            template_name = simple_docx_template
            filename = "custom_report"

            def get_context_data(self, **kwargs):
                return {"name": "Test", "title": "Title"}

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {}

        response = view.get(get_request)

        assert 'filename="custom_report.docx"' in response["Content-Disposition"]

    def test_get_with_url_kwargs(self, get_request, simple_docx_template):
        """Test GET request passes URL kwargs to context."""

        class TestView(DocxTemplateView):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                context = {"name": "Test", "title": "Title"}
                context.update(kwargs)
                return context

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 123}

        response = view.get(get_request, pk=123)

        assert response.status_code == 200

    @patch("django_docxtpl.response.convert_docx")
    def test_get_with_pdf_format(self, mock_convert, get_request, simple_docx_template):
        """Test GET request with PDF output format."""
        mock_convert.return_value = b"%PDF fake"

        class TestView(DocxTemplateView):
            template_name = simple_docx_template
            output_format = "pdf"

            def get_context_data(self, **kwargs):
                return {"name": "Test", "title": "Title"}

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {}

        response = view.get(get_request)

        assert response["Content-Type"] == "application/pdf"

    def test_get_with_get_context_data_with_docx(
        self, get_request, simple_docx_template
    ):
        """Test GET request uses get_context_data_with_docx when defined."""
        received_docx = None

        class TestView(DocxTemplateView):
            template_name = simple_docx_template

            def get_context_data_with_docx(self, docx, **kwargs):
                nonlocal received_docx
                received_docx = docx
                return {"name": "FromDocx", "title": "Title"}

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {}

        response = view.get(get_request)

        from docxtpl import DocxTemplate

        assert received_docx is not None
        assert isinstance(received_docx, DocxTemplate)
        assert response.status_code == 200

    def test_get_context_data_with_docx_receives_url_kwargs(
        self, get_request, simple_docx_template
    ):
        """Test get_context_data_with_docx receives URL kwargs."""
        received_kwargs = None

        class TestView(DocxTemplateView):
            template_name = simple_docx_template

            def get_context_data_with_docx(self, docx, **kwargs):
                nonlocal received_kwargs
                received_kwargs = kwargs
                return {"name": "Test", "title": "Title"}

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 42, "slug": "test-slug"}

        view.get(get_request, pk=42, slug="test-slug")

        assert received_kwargs == {"pk": 42, "slug": "test-slug"}


class MockModel:
    """Mock Django model for testing."""

    __name__ = "MockModel"

    def __init__(self, pk, name):
        self.pk = pk
        self.name = name


class MockQuerySet:
    """Mock QuerySet for testing."""

    def __init__(self, objects):
        self._objects = {obj.pk: obj for obj in objects}

    def filter(self, **kwargs):
        if "pk" in kwargs:
            obj = self._objects.get(kwargs["pk"])
            return MockFilterResult(obj)
        if "slug" in kwargs:
            for obj in self._objects.values():
                if getattr(obj, "slug", None) == kwargs["slug"]:
                    return MockFilterResult(obj)
            return MockFilterResult(None)
        return MockFilterResult(None)


class MockFilterResult:
    """Mock filter result for testing."""

    def __init__(self, obj):
        self._obj = obj

    def first(self):
        return self._obj


class TestDocxTemplateDetailView:
    """Tests for DocxTemplateDetailView."""

    def test_get_object_by_pk(self, get_request, simple_docx_template):
        """Test retrieving object by primary key."""
        mock_obj = MockModel(pk=1, name="Test Object")
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_model.objects = MockQuerySet([mock_obj])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 1}

        obj = view.get_object()

        assert obj.pk == 1
        assert obj.name == "Test Object"

    def test_get_object_by_slug(self, get_request, simple_docx_template):
        """Test retrieving object by slug."""
        mock_obj = MockModel(pk=1, name="Test Object")
        mock_obj.slug = "test-slug"
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_model.objects = MockQuerySet([mock_obj])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"slug": "test-slug"}

        obj = view.get_object()

        assert obj.pk == 1

    def test_get_object_not_found(self, get_request, simple_docx_template):
        """Test Http404 when object not found."""
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_model.objects = MockQuerySet([])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 999}

        with pytest.raises(Http404):
            view.get_object()

    def test_get_object_no_model(self, get_request):
        """Test error when model not set."""

        class TestView(DocxTemplateDetailView):
            template_name = "test.docx"

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 1}

        with pytest.raises(ValueError, match="requires a definition of 'model'"):
            view.get_object()

    def test_get_object_no_pk_or_slug(self, get_request, simple_docx_template):
        """Test error when neither pk nor slug provided."""
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {}

        with pytest.raises(ValueError, match="Expected URL parameter"):
            view.get_object()

    def test_get_context_object_name_default(self, simple_docx_template):
        """Test default context object name is model name lowercase."""
        mock_model = MagicMock()
        mock_model.__name__ = "Invoice"

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()

        assert view.get_context_object_name() == "invoice"

    def test_get_context_object_name_custom(self, simple_docx_template):
        """Test custom context object name."""

        class TestView(DocxTemplateDetailView):
            template_name = simple_docx_template
            context_object_name = "my_object"

        view = TestView()

        assert view.get_context_object_name() == "my_object"

    def test_get_context_data_includes_object(self, get_request, simple_docx_template):
        """Test context includes the object."""
        mock_obj = MockModel(pk=1, name="Test")
        mock_model = MagicMock()
        mock_model.__name__ = "MockModel"
        mock_model.objects = MockQuerySet([mock_obj])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 1}
        view.object = mock_obj

        context = view.get_context_data()

        assert context["object"] == mock_obj
        assert context["mockmodel"] == mock_obj

    def test_get_returns_response(self, get_request, simple_docx_template):
        """Test GET request returns document response."""
        mock_obj = MockModel(pk=1, name="Test")
        mock_model = MagicMock()
        mock_model.__name__ = "Item"
        mock_model.objects = MockQuerySet([mock_obj])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["name"] = self.object.name
                context["title"] = "Document"
                return context

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 1}

        response = view.get(get_request, pk=1)

        assert response.status_code == 200

    def test_get_with_custom_filename_from_object(
        self, get_request, simple_docx_template
    ):
        """Test dynamic filename based on object."""
        mock_obj = MockModel(pk=1, name="Invoice123")
        mock_model = MagicMock()
        mock_model.__name__ = "Invoice"
        mock_model.objects = MockQuerySet([mock_obj])

        class TestView(DocxTemplateDetailView):
            model = mock_model
            template_name = simple_docx_template

            def get_filename(self):
                return f"invoice_{self.object.name}"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["name"] = self.object.name
                context["title"] = "Invoice"
                return context

        view = TestView()
        view.request = get_request
        view.args = ()
        view.kwargs = {"pk": 1}

        response = view.get(get_request, pk=1)

        assert 'filename="invoice_Invoice123.docx"' in response["Content-Disposition"]

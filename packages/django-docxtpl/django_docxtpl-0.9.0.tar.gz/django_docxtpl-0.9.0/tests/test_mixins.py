"""Tests for django_docxtpl.mixins module."""

from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.views import View

from django_docxtpl.mixins import DocxTemplateResponseMixin


@pytest.fixture
def request_factory():
    """Django request factory."""
    return RequestFactory()


@pytest.fixture
def get_request(request_factory):
    """A simple GET request."""
    return request_factory.get("/")


class TestDocxTemplateResponseMixin:
    """Tests for DocxTemplateResponseMixin."""

    def test_get_template_name(self, simple_docx_template):
        """Test get_template_name returns template_name attribute."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        assert view.get_template_name() == simple_docx_template

    def test_get_template_name_not_set(self):
        """Test get_template_name raises error when not set."""

        class TestView(DocxTemplateResponseMixin, View):
            pass

        view = TestView()

        with pytest.raises(ValueError, match="requires either a definition"):
            view.get_template_name()

    def test_get_filename(self):
        """Test get_filename returns filename attribute."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"
            filename = "my_document"

        view = TestView()
        assert view.get_filename() == "my_document"

    def test_get_filename_default(self):
        """Test get_filename default value."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"

        view = TestView()
        assert view.get_filename() == "document"

    def test_get_output_format(self):
        """Test get_output_format returns output_format attribute."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"
            output_format = "pdf"

        view = TestView()
        assert view.get_output_format() == "pdf"

    def test_get_output_format_default(self):
        """Test get_output_format default value."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"

        view = TestView()
        assert view.get_output_format() == "docx"

    def test_get_context_data(self):
        """Test get_context_data returns kwargs."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"

        view = TestView()
        context = view.get_context_data(foo="bar", num=42)

        assert context == {"foo": "bar", "num": 42}

    def test_get_context_data_override(self):
        """Test get_context_data can be overridden."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = "test.docx"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["custom"] = "value"
                return context

        view = TestView()
        context = view.get_context_data(foo="bar")

        assert context == {"foo": "bar", "custom": "value"}

    def test_render_to_response(
        self, get_request, simple_docx_template, sample_context
    ):
        """Test render_to_response creates DocxTemplateResponse."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            filename = "test_doc"

        view = TestView()
        view.request = get_request

        response = view.render_to_response(sample_context)

        assert response.status_code == 200
        assert 'filename="test_doc.docx"' in response["Content-Disposition"]

    def test_render_to_response_with_get_context_data(
        self, get_request, simple_docx_template
    ):
        """Test render_to_response uses get_context_data when context is None."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                return {"name": "FromMethod", "title": "Title"}

        view = TestView()
        view.request = get_request

        response = view.render_to_response()

        assert response.status_code == 200

    def test_render_to_response_pdf(self, get_request, simple_docx_template):
        """Test render_to_response with PDF output format."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            output_format = "pdf"

        view = TestView()
        view.request = get_request

        with patch("django_docxtpl.response.convert_docx") as mock_convert:
            mock_convert.return_value = b"%PDF fake"

            response = view.render_to_response({"name": "Test", "title": "Title"})

            assert response["Content-Type"] == "application/pdf"

    def test_as_attachment_default(self, get_request, simple_docx_template):
        """Test as_attachment is True by default."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        view.request = get_request

        response = view.render_to_response({"name": "Test", "title": "Title"})

        assert response["Content-Disposition"].startswith("attachment;")

    def test_as_attachment_false(self, get_request, simple_docx_template):
        """Test as_attachment can be set to False."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            as_attachment = False

        view = TestView()
        view.request = get_request

        response = view.render_to_response({"name": "Test", "title": "Title"})

        assert response["Content-Disposition"].startswith("inline;")


class TestDynamicMethods:
    """Tests for dynamically overriding mixin methods."""

    def test_dynamic_template_name(self, get_request, simple_docx_template):
        """Test dynamically determining template name."""

        class TestView(DocxTemplateResponseMixin, View):
            def get_template_name(self):
                return simple_docx_template

        view = TestView()
        view.request = get_request

        response = view.render_to_response({"name": "Test", "title": "Title"})
        assert response.status_code == 200

    def test_dynamic_filename(self, get_request, simple_docx_template):
        """Test dynamically determining filename."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_filename(self):
                return "dynamic_name"

        view = TestView()
        view.request = get_request

        response = view.render_to_response({"name": "Test", "title": "Title"})
        assert 'filename="dynamic_name.docx"' in response["Content-Disposition"]

    def test_dynamic_output_format(self, get_request, simple_docx_template):
        """Test dynamically determining output format."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_output_format(self):
                return "docx"  # Keep docx to avoid LibreOffice dependency

        view = TestView()
        view.request = get_request

        response = view.render_to_response({"name": "Test", "title": "Title"})
        assert response.status_code == 200


class TestUpdateFieldsMixin:
    """Tests for update_fields functionality in mixin."""

    def test_get_update_fields_default(self, simple_docx_template):
        """Test get_update_fields returns False by default."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        assert view.get_update_fields() is False

    def test_get_update_fields_attribute(self, simple_docx_template):
        """Test get_update_fields returns update_fields attribute."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            update_fields = True

        view = TestView()
        assert view.get_update_fields() is True

    def test_get_update_fields_override(self, simple_docx_template):
        """Test get_update_fields can be overridden."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_update_fields(self):
                return True

        view = TestView()
        assert view.get_update_fields() is True

    def test_render_to_response_passes_update_fields(
        self, get_request, simple_docx_template
    ):
        """Test render_to_response passes update_fields to response."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            update_fields = True

        view = TestView()
        view.request = get_request

        with patch("django_docxtpl.mixins.DocxTemplateResponse") as mock_response:
            mock_response.return_value = MagicMock(status_code=200)

            view.render_to_response({"name": "Test", "title": "Title"})

            mock_response.assert_called_once()
            _, kwargs = mock_response.call_args
            assert kwargs.get("update_fields") is True

    def test_dynamic_update_fields(self, get_request, simple_docx_template):
        """Test dynamically determining update_fields."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_update_fields(self):
                # Only update fields for PDF output
                return self.get_output_format() == "pdf"

        view = TestView()
        view.request = get_request

        # Default output is docx, so update_fields should be False
        assert view.get_update_fields() is False

        # Change output format
        view.output_format = "pdf"
        assert view.get_update_fields() is True


class TestGetContextDataWithDocx:
    """Tests for get_context_data_with_docx method."""

    def test_get_context_data_with_docx_default_returns_none(
        self, simple_docx_template
    ):
        """Test that default get_context_data_with_docx returns None."""
        import tempfile
        from pathlib import Path

        from docxtpl import DocxTemplate

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        doc = DocxTemplate(simple_docx_template)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = view.get_context_data_with_docx(doc, Path(tmp_dir))

        assert result is None

    def test_get_context_data_with_docx_override(self, simple_docx_template):
        """Test that get_context_data_with_docx can be overridden."""
        import tempfile
        from pathlib import Path

        from docxtpl import DocxTemplate

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
                return {
                    "name": "FromDocx",
                    "title": "DocxTitle",
                    "docx_type": type(docx).__name__,
                }

        view = TestView()
        doc = DocxTemplate(simple_docx_template)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = view.get_context_data_with_docx(doc, Path(tmp_dir))

        assert result == {
            "name": "FromDocx",
            "title": "DocxTitle",
            "docx_type": "DocxTemplate",
        }

    def test_get_context_data_with_docx_receives_kwargs(self, simple_docx_template):
        """Test that get_context_data_with_docx receives kwargs."""
        import tempfile
        from pathlib import Path

        from docxtpl import DocxTemplate

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
                return {"received_kwargs": kwargs}

        view = TestView()
        doc = DocxTemplate(simple_docx_template)
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = view.get_context_data_with_docx(
                doc, Path(tmp_dir), pk=123, slug="test"
            )

        assert result == {"received_kwargs": {"pk": 123, "slug": "test"}}

    def test_render_to_response_uses_get_context_data_with_docx(
        self, get_request, simple_docx_template
    ):
        """Test that render_to_response uses get_context_data_with_docx when defined."""
        received_docx = None
        received_tmp_dir = None

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
                nonlocal received_docx, received_tmp_dir
                received_docx = docx
                received_tmp_dir = tmp_dir
                return {"name": "WithDocx", "title": "Title"}

        view = TestView()
        view.request = get_request

        response = view.render_to_response()

        from pathlib import Path

        from docxtpl import DocxTemplate

        assert received_docx is not None
        assert isinstance(received_docx, DocxTemplate)
        assert received_tmp_dir is not None
        assert isinstance(received_tmp_dir, Path)
        assert response.status_code == 200

    def test_render_to_response_falls_back_to_get_context_data(
        self, get_request, simple_docx_template
    ):
        """Test render_to_response falls back when with_docx returns None."""
        get_context_data_called = False

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                nonlocal get_context_data_called
                get_context_data_called = True
                return {"name": "Fallback", "title": "Title"}

        view = TestView()
        view.request = get_request

        response = view.render_to_response()

        assert get_context_data_called
        assert response.status_code == 200

    def test_get_context_data_with_docx_takes_priority(
        self, get_request, simple_docx_template
    ):
        """Test that get_context_data_with_docx takes priority over get_context_data."""
        from io import BytesIO
        from zipfile import ZipFile

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                return {"name": "NormalMethod", "title": "Title1"}

            def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
                return {"name": "DocxMethod", "title": "Title2"}

        view = TestView()
        view.request = get_request

        response = view.render_to_response()

        # Extract document.xml to verify which context was used
        docx_content = BytesIO(response.content)
        with ZipFile(docx_content) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            assert "DocxMethod" in doc_xml
            assert "NormalMethod" not in doc_xml

    def test_render_to_response_with_explicit_context_bypasses_methods(
        self, get_request, simple_docx_template
    ):
        """Test that explicit context in render_to_response bypasses both methods."""
        from io import BytesIO
        from zipfile import ZipFile

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_context_data(self, **kwargs):
                return {"name": "FromMethod", "title": "Title"}

            def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
                return {"name": "FromDocxMethod", "title": "Title"}

        view = TestView()
        view.request = get_request

        response = view.render_to_response(
            {"name": "ExplicitContext", "title": "Title"}
        )

        # Extract document.xml to verify explicit context was used
        docx_content = BytesIO(response.content)
        with ZipFile(docx_content) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            assert "ExplicitContext" in doc_xml


class TestJinjaEnvMixin:
    """Tests for jinja_env support in DocxTemplateResponseMixin."""

    def test_get_jinja_env_default(self, simple_docx_template):
        """Test get_jinja_env returns None by default."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        assert view.get_jinja_env() is None

    def test_get_jinja_env_attribute(self, simple_docx_template):
        """Test get_jinja_env returns jinja_env attribute."""
        from jinja2 import Environment

        jinja_env = Environment(autoescape=True)

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        view.jinja_env = jinja_env
        assert view.get_jinja_env() is jinja_env

    def test_get_jinja_env_override(self, simple_docx_template):
        """Test get_jinja_env can be overridden."""
        from jinja2 import Environment

        custom_env = Environment(autoescape=True)

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_jinja_env(self):
                return custom_env

        view = TestView()
        assert view.get_jinja_env() is custom_env

    def test_render_to_response_passes_jinja_env(
        self, get_request, simple_docx_template
    ):
        """Test render_to_response passes jinja_env to response."""
        from jinja2 import Environment

        jinja_env = Environment(autoescape=True)

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        view.jinja_env = jinja_env
        view.request = get_request

        with patch("django_docxtpl.mixins.DocxTemplateResponse") as mock_response:
            mock_response.return_value = MagicMock(status_code=200)

            view.render_to_response({"name": "Test", "title": "Title"})

            mock_response.assert_called_once()
            _, kwargs = mock_response.call_args
            assert kwargs.get("jinja_env") is jinja_env

    def test_jinja_env_with_custom_filter(self, get_request, tmp_path):
        """Test mixin with custom jinja_env filter renders correctly."""
        from io import BytesIO
        from zipfile import ZipFile

        from docx import Document
        from jinja2 import Environment

        # Create a template with custom filter syntax
        doc = Document()
        doc.add_paragraph("Value: {{ value|milers }}")
        template_path = tmp_path / "filter_template.docx"
        doc.save(template_path)

        # Create custom jinja_env with filter
        def format_milers(value):
            return f"{value:,.0f}".replace(",", ".")

        jinja_env = Environment(autoescape=True)
        jinja_env.filters["milers"] = format_milers

        class TestView(DocxTemplateResponseMixin, View):
            template_name = template_path

            def get_jinja_env(self):
                return jinja_env

            def get_context_data(self, **kwargs):
                return {"value": 1234567}

        view = TestView()
        view.request = get_request

        response = view.render_to_response()

        assert response.status_code == 200

        # Verify the filter was applied
        docx_content = BytesIO(response.content)
        with ZipFile(docx_content) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            assert "1.234.567" in doc_xml


class TestAutoescapeMixin:
    """Tests for autoescape support in DocxTemplateResponseMixin."""

    def test_get_autoescape_default(self, simple_docx_template):
        """Test get_autoescape returns False by default."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

        view = TestView()
        assert view.get_autoescape() is False

    def test_get_autoescape_attribute(self, simple_docx_template):
        """Test get_autoescape returns autoescape attribute."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            autoescape = True

        view = TestView()
        assert view.get_autoescape() is True

    def test_get_autoescape_override(self, simple_docx_template):
        """Test get_autoescape can be overridden."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template

            def get_autoescape(self):
                return True

        view = TestView()
        assert view.get_autoescape() is True

    def test_render_to_response_passes_autoescape(
        self, get_request, simple_docx_template
    ):
        """Test render_to_response passes autoescape to response."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            autoescape = True

        view = TestView()
        view.request = get_request

        with patch("django_docxtpl.mixins.DocxTemplateResponse") as mock_response:
            mock_response.return_value = MagicMock(status_code=200)

            view.render_to_response({"name": "Test", "title": "Title"})

            mock_response.assert_called_once()
            _, kwargs = mock_response.call_args
            assert kwargs.get("autoescape") is True

    def test_dynamic_autoescape(self, get_request, simple_docx_template):
        """Test dynamically determining autoescape."""

        class TestView(DocxTemplateResponseMixin, View):
            template_name = simple_docx_template
            has_user_input = False

            def get_autoescape(self):
                # Enable autoescape when context has user input
                return self.has_user_input

        view = TestView()
        view.request = get_request

        # Default has_user_input is False
        assert view.get_autoescape() is False

        # Change has_user_input
        view.has_user_input = True
        assert view.get_autoescape() is True

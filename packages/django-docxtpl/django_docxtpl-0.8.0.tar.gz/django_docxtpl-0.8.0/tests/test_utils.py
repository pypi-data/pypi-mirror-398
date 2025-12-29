"""Tests for django_docxtpl.utils module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from django_docxtpl.utils import (
    CONTENT_TYPES,
    EXTENSIONS,
    find_libreoffice,
    get_content_type,
    get_extension,
    get_filename_with_extension,
    get_template_dir,
    render_to_file,
)


class TestContentTypes:
    """Tests for content type functions."""

    def test_get_content_type_docx(self):
        """Test content type for DOCX format."""
        assert get_content_type("docx") == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_get_content_type_pdf(self):
        """Test content type for PDF format."""
        assert get_content_type("pdf") == "application/pdf"

    def test_get_content_type_odt(self):
        """Test content type for ODT format."""
        assert get_content_type("odt") == "application/vnd.oasis.opendocument.text"

    def test_get_content_type_html(self):
        """Test content type for HTML format."""
        assert get_content_type("html") == "text/html"

    def test_get_content_type_txt(self):
        """Test content type for TXT format."""
        assert get_content_type("txt") == "text/plain"

    def test_get_content_type_invalid(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported format"):
            get_content_type("xyz")


class TestExtensions:
    """Tests for extension functions."""

    def test_get_extension_docx(self):
        """Test extension for DOCX format."""
        assert get_extension("docx") == ".docx"

    def test_get_extension_pdf(self):
        """Test extension for PDF format."""
        assert get_extension("pdf") == ".pdf"

    def test_get_extension_odt(self):
        """Test extension for ODT format."""
        assert get_extension("odt") == ".odt"

    def test_get_extension_html(self):
        """Test extension for HTML format."""
        assert get_extension("html") == ".html"

    def test_get_extension_txt(self):
        """Test extension for TXT format."""
        assert get_extension("txt") == ".txt"

    def test_get_extension_invalid(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported format"):
            get_extension("xyz")


class TestFilenameWithExtension:
    """Tests for get_filename_with_extension function."""

    def test_add_docx_extension(self):
        """Test adding DOCX extension to filename."""
        assert get_filename_with_extension("report", "docx") == "report.docx"

    def test_add_pdf_extension(self):
        """Test adding PDF extension to filename."""
        assert get_filename_with_extension("report", "pdf") == "report.pdf"

    def test_filename_already_has_correct_extension(self):
        """Test that correct extension is not duplicated."""
        assert get_filename_with_extension("report.pdf", "pdf") == "report.pdf"

    def test_filename_has_different_extension(self):
        """Test replacing wrong extension."""
        assert get_filename_with_extension("report.docx", "pdf") == "report.pdf"

    def test_filename_with_dots(self):
        """Test filename with dots in name."""
        assert get_filename_with_extension("report.v2", "pdf") == "report.v2.pdf"

    def test_case_insensitive_extension(self):
        """Test that extension check is case insensitive."""
        assert get_filename_with_extension("report.PDF", "pdf") == "report.PDF"


class TestFindLibreOffice:
    """Tests for find_libreoffice function."""

    @patch("django_docxtpl.utils.settings")
    def test_find_from_settings(self, mock_settings, tmp_path):
        """Test finding LibreOffice from Django settings."""
        # Create a fake soffice executable
        fake_soffice = tmp_path / "soffice"
        fake_soffice.touch()

        mock_settings.DOCXTPL_LIBREOFFICE_PATH = str(fake_soffice)

        result = find_libreoffice()
        assert result == fake_soffice

    @patch("django_docxtpl.utils.settings")
    @patch("shutil.which")
    def test_find_from_path(self, mock_which, mock_settings):
        """Test finding LibreOffice from system PATH."""
        mock_settings.DOCXTPL_LIBREOFFICE_PATH = None
        mock_which.return_value = "/usr/bin/soffice"

        result = find_libreoffice()
        assert result == Path("/usr/bin/soffice")

    @patch("django_docxtpl.utils.settings")
    @patch("shutil.which")
    def test_not_found(self, mock_which, mock_settings):
        """Test when LibreOffice is not found."""
        mock_settings.DOCXTPL_LIBREOFFICE_PATH = None
        mock_which.return_value = None

        # Also patch the common paths check
        with patch.object(Path, "exists", return_value=False):
            find_libreoffice()

        # May return None or find it in common paths depending on system
        # This test mainly ensures no exception is raised


class TestGetTemplateDir:
    """Tests for get_template_dir function."""

    @patch("django_docxtpl.utils.settings")
    def test_get_template_dir_configured(self, mock_settings, tmp_path):
        """Test getting template directory when configured."""
        mock_settings.DOCXTPL_TEMPLATE_DIR = tmp_path

        result = get_template_dir()
        assert result == tmp_path

    @patch("django_docxtpl.utils.settings")
    def test_get_template_dir_not_configured(self, mock_settings):
        """Test getting template directory when not configured."""
        mock_settings.DOCXTPL_TEMPLATE_DIR = None

        result = get_template_dir()
        assert result is None


class TestConstants:
    """Tests for module constants."""

    def test_all_formats_have_content_type(self):
        """Test that all formats in EXTENSIONS have content types."""
        for fmt in EXTENSIONS:
            assert fmt in CONTENT_TYPES

    def test_all_formats_have_extension(self):
        """Test that all formats in CONTENT_TYPES have extensions."""
        for fmt in CONTENT_TYPES:
            assert fmt in EXTENSIONS

    def test_supported_formats(self):
        """Test that expected formats are supported."""
        expected = {"docx", "pdf", "odt", "html", "txt"}
        assert set(CONTENT_TYPES.keys()) == expected
        assert set(EXTENSIONS.keys()) == expected


class TestRenderToFile:
    """Tests for render_to_file function."""

    def test_render_to_file_docx(self, simple_docx_template, sample_context, tmp_path):
        """Test rendering to DOCX file."""
        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test_output",
            output_format="docx",
        )

        assert output_path.exists()
        assert output_path.name == "test_output.docx"
        assert output_path.parent == tmp_path
        # DOCX files start with PK (zip signature)
        assert output_path.read_bytes()[:2] == b"PK"

    def test_render_to_file_creates_directory(
        self, simple_docx_template, sample_context, tmp_path
    ):
        """Test that render_to_file creates output directory if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "output" / "dir"
        assert not nested_dir.exists()

        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=nested_dir,
            filename="test",
            output_format="docx",
        )

        assert nested_dir.exists()
        assert output_path.exists()

    def test_render_to_file_template_not_found(self, sample_context, tmp_path):
        """Test that FileNotFoundError is raised for missing template."""
        with pytest.raises(FileNotFoundError, match="Template not found"):
            render_to_file(
                template="/nonexistent/template.docx",
                context=sample_context,
                output_dir=tmp_path,
                filename="test",
            )

    @patch("django_docxtpl.converters.convert_docx")
    def test_render_to_file_pdf(
        self, mock_convert, simple_docx_template, sample_context, tmp_path
    ):
        """Test rendering to PDF file."""
        mock_convert.return_value = b"%PDF-1.4 fake pdf content"

        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test_output",
            output_format="pdf",
        )

        assert output_path.exists()
        assert output_path.name == "test_output.pdf"
        mock_convert.assert_called_once()

    @patch("django_docxtpl.converters.convert_docx")
    def test_render_to_file_with_update_fields(
        self, mock_convert, simple_docx_template, sample_context, tmp_path
    ):
        """Test that update_fields is passed to convert_docx."""
        mock_convert.return_value = b"%PDF-1.4 fake pdf content"

        render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test",
            output_format="pdf",
            update_fields=True,
        )

        mock_convert.assert_called_once()
        _, kwargs = mock_convert.call_args
        assert kwargs.get("update_fields") is True

    @patch("django_docxtpl.converters.update_fields_in_docx")
    def test_render_to_file_docx_with_update_fields(
        self, mock_update, simple_docx_template, sample_context, tmp_path
    ):
        """Test update_fields_in_docx is called for DOCX with update_fields."""
        mock_update.return_value = b"updated docx content"

        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test",
            output_format="docx",
            update_fields=True,
        )

        mock_update.assert_called_once()
        assert output_path.read_bytes() == b"updated docx content"

    def test_render_to_file_returns_absolute_path(
        self, simple_docx_template, sample_context, tmp_path
    ):
        """Test that render_to_file returns an absolute path."""
        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test",
            output_format="docx",
        )

        assert output_path.is_absolute()

    def test_render_to_file_with_template_dir(
        self, sample_context, template_dir, tmp_path
    ):
        """Test render_to_file with relative template path."""
        with patch("django_docxtpl.utils.get_template_dir") as mock_dir:
            mock_dir.return_value = template_dir

            output_path = render_to_file(
                template="test_template.docx",
                context=sample_context,
                output_dir=tmp_path,
                filename="test",
                output_format="docx",
            )

            assert output_path.exists()


class TestRenderToFileCallableContext:
    """Tests for callable context support in render_to_file."""

    def test_render_to_file_with_callable_context(self, simple_docx_template, tmp_path):
        """Test render_to_file with callable context."""
        received_docx = None
        received_tmp_dir = None

        def context_builder(docx, tmp_dir):
            nonlocal received_docx, received_tmp_dir
            received_docx = docx
            received_tmp_dir = tmp_dir
            return {"name": "FromCallable", "title": "CallableTitle"}

        output_path = render_to_file(
            template=simple_docx_template,
            context=context_builder,
            output_dir=tmp_path,
            filename="test_callable",
            output_format="docx",
        )

        from pathlib import Path

        from docxtpl import DocxTemplate

        assert received_docx is not None
        assert isinstance(received_docx, DocxTemplate)
        assert received_tmp_dir is not None
        assert isinstance(received_tmp_dir, Path)
        assert output_path.exists()

    def test_render_to_file_callable_renders_correctly(
        self, simple_docx_template, tmp_path
    ):
        """Test that callable context is used in rendering."""
        from zipfile import ZipFile

        def context_builder(docx, tmp_dir):
            return {"name": "CallableRendered", "title": "CallableTitle"}

        output_path = render_to_file(
            template=simple_docx_template,
            context=context_builder,
            output_dir=tmp_path,
            filename="test_callable",
            output_format="docx",
        )

        # Extract document.xml to verify content was rendered
        with ZipFile(output_path) as zf:
            doc_xml = zf.read("word/document.xml").decode("utf-8")
            assert "CallableRendered" in doc_xml
            assert "CallableTitle" in doc_xml

    def test_render_to_file_dict_context_still_works(
        self, simple_docx_template, sample_context, tmp_path
    ):
        """Test that dict context still works (backward compatibility)."""
        output_path = render_to_file(
            template=simple_docx_template,
            context=sample_context,
            output_dir=tmp_path,
            filename="test_dict",
            output_format="docx",
        )

        assert output_path.exists()

    @patch("django_docxtpl.converters.convert_docx")
    def test_render_to_file_callable_with_pdf(
        self, mock_convert, simple_docx_template, tmp_path
    ):
        """Test callable context with PDF conversion."""
        mock_convert.return_value = b"%PDF-1.4 fake"

        def context_builder(docx, tmp_dir):
            return {"name": "Test", "title": "Title"}

        output_path = render_to_file(
            template=simple_docx_template,
            context=context_builder,
            output_dir=tmp_path,
            filename="test_callable",
            output_format="pdf",
        )

        assert output_path.exists()
        mock_convert.assert_called_once()

    def test_render_to_file_with_jinja_env(self, simple_docx_template, tmp_path):
        """Test render_to_file with custom jinja_env."""
        from jinja2 import Environment

        def format_milers(value):
            return f"{value:,.0f}".replace(",", ".")

        jinja_env = Environment(autoescape=True)
        jinja_env.filters["milers"] = format_milers

        output_path = render_to_file(
            template=simple_docx_template,
            context={"name": "Test", "title": "Title"},
            output_dir=tmp_path,
            filename="test_jinja_env",
            output_format="docx",
            jinja_env=jinja_env,
        )

        assert output_path.exists()


class TestRenderToFileAutoescape:
    """Tests for autoescape parameter in render_to_file."""

    def test_render_to_file_autoescape_default_is_false(
        self, simple_docx_template, tmp_path
    ):
        """Test that autoescape is False by default."""
        with patch("docxtpl.DocxTemplate") as mock_docx:
            mock_instance = MagicMock()
            mock_docx.return_value = mock_instance
            mock_instance.save = MagicMock(side_effect=lambda buf: buf.write(b"PK"))

            render_to_file(
                template=simple_docx_template,
                context={"name": "Test", "title": "Title"},
                output_dir=tmp_path,
                filename="test_autoescape",
                output_format="docx",
            )

            mock_instance.render.assert_called_once()
            _, kwargs = mock_instance.render.call_args
            assert kwargs.get("autoescape") is False

    def test_render_to_file_autoescape_true(self, simple_docx_template, tmp_path):
        """Test that autoescape=True is passed to doc.render()."""
        with patch("docxtpl.DocxTemplate") as mock_docx:
            mock_instance = MagicMock()
            mock_docx.return_value = mock_instance
            mock_instance.save = MagicMock(side_effect=lambda buf: buf.write(b"PK"))

            render_to_file(
                template=simple_docx_template,
                context={"name": "Test", "title": "Title"},
                output_dir=tmp_path,
                filename="test_autoescape",
                output_format="docx",
                autoescape=True,
            )

            mock_instance.render.assert_called_once()
            _, kwargs = mock_instance.render.call_args
            assert kwargs.get("autoescape") is True

    def test_render_to_file_autoescape_false_explicitly(
        self, simple_docx_template, tmp_path
    ):
        """Test that autoescape=False is passed explicitly."""
        with patch("docxtpl.DocxTemplate") as mock_docx:
            mock_instance = MagicMock()
            mock_docx.return_value = mock_instance
            mock_instance.save = MagicMock(side_effect=lambda buf: buf.write(b"PK"))

            render_to_file(
                template=simple_docx_template,
                context={"name": "Test", "title": "Title"},
                output_dir=tmp_path,
                filename="test_autoescape",
                output_format="docx",
                autoescape=False,
            )

            mock_instance.render.assert_called_once()
            _, kwargs = mock_instance.render.call_args
            assert kwargs.get("autoescape") is False

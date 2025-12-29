"""Tests for django_docxtpl.converters module."""

from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from django_docxtpl.converters import (
    ConversionError,
    LibreOfficeNotFoundError,
    convert_docx,
    update_fields_in_docx,
)


class TestConvertDocx:
    """Tests for convert_docx function."""

    def test_docx_format_raises_error(self, rendered_docx_bytes):
        """Test that converting to DOCX raises ValueError."""
        with pytest.raises(ValueError, match="No conversion needed"):
            convert_docx(rendered_docx_bytes, "docx")

    @patch("django_docxtpl.converters.find_libreoffice")
    def test_libreoffice_not_found(self, mock_find, rendered_docx_bytes):
        """Test that missing LibreOffice raises error."""
        mock_find.return_value = None

        with pytest.raises(LibreOfficeNotFoundError, match="LibreOffice not found"):
            convert_docx(rendered_docx_bytes, "pdf")

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("subprocess.run")
    def test_conversion_success(
        self, mock_run, mock_find, rendered_docx_bytes, tmp_path
    ):
        """Test successful conversion."""
        # Setup mocks
        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        # Create fake output file in the temp directory
        # We need to patch tempfile to use our tmp_path
        with patch("tempfile.TemporaryDirectory") as mock_tempdir:
            mock_tempdir.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            mock_tempdir.return_value.__exit__ = MagicMock(return_value=False)

            # Create the expected output file
            output_file = tmp_path / "input.pdf"
            output_file.write_bytes(b"%PDF-1.4 fake pdf content")

            result = convert_docx(rendered_docx_bytes, "pdf")

            assert result == b"%PDF-1.4 fake pdf content"

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("subprocess.run")
    def test_conversion_failure(self, mock_run, mock_find, rendered_docx_bytes):
        """Test conversion failure handling."""
        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.return_value = MagicMock(
            returncode=1, stderr="Error: conversion failed", stdout=""
        )

        with pytest.raises(ConversionError, match="conversion failed"):
            convert_docx(rendered_docx_bytes, "pdf")

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("subprocess.run")
    def test_conversion_timeout(self, mock_run, mock_find, rendered_docx_bytes):
        """Test conversion timeout handling."""
        import subprocess

        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="soffice", timeout=60)

        with pytest.raises(ConversionError, match="timed out"):
            convert_docx(rendered_docx_bytes, "pdf", timeout=60)

    def test_accepts_bytesio(self, rendered_docx_bytes):
        """Test that function accepts BytesIO input."""
        buffer = BytesIO(rendered_docx_bytes)

        with patch("django_docxtpl.converters.find_libreoffice") as mock_find:
            mock_find.return_value = None

            # Should raise LibreOfficeNotFoundError, not TypeError
            with pytest.raises(LibreOfficeNotFoundError):
                convert_docx(buffer, "pdf")

            # Buffer should be reset to start
            assert buffer.tell() == 0


class TestConversionError:
    """Tests for ConversionError exception."""

    def test_conversion_error_message(self):
        """Test ConversionError stores message."""
        error = ConversionError("Something went wrong")
        assert str(error) == "Something went wrong"

    def test_libreoffice_not_found_is_conversion_error(self):
        """Test LibreOfficeNotFoundError is subclass of ConversionError."""
        assert issubclass(LibreOfficeNotFoundError, ConversionError)


class TestUpdateFieldsInDocx:
    """Tests for update_fields_in_docx function."""

    @patch("django_docxtpl.converters.find_libreoffice")
    def test_libreoffice_not_found(self, mock_find, rendered_docx_bytes):
        """Test that missing LibreOffice raises error."""
        mock_find.return_value = None

        with pytest.raises(LibreOfficeNotFoundError, match="LibreOffice not found"):
            update_fields_in_docx(rendered_docx_bytes)

    @patch("django_docxtpl.converters.find_libreoffice")
    def test_update_fields_success(self, mock_find, rendered_docx_bytes, tmp_path):
        """Test successful field update."""
        import django_docxtpl.converters as converters_module

        mock_find.return_value = Path("/usr/bin/soffice")

        def side_effect_run(*args, **kwargs):
            # Simulate LibreOffice writing the output file
            output_file = tmp_path / "input.docx"
            output_file.write_bytes(b"updated docx content")
            return MagicMock(returncode=0, stderr="", stdout="")

        # Create the mock for TemporaryDirectory as a context manager
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=str(tmp_path))
        mock_cm.__exit__ = MagicMock(return_value=False)

        with patch.object(
            converters_module.subprocess, "run", side_effect=side_effect_run
        ):
            with patch.object(
                converters_module.tempfile, "TemporaryDirectory", return_value=mock_cm
            ):
                result = update_fields_in_docx(rendered_docx_bytes)

                assert result == b"updated docx content"

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("subprocess.run")
    def test_update_fields_failure(self, mock_run, mock_find, rendered_docx_bytes):
        """Test field update failure handling."""
        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.return_value = MagicMock(
            returncode=1, stderr="Error: update failed", stdout=""
        )

        with pytest.raises(ConversionError, match="update failed"):
            update_fields_in_docx(rendered_docx_bytes)

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("subprocess.run")
    def test_update_fields_timeout(self, mock_run, mock_find, rendered_docx_bytes):
        """Test field update timeout handling."""
        import subprocess

        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="soffice", timeout=60)

        with pytest.raises(ConversionError, match="timed out"):
            update_fields_in_docx(rendered_docx_bytes, timeout=60)

    def test_accepts_bytesio(self, rendered_docx_bytes):
        """Test that function accepts BytesIO input."""
        buffer = BytesIO(rendered_docx_bytes)

        with patch("django_docxtpl.converters.find_libreoffice") as mock_find:
            mock_find.return_value = None

            # Should raise LibreOfficeNotFoundError, not TypeError
            with pytest.raises(LibreOfficeNotFoundError):
                update_fields_in_docx(buffer)

            # Buffer should be reset to start
            assert buffer.tell() == 0


class TestConvertDocxWithUpdateFields:
    """Tests for convert_docx with update_fields parameter."""

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("django_docxtpl.converters.update_fields_in_docx")
    @patch("subprocess.run")
    def test_update_fields_called_when_true(
        self, mock_run, mock_update, mock_find, rendered_docx_bytes, tmp_path
    ):
        """Test that update_fields_in_docx is called when update_fields=True."""
        mock_find.return_value = Path("/usr/bin/soffice")
        mock_update.return_value = b"updated content"
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        with patch("tempfile.TemporaryDirectory") as mock_tempdir:
            mock_tempdir.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            mock_tempdir.return_value.__exit__ = MagicMock(return_value=False)

            # Create the expected output file
            output_file = tmp_path / "input.pdf"
            output_file.write_bytes(b"%PDF-1.4 fake pdf content")

            convert_docx(rendered_docx_bytes, "pdf", update_fields=True)

            mock_update.assert_called_once()

    @patch("django_docxtpl.converters.find_libreoffice")
    @patch("django_docxtpl.converters.update_fields_in_docx")
    @patch("subprocess.run")
    def test_update_fields_not_called_when_false(
        self, mock_run, mock_update, mock_find, rendered_docx_bytes, tmp_path
    ):
        """Test that update_fields_in_docx is not called when update_fields=False."""
        mock_find.return_value = Path("/usr/bin/soffice")
        mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")

        with patch("tempfile.TemporaryDirectory") as mock_tempdir:
            mock_tempdir.return_value.__enter__ = MagicMock(return_value=str(tmp_path))
            mock_tempdir.return_value.__exit__ = MagicMock(return_value=False)

            # Create the expected output file
            output_file = tmp_path / "input.pdf"
            output_file.write_bytes(b"%PDF-1.4 fake pdf content")

            convert_docx(rendered_docx_bytes, "pdf", update_fields=False)

            mock_update.assert_not_called()

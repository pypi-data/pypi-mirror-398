# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2025-12-27

### Changed
- **Breaking:** Callable context now receives two parameters: `(docx, tmp_dir)` instead of just `(docx)`
- `get_context_data_with_docx(docx, tmp_dir, **kwargs)` method signature updated to include `tmp_dir` parameter

### Added
- `tmp_dir` parameter (a `Path` to a temporary directory) passed to callable context functions
- Temporary directory is automatically created before rendering and cleaned up after
- Enables generating temporary files (e.g., chart images) that are needed during template rendering

## [0.7.0] - 2025-12-27

- Fix readme documentation

## [0.6.0] - 2025-12-27

- Unpublished

### Added
- `autoescape` parameter in `DocxTemplateResponse` to enable Jinja2 autoescaping when rendering templates (default is `False`)
- `autoescape` attribute and `get_autoescape()` method in `DocxTemplateResponseMixin` for class-based views
- `autoescape` parameter in `render_to_file()` for background task document generation

## [0.5.0] - 2025-12-16

### Added
- `jinja_env` parameter in `DocxTemplateResponse` to support custom Jinja2 filters, globals, and configuration
- `jinja_env` attribute and `get_jinja_env()` method in `DocxTemplateResponseMixin` for class-based views
- `jinja_env` attribute documented in `DocxTemplateView` and `DocxTemplateDetailView`

## [0.4.0] - 2025-12-16

### Added
- `jinja_env` parameter in `render_to_file()` to support custom Jinja2 filters, globals, and configuration

## [0.3.0] - 2024-12-14

### Added
- `get_context_data_with_docx(docx, **kwargs)` method in `DocxTemplateResponseMixin` for building context with access to the `DocxTemplate` instance (enables `InlineImage`, `RichText`, `Subdoc`, etc.)
- Support for callable context in `DocxTemplateResponse` - context can now be a function that receives the `DocxTemplate` instance
- Support for callable context in `render_to_file()` utility function
- `ContextType` type alias exported for type hints
- Comprehensive documentation for working with `InlineImage` in class-based views, function-based views, and background tasks

### Changed
- `DocxTemplateView.get()` now passes URL kwargs to context methods
- `DocxTemplateDetailView.get()` now passes URL kwargs to context methods
- `render_to_response()` now builds a context callable internally when no explicit context is provided

## [0.2.0] - 2024-12-14

### Added
- `update_fields` parameter to update TOC, charts, cross-references, and other dynamic fields using LibreOffice
- `update_fields_in_docx()` function to process DOCX files and update all fields
- `render_to_file()` utility function for generating documents to disk (useful for background tasks with Celery, Huey, RQ)
- `get_update_fields()` method in mixins for dynamic control
- LibreOffice installation instructions for headless servers (Ubuntu, Alpine, RHEL)
- Performance considerations and task queue examples in documentation

### Changed
- `convert_docx()` now accepts `update_fields` parameter
- `DocxTemplateResponse` now accepts `update_fields` parameter
- `DocxTemplateView` and `DocxTemplateDetailView` now support `update_fields` attribute

## [0.1.0] - 2024-12-14

### Added
- Initial release
- `DocxTemplateResponse` for function-based views
- `DocxTemplateView` for class-based views
- `DocxTemplateDetailView` for model-based document generation
- `DocxTemplateResponseMixin` for custom view classes
- Multi-format output support: DOCX, PDF, ODT, HTML, TXT
- Automatic LibreOffice detection
- Automatic file extension based on output format
- Django settings: `DOCXTPL_TEMPLATE_DIR`, `DOCXTPL_LIBREOFFICE_PATH`
- Full type hints support
- Comprehensive test suite

### Dependencies
- Python >= 3.10
- Django >= 4.2
- docxtpl >= 0.16

[Unreleased]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ctrl-alt-d/django-docxtpl/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ctrl-alt-d/django-docxtpl/releases/tag/v0.1.0

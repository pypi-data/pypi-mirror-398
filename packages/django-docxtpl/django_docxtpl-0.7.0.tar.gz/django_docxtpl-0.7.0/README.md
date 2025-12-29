# django-docxtpl

[![PyPI version](https://badge.fury.io/py/django-docxtpl.svg)](https://badge.fury.io/py/django-docxtpl)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-docxtpl.svg)](https://pypi.org/project/django-docxtpl/)
[![Django Versions](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1-blue.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Django integration for [docxtpl](https://docxtpl.readthedocs.io/) - generate documents from Word templates with Jinja2 syntax and export to multiple formats.

## Features

- 📝 Generate Word documents (.docx) from templates using Jinja2 syntax
- 📄 Export to multiple formats: **DOCX**, **PDF**, **ODT**, **HTML**, **TXT**
- 🔄 Automatic format conversion via LibreOffice headless
- 📑 **Update Table of Contents (TOC), charts, and dynamic fields** automatically
- 🎯 Simple API with `DocxTemplateResponse`
- 🏗️ Class-based views with `DocxTemplateView` and `DocxTemplateDetailView`
- ⚡ Automatic file extension based on output format

## Installation

```bash
pip install django-docxtpl
```

For PDF and other format conversions, you'll need LibreOffice installed:

```bash
# Ubuntu/Debian
sudo apt install libreoffice-core libreoffice-writer

# Ubuntu/Debian (headless server - minimal installation)
sudo apt install libreoffice-core libreoffice-writer-nogui

# macOS
brew install --cask libreoffice

# Alpine Linux (Docker)
apk add libreoffice-writer

# RHEL/CentOS/Fedora
sudo dnf install libreoffice-writer
```

## Quick Start

### 1. Add to INSTALLED_APPS (optional)

```python
INSTALLED_APPS = [
    ...
    "django_docxtpl",
]
```

### 2. Create a Word template

Create a `.docx` file with Jinja2 placeholders:

```
Hello {{ name }}!

Your order #{{ order_number }} has been confirmed.
```

### 3. Use in your views

**Function-based view:**

```python
from django_docxtpl import DocxTemplateResponse

def generate_document(request):
    context = {
        "name": "John Doe",
        "order_number": "12345",
    }
    return DocxTemplateResponse(
        request,
        template="documents/order.docx",
        context=context,
        filename="order_confirmation",  # Extension added automatically
        output_format="pdf",  # or "docx", "odt", "html", "txt"
    )
```

**Class-based view:**

```python
from django_docxtpl import DocxTemplateView

class OrderDocumentView(DocxTemplateView):
    template_name = "documents/order.docx"
    filename = "order_confirmation"
    output_format = "pdf"

    def get_context_data(self, **kwargs):
        return {
            "name": self.request.user.get_full_name(),
            "order_number": kwargs.get("order_id"),
        }
```

**Detail view for model instances:**

```python
from django_docxtpl import DocxTemplateDetailView

class InvoiceDocumentView(DocxTemplateDetailView):
    model = Invoice
    template_name = "documents/invoice.docx"
    output_format = "pdf"
    context_object_name = "invoice"

    def get_filename(self):
        return f"invoice_{self.object.number}"
```

## Configuration

Add these optional settings to your `settings.py`:

```python
# Directory where your .docx templates are stored
DOCXTPL_TEMPLATE_DIR = BASE_DIR / "docx_templates"

# Path to LibreOffice executable (auto-detected if not set)
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"
```

## Supported Output Formats

| Format | Extension | Requires LibreOffice |
|--------|-----------|---------------------|
| DOCX   | `.docx`   | No (Yes if `update_fields=True`) |
| PDF    | `.pdf`    | Yes                 |
| ODT    | `.odt`    | Yes                 |
| HTML   | `.html`   | Yes                 |
| TXT    | `.txt`    | Yes                 |

## Template Syntax

django-docxtpl uses [docxtpl](https://docxtpl.readthedocs.io/) which supports full Jinja2 syntax:

```
{% for item in items %}
- {{ item.name }}: {{ item.price }}€
{% endfor %}

Total: {{ total }}€

{% if discount %}
Discount applied: {{ discount }}%
{% endif %}
```

See the [docxtpl documentation](https://docxtpl.readthedocs.io/) for advanced features like images, tables, and rich text.

## Updating TOC and Charts

If your template contains a Table of Contents (TOC), charts, or other dynamic fields that need to be updated after rendering, use the `update_fields` parameter:

```python
# Function-based view
return DocxTemplateResponse(
    request,
    template="reports/annual_report.docx",
    context=context,
    output_format="pdf",
    update_fields=True,  # Updates TOC, charts, page numbers, etc.
)

# Class-based view
class AnnualReportView(DocxTemplateView):
    template_name = "reports/annual_report.docx"
    output_format = "pdf"
    update_fields = True
```

**Note:** This feature requires LibreOffice, even when output format is DOCX.

## Working with Images (InlineImage)

To insert images in your documents, use docxtpl's `InlineImage`. Since it requires access to the `DocxTemplate` instance, use `get_context_data_with_docx()` in class-based views or a callable context in function-based views:

**Class-based view:**

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import DocxTemplateView

class ReportWithLogoView(DocxTemplateView):
    template_name = "reports/report.docx"
    output_format = "pdf"

    def get_context_data_with_docx(self, docx, **kwargs):
        """Build context with access to DocxTemplate instance."""
        return {
            "title": "Annual Report",
            "logo": InlineImage(docx, "static/logo.png", width=Mm(30)),
        }
```

**Function-based view:**

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import DocxTemplateResponse

def report_with_image(request):
    def build_context(docx):
        return {
            "title": "Report",
            "logo": InlineImage(docx, "static/logo.png", width=Mm(30)),
        }

    return DocxTemplateResponse(
        request,
        template="reports/report.docx",
        context=build_context,  # Callable receives DocxTemplate instance
        output_format="pdf",
    )
```

See the [advanced documentation](docs/advanced.md#working-with-images-inlineimage) for more examples.

## Performance Considerations

Document generation, especially PDF conversion with LibreOffice, can be slow (1-5 seconds per document). For production environments, consider:

1. **Use a task queue** - Offload document generation to background workers using [Celery](https://docs.celeryq.dev/), [Django-RQ](https://github.com/rq/django-rq), or [Huey](https://huey.readthedocs.io/):

Example 1:

```python
# tasks.py (Huey example)
from huey.contrib.djhuey import task
from django.core.files.base import ContentFile
from django_docxtpl.converters import convert_docx
from docxtpl import DocxTemplate
from io import BytesIO

@task()
def generate_report_pdf(report_id):
    report = Report.objects.get(pk=report_id)
    
    doc = DocxTemplate("templates/report.docx")
    doc.render({"report": report})
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    pdf_content = convert_docx(buffer, "pdf", update_fields=True)
    
    # Save to storage, send email, etc.
    report.pdf_file.save(f"report_{report_id}.pdf", ContentFile(pdf_content))
```


Example 2:

```python
# tasks.py (Huey example) - Using render_to_file utility
from huey.contrib.djhuey import task
from django_docxtpl import render_to_file

@task()
def generate_report_to_disk(output_dir, filename, context):
    """Generate a document and save it to disk."""
    output_path = render_to_file(
        template="reports/monthly.docx",
        context=context,
        output_dir=output_dir,
        filename=filename,
        output_format="pdf",
        update_fields=True,
    )
    return str(output_path)
```



2. **Serve DOCX when possible** - Skip LibreOffice conversion for faster response times
3. **Cache generated documents** - Store frequently requested documents

## API Reference

### DocxTemplateResponse

```python
DocxTemplateResponse(
    request,
    template,           # Path to .docx template
    context=None,       # Template context dict or callable(docx) -> dict
    filename="document",# Output filename (without extension)
    output_format="docx",# Output format
    as_attachment=True, # Download as attachment or inline
    update_fields=False,# Update TOC, charts, and dynamic fields
    autoescape=False,   # Enable Jinja2 autoescaping
)
```

### DocxTemplateView

Class attributes:
- `template_name` - Path to .docx template
- `filename` - Output filename (default: "document")
- `output_format` - Output format (default: "docx")
- `as_attachment` - Serve as attachment (default: True)
- `update_fields` - Update TOC, charts, and dynamic fields (default: False)
- `autoescape` - Enable Jinja2 autoescaping (default: False)

Override methods:
- `get_template_name()` - Dynamic template selection
- `get_filename()` - Dynamic filename
- `get_output_format()` - Dynamic format selection
- `get_update_fields()` - Dynamic field update control
- `get_autoescape()` - Dynamic autoescape control
- `get_context_data(**kwargs)` - Provide template context
- `get_context_data_with_docx(docx, **kwargs)` - Provide context with DocxTemplate access (for InlineImage, etc.)

### DocxTemplateDetailView

Same as `DocxTemplateView` plus:
- `model` - Django model class
- `pk_url_kwarg` - URL kwarg for primary key (default: "pk")
- `slug_url_kwarg` - URL kwarg for slug (default: "slug")
- `slug_field` - Model field for slug lookup (default: "slug")
- `context_object_name` - Context variable name for object

## Error Handling

```python
from django_docxtpl import ConversionError, LibreOfficeNotFoundError

try:
    response = DocxTemplateResponse(request, template="doc.docx", output_format="pdf")
except LibreOfficeNotFoundError:
    # LibreOffice not installed
    pass
except ConversionError as e:
    # Conversion failed
    pass
```

## Development

```bash
# Clone the repository
git clone https://github.com/ctrl-alt-d/django-docxtpl.git
cd django-docxtpl

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with development dependencies
pip install flit
flit install -s --deps develop

# Run tests
pytest

# Run linter
ruff check .

# Format code
ruff format .
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- [docxtpl](https://github.com/elapouya/python-docxtpl) - Python library for generating docx documents
- [python-docx](https://github.com/python-openxml/python-docx) - Python library for Word documents

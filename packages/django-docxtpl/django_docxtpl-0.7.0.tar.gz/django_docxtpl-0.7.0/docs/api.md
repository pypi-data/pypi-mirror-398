# API Reference

Complete API documentation for django-docxtpl.

## Response Classes

### DocxTemplateResponse

An `HttpResponse` subclass that renders a DOCX template and returns it as a downloadable document.

```python
from django_docxtpl import DocxTemplateResponse

response = DocxTemplateResponse(
    request,
    template,
    context=None,
    filename="document",
    output_format="docx",
    as_attachment=True,
    update_fields=False,
    jinja_env=None,
    **kwargs
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `request` | `HttpRequest` | required | The Django request object |
| `template` | `str \| Path` | required | Path to the DOCX template file |
| `context` | `dict \| Callable \| None` | `None` | Context dictionary or callable that receives `DocxTemplate` instance |
| `filename` | `str` | `"document"` | Output filename (without extension) |
| `output_format` | `OutputFormat` | `"docx"` | Output format: `"docx"`, `"pdf"`, `"odt"`, `"html"`, `"txt"` |
| `as_attachment` | `bool` | `True` | If `True`, browser downloads file; if `False`, displays inline |
| `update_fields` | `bool` | `False` | If `True`, updates TOC, charts, and other dynamic fields using LibreOffice |
| `jinja_env` | `Environment \| None` | `None` | Custom Jinja2 Environment with filters, globals, or other configuration |
| `autoescape` | `bool` | `False` | If `True`, enables Jinja2 autoescaping to escape HTML/XML special characters |
| `**kwargs` | | | Additional arguments passed to `HttpResponse` |

**Context as callable:** When `context` is a callable, it receives the `DocxTemplate` instance as its argument. This allows creating `InlineImage`, `RichText`, and other objects that require the template instance:

```python
from docxtpl import InlineImage
from docx.shared import Mm

def build_context(docx):
    return {
        "title": "Report",
        "logo": InlineImage(docx, "logo.png", width=Mm(30)),
    }

response = DocxTemplateResponse(
    request,
    template="report.docx",
    context=build_context,
)
```

#### Example

```python
from django_docxtpl import DocxTemplateResponse

def invoice_pdf(request, invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)
    
    return DocxTemplateResponse(
        request,
        template="invoices/template.docx",
        context={
            "invoice": invoice,
            "items": invoice.items.all(),
            "company": get_company_info(),
        },
        filename=f"invoice_{invoice.number}",
        output_format="pdf",
    )
```

## View Classes

### DocxTemplateView

A class-based view for generating documents. Inherits from Django's `View` and `DocxTemplateResponseMixin`.

```python
from django_docxtpl import DocxTemplateView

class MyDocumentView(DocxTemplateView):
    template_name = "path/to/template.docx"
    filename = "document"
    output_format = "docx"
    as_attachment = True

    def get_context_data(self, **kwargs):
        return {"key": "value"}
```

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `template_name` | `str \| Path \| None` | `None` | Path to the DOCX template |
| `filename` | `str` | `"document"` | Output filename (without extension) |
| `output_format` | `OutputFormat` | `"docx"` | Output format |
| `as_attachment` | `bool` | `True` | Download as attachment |
| `update_fields` | `bool` | `False` | Update TOC, charts, and dynamic fields |
| `autoescape` | `bool` | `False` | Enable Jinja2 autoescaping |
| `jinja_env` | `Environment \| None` | `None` | Custom Jinja2 Environment with filters |

#### Methods

##### get_template_name() → str | Path

Returns the template path. Override to dynamically determine the template.

```python
def get_template_name(self):
    if self.request.GET.get("format") == "detailed":
        return "reports/detailed.docx"
    return "reports/summary.docx"
```

##### get_filename() → str

Returns the output filename. Override for dynamic filenames.

```python
def get_filename(self):
    return f"report_{date.today().isoformat()}"
```

##### get_output_format() → OutputFormat

Returns the output format. Override for dynamic format selection.

```python
def get_output_format(self):
    return self.request.GET.get("format", "pdf")
```

##### get_update_fields() → bool

Returns whether to update dynamic fields (TOC, charts, etc.). Override for dynamic control.

```python
def get_update_fields(self):
    # Only update fields when generating PDF
    return self.get_output_format() == "pdf"
```

##### get_jinja_env() → Environment | None

Returns a custom Jinja2 Environment for template rendering. Override to add custom filters, globals, or other Jinja2 configuration.

```python
from jinja2 import Environment

def get_jinja_env(self):
    def format_currency(value):
        return f"{value:,.2f} €".replace(",", ".")
    
    env = Environment(autoescape=True)
    env.filters["currency"] = format_currency
    return env
```

##### get_autoescape() → bool

Returns whether to enable Jinja2 autoescaping when rendering. Override for dynamic control.

```python
def get_autoescape(self):
    # Enable autoescaping when context contains user input
    return self.has_user_content
```

##### get_context_data(**kwargs) → dict

Returns the context dictionary for template rendering. Use this for simple contexts without images.

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["user"] = self.request.user
    context["data"] = self.get_report_data()
    return context
```

##### get_context_data_with_docx(docx, **kwargs) → dict | None

Returns the context dictionary with access to the `DocxTemplate` instance. Use this when you need to create `InlineImage`, `RichText`, `Subdoc`, or other docxtpl objects that require the template instance.

If this method returns a non-`None` value, it takes precedence over `get_context_data()`.

```python
from docxtpl import InlineImage, RichText
from docx.shared import Mm

def get_context_data_with_docx(self, docx, **kwargs):
    return {
        "title": "Report with Images",
        "logo": InlineImage(docx, "static/logo.png", width=Mm(30)),
        "signature": InlineImage(docx, "static/signature.png", width=Mm(50)),
        "styled_text": RichText("Important", bold=True, color="FF0000"),
    }
```

**Parameters:**
- `docx` (`DocxTemplate`): The template instance being rendered
- `**kwargs`: URL keyword arguments (e.g., `pk`, `slug`)

##### render_to_response(context=None) → HttpResponse

Renders the template and returns the response. Usually called automatically.

### DocxTemplateDetailView

A view for generating documents from a single model instance. Similar to Django's `DetailView`.

```python
from django_docxtpl import DocxTemplateDetailView

class InvoiceDocumentView(DocxTemplateDetailView):
    model = Invoice
    template_name = "invoices/template.docx"
    output_format = "pdf"
    context_object_name = "invoice"

    def get_filename(self):
        return f"invoice_{self.object.number}"
```

#### Additional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `type \| None` | `None` | The Django model class |
| `pk_url_kwarg` | `str` | `"pk"` | URL keyword argument for primary key |
| `slug_url_kwarg` | `str` | `"slug"` | URL keyword argument for slug |
| `slug_field` | `str` | `"slug"` | Model field for slug lookup |
| `context_object_name` | `str \| None` | `None` | Context variable name for the object |

#### Additional Methods

##### get_object() → Model

Retrieves the model instance based on URL parameters.

```python
def get_object(self):
    obj = super().get_object()
    # Add permission check
    if obj.user != self.request.user:
        raise PermissionDenied
    return obj
```

##### get_context_object_name() → str

Returns the name used for the object in context.

## Mixins

### DocxTemplateResponseMixin

A mixin that provides document rendering functionality. Use with Django's `View` or other view classes.

```python
from django.views import View
from django_docxtpl import DocxTemplateResponseMixin

class CustomView(DocxTemplateResponseMixin, View):
    template_name = "template.docx"

    def get(self, request):
        context = self.get_context_data()
        return self.render_to_response(context)
```

## Utility Functions

### get_content_type(output_format) → str

Returns the MIME content type for a format.

```python
from django_docxtpl.utils import get_content_type

get_content_type("pdf")  # "application/pdf"
get_content_type("docx")  # "application/vnd.openxmlformats-..."
```

### get_extension(output_format) → str

Returns the file extension for a format.

```python
from django_docxtpl.utils import get_extension

get_extension("pdf")  # ".pdf"
get_extension("docx")  # ".docx"
```

### get_filename_with_extension(filename, output_format) → str

Adds the correct extension to a filename.

```python
from django_docxtpl.utils import get_filename_with_extension

get_filename_with_extension("report", "pdf")  # "report.pdf"
get_filename_with_extension("doc.docx", "pdf")  # "doc.pdf"
```

### find_libreoffice() → Path | None

Finds the LibreOffice executable.

```python
from django_docxtpl.utils import find_libreoffice

path = find_libreoffice()
if path:
    print(f"Found LibreOffice at: {path}")
```

### get_template_dir() → Path | None

Returns the configured template directory.

```python
from django_docxtpl.utils import get_template_dir

template_dir = get_template_dir()
```

## Conversion Functions

### convert_docx(docx_content, output_format, timeout=60, update_fields=False) → bytes

Converts DOCX content to another format using LibreOffice.

```python
from django_docxtpl.converters import convert_docx

# Convert DOCX bytes to PDF
with open("document.docx", "rb") as f:
    docx_bytes = f.read()

pdf_bytes = convert_docx(docx_bytes, "pdf")

with open("document.pdf", "wb") as f:
    f.write(pdf_bytes)

# Convert with field updates (TOC, charts)
pdf_bytes = convert_docx(docx_bytes, "pdf", update_fields=True)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `docx_content` | `bytes \| BytesIO` | required | DOCX content |
| `output_format` | `OutputFormat` | required | Target format |
| `timeout` | `int` | `60` | Conversion timeout in seconds |
| `update_fields` | `bool` | `False` | Update TOC, charts, and dynamic fields before conversion |

### update_fields_in_docx(docx_content, timeout=60) → bytes

Updates all dynamic fields in a DOCX document using LibreOffice, including:
- Table of Contents (TOC)
- Charts and graphs
- Cross-references
- Page numbers
- Date fields

```python
from django_docxtpl import update_fields_in_docx

# Read a DOCX file
with open("document_with_toc.docx", "rb") as f:
    docx_bytes = f.read()

# Update all fields
updated_bytes = update_fields_in_docx(docx_bytes)

# Save the updated document
with open("document_updated.docx", "wb") as f:
    f.write(updated_bytes)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `docx_content` | `bytes \| BytesIO` | required | DOCX content |
| `timeout` | `int` | `60` | Operation timeout in seconds |

### render_to_file(template, context, output_dir, filename, ...) → Path

Renders a DOCX template and saves it directly to disk. This function is ideal for background tasks (Celery, Huey, RQ) where you need to generate documents without an HTTP response.

```python
from django_docxtpl import render_to_file

# Generate a PDF report
output_path = render_to_file(
    template="reports/monthly.docx",
    context={"month": "December", "data": report_data},
    output_dir="/var/reports",
    filename="monthly_report_2024",
    output_format="pdf",
    update_fields=True,
)

print(f"Report saved to: {output_path}")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `template` | `str \| Path` | required | Path to the DOCX template (absolute or relative to `DOCXTPL_TEMPLATE_DIR`) |
| `context` | `dict \| Callable` | required | Context dictionary or callable that receives `DocxTemplate` instance |
| `output_dir` | `str \| Path` | required | Directory where the output file will be saved |
| `filename` | `str` | required | Output filename (without extension) |
| `output_format` | `OutputFormat` | `"docx"` | Output format: `"docx"`, `"pdf"`, `"odt"`, `"html"`, `"txt"` |
| `update_fields` | `bool` | `False` | Update TOC, charts, and dynamic fields |
| `jinja_env` | `Environment \| None` | `None` | Custom Jinja2 Environment with filters, globals, or other configuration |
| `autoescape` | `bool` | `False` | Enable Jinja2 autoescaping to escape HTML/XML special characters |

**Context as callable:** When `context` is a callable, it receives the `DocxTemplate` instance, allowing you to use `InlineImage` and other objects that require the template:

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import render_to_file

def build_context(docx):
    return {
        "title": "Report",
        "chart": InlineImage(docx, "chart.png", width=Mm(150)),
    }

output_path = render_to_file(
    template="reports/monthly.docx",
    context=build_context,
    output_dir="/var/reports",
    filename="report",
    output_format="pdf",
)
```

**Custom Jinja2 filters:** Use the `jinja_env` parameter to add custom filters:

```python
from jinja2 import Environment
from django_docxtpl import render_to_file

def format_currency(value):
    return f"{value:,.2f} €".replace(",", ".")

jinja_env = Environment(autoescape=True)
jinja_env.filters["currency"] = format_currency

output_path = render_to_file(
    template="invoices/template.docx",
    context={"total": 1234.56},
    output_dir="/var/invoices",
    filename="invoice",
    output_format="pdf",
    jinja_env=jinja_env,
)
```

In your template, use the filter: `{{ total|currency }}` → `1.234,56 €`

#### Returns

`Path` - Absolute path to the generated file.

#### Raises

- `FileNotFoundError` - If the template file doesn't exist
- `LibreOfficeNotFoundError` - If LibreOffice is needed but not found
- `ConversionError` - If the conversion fails

#### Example with Huey

```python
from huey import crontab
from huey.contrib.djhuey import task
from django_docxtpl import render_to_file

@task()
def generate_monthly_report(year: int, month: int) -> str:
    """Background task to generate monthly report."""
    report_data = compile_monthly_data(year, month)
    
    output_path = render_to_file(
        template="reports/monthly.docx",
        context={
            "year": year,
            "month": month,
            "data": report_data,
        },
        output_dir=f"/var/reports/{year}",
        filename=f"report_{year}_{month:02d}",
        output_format="pdf",
        update_fields=True,
    )
    
    return str(output_path)
```

## Exceptions

### ConversionError

Base exception for conversion errors.

```python
from django_docxtpl import ConversionError

try:
    response = DocxTemplateResponse(...)
except ConversionError as e:
    logger.error(f"Document conversion failed: {e}")
```

### LibreOfficeNotFoundError

Raised when LibreOffice is not found and format conversion is needed.

```python
from django_docxtpl import LibreOfficeNotFoundError

try:
    response = DocxTemplateResponse(..., output_format="pdf")
except LibreOfficeNotFoundError:
    # Fall back to DOCX
    response = DocxTemplateResponse(..., output_format="docx")
```

## Type Aliases

### OutputFormat

A string literal type for supported output formats.

```python
from django_docxtpl import OutputFormat

format: OutputFormat = "pdf"  # Valid values: "docx", "pdf", "odt", "html", "txt"
```

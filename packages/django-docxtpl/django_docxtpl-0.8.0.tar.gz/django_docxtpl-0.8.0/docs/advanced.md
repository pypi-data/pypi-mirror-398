# Advanced Usage

This guide covers advanced scenarios and best practices for using django-docxtpl.

## Dynamic Template Selection

Select templates based on request parameters or model data:

```python
from django_docxtpl import DocxTemplateView

class ReportView(DocxTemplateView):
    def get_template_name(self):
        report_type = self.kwargs.get("report_type", "summary")
        templates = {
            "summary": "reports/summary.docx",
            "detailed": "reports/detailed.docx",
            "executive": "reports/executive.docx",
        }
        return templates.get(report_type, templates["summary"])

    def get_context_data(self, **kwargs):
        return {
            "data": self.get_report_data(),
            "generated_at": timezone.now(),
        }
```

## Dynamic Format Selection

Let users choose the output format:

```python
from django_docxtpl import DocxTemplateView

class DocumentView(DocxTemplateView):
    template_name = "documents/template.docx"

    def get_output_format(self):
        format = self.request.GET.get("format", "pdf")
        if format not in ["docx", "pdf", "odt"]:
            format = "pdf"
        return format

    def get_filename(self):
        return f"document_{timezone.now().strftime('%Y%m%d')}"
```

**URL usage:**
- `/document/?format=pdf` → Downloads PDF
- `/document/?format=docx` → Downloads DOCX

## Updating Table of Contents and Charts

When your template contains a Table of Contents (TOC), charts, or other dynamic fields, these need to be updated after rendering with new content. Use the `update_fields` parameter to have LibreOffice regenerate these fields:

### Class-Based View

```python
from django_docxtpl import DocxTemplateView

class ReportWithTOCView(DocxTemplateView):
    template_name = "reports/report_with_toc.docx"
    filename = "report"
    output_format = "pdf"
    update_fields = True  # Updates TOC, charts, page numbers, etc.

    def get_context_data(self, **kwargs):
        return {
            "title": "Annual Report",
            "chapters": self.get_chapters(),
        }
```

### Dynamic Field Update

```python
from django_docxtpl import DocxTemplateView

class DocumentView(DocxTemplateView):
    template_name = "documents/template.docx"

    def get_update_fields(self):
        # Only update fields when generating PDF
        return self.get_output_format() != "docx"
```

### Function-Based View

```python
from django_docxtpl import DocxTemplateResponse

def report_with_toc(request):
    return DocxTemplateResponse(
        request,
        template="reports/report_with_toc.docx",
        context={"title": "My Report", "sections": get_sections()},
        filename="report",
        output_format="pdf",
        update_fields=True,  # Regenerates TOC and charts
    )
```

### Standalone Function

For processing documents outside of a view:

```python
from django_docxtpl import update_fields_in_docx

# Read a DOCX file
with open("document.docx", "rb") as f:
    docx_content = f.read()

# Update all fields (TOC, charts, cross-references, etc.)
updated_content = update_fields_in_docx(docx_content)

# Save the updated document
with open("document_updated.docx", "wb") as f:
    f.write(updated_content)
```

**What gets updated:**
- Table of Contents (TOC)
- Charts and graphs
- Cross-references
- Page numbers
- Date fields
- Other calculated fields

**Note:** The `update_fields` feature requires LibreOffice, even when the output format is DOCX.

## Custom Jinja2 Filters

docxtpl uses Jinja2 for template rendering. You can add custom filters to format data in your templates.

### Function-Based View

```python
from jinja2 import Environment
from django_docxtpl import DocxTemplateResponse

def format_currency(value):
    """Format number as currency: 1234.56 → 1.234,56 €"""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def format_thousands(value):
    """Format number with thousand separators: 1234567 → 1.234.567"""
    return f"{value:,.0f}".replace(",", ".")

def invoice_view(request, invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)

    # Create custom Jinja2 Environment
    jinja_env = Environment(autoescape=True)
    jinja_env.filters["currency"] = format_currency
    jinja_env.filters["thousands"] = format_thousands

    return DocxTemplateResponse(
        request,
        template="invoices/template.docx",
        context={
            "invoice": invoice,
            "total": invoice.total,
            "quantity": invoice.quantity,
        },
        filename=f"invoice_{invoice.number}",
        output_format="pdf",
        jinja_env=jinja_env,
    )
```

In your template:
```
Total: {{ total|currency }}
Quantity: {{ quantity|thousands }}
```

Output:
```
Total: 1.234,56 €
Quantity: 1.234.567
```

### Class-Based View

```python
from jinja2 import Environment
from django_docxtpl import DocxTemplateView

def format_currency(value):
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

class InvoiceView(DocxTemplateView):
    template_name = "invoices/template.docx"
    output_format = "pdf"

    def get_jinja_env(self):
        env = Environment(autoescape=True)
        env.filters["currency"] = format_currency
        return env

    def get_context_data(self, **kwargs):
        invoice = Invoice.objects.get(pk=kwargs.get("pk"))
        return {"invoice": invoice, "total": invoice.total}
```

### Class-Based View with Attribute

```python
from jinja2 import Environment
from django_docxtpl import DocxTemplateView

# Create environment at module level (reusable)
def format_currency(value):
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

invoice_jinja_env = Environment(autoescape=True)
invoice_jinja_env.filters["currency"] = format_currency

class InvoiceView(DocxTemplateView):
    template_name = "invoices/template.docx"
    output_format = "pdf"
    jinja_env = invoice_jinja_env  # Set as class attribute

    def get_context_data(self, **kwargs):
        return {"total": 1234.56}
```

### Background Tasks (render_to_file)

```python
from jinja2 import Environment
from django_docxtpl import render_to_file

def format_date_catalan(value):
    months = ["gener", "febrer", "març", "abril", "maig", "juny",
              "juliol", "agost", "setembre", "octubre", "novembre", "desembre"]
    return f"{value.day} de {months[value.month-1]} del {value.year}"

jinja_env = Environment(autoescape=True)
jinja_env.filters["data_cat"] = format_date_catalan

output_path = render_to_file(
    template="reports/monthly.docx",
    context={"date": date.today(), "data": report_data},
    output_dir="/var/reports",
    filename="report",
    output_format="pdf",
    jinja_env=jinja_env,
)
```

In your template: `{{ date|data_cat }}` → `16 de desembre del 2025`

## Working with Images (InlineImage)

docxtpl supports inserting images into templates using `InlineImage`. Since `InlineImage` requires access to the `DocxTemplate` instance, django-docxtpl provides several ways to handle this.

First, add a placeholder in your template:

```
{{ logo }}
```

### Class-Based View (Recommended)

Use `get_context_data_with_docx()` to get access to the `DocxTemplate` instance and temporary directory:

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import DocxTemplateView

class DocumentWithLogoView(DocxTemplateView):
    template_name = "documents/letterhead.docx"
    filename = "report"
    output_format = "pdf"

    def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
        """Build context with access to DocxTemplate and temp directory."""
        return {
            "title": "Company Report",
            "logo": InlineImage(
                docx,
                image_descriptor="static/images/logo.png",
                width=Mm(30)
            ),
            "signature": InlineImage(
                docx,
                image_descriptor="static/images/signature.png",
                width=Mm(50)
            ),
        }
```

### Function-Based View

Use a callable as the `context` parameter:

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import DocxTemplateResponse

def document_with_image(request):
    def build_context(docx, tmp_dir):
        return {
            "title": "Company Report",
            "logo": InlineImage(
                docx,
                image_descriptor="static/images/logo.png",
                width=Mm(30)
            ),
        }

    return DocxTemplateResponse(
        request,
        template="documents/letterhead.docx",
        context=build_context,  # Pass the callable
        filename="report",
        output_format="pdf",
    )
```

### Background Tasks (render_to_file)

Use a callable with `render_to_file` for background document generation. The temporary directory is useful for generated images:

```python
from huey.contrib.djhuey import task
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import render_to_file

@task()
def generate_report_with_chart(report_id, output_dir):
    """Generate a report with embedded chart image."""
    report = Report.objects.get(pk=report_id)

    def build_context(docx, tmp_dir):
        # Generate chart to temp directory (auto-cleaned after render)
        chart_path = tmp_dir / "chart.png"
        generate_chart_image(report, chart_path)
        
        return {
            "title": report.title,
            "chart": InlineImage(docx, image_descriptor=str(chart_path), width=Mm(150)),
            "data": report.data,
        }

    output_path = render_to_file(
        template="reports/report_with_chart.docx",
        context=build_context,
        output_dir=output_dir,
        filename=f"report_{report_id}",
        output_format="pdf",
    )
    return str(output_path)
```

### Mixed Context (Simple Values + Images)

You can still use `get_context_data()` for simple values and only override `get_context_data_with_docx()` when you need images:

```python
from docxtpl import InlineImage
from docx.shared import Mm
from django_docxtpl import DocxTemplateView

class InvoiceView(DocxTemplateView):
    template_name = "invoices/invoice.docx"
    output_format = "pdf"

    def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
        # Get base context from parent (includes object for DetailView)
        invoice = Invoice.objects.get(pk=kwargs.get("pk"))
        
        return {
            "invoice": invoice,
            "company_logo": InlineImage(
                docx,
                image_descriptor="static/images/company_logo.png",
                width=Mm(40)
            ),
            "qr_code": InlineImage(
                docx,
                image_descriptor=invoice.qr_code_path,
                width=Mm(25)
            ),
        }
```

### Image from URL or BytesIO

`InlineImage` accepts file paths, URLs, or BytesIO objects:

```python
from io import BytesIO
import requests
from docxtpl import InlineImage
from docx.shared import Mm

def get_context_data_with_docx(self, docx, tmp_dir, **kwargs):
    # From file path
    logo = InlineImage(docx, "static/logo.png", width=Mm(30))
    
    # From BytesIO (e.g., generated image)
    chart_buffer = generate_chart_as_bytesio()
    chart = InlineImage(docx, chart_buffer, width=Mm(100))
    
    # From URL (download first)
    response = requests.get("https://example.com/image.png")
    image_buffer = BytesIO(response.content)
    remote_image = InlineImage(docx, image_buffer, width=Mm(50))
    
    # Using temp directory for generated files
    generated_path = tmp_dir / "generated.png"
    generate_image(generated_path)
    generated = InlineImage(docx, str(generated_path), width=Mm(60))
    
    return {
        "logo": logo,
        "chart": chart,
        "remote_image": remote_image,
        "generated": generated,
    }
```

## Working with Tables

### Simple Table

Template:
```
{% for row in table_data %}
{{ row.name }} | {{ row.value }}
{% endfor %}
```

### Complex Table with Merged Cells

For complex tables, create the table structure in Word, then use docxtpl's table syntax:

```
{%tr for item in items %}
{{ item.name }}
{{ item.quantity }}
{{ item.price }}
{%tr endfor %}
```

## Generating Multiple Documents

### Batch Generation

```python
import zipfile
from io import BytesIO
from django.http import HttpResponse
from django_docxtpl.response import DocxTemplateResponse

def batch_invoices(request, invoice_ids):
    """Generate multiple invoices as a ZIP file."""
    invoices = Invoice.objects.filter(pk__in=invoice_ids)
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for invoice in invoices:
            # Generate each document
            doc_response = DocxTemplateResponse(
                request,
                template="invoices/template.docx",
                context={"invoice": invoice},
                filename=f"invoice_{invoice.number}",
                output_format="pdf",
            )
            
            # Add to ZIP
            zip_file.writestr(
                f"invoice_{invoice.number}.pdf",
                doc_response.content
            )
    
    zip_buffer.seek(0)
    
    response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="invoices.zip"'
    return response
```

## Async Document Generation

For large documents or high-traffic scenarios, use Celery:

```python
# tasks.py
from celery import shared_task
from django_docxtpl.converters import convert_docx
from docxtpl import DocxTemplate
from io import BytesIO

@shared_task
def generate_report_async(report_id):
    """Generate a report asynchronously."""
    report = Report.objects.get(pk=report_id)
    
    # Render template
    doc = DocxTemplate("templates/reports/template.docx")
    doc.render({"report": report, "data": report.get_data()})
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    # Convert to PDF
    pdf_content = convert_docx(buffer, "pdf")
    
    # Save to storage
    report.pdf_file.save(
        f"report_{report.id}.pdf",
        ContentFile(pdf_content)
    )
    report.status = "completed"
    report.save()
    
    return report.id
```

```python
# views.py
from .tasks import generate_report_async

def request_report(request, report_id):
    """Start async report generation."""
    report = Report.objects.get(pk=report_id)
    report.status = "processing"
    report.save()
    
    generate_report_async.delay(report_id)
    
    return JsonResponse({"status": "processing", "report_id": report_id})
```

## Custom Response Headers

```python
from django_docxtpl import DocxTemplateResponse

def document_with_custom_headers(request):
    response = DocxTemplateResponse(
        request,
        template="template.docx",
        context={"data": "value"},
        filename="document",
    )
    
    # Add custom headers
    response["X-Document-Generated"] = timezone.now().isoformat()
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response
```

## Inline Display (No Download)

Display the document in the browser (works for PDF in modern browsers):

```python
DocxTemplateResponse(
    request,
    template="document.docx",
    context=context,
    filename="preview",
    output_format="pdf",
    as_attachment=False,  # Display inline instead of download
)
```

## Error Handling Best Practices

```python
from django.http import HttpResponseServerError
from django_docxtpl import (
    DocxTemplateResponse,
    ConversionError,
    LibreOfficeNotFoundError,
)
import logging

logger = logging.getLogger(__name__)

def generate_document(request):
    try:
        return DocxTemplateResponse(
            request,
            template="template.docx",
            context=get_context(),
            output_format="pdf",
        )
    except FileNotFoundError:
        logger.error("Template not found")
        return HttpResponseServerError("Document template not found")
    except LibreOfficeNotFoundError:
        logger.warning("LibreOffice not available, falling back to DOCX")
        return DocxTemplateResponse(
            request,
            template="template.docx",
            context=get_context(),
            output_format="docx",
        )
    except ConversionError as e:
        logger.error(f"Conversion failed: {e}")
        return HttpResponseServerError("Failed to generate document")
```

## Testing Document Generation

```python
# tests.py
from django.test import TestCase, Client
from io import BytesIO
from docx import Document

class DocumentGenerationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_generates_valid_docx(self):
        response = self.client.get("/document/?format=docx")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        # Verify it's a valid DOCX
        doc = Document(BytesIO(response.content))
        self.assertTrue(len(doc.paragraphs) > 0)

    def test_generates_pdf(self):
        response = self.client.get("/document/?format=pdf")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        
        # PDF files start with %PDF
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_correct_filename(self):
        response = self.client.get("/invoice/123/pdf/")
        
        self.assertIn(
            'filename="invoice_123.pdf"',
            response["Content-Disposition"]
        )
```

## Performance Tips

### 1. Cache Templates

If you're generating many documents from the same template, consider caching:

```python
from functools import lru_cache
from docxtpl import DocxTemplate

@lru_cache(maxsize=10)
def get_cached_template(template_path):
    return DocxTemplate(template_path)
```

### 2. Use Streaming for Large Documents

For very large documents, consider streaming the response.

### 3. Optimize LibreOffice Calls

LibreOffice conversion is the slowest part. Minimize conversions by:
- Offering DOCX as the default format
- Using async generation for non-interactive use cases
- Caching generated documents when possible

### 4. Monitor Memory Usage

Document generation can be memory-intensive. Monitor your application and consider:
- Using Celery for heavy workloads
- Setting appropriate worker memory limits
- Implementing request queuing for peak times

## Custom Jinja2 Filters

You can add custom Jinja2 filters for formatting values in your templates.

### In Background Tasks

Use the `jinja_env` parameter in `render_to_file()`:

```python
from jinja2 import Environment
from django_docxtpl import render_to_file

def format_thousands(value):
    """Format number with thousands separator: 1234567 → 1.234.567"""
    return f"{value:,.0f}".replace(",", ".")

def format_currency(value):
    """Format as currency: 1234.56 → 1.234,56 €"""
    return f"{value:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

# Create Jinja2 environment with custom filters
jinja_env = Environment(autoescape=True)
jinja_env.filters["thousands"] = format_thousands
jinja_env.filters["currency"] = format_currency

output_path = render_to_file(
    template="reports/sales.docx",
    context={
        "total_sales": 1234567,
        "revenue": 98765.43,
    },
    output_dir="/var/reports",
    filename="sales_report",
    output_format="pdf",
    jinja_env=jinja_env,
)
```

In your DOCX template:
- `{{ total_sales|thousands }}` → `1.234.567`
- `{{ revenue|currency }}` → `98.765,43 €`

### Alternative: Functions in Context

If you prefer not to use filters, you can pass formatting functions directly in the context:

```python
def format_thousands(value):
    return f"{value:,.0f}".replace(",", ".")

output_path = render_to_file(
    template="reports/sales.docx",
    context={
        "total_sales": 1234567,
        "fmt_thousands": format_thousands,  # Pass function in context
    },
    output_dir="/var/reports",
    filename="sales_report",
    output_format="pdf",
)
```

In your DOCX template, call it as a function:
- `{{ fmt_thousands(total_sales) }}` → `1.234.567`

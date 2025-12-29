# Quick Start

This guide will help you generate your first document with django-docxtpl in just a few minutes.

## Step 1: Create a Word Template

Create a Word document (`.docx`) with Jinja2 placeholders. For example, create `templates/documents/welcome.docx`:

```
Welcome, {{ name }}!

Thank you for joining {{ company_name }}.

Your account details:
- Username: {{ username }}
- Email: {{ email }}
- Member since: {{ join_date }}

Best regards,
The {{ company_name }} Team
```

You can use any Word features (fonts, styles, tables, images) - the template engine preserves all formatting.

## Step 2: Create a View

### Option A: Function-Based View

```python
# views.py
from django_docxtpl import DocxTemplateResponse

def welcome_document(request):
    context = {
        "name": request.user.get_full_name(),
        "company_name": "Acme Inc.",
        "username": request.user.username,
        "email": request.user.email,
        "join_date": request.user.date_joined.strftime("%B %d, %Y"),
    }
    
    return DocxTemplateResponse(
        request,
        template="documents/welcome.docx",
        context=context,
        filename="welcome_letter",
        output_format="docx",  # or "pdf"
    )
```

### Option B: Class-Based View

```python
# views.py
from django_docxtpl import DocxTemplateView

class WelcomeDocumentView(DocxTemplateView):
    template_name = "documents/welcome.docx"
    filename = "welcome_letter"
    output_format = "docx"

    def get_context_data(self, **kwargs):
        user = self.request.user
        return {
            "name": user.get_full_name(),
            "company_name": "Acme Inc.",
            "username": user.username,
            "email": user.email,
            "join_date": user.date_joined.strftime("%B %d, %Y"),
        }
```

## Step 3: Add URL Route

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Function-based view
    path("welcome/", views.welcome_document, name="welcome_document"),
    
    # Or class-based view
    path("welcome/", views.WelcomeDocumentView.as_view(), name="welcome_document"),
]
```

## Step 4: Test It

Start your Django development server and navigate to `/welcome/`. The browser will download a Word document (or PDF, depending on your `output_format`).

## Generating PDFs

To generate PDFs instead of DOCX files, simply change the `output_format`:

```python
return DocxTemplateResponse(
    request,
    template="documents/welcome.docx",
    context=context,
    filename="welcome_letter",
    output_format="pdf",  # Changed from "docx" to "pdf"
)
```

> **Note**: PDF generation requires LibreOffice to be installed. See [Installation](installation.md) for details.

## Working with Model Data

### Using DocxTemplateDetailView

For generating documents from model instances, use `DocxTemplateDetailView`:

```python
# models.py
from django.db import models

class Invoice(models.Model):
    number = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=200)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
```

```python
# views.py
from django_docxtpl import DocxTemplateDetailView
from .models import Invoice

class InvoicePDFView(DocxTemplateDetailView):
    model = Invoice
    template_name = "documents/invoice.docx"
    output_format = "pdf"
    context_object_name = "invoice"

    def get_filename(self):
        return f"invoice_{self.object.number}"
```

```python
# urls.py
urlpatterns = [
    path("invoice/<int:pk>/pdf/", InvoicePDFView.as_view(), name="invoice_pdf"),
]
```

Now visiting `/invoice/123/pdf/` will generate a PDF for invoice #123.

## Template Syntax Examples

### Variables

```
Customer: {{ customer.name }}
Total: {{ total }}€
```

### Loops

```
{% for item in items %}
- {{ item.name }}: {{ item.quantity }} x {{ item.price }}€
{% endfor %}
```

### Conditionals

```
{% if discount %}
Discount: {{ discount }}%
{% endif %}
```

### Filters

```
Date: {{ date|date:"F d, Y" }}
Price: {{ price|floatformat:2 }}
```

For more advanced template features, see the [docxtpl documentation](https://docxtpl.readthedocs.io/).

## Next Steps

- [Configuration](configuration.md) - Learn about all configuration options
- [API Reference](api.md) - Detailed API documentation
- [Advanced Usage](advanced.md) - Complex scenarios and best practices

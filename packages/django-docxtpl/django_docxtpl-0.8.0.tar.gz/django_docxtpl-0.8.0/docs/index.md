# django-docxtpl Documentation

Welcome to the django-docxtpl documentation!

## Table of Contents

- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [Configuration](configuration.md)
- [API Reference](api.md)
- [Advanced Usage](advanced.md)
- [Changelog](changelog.md)

## Overview

django-docxtpl is a Django package that integrates [docxtpl](https://docxtpl.readthedocs.io/) with Django, enabling you to generate Word documents (.docx) from templates using Jinja2 syntax and export them to multiple formats including PDF, ODT, HTML, and TXT.

## Key Features

- **Template-based Generation**: Use Word documents as templates with Jinja2 placeholders
- **Multiple Output Formats**: Export to DOCX, PDF, ODT, HTML, or TXT
- **Automatic Conversion**: LibreOffice headless handles format conversion
- **Django Integration**: Familiar patterns with responses, views, and mixins
- **Type Hints**: Full type annotation support for better IDE integration

## Requirements

- Python >= 3.10
- Django >= 4.2
- docxtpl >= 0.16
- LibreOffice (for PDF and other format conversions)

## Quick Example

```python
from django_docxtpl import DocxTemplateResponse

def invoice_view(request, invoice_id):
    invoice = Invoice.objects.get(pk=invoice_id)
    return DocxTemplateResponse(
        request,
        template="invoices/template.docx",
        context={"invoice": invoice},
        filename=f"invoice_{invoice.number}",
        output_format="pdf",
    )
```

## License

MIT License - see [LICENSE](https://github.com/ctrl-alt-d/django-docxtpl/blob/main/LICENSE) for details.

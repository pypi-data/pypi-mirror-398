# Configuration

django-docxtpl can be configured through Django settings. All settings are optional.

## Available Settings

### DOCXTPL_TEMPLATE_DIR

**Type**: `Path` or `str`  
**Default**: `None`

The base directory where your DOCX templates are stored. When set, you can use relative paths in your views.

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DOCXTPL_TEMPLATE_DIR = BASE_DIR / "docx_templates"
```

**Directory structure example:**

```
your_project/
├── docx_templates/
│   ├── invoices/
│   │   └── template.docx
│   ├── reports/
│   │   └── monthly.docx
│   └── letters/
│       └── welcome.docx
├── your_app/
│   └── views.py
└── settings.py
```

**Usage in views:**

```python
# With DOCXTPL_TEMPLATE_DIR set, use relative paths:
DocxTemplateResponse(
    request,
    template="invoices/template.docx",  # Relative to DOCXTPL_TEMPLATE_DIR
    context=context,
    filename="invoice",
)

# Or use absolute paths (always works):
DocxTemplateResponse(
    request,
    template="/path/to/your/template.docx",
    context=context,
    filename="invoice",
)
```

### DOCXTPL_LIBREOFFICE_PATH

**Type**: `Path` or `str`  
**Default**: `None` (auto-detected)

The path to the LibreOffice executable. If not set, django-docxtpl will automatically search for LibreOffice in:

1. System PATH (`soffice` or `libreoffice` commands)
2. Common installation locations:
   - macOS: `/Applications/LibreOffice.app/Contents/MacOS/soffice`
   - Linux: `/usr/bin/soffice`, `/usr/bin/libreoffice`
   - Windows: `C:\Program Files\LibreOffice\program\soffice.exe`

```python
# settings.py

# Linux
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"

# macOS
DOCXTPL_LIBREOFFICE_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Windows
DOCXTPL_LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"

# Custom location
DOCXTPL_LIBREOFFICE_PATH = "/opt/libreoffice/program/soffice"
```

## Environment-Specific Configuration

### Development

```python
# settings/development.py
DOCXTPL_TEMPLATE_DIR = BASE_DIR / "docx_templates"
# LibreOffice auto-detected on dev machine
```

### Production

```python
# settings/production.py
DOCXTPL_TEMPLATE_DIR = Path("/var/www/myapp/templates/docx")
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"
```

### Docker

```python
# settings/docker.py
import os

DOCXTPL_TEMPLATE_DIR = Path(os.environ.get("DOCX_TEMPLATE_DIR", "/app/templates/docx"))
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"
```

## Checking Configuration

You can verify your configuration programmatically:

```python
from django_docxtpl.utils import find_libreoffice, get_template_dir

# Check LibreOffice
libreoffice = find_libreoffice()
print(f"LibreOffice: {libreoffice or 'Not found'}")

# Check template directory
template_dir = get_template_dir()
print(f"Template directory: {template_dir or 'Not configured'}")
```

## Output Formats

The following output formats are supported:

| Format | `output_format` | MIME Type | LibreOffice Required |
|--------|-----------------|-----------|---------------------|
| Word Document | `"docx"` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | No |
| PDF | `"pdf"` | `application/pdf` | Yes |
| OpenDocument | `"odt"` | `application/vnd.oasis.opendocument.text` | Yes |
| HTML | `"html"` | `text/html` | Yes |
| Plain Text | `"txt"` | `text/plain` | Yes |

## Conversion Timeout

When converting documents, LibreOffice is invoked as a subprocess. The default timeout is 60 seconds. This is currently not configurable via settings but can be passed to the converter directly:

```python
from django_docxtpl.converters import convert_docx

# Custom timeout for large documents
converted = convert_docx(docx_bytes, "pdf", timeout=120)
```

## Best Practices

### 1. Use a Dedicated Template Directory

Keep your DOCX templates separate from Django HTML templates:

```
project/
├── templates/          # Django HTML templates
└── docx_templates/     # DOCX templates for document generation
```

### 2. Version Control Templates

Include your DOCX templates in version control. They're essentially code.

### 3. Test Template Rendering

Create tests for your document generation:

```python
def test_invoice_generation(self):
    response = self.client.get(f"/invoice/{invoice.pk}/pdf/")
    self.assertEqual(response.status_code, 200)
    self.assertEqual(
        response["Content-Type"],
        "application/pdf"
    )
```

### 4. Handle Missing LibreOffice Gracefully

```python
from django_docxtpl import DocxTemplateResponse, LibreOfficeNotFoundError

def generate_document(request):
    try:
        return DocxTemplateResponse(
            request,
            template="template.docx",
            context=context,
            output_format="pdf",
        )
    except LibreOfficeNotFoundError:
        # Fallback to DOCX if LibreOffice is not available
        return DocxTemplateResponse(
            request,
            template="template.docx",
            context=context,
            output_format="docx",
        )
```

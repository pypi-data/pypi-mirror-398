# Installation

## Basic Installation

Install django-docxtpl using pip:

```bash
pip install django-docxtpl
```

Or using Poetry:

```bash
poetry add django-docxtpl
```

## Dependencies

django-docxtpl automatically installs:

- **django** >= 4.2
- **docxtpl** >= 0.16
- **python-docx** (installed as a dependency of docxtpl)
- **Jinja2** (installed as a dependency of docxtpl)

## LibreOffice (Optional)

LibreOffice is required **only** if you want to convert documents to formats other than DOCX (e.g., PDF, ODT, HTML, TXT).

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install libreoffice-core libreoffice-writer
```

### macOS

Using Homebrew:

```bash
brew install --cask libreoffice
```

### Windows

Download and install from [libreoffice.org](https://www.libreoffice.org/download/download/).

### Docker

If you're using Docker, add LibreOffice to your Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install LibreOffice
RUN apt-get update && apt-get install -y \
    libreoffice-core \
    libreoffice-writer \
    && rm -rf /var/lib/apt/lists/*

# ... rest of your Dockerfile
```

## Django Configuration

### Add to INSTALLED_APPS (Optional)

Adding `django_docxtpl` to `INSTALLED_APPS` is optional but recommended:

```python
INSTALLED_APPS = [
    # ...
    "django_docxtpl",
]
```

### Configure Template Directory (Optional)

Set a default directory for your DOCX templates:

```python
# settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DOCXTPL_TEMPLATE_DIR = BASE_DIR / "docx_templates"
```

### Configure LibreOffice Path (Optional)

If LibreOffice is not in your system PATH, specify its location:

```python
# settings.py

# Linux
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"

# macOS
DOCXTPL_LIBREOFFICE_PATH = "/Applications/LibreOffice.app/Contents/MacOS/soffice"

# Windows
DOCXTPL_LIBREOFFICE_PATH = r"C:\Program Files\LibreOffice\program\soffice.exe"
```

## Verifying Installation

You can verify the installation by checking if LibreOffice is detected:

```python
from django_docxtpl.utils import find_libreoffice

libreoffice_path = find_libreoffice()
if libreoffice_path:
    print(f"LibreOffice found at: {libreoffice_path}")
else:
    print("LibreOffice not found - PDF conversion will not be available")
```

## Development Installation

For development, clone the repository and install with development dependencies:

```bash
git clone https://github.com/ctrl-alt-d/django-docxtpl.git
cd django-docxtpl

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install flit
flit install -s --deps develop
```

This installs additional tools for development:

- pytest & pytest-django (testing)
- ruff (linting and formatting)
- mypy & django-stubs (type checking)

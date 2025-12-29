# CLAUDE.md - Guia del Projecte django-docxtpl

## Descripció del Projecte

`django-docxtpl` és un paquet Python que integra [docxtpl](https://docxtpl.readthedocs.io/) amb Django, permetent generar documents a partir de plantilles Word (.docx) amb el motor de templates Jinja2.

### Formats de Sortida

A més de DOCX, el paquet permet exportar a múltiples formats mitjançant **LibreOffice/OpenOffice en mode headless**:

- `docx` - Microsoft Word (format natiu, sense conversió)
- `pdf` - PDF
- `odt` - OpenDocument Text
- `html` - HTML
- `txt` - Text pla

L'extensió del fitxer s'afegeix automàticament segons el format seleccionat.

## Arquitectura

```
django-docxtpl/
├── django_docxtpl/          # Paquet principal
│   ├── __init__.py
│   ├── views.py             # Vistes genèriques per servir documents
│   ├── mixins.py            # Mixins per a Class-Based Views
│   ├── response.py          # HttpResponse especialitzat per documents
│   ├── converters.py        # Conversió de formats amb LibreOffice
│   └── utils.py             # Funcions utilitàries
├── tests/                   # Tests amb pytest
├── docs/                    # Documentació
├── pyproject.toml           # Configuració del paquet
└── README.md
```

## Convencions de Codi

### Estil Python
- **Python**: >= 3.10
- **Django**: >= 4.2
- **Formatejador**: `ruff format`
- **Linter**: `ruff check`
- **Type hints**: Obligatoris en funcions públiques
- **Docstrings**: Format Google style

### Nomenclatura
- Classes: `PascalCase`
- Funcions i variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Fitxers: `snake_case.py`

### Imports
Ordre d'imports (amb una línia en blanc entre grups):
1. Biblioteca estàndard
2. Tercers (django, docxtpl)
3. Locals

```python
from pathlib import Path
from typing import Any

from django.http import HttpResponse
from docxtpl import DocxTemplate

from django_docxtpl.utils import get_template_path
```

## Dependències Principals

- `django >= 4.2`
- `docxtpl >= 0.16`
- `python-docx` (dependència de docxtpl)

### Dependències de Desenvolupament
- `pytest`
- `pytest-django`
- `ruff`
- `mypy`

## Comandes Habituals

```bash
# Instal·lar flit (eina de packaging)
pip install flit

# Instal·lar en mode desenvolupament (symlink)
flit install -s

# Instal·lar amb dependències de desenvolupament
flit install -s --deps develop

# Executar tests
pytest

# Executar linter
ruff check .

# Formatejar codi
ruff format .

# Type checking
mypy django_docxtpl/

# Publicar a PyPI
flit publish
```

## Patrons de Disseny

### Response per Documents
```python
from django_docxtpl import DocxTemplateResponse

# Generar DOCX (format per defecte)
def my_view(request):
    context = {"name": "World"}
    return DocxTemplateResponse(
        request,
        template="my_template.docx",
        context=context,
        filename="output",  # Resultat: output.docx
    )

# Generar PDF (conversió amb LibreOffice)
def my_pdf_view(request):
    context = {"name": "World"}
    return DocxTemplateResponse(
        request,
        template="my_template.docx",
        context=context,
        filename="output",  # Resultat: output.pdf
        output_format="pdf",
    )
```

### Class-Based View amb Mixin
```python
from django.views.generic import View
from django_docxtpl.mixins import DocxTemplateResponseMixin

class MyDocxView(DocxTemplateResponseMixin, View):
    template_name = "my_template.docx"
    filename = "output"  # L'extensió s'afegeix automàticament
    output_format = "docx"  # Opcional, "docx" per defecte

    def get_context_data(self):
        return {"name": "World"}


class MyPdfView(DocxTemplateResponseMixin, View):
    template_name = "my_template.docx"
    filename = "report"  # Resultat: report.pdf
    output_format = "pdf"

    def get_context_data(self):
        return {"name": "World"}
```

## Tests

- Utilitzar `pytest` amb `pytest-django`
- Fixtures per plantilles de test a `tests/templates/`
- Cobertura mínima: 80%

```python
# Exemple de test
def test_docx_response_content_type(client):
    response = client.get("/generate-doc/")
    assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
```

## Configuració Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    "django_docxtpl",
]

# Opcional: directori de plantilles DOCX
DOCXTPL_TEMPLATE_DIR = BASE_DIR / "docx_templates"

# Opcional: ruta a l'executable de LibreOffice (autodetectat per defecte)
DOCXTPL_LIBREOFFICE_PATH = "/usr/bin/soffice"
```

### Requisits del Sistema

Per a la conversió de formats (PDF, ODT, etc.), cal tenir instal·lat **LibreOffice**:

```bash
# Ubuntu/Debian
sudo apt install libreoffice-core libreoffice-writer

# macOS
brew install --cask libreoffice

# El paquet detecta automàticament la ubicació de LibreOffice
```

## Principis de Disseny

1. **Simplicitat**: API clara i fàcil d'usar
2. **Integració Django**: Seguir els patrons de Django (CBV, responses, settings)
3. **Flexibilitat**: Permetre personalització sense complicar l'ús bàsic
4. **Documentació**: Docstrings complets i exemples clars

## Notes per al Desenvolupament

- Els fitxers `.docx` de plantilla són binaris, no incloure'ls directament al codi
- Utilitzar `BytesIO` per generar documents en memòria
- Sempre tancar els recursos de docxtpl correctament
- Considerar streaming per documents grans
- La conversió amb LibreOffice és síncrona i pot ser lenta; considerar tasques asíncrones (Celery) per documents grans o múltiples conversions
- Utilitzar fitxers temporals per la conversió i netejar-los després
- LibreOffice headless es crida amb: `soffice --headless --convert-to <format> --outdir <dir> <input>`

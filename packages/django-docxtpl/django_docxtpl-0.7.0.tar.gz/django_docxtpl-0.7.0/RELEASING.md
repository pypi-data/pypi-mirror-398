# Guia de Releases

Aquesta guia explica com publicar noves versions de `django-docxtpl` a PyPI.

## Prerequisits

### 1. Configurar PyPI Trusted Publisher (només la primera vegada)

1. Crea un compte a [pypi.org](https://pypi.org) si no en tens
2. Ves a **Account Settings** → **Publishing** → **Add a new pending publisher**
3. Omple el formulari:
   - **Project name**: `django-docxtpl`
   - **Owner**: `ctrl-alt-d`
   - **Repository**: `django-docxtpl`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

### 2. Configurar l'environment a GitHub (només la primera vegada)

1. Ves al repositori → **Settings** → **Environments**
2. Crea un environment anomenat `pypi`
3. (Opcional) Afegeix protecció requerint aprovació manual

## Procés de Release

### 1. Actualitzar la versió

Edita `django_docxtpl/__init__.py` i actualitza `__version__`:

```python
__version__ = "X.Y.Z"
```

Seguim [Semantic Versioning](https://semver.org/):
- **MAJOR** (X): Canvis incompatibles amb l'API
- **MINOR** (Y): Nova funcionalitat compatible
- **PATCH** (Z): Correccions de bugs compatibles

### 2. Actualitzar el changelog

Edita `docs/changelog.md` amb els canvis de la nova versió.

### 3. Commit i push

```bash
git add django_docxtpl/__init__.py docs/changelog.md
git commit -m "Bump version to X.Y.Z"
git push origin main
```

### 4. Crear el tag

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Quan facis push del tag, automàticament:
1. Es crearà un **GitHub Release** amb notes generades automàticament
2. Es publicarà el paquet a **PyPI**

### 5. Verificar la publicació

El workflow `publish.yml` s'executarà automàticament. Pots verificar:

1. L'estat a **Actions** del repositori
2. El paquet a [pypi.org/project/django-docxtpl](https://pypi.org/project/django-docxtpl/)

## Publicació manual (si cal)

Si necessites publicar manualment:

```bash
# Instal·lar flit
pip install flit

# Construir el paquet
flit build

# Publicar (requereix token de PyPI)
flit publish
```

Per configurar el token:

```bash
# Crear token a PyPI: Account Settings → API tokens
# Configurar a ~/.pypirc o com a variable d'entorn
export FLIT_USERNAME=__token__
export FLIT_PASSWORD=pypi-XXXXXXXXXXXX
```

## Checklist pre-release

- [ ] Tots els tests passen (`pytest`)
- [ ] Linter sense errors (`ruff check .`)
- [ ] Format correcte (`ruff format --check .`)
- [ ] Type checking correcte (`mypy django_docxtpl/`)
- [ ] Versió actualitzada a `__init__.py`
- [ ] Changelog actualitzat
- [ ] README actualitzat si cal

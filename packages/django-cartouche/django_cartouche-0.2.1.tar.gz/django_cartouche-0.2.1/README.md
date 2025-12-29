# django-cartouche

![PyPI - Version](https://img.shields.io/pypi/v/django-cartouche)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-cartouche/)
[![CI](https://github.com/rnegron/django-cartouche/actions/workflows/ci.yml/badge.svg)](https://github.com/rnegron/django-cartouche/actions/workflows/ci.yml)
[![docs](https://app.readthedocs.org/projects/django-cartouche/badge)](https://django-cartouche.readthedocs.io/en/latest/)
[![codecov](https://codecov.io/github/rnegron/django-cartouche/graph/badge.svg?token=EMRGIAU3UZ)](https://codecov.io/github/rnegron/django-cartouche)

Django [Cartouche](https://en.wikipedia.org/wiki/Cartouche) enables inline (in-HTML) .po translation editing for Django projects. Click on any string marked for translation in your browser to edit it directly during development.

## Installation

Install as a development dependency:

```bash
pip install django-cartouche --group dev
# or with uv
uv add django-cartouche --dev
```

## Configuration

django-cartouche should only be installed in development environments. Configure it in your local/development settings file (e.g., `settings/local.py` or `settings/dev.py`):

```python
# settings/local.py

from .base import *

DEBUG = True

INSTALLED_APPS += [
    "cartouche",
]

MIDDLEWARE += [
    "cartouche.middleware.CartoucheMiddleware",  # Must be after LocaleMiddleware
]
```

Conditionally include URLs in your `urls.py`:

```python
from django.conf import settings

urlpatterns = [
    # ...
]

if settings.DEBUG:
    urlpatterns += [
        path("cartouche/", include("cartouche.urls")),
    ]
```

Set the `lang` attribute on your `<html>` element for locale detection:

```html
{% load i18n %}
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE }}">
```

The editor only activates when `DEBUG=True`, but following these practices ensures cartouche is never present in production.

## How It Works

When a page renders, django-cartouche tracks all translation calls (`gettext`, `pgettext`) and injects a manifest of translated strings into the HTML response. The frontend script then walks the DOM, finds matching text, and wraps it in editable spans.

When you edit a string and save (blur or press Enter):

1. The original source string (`msgid`) is used to locate the entry in your `.po` file
2. The `lang` attribute on `<html>` determines which locale's `.po` file to update
3. The `.po` file is saved and `compilemessages` runs automatically

For example, if your source is English and you're viewing the site in Spanish (`<html lang="es">`):

- `{% trans "Welcome" %}` displays "Bienvenido" (from `locale/es/LC_MESSAGES/django.po`)
- Clicking on "Bienvenido" lets you edit the Spanish translation
- Saving updates `msgstr` in the Spanish `.po` file

To edit translations for a different language, switch your site's active locale first. Each language has its own `.po` file, and the `lang` attribute tells cartouche which one to modify.

## Demo

The project ships with a simple demo project so you can see it in action locally:

`cd demo && python manage.py runserver`

Notice how changing the strings in-browser modifies your `.po` files and re-compiles them into `.mo` files.


## Development

```bash
uv sync                              # Install dependencies
uv run pre-commit install            # Install git hooks (one-time)
ruff check src/ && ruff format src/  # Lint and format
pytest --cov                         # Run tests with coverage
```

### Making Commits

Use the interactive CLI for guided conventional commits:

```bash
uv run cz commit
```

Or use standard git with conventional format:

```bash
git commit -m "feat: add new feature"
git commit -m "fix(compiler): handle edge case"
```

## Feedback

If you end up using django-cartouche, I'd genuinely like to hear about your experience. Whether you've found it helpful, run into issues or have ideas for improvements, your feedback is welcome.

**[Share your feedback here →](https://github.com/rnegron/django-cartouche/issues/new?template=feedback.md)**

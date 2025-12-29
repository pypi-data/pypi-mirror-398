# Configuration

Configure django-cartouche in your local/development settings file (e.g., `settings/local.py` or `settings/dev.py`).

## Settings

Add `cartouche` to your installed apps and add the middleware after `LocaleMiddleware`:

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

!!! warning "Middleware Order"
    `CartoucheMiddleware` must be placed **after** `LocaleMiddleware` in the middleware list. The middleware relies on locale detection being already configured.

## URLs

Conditionally include the cartouche URLs in your `urls.py`:

```python
from django.conf import settings

urlpatterns = [
    # your existing patterns...
]

if settings.DEBUG:
    urlpatterns += [
        path("cartouche/", include("cartouche.urls")),
    ]
```

## HTML Setup

Set the `lang` attribute on your `<html>` element for locale detection:

```html
<html lang="{{ LANGUAGE_CODE }}">
```

This tells django-cartouche which language's `.po` file to update when you edit a translation.

## Usage

Once configured, run your development server:

```bash
python manage.py runserver
```

Translated strings appear with visual indicators:

- **Blue underline**: Translated strings (msgstr differs from msgid)
- **Amber underline**: Untranslated strings (msgstr equals msgid or is empty)

Hover over any string to see it highlighted. Click to edit inline. Changes are saved to your `.po` files and messages are recompiled automatically.

!!! note "Development Only"
    The editor only activates when `DEBUG=True`. Following the configuration above ensures django-cartouche is never present in production.

# django-cartouche

Inline .po translation editing for Django. Click on any translated string in the browser to edit it directly during development.

## How It Works

When running with `DEBUG=True`, django-cartouche:

1. Tracks all `gettext` and `pgettext` calls during request processing
2. Injects an editor overlay into HTML responses
3. Makes translated strings clickable and editable
4. Saves changes directly to your `.po` files and recompiles messages

## Quick Start

1. [Install](installation.md) as a dev dependency
2. Add `cartouche` to `INSTALLED_APPS`
3. Add `CartoucheMiddleware` after `LocaleMiddleware`
4. Include URLs and set `<html lang="{{ LANGUAGE_CODE }}">`

See [Configuration](configuration.md) for complete setup instructions.

## Requirements

- Python 3.10+
- Django 4.2+

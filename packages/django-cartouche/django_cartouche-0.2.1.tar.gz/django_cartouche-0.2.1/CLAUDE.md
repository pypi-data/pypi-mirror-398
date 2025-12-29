# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

django-cartouche is a Django library for inline .po translation editing. It allows developers to edit translations directly in the browser during development (DEBUG=True only). When a translated string is displayed, users can click on it to edit the translation inline, which updates the .po file and recompiles messages automatically.

## Development Commands

```bash
# Install dependencies
uv sync

# Run tests with coverage
pytest --cov

# Run the demo server
cd demo && python manage.py runserver

# Lint and format
ruff check src/
ruff format src/

# Compile messages after .po changes
cd demo && python manage.py compilemessages

# Extract messages from source
cd demo && python manage.py makemessages -l es

# Serve docs locally
mkdocs serve
```

## Commit Conventions

This project uses conventional commits enforced by commitizen and pre-commit hooks.

### Setup (one-time)

```bash
uv run pre-commit install
```

### Commit Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style (formatting, no logic change)
- `refactor:` - Code refactoring (no feature/fix)
- `perf:` - Performance improvement
- `test:` - Adding/updating tests
- `build:` - Build system changes
- `ci:` - CI configuration
- `chore:` - Maintenance tasks

### Format

```
<type>(<scope>): <description>

[optional body]
```

Breaking changes: Add `!` after type/scope: `feat!: remove deprecated API`

### Interactive Mode

```bash
uv run cz commit  # Guided commit message creation
```

## Architecture

The library consists of four main components that work together:

1. **Tracking (`tracking.py`)**: Patches Django's `gettext` and `pgettext` at app startup to log all translation calls per-request using a ContextVar. Only logs entries where the translation differs from the msgid.

2. **Middleware (`middleware.py`)**: Injects a JSON manifest of logged translations plus CSS/JS assets into HTML responses before `</body>`. Only active when `DEBUG=True` and response is HTML.

3. **Frontend (`static/cartouche/editor.js`)**: Walks the DOM to find translated text, wraps matches in contentEditable spans, and POSTs edits to `/cartouche/save/` on blur.

4. **Compiler (`compiler.py`)**: Locates the msgid in .po files (searching LOCALE_PATHS and app locale directories), updates the msgstr, saves, and runs `compilemessages`.

## Integration Points

- Add `"cartouche"` to `INSTALLED_APPS`
- Add `CartoucheMiddleware` after `LocaleMiddleware`
- Include `cartouche.urls` at `/cartouche/`
- Set `lang` attribute on `<html>` element for locale detection

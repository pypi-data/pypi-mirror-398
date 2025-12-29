# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-26

### Added

- Initial release of django-cartouche
- Translation tracking via patched `gettext` and `pgettext` functions
- Middleware to inject translation manifest and editor assets into HTML responses
- Frontend editor with contentEditable spans for inline translation editing
- `.po` file compiler that updates msgstr and runs `compilemessages`
- Debug-only activation for development safety
- Support for Django 4.2+ and Python 3.10+
- Comprehensive test suite with pytest-django
- MkDocs documentation site
- GitHub Actions CI workflows
- Pre-commit hooks with commitizen for conventional commits

[Unreleased]: https://github.com/rnegron/django-cartouche/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rnegron/django-cartouche/releases/tag/v0.1.0

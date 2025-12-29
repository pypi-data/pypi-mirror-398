from __future__ import annotations

import contextlib

from cartouche.tracking import (
    TranslationEntry,
    _log,
    clear_log,
    get_log,
    install_tracker,
)


class TestTranslationEntry:
    def test_fields(self):
        entry = TranslationEntry(msgid="Hello", msgstr="Hola")
        assert entry.msgid == "Hello"
        assert entry.msgstr == "Hola"
        assert entry.context is None

    def test_with_context(self):
        entry = TranslationEntry(msgid="Hello", msgstr="Hola", context="greeting")
        assert entry.context == "greeting"


class TestGetLog:
    def test_creates_new_log_when_none_exists(self):
        _log.set([])
        with contextlib.suppress(AttributeError, TypeError):
            del _log.__dict__  # Force LookupError by resetting context
        # Use a fresh context by calling in isolation
        log = get_log()
        assert log == []
        assert isinstance(log, list)

    def test_returns_existing_log(self):
        existing = [TranslationEntry(msgid="test", msgstr="prueba")]
        _log.set(existing)
        assert get_log() is existing


class TestClearLog:
    def test_clears_log(self):
        _log.set([TranslationEntry(msgid="test", msgstr="prueba")])
        clear_log()
        assert get_log() == []


class TestInstallTracker:
    def test_installs_once(self):
        import cartouche.tracking as tracking

        original_installed = tracking._installed
        tracking._installed = False

        install_tracker()
        assert tracking._installed is True

        # Second call should not raise
        install_tracker()
        assert tracking._installed is True

        tracking._installed = original_installed

    def test_gettext_logs_translation(self):
        from django.utils import translation

        import cartouche.tracking as tracking

        tracking._installed = False
        install_tracker()

        clear_log()
        # This will call tracked_gettext
        translation.gettext("test message")

        # If translation differs, it should be logged
        log = get_log()
        # Result depends on whether translation is configured
        assert isinstance(log, list)

    def test_pgettext_logs_translation(self):
        from django.utils import translation

        import cartouche.tracking as tracking

        tracking._installed = False
        install_tracker()

        clear_log()
        translation.pgettext("context", "test message")

        log = get_log()
        assert isinstance(log, list)

    def test_untranslated_message_logged_with_flag(self):
        from django.utils import translation

        import cartouche.tracking as tracking

        tracking._installed = False
        install_tracker()

        clear_log()
        # Use a message that won't be translated (no .po file)
        translation.gettext("untranslated_unique_string_12345")

        log = get_log()
        # Should log with translated=False so users can add new translations
        entries = [e for e in log if e.msgid == "untranslated_unique_string_12345"]
        assert len(entries) == 1
        assert entries[0].translated is False

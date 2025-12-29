from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from cartouche.compiler import _locale_dirs, find_po_entry, update_translation


class TestLocaleDirs:
    def test_yields_locale_paths(self):
        with patch("cartouche.compiler.settings") as mock_settings:
            mock_settings.LOCALE_PATHS = ["/path/to/locale"]
            with patch("cartouche.compiler.apps") as mock_apps:
                mock_apps.get_app_configs.return_value = []
                dirs = list(_locale_dirs())

        assert Path("/path/to/locale") in dirs

    def test_yields_app_locale_dirs(self, tmp_path):
        app_locale = tmp_path / "locale"
        app_locale.mkdir()

        mock_config = MagicMock()
        mock_config.path = str(tmp_path)

        with patch("cartouche.compiler.settings") as mock_settings:
            mock_settings.LOCALE_PATHS = []
            with patch("cartouche.compiler.apps") as mock_apps:
                mock_apps.get_app_configs.return_value = [mock_config]
                dirs = list(_locale_dirs())

        assert app_locale in dirs

    def test_skips_nonexistent_app_locale(self, tmp_path):
        mock_config = MagicMock()
        mock_config.path = str(tmp_path)  # No locale subdir

        with patch("cartouche.compiler.settings") as mock_settings:
            mock_settings.LOCALE_PATHS = []
            with patch("cartouche.compiler.apps") as mock_apps:
                mock_apps.get_app_configs.return_value = [mock_config]
                dirs = list(_locale_dirs())

        assert len(dirs) == 0

    def test_handles_missing_locale_paths_attr(self):
        with patch("cartouche.compiler.settings") as mock_settings:
            del mock_settings.LOCALE_PATHS
            mock_settings.configure_mock(**{"LOCALE_PATHS": []})
            with patch("cartouche.compiler.apps") as mock_apps:
                mock_apps.get_app_configs.return_value = []
                dirs = list(_locale_dirs())

        assert dirs == []


class TestFindPoEntry:
    def test_finds_entry(self, tmp_path):
        locale_dir = tmp_path / "es" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_path = locale_dir / "django.po"
        po_path.write_text(
            """
msgid "Hello"
msgstr "Hola"
"""
        )

        with patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]):
            result = find_po_entry("Hello", "es")

        assert result is not None
        path, po, entry = result
        assert path == po_path
        assert entry.msgstr == "Hola"

    def test_returns_none_when_not_found(self, tmp_path):
        locale_dir = tmp_path / "es" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_path = locale_dir / "django.po"
        po_path.write_text(
            """
msgid "Hello"
msgstr "Hola"
"""
        )

        with patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]):
            result = find_po_entry("Goodbye", "es")

        assert result is None

    def test_returns_none_when_po_missing(self, tmp_path):
        with patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]):
            result = find_po_entry("Hello", "es")

        assert result is None

    def test_finds_entry_with_context(self, tmp_path):
        locale_dir = tmp_path / "es" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_path = locale_dir / "django.po"
        po_path.write_text(
            """
msgctxt "greeting"
msgid "Hello"
msgstr "Hola amigo"
"""
        )

        with patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]):
            result = find_po_entry("Hello", "es", context="greeting")

        assert result is not None
        _, _, entry = result
        assert entry.msgstr == "Hola amigo"


class TestUpdateTranslation:
    def test_updates_and_compiles(self, tmp_path):
        locale_dir = tmp_path / "es" / "LC_MESSAGES"
        locale_dir.mkdir(parents=True)
        po_path = locale_dir / "django.po"
        po_path.write_text(
            """
msgid "Hello"
msgstr "Hola"
"""
        )

        with (
            patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]),
            patch("cartouche.compiler.call_command") as mock_cmd,
        ):
            result = update_translation("Hello", "Buenos dias", "es")

        assert result == po_path
        mock_cmd.assert_called_once_with("compilemessages", locale=["es"], verbosity=0)

        # Verify file was updated
        import polib

        po = polib.pofile(str(po_path))
        assert po.find("Hello").msgstr == "Buenos dias"

    def test_returns_none_when_not_found(self, tmp_path):
        with patch("cartouche.compiler._locale_dirs", return_value=[tmp_path]):
            result = update_translation("Missing", "No existe", "es")

        assert result is None

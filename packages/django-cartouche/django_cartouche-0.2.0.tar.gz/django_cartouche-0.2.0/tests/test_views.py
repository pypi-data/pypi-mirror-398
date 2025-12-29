from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from django.test import RequestFactory

from cartouche.views import save


@pytest.fixture
def rf():
    return RequestFactory()


class TestSaveView:
    def test_forbidden_when_debug_false(self, rf):
        request = rf.post(
            "/cartouche/save/",
            data=json.dumps({"msgid": "Hello", "msgstr": "Hola", "locale": "es"}),
            content_type="application/json",
        )

        with patch("cartouche.views.settings") as mock_settings:
            mock_settings.DEBUG = False
            response = save(request)

        assert response.status_code == 403

    def test_success_response(self, rf, tmp_path):
        request = rf.post(
            "/cartouche/save/",
            data=json.dumps({"msgid": "Hello", "msgstr": "Hola", "locale": "es"}),
            content_type="application/json",
        )

        with (
            patch("cartouche.views.settings") as mock_settings,
            patch("cartouche.views.update_translation") as mock_update,
        ):
            mock_settings.DEBUG = True
            mock_update.return_value = Path("/path/to/django.po")
            response = save(request)

        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["ok"] is True
        assert data["file"] == "/path/to/django.po"

    def test_not_found_response(self, rf):
        request = rf.post(
            "/cartouche/save/",
            data=json.dumps({"msgid": "Missing", "msgstr": "No existe", "locale": "es"}),
            content_type="application/json",
        )

        with (
            patch("cartouche.views.settings") as mock_settings,
            patch("cartouche.views.update_translation") as mock_update,
        ):
            mock_settings.DEBUG = True
            mock_update.return_value = None
            response = save(request)

        assert response.status_code == 404
        data = json.loads(response.content)
        assert data["ok"] is False
        assert "not found" in data["error"]

    def test_with_context(self, rf, tmp_path):
        request = rf.post(
            "/cartouche/save/",
            data=json.dumps(
                {
                    "msgid": "Hello",
                    "msgstr": "Hola",
                    "locale": "es",
                    "ctx": "greeting",
                }
            ),
            content_type="application/json",
        )

        with (
            patch("cartouche.views.settings") as mock_settings,
            patch("cartouche.views.update_translation") as mock_update,
        ):
            mock_settings.DEBUG = True
            mock_update.return_value = Path("/path/to/django.po")
            save(request)

        mock_update.assert_called_once_with(
            msgid="Hello",
            new_msgstr="Hola",
            locale="es",
            context="greeting",
        )


class TestSaveViewIntegration:
    def test_require_post(self, rf):
        request = rf.get("/cartouche/save/")

        with patch("cartouche.views.settings") as mock_settings:
            mock_settings.DEBUG = True
            response = save(request)

        assert response.status_code == 405

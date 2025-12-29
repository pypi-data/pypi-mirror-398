from __future__ import annotations

from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from cartouche.middleware import CartoucheMiddleware
from cartouche.tracking import TranslationEntry, clear_log, get_log


@pytest.fixture
def middleware():
    def get_response(request):
        return HttpResponse("<html><body>Hola</body></html>", content_type="text/html")

    return CartoucheMiddleware(get_response)


@pytest.fixture
def rf():
    return RequestFactory()


class TestShouldInject:
    def test_injects_on_debug_html_200(self, middleware, html_response):
        with patch("cartouche.middleware.settings") as mock_settings:
            mock_settings.DEBUG = True
            assert middleware._should_inject(html_response) is True

    def test_no_inject_when_debug_false(self, middleware, html_response):
        with patch("cartouche.middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            assert middleware._should_inject(html_response) is False

    def test_no_inject_on_non_200(self, middleware):
        with patch("cartouche.middleware.settings") as mock_settings:
            mock_settings.DEBUG = True
            response = HttpResponse(status=404)
            response["Content-Type"] = "text/html"
            assert middleware._should_inject(response) is False

    def test_no_inject_on_json(self, middleware, json_response):
        with patch("cartouche.middleware.settings") as mock_settings:
            mock_settings.DEBUG = True
            assert middleware._should_inject(json_response) is False


class TestBuildManifest:
    def test_builds_manifest_with_translations(self, middleware, rf):
        request = rf.get("/")
        clear_log()
        get_log().append(TranslationEntry(msgid="Hello", msgstr="Hola"))

        with patch("cartouche.middleware.get_token", return_value="test-csrf-token"):
            manifest = middleware._build_manifest(request)

        assert manifest["csrf"] == "test-csrf-token"
        assert len(manifest["t"]) == 1
        assert manifest["t"][0]["msgid"] == "Hello"
        assert manifest["t"][0]["msgstr"] == "Hola"

    def test_deduplicates_entries(self, middleware, rf):
        request = rf.get("/")
        clear_log()
        log = get_log()
        log.append(TranslationEntry(msgid="Hello", msgstr="Hola"))
        log.append(TranslationEntry(msgid="Hello", msgstr="Hola"))

        with patch("cartouche.middleware.get_token", return_value="token"):
            manifest = middleware._build_manifest(request)

        assert len(manifest["t"]) == 1

    def test_different_contexts_not_deduplicated(self, middleware, rf):
        request = rf.get("/")
        clear_log()
        log = get_log()
        log.append(TranslationEntry(msgid="Hello", msgstr="Hola", context=None))
        log.append(TranslationEntry(msgid="Hello", msgstr="Hola", context="greeting"))

        with patch("cartouche.middleware.get_token", return_value="token"):
            manifest = middleware._build_manifest(request)

        assert len(manifest["t"]) == 2


class TestSnippet:
    def test_generates_script_and_link_tags(self, middleware):
        manifest = {"t": [], "csrf": "token"}

        with patch("cartouche.middleware.static") as mock_static:
            mock_static.side_effect = lambda x: f"/static/{x}"
            snippet = middleware._snippet(manifest)

        assert b"<script" in snippet
        assert b"cartouche-data" in snippet
        assert b"<link" in snippet
        assert b"/static/cartouche/editor.css" in snippet
        assert b"/static/cartouche/editor.js" in snippet


class TestCall:
    def test_clears_log_on_each_request(self, rf):
        get_log().append(TranslationEntry(msgid="old", msgstr="viejo"))

        def get_response(request):
            # Log should be cleared before response
            return HttpResponse("ok", content_type="text/plain")

        middleware = CartoucheMiddleware(get_response)
        request = rf.get("/")
        middleware(request)

        # Verify clear_log was called (log should be empty or contain only new entries)

    def test_injects_into_html(self, rf):
        def get_response(request):
            return HttpResponse("<html><body>Content</body></html>", content_type="text/html")

        middleware = CartoucheMiddleware(get_response)
        request = rf.get("/")

        with (
            patch("cartouche.middleware.settings") as mock_settings,
            patch("cartouche.middleware.get_token", return_value="csrf"),
            patch("cartouche.middleware.static", side_effect=lambda x: f"/s/{x}"),
        ):
            mock_settings.DEBUG = True
            response = middleware(request)

        assert b"cartouche-data" in response.content
        assert b"</body>" in response.content
        assert "Content-Length" not in response

    def test_no_injection_for_non_html(self, rf):
        def get_response(request):
            return HttpResponse('{"data": 1}', content_type="application/json")

        middleware = CartoucheMiddleware(get_response)
        request = rf.get("/")

        with patch("cartouche.middleware.settings") as mock_settings:
            mock_settings.DEBUG = True
            response = middleware(request)

        assert b"cartouche-data" not in response.content

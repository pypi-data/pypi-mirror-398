from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.conf import settings
from django.middleware.csrf import get_token
from django.templatetags.static import static

from cartouche.tracking import clear_log, get_log

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


class CartoucheMiddleware:
    def __init__(self, get_response: object) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        clear_log()
        response = self.get_response(request)

        if not self._should_inject(response):
            return response

        manifest = self._build_manifest(request)
        response.content = response.content.replace(
            b"</body>",
            self._snippet(manifest) + b"</body>",
        )
        del response["Content-Length"]
        return response

    def _should_inject(self, response: HttpResponse) -> bool:
        return (
            settings.DEBUG
            and response.status_code == 200
            and response.get("Content-Type", "").startswith("text/html")
        )

    def _build_manifest(self, request: HttpRequest) -> dict:
        seen: dict[tuple[str, str | None], dict] = {}
        for entry in get_log():
            key = (entry.msgid, entry.context)
            if key not in seen:
                seen[key] = {
                    "msgid": entry.msgid,
                    "msgstr": entry.msgstr,
                    "ctx": entry.context,
                    "translated": entry.translated,
                }
        return {
            "t": list(seen.values()),
            "csrf": get_token(request),
        }

    def _snippet(self, manifest: dict) -> bytes:
        css_url = static("cartouche/editor.css")
        js_url = static("cartouche/editor.js")
        return f"""
<script id="cartouche-data" type="application/json">{json.dumps(manifest)}</script>
<link rel="stylesheet" href="{css_url}">
<script src="{js_url}" defer></script>
""".encode()

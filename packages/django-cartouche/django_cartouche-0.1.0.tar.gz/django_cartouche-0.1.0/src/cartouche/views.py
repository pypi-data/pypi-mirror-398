from __future__ import annotations

import json
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST

from cartouche.compiler import update_translation

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@require_POST
def save(request: HttpRequest) -> HttpResponse:
    if not settings.DEBUG:
        return HttpResponseForbidden()

    data = json.loads(request.body)
    po_path = update_translation(
        msgid=data["msgid"],
        new_msgstr=data["msgstr"],
        locale=data["locale"],
        context=data.get("ctx"),
    )

    if po_path:
        return JsonResponse({"ok": True, "file": str(po_path)})
    return JsonResponse({"ok": False, "error": "msgid not found"}, status=404)

from __future__ import annotations

import pytest
from django.http import HttpResponse
from django.test import RequestFactory


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def html_response() -> HttpResponse:
    response = HttpResponse("<html><body>Hello</body></html>", content_type="text/html")
    response["Content-Length"] = len(response.content)
    return response


@pytest.fixture
def json_response() -> HttpResponse:
    return HttpResponse('{"key": "value"}', content_type="application/json")

from __future__ import annotations

from django.urls import reverse


class TestUrls:
    def test_save_url_resolves(self):
        url = reverse("cartouche:save")
        assert url == "/cartouche/save/"

from __future__ import annotations

from django.apps import AppConfig


class CartoucheConfig(AppConfig):
    name = "cartouche"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self) -> None:
        from django.conf import settings

        if settings.DEBUG:
            from cartouche import tracking

            tracking.install_tracker()

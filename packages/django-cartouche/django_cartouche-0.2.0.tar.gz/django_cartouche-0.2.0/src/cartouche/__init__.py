from __future__ import annotations

from importlib.metadata import version

__version__ = version("django-cartouche")

default_app_config = "cartouche.apps.CartoucheConfig"

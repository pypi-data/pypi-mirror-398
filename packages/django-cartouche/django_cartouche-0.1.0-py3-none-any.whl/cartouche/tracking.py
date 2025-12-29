from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_log: ContextVar[list[TranslationEntry]] = ContextVar("cartouche_log")
_installed: bool = False


@dataclass(slots=True)
class TranslationEntry:
    msgid: str
    msgstr: str
    context: str | None = None


def get_log() -> list[TranslationEntry]:
    try:
        return _log.get()
    except LookupError:
        new_log: list[TranslationEntry] = []
        _log.set(new_log)
        return new_log


def clear_log() -> None:
    _log.set([])


def install_tracker() -> None:
    """Safe to call multiple times; only installs once."""
    global _installed  # noqa: PLW0603
    if _installed:
        return

    from django.utils import translation

    _original_gettext: Callable[[str], str] = translation.gettext
    _original_pgettext: Callable[[str, str], str] = translation.pgettext

    def tracked_gettext(message: str) -> str:
        result = _original_gettext(message)
        if message != result:
            get_log().append(TranslationEntry(msgid=message, msgstr=result))
        return result

    def tracked_pgettext(context: str, message: str) -> str:
        result = _original_pgettext(context, message)
        if message != result:
            get_log().append(TranslationEntry(msgid=message, msgstr=result, context=context))
        return result

    translation.gettext = tracked_gettext
    translation.pgettext = tracked_pgettext

    _installed = True

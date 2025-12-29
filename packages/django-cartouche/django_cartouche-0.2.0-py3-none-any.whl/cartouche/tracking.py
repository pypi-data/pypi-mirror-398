from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_log: ContextVar[list[TranslationEntry]] = ContextVar("cartouche_log")
_installed: bool = False
_original_gettext: Callable[[str], str] | None = None
_original_pgettext: Callable[[str, str], str] | None = None


@dataclass(slots=True)
class TranslationEntry:
    msgid: str
    msgstr: str
    context: str | None = None
    translated: bool = True


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
    global _installed, _original_gettext, _original_pgettext  # noqa: PLW0603
    if _installed:
        return

    from django.utils import translation

    # Force _trans to resolve its lazy backend before we patch.
    # Without this, _trans.gettext wouldn't exist yet.
    _ = translation.gettext("")

    _trans = translation._trans

    # Only capture the real originals once to prevent stacking patches
    if _original_gettext is None:
        _original_gettext = _trans.gettext
        _original_pgettext = _trans.pgettext

    def tracked_gettext(message: str) -> str:
        assert _original_gettext is not None
        result = _original_gettext(message)
        get_log().append(
            TranslationEntry(msgid=message, msgstr=result, translated=(message != result))
        )
        return result

    def tracked_pgettext(context: str, message: str) -> str:
        assert _original_pgettext is not None
        result = _original_pgettext(context, message)
        get_log().append(
            TranslationEntry(
                msgid=message, msgstr=result, context=context, translated=(message != result)
            )
        )
        return result

    _trans.gettext = tracked_gettext
    _trans.pgettext = tracked_pgettext

    _installed = True

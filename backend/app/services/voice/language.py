from __future__ import annotations

"""Language helpers shared by speech-to-text and text-to-speech.

Phase 1 supports Hindi, Kannada and English. ``auto`` keeps Sarvam's
adaptive language detection enabled until the caller locks a language.
"""

SUPPORTED_STT_LANGUAGES: tuple[str, ...] = (
    "auto",
    "hi-IN",
    "kn-IN",
    "en-IN",
)

_ALIASES = {
    "auto": "auto",
    "autodetect": "auto",
    "automatic": "auto",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "hindi": "hi-IN",
    "kn": "kn-IN",
    "kn-in": "kn-IN",
    "kannada": "kn-IN",
    "en": "en-IN",
    "en-in": "en-IN",
    "english": "en-IN",
}


def normalize_language_code(
    value: str | None,
    default: str = "auto",
) -> str:
    """Return a canonical ``auto`` / ``hi-IN`` / ``kn-IN`` / ``en-IN`` code."""

    if value is None or not str(value).strip():
        return default

    key = str(value).strip().replace("_", "-").lower()
    code = _ALIASES.get(key)
    if code is None:
        raise ValueError(
            "Unsupported language "
            f"{value!r}; expected one of "
            + ", ".join(SUPPORTED_STT_LANGUAGES)
        )
    return code


def cartesia_language_code(
    value: str | None,
    default: str = "en-IN",
) -> str:
    """Map a session language to a Cartesia ``language`` value.

    Cartesia speaks ``hi-IN``, ``kn-IN`` and ``en-IN`` natively. ``auto``
    has no meaning for synthesis, so the configured default is used.
    """

    code = normalize_language_code(value, default="auto")
    if code == "auto":
        return default
    return code

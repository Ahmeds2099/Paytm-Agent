"""Decide what a merchant's answer to "which language?" means.

Phase 3 removes automatic language detection from the response path. Until the
merchant answers, every final transcript goes through this gate instead of the
reply model. Keeping the decision pure (transcript in, action out) makes the
unclear path and the never-switch-by-itself rule testable without a socket.

Actions:

* ``lock``       - a language was named; lock it and confirm in that language.
* ``retry``      - unclear on the first try; ask once more, slowly.
* ``default``    - still unclear after the allowed tries; use English and
                   offer a human, as the brief requires.
* ``opt_out``    - the merchant asked not to be called; stop immediately.
* ``human_request`` - the merchant asked for a person before choosing.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.intent import classify_rule, extract_language
from app.services.voice.language import normalize_language_code

MAX_LANGUAGE_ATTEMPTS = 2
FALLBACK_LANGUAGE = "en-IN"


@dataclass(frozen=True)
class LanguageGateResult:
    action: str
    language: str | None
    attempts: int


def detect_language_choice(transcript: str) -> str | None:
    """Return the language named by an explicit choice, or ``None``.

    "Explicit" is the rule classifier's call: a bare language name, or one
    inside a short turn, or one next to a word like *speak* or *language*.
    A stray language word buried in a longer sentence is not a choice, which
    is what keeps the call from switching on its own.
    """

    rule = classify_rule(transcript)
    if rule is not None and rule.label == "language_choice":
        code = rule.slots.get("language") or extract_language(transcript)
        if code:
            try:
                return normalize_language_code(code)
            except ValueError:
                return None
    return None


def resolve_language_gate(
    transcript: str,
    attempts: int,
    *,
    default_language: str = FALLBACK_LANGUAGE,
    max_attempts: int = MAX_LANGUAGE_ATTEMPTS,
) -> LanguageGateResult:
    """Classify one answer during the language-selection state."""

    rule = classify_rule(transcript)
    if rule is not None and rule.label == "opt_out":
        return LanguageGateResult("opt_out", None, attempts)
    if rule is not None and rule.label == "human_request":
        language = rule.slots.get("language") or extract_language(transcript)
        return LanguageGateResult("human_request", language, attempts)

    code = detect_language_choice(transcript)
    if code is not None:
        return LanguageGateResult("lock", code, 0)

    next_attempts = max(0, attempts) + 1
    if next_attempts >= max_attempts:
        try:
            fallback = normalize_language_code(default_language)
        except ValueError:
            fallback = FALLBACK_LANGUAGE
        if fallback == "auto":
            fallback = FALLBACK_LANGUAGE
        return LanguageGateResult("default", fallback, next_attempts)

    return LanguageGateResult("retry", None, next_attempts)


def detect_language_change(transcript: str, current: str | None) -> str | None:
    """Return a new language only when the merchant explicitly asks for one."""

    code = detect_language_choice(transcript)
    if code is None or code == "auto" or code == current:
        return None
    return code

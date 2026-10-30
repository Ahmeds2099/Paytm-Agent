"""Spoken-style guard for assistant replies.

The system prompt asks for short, list-free speech. Models drift, so this
module enforces the two rules that break a voice call most visibly:

* strip written formatting before it reaches text to speech, and
* stop after the sentence budget, offering to continue instead of monologuing.

Sentence budget, per the owner's instruction: aim for three, allow a fourth
when it is a question, and never exceed five.
"""

from __future__ import annotations

import re

from app.core.config import settings

CLOSING_QUESTIONS = {
    "hi-IN": "क्या आप इसके बारे में और जानना चाहेंगे?",
    "kn-IN": "ಇದರ ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ತಿಳಿಯಲು ಬಯಸುವಿರಾ?",
    "en-IN": "Would you like to know more?",
}

APOLOGY_LINES = {
    "hi-IN": (
        "क्षमा करें, मुझे अभी जवाब देने में दिक्कत हो रही है। "
        "क्या आप थोड़ी देर बाद फिर पूछ सकते हैं?"
    ),
    "kn-IN": (
        "ಕ್ಷಮಿಸಿ, ಈಗ ಉತ್ತರಿಸಲು ಸ್ವಲ್ಪ ತೊಂದರೆ ಆಗುತ್ತಿದೆ. "
        "ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಕೇಳಬಹುದೇ?"
    ),
    "en-IN": (
        "Sorry, I'm having trouble answering right now. "
        "Could you ask me again in a moment?"
    ),
}

# A chunk this long is spoken even without a sentence ending, so first audio
# is not held back by a model that writes one long sentence. It is cut at a
# word boundary and does not count against the sentence budget.
MAX_CHUNK_CHARS = 140

_SENTENCE_END = re.compile(r"[.!?।॥]+[\"'”’)\]]*(?=\s|$)")
_ABBREVIATIONS = {"rs", "mr", "mrs", "dr", "no", "vs", "etc", "e.g", "i.e"}


def closing_question(language: str | None) -> str:
    """Localized "would you like to know more?" or an empty string."""

    return CLOSING_QUESTIONS.get(language or "", "")


def apology_line(language: str | None) -> str:
    """Localized spoken apology for a failed model call."""

    return APOLOGY_LINES.get(language or "", APOLOGY_LINES["en-IN"])


def strip_voice_markup(text: str) -> str:
    """Remove formatting that should never be read aloud."""

    if not text:
        return ""

    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.M)
    text = re.sub(
        r"^\s{0,3}(?:[-*+•]|\d+[.)]|\(\d+\))\s+",
        "",
        text,
        flags=re.M,
    )
    text = re.sub(r"^\s*(?:\d+[.)]|[-*+•])\s+", "", text)
    text = re.sub(r"(\*\*|__|\*|_)", "", text)
    text = text.replace("|", " ")
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _is_sentence_boundary(text: str, match: re.Match) -> bool:
    core = text[: match.end()].strip()
    if not core:
        return False

    bare = core.rstrip(".।॥!?\"'”’)] ").strip()
    if not bare:
        return False
    if re.fullmatch(r"\d+", bare):
        # "1." at the start of a numbered step is a list marker, not a stop.
        return False
    if bare.lower() in _ABBREVIATIONS:
        return False
    return True


def split_first_sentence(text: str) -> tuple[str | None, str]:
    """Return ``(sentence, remainder)`` or ``(None, text)``."""

    for match in _SENTENCE_END.finditer(text):
        if _is_sentence_boundary(text, match):
            return text[: match.end()].strip(), text[match.end() :]
    return None, text


def split_sentences(text: str) -> list[str]:
    """Split into spoken sentences, tolerating Devanagari and Kannada stops."""

    sentences: list[str] = []
    remainder = strip_voice_markup(text)

    while remainder:
        sentence, rest = split_first_sentence(remainder)
        if sentence is None:
            tail = strip_voice_markup(remainder)
            if tail:
                sentences.append(tail)
            break
        cleaned = strip_voice_markup(sentence)
        if cleaned:
            sentences.append(cleaned)
        remainder = rest.lstrip()

    return sentences


def count_sentences(text: str) -> int:
    return len(split_sentences(text))


class VoiceReplyGuard:
    """Streaming reply guard that enforces markup and sentence rules."""

    def __init__(
        self,
        language: str | None = None,
        soft: int | None = None,
        max_sentences: int | None = None,
    ) -> None:
        self.language = language
        self.soft = soft or settings.VOICE_REPLY_SOFT_SENTENCES
        self.max = max_sentences or settings.VOICE_REPLY_MAX_SENTENCES
        self.buffer = ""
        self.units = 0
        self.finished = False

    def feed(self, token: str) -> list[str]:
        """Accept a token and return any sentences approved for speech."""

        if self.finished or not token:
            return []

        self.buffer += token
        approved: list[str] = []

        while not self.finished:
            sentence, rest = split_first_sentence(self.buffer)

            if sentence is not None:
                self.buffer = rest
                cleaned = strip_voice_markup(sentence)
                if cleaned:
                    approved.extend(self._approve(cleaned, counts=True))
                continue

            if len(self.buffer) < MAX_CHUNK_CHARS:
                break

            chunk, rest = self._cut_at_word(self.buffer)
            self.buffer = rest
            cleaned = strip_voice_markup(chunk)
            if cleaned:
                approved.extend(self._approve(cleaned, counts=False))

        if self.finished:
            self.buffer = ""

        return approved

    def flush(self) -> list[str]:
        """Release whatever is buffered when the model stops."""

        if self.finished:
            return []

        text = strip_voice_markup(self.buffer)
        self.buffer = ""

        if not text:
            return []

        return self._approve(text, counts=True)

    @staticmethod
    def _cut_at_word(text: str) -> tuple[str, str]:
        cut = text.rfind(" ", 0, MAX_CHUNK_CHARS)
        if cut <= 0:
            cut = MAX_CHUNK_CHARS
        return text[:cut].rstrip(), text[cut:].lstrip()

    def _approve(self, sentence: str, counts: bool = True) -> list[str]:
        if not counts:
            # A continuation of a long sentence: speak it, but do not spend a
            # sentence from the budget.
            return [sentence]

        is_question = sentence.rstrip().endswith("?")
        next_unit = self.units + 1

        if next_unit <= self.soft:
            self.units = next_unit
            return [sentence]

        if next_unit <= self.max and is_question:
            self.units = next_unit
            if next_unit >= self.max:
                self.finished = True
            return [sentence]

        # Budget spent and the next unit is not a question. Close with a short
        # offer instead of continuing.
        self.finished = True
        question = closing_question(self.language)

        if question and self.units < self.max:
            self.units += 1
            return [question]

        return []


def apply_reply_budget(text: str, language: str | None = None) -> str:
    """Apply the guard to a complete reply, for non-streaming callers."""

    guard = VoiceReplyGuard(language=language)
    parts = guard.feed(strip_voice_markup(text))
    parts.extend(guard.flush())
    return " ".join(parts).strip()

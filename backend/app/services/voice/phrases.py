"""Fixed spoken phrases for the language-selection step.

Every line is short enough to be read aloud once and understood on a phone
call. The greeting is deliberately trilingual because it runs before the
merchant has chosen a language: it introduces the assistant, gives the
recording notice, and asks the one question this phase exists to answer.

Keeping the text here (instead of inline in the handler) means the same string
is used to pre-render the audio and to show it in the transcript, so the two
can never drift apart.
"""

from __future__ import annotations

# Phrase id -> language -> text.
PHRASES: dict[str, dict[str, str]] = {
    "greeting": {
        "hi-IN": (
            "नमस्ते, पेटीएम वॉइस असिस्टेंट। "
            "यह कॉल रिकॉर्ड हो सकती है। "
            "हिंदी, कन्नड़ या अंग्रेज़ी?"
        ),
        "kn-IN": (
            "ನಮಸ್ಕಾರ, ಪೇಟಿಎಂ ಧ್ವನಿ ಸಹಾಯಕ. "
            "ಈ ಕರೆ ರೆಕಾರ್ಡ್ ಆಗಬಹುದು. "
            "ಹಿಂದಿ, ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್?"
        ),
        "en-IN": (
            "Hello, Paytm voice assistant. "
            "This call may be recorded. "
            "Hindi, Kannada or English?"
        ),
    },
    "confirm": {
        "hi-IN": (
            "ठीक है, अब हिंदी में बात करेंगे। "
            "बताइए, क्या मदद कर सकता हूँ?"
        ),
        "kn-IN": (
            "ಸರಿ, ಇನ್ನು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತೇವೆ. "
            "ಹೇಳಿ, ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
        ),
        "en-IN": (
            "Okay, we will continue in English. "
            "How can I help you?"
        ),
    },
    "changed": {
        "hi-IN": "ठीक है, अब हिंदी में बात करेंगे।",
        "kn-IN": "ಸರಿ, ಇನ್ನು ನಾವು ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡುತ್ತೇವೆ.",
        "en-IN": "Okay, we will continue in English.",
    },
    "retry": {
        "hi-IN": "समझ नहीं आया। हिंदी, कन्नड़ या अंग्रेज़ी?",
        "kn-IN": "ಅರ್ಥ ಆಗಲಿಲ್ಲ. ಹಿಂದಿ, ಕನ್ನಡ ಅಥವಾ ಇಂಗ್ಲಿಷ್?",
        "en-IN": "I did not catch that. Hindi, Kannada or English?",
    },
    # Spoken when two tries did not resolve a language. English is the
    # fallback the brief asks for, plus the offer of a human.
    "default_english": {
        "en-IN": (
            "No problem, I will continue in English. "
            "If you prefer, I can also connect you to a human colleague."
        ),
    },
    "opt_out": {
        "hi-IN": "ठीक है, मैं आपको और कॉल नहीं करूँगा। धन्यवाद।",
        "kn-IN": "ಸರಿ, ನಾನು ನಿಮಗೆ ಇನ್ನು ಕರೆ ಮಾಡುವುದಿಲ್ಲ. ಧನ್ಯವಾದ.",
        "en-IN": "Okay, I will not call you again. Thank you.",
    },
    "human_request": {
        "hi-IN": "ठीक है, मैं आपको एक साथी से जोड़ता हूँ।",
        "kn-IN": "ಸರಿ, ನಾನು ನಿಮ್ಮನ್ನು ಒಬ್ಬ ಸಹೋದ್ಯೋಗಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತೇನೆ.",
        "en-IN": "Okay, I will connect you to a human colleague.",
    },
}

LANGUAGE_NAMES: dict[str, str] = {
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "en-IN": "English",
}

# Order the trilingual greeting plays in. Hindi and Kannada first signals that
# both are real options; English closes because it is the fallback.
GREETING_ORDER: tuple[str, ...] = ("hi-IN", "kn-IN", "en-IN")


def phrase_text(phrase_id: str, language: str) -> str:
    """Return the text for a phrase, falling back to English."""

    by_language = PHRASES.get(phrase_id, {})
    return by_language.get(language) or by_language.get("en-IN", "")


def phrase_languages(phrase_id: str) -> tuple[str, ...]:
    return tuple(PHRASES.get(phrase_id, {}).keys())


def required_clips(phrase_id: str) -> tuple[tuple[str, str], ...]:
    """(phrase_id, language) pairs that should be pre-rendered."""

    return tuple((phrase_id, language) for language in phrase_languages(phrase_id))

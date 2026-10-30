"""Fixed spoken phrases for the language-selection step.

Every line is short enough to be read aloud once and understood on a phone
call. The greeting is a single English line that asks the merchant which
language they prefer. Retry remains trilingual so merchants who did not
understand the English prompt still get a chance in their language.

Keeping the text here (instead of inline in the handler) means the same string
is used to pre-render the audio and to show it in the transcript, so the two
can never drift apart.
"""

from __future__ import annotations

# Phrase id -> language -> text.
PHRASES: dict[str, dict[str, str]] = {
    "greeting": {
        # Owner decision 2026-10-30: single English line, with Paytm welcome prefix.
        # Retry stays trilingual so non-English speakers still get a second chance.
        "en-IN": "Hello and welcome to Paytm. Would you be comfortable in English, Hindi or Kannada?",
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
    "demo_open_opt_out": {
        "hi-IN": (
            "हम Paytm से आपके व्यवसाय के लिए एक विशेष ऋण ऑफ़र के बारे में "
            "बात करने के लिए कॉल कर रहे हैं। क्या आप इसके बारे में सुनना चाहेंगी?"
        ),
        "kn-IN": (
            "ನಿಮ್ಮ ವ್ಯವಹಾರಕ್ಕಾಗಿ ವಿಶೇಷ ಸಾಲದ ಆಫರ್ ಕುರಿತು ಮಾತನಾಡಲು Paytm ನಿಂದ ಕರೆ "
            "ಮಾಡುತ್ತಿದ್ದೇವೆ. ಇದರ ಬಗ್ಗೆ ಕೇಳಲು ಆಸಕ್ತಿ ಇದೆಯೇ?"
        ),
        "en-IN": (
            "We're calling from Paytm with a promotional loan offer for your "
            "business. Would you be interested in hearing more?"
        ),
    },
    "demo_opt_out_ack": {
        "hi-IN": (
            "ठीक है, मैंने इस ऋण ऑफ़र के लिए आपकी पसंद दर्ज कर ली है और आगे "
            "प्रचार संबंधी कॉल नहीं किए जाएंगे। धन्यवाद। अलविदा।"
        ),
        "kn-IN": (
            "ಸರಿ, ಈ ಸಾಲದ ಆಫರ್‌ಗಾಗಿ ನಿಮ್ಮ ಆಯ್ಕೆಯನ್ನು ದಾಖಲಿಸಿದ್ದೇನೆ. ಇನ್ನು ಮುಂದೆ "
            "ಪ್ರಚಾರದ ಕರೆಗಳು ಬರುವುದಿಲ್ಲ. ಧನ್ಯವಾದಗಳು. ನಮಸ್ಕಾರ."
        ),
        "en-IN": (
            "Understood. I've recorded your choice and you will not receive "
            "further promotional calls. Thank you. Goodbye."
        ),
    },
    "opt_out_save_failed": {
        "hi-IN": (
            "माफ़ कीजिए, मैं इस अनुरोध को डेमो रिकॉर्ड में सहेज नहीं पाया। "
            "मैं अभी यह कॉल समाप्त कर रहा हूँ।"
        ),
        "kn-IN": (
            "ಕ್ಷಮಿಸಿ, ಈ ವಿನಂತಿಯನ್ನು ಡೆಮೋ ದಾಖಲೆಯಲ್ಲಿ ಉಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. "
            "ನಾನು ಈಗ ಈ ಕರೆಯನ್ನು ಮುಕ್ತಾಯಗೊಳಿಸುತ್ತೇನೆ."
        ),
        "en-IN": (
            "I'm sorry, I couldn't save this request in the demo record. "
            "I'm ending this call now."
        ),
    },
    "settlement_priority_offer": {
        "hi-IN": (
            "मैं समझती हूँ कि आपको आज पैसों की ज़रूरत है। क्या आप चाहेंगी "
            "कि मैं इसे प्राथमिकता टिकट के रूप में दर्ज करूँ?"
        ),
        "kn-IN": (
            "ನಿಮಗೆ ಇಂದು ಹಣದ ಅಗತ್ಯವಿದೆ ಎಂಬುದನ್ನು ನಾನು ಅರ್ಥಮಾಡಿಕೊಂಡಿದ್ದೇನೆ. "
            "ಇದನ್ನು ಆದ್ಯತೆಯ ಟಿಕೆಟ್ ಆಗಿ ದಾಖಲಿಸಬೇಕೇ?"
        ),
        "en-IN": (
            "I understand you need the money today. Would you like me to "
            "raise a priority support ticket?"
        ),
    },
}

LANGUAGE_NAMES: dict[str, str] = {
    "hi-IN": "Hindi",
    "kn-IN": "Kannada",
    "en-IN": "English",
}

# Owner decision 2026-10-30: greeting is now a single English line.
# Retry phrases remain trilingual for merchants who did not understand English.
GREETING_ORDER: tuple[str, ...] = ("en-IN",)


def phrase_text(phrase_id: str, language: str) -> str:
    """Return the text for a phrase, falling back to English."""

    by_language = PHRASES.get(phrase_id, {})
    return by_language.get(language) or by_language.get("en-IN", "")


def phrase_languages(phrase_id: str) -> tuple[str, ...]:
    return tuple(PHRASES.get(phrase_id, {}).keys())


def required_clips(phrase_id: str) -> tuple[tuple[str, str], ...]:
    """(phrase_id, language) pairs that should be pre-rendered."""

    return tuple((phrase_id, language) for language in phrase_languages(phrase_id))

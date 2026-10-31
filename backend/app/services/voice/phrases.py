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
    "demo_greeting_opt_out": {
        "en-IN": (
            "Hello, this call is from Paytm. Would you be comfortable "
            "continuing in English, Hindi or Kannada?"
        ),
    },
    "confirm": {
        "hi-IN": (
            "ठीक है, अब हिंदी में बात करेंगे। "
            "बताइए, मैं आपकी क्या मदद कर सकती हूँ?"
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
        "hi-IN": "ठीक है, मैं आपको इस ऑफ़र के लिए दोबारा कॉल नहीं करूँगी। धन्यवाद।",
        "kn-IN": "ಸರಿ, ನಾನು ನಿಮಗೆ ಇನ್ನು ಕರೆ ಮಾಡುವುದಿಲ್ಲ. ಧನ್ಯವಾದ.",
        "en-IN": "Okay, I will not call you again. Thank you.",
    },
    "human_request": {
        "hi-IN": "ठीक है, मैं आपको एक वरिष्ठ सहयोगी से जोड़ती हूँ।",
        "kn-IN": "ಸರಿ, ನಾನು ನಿಮ್ಮನ್ನು ಒಬ್ಬ ಸಹೋದ್ಯೋಗಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತೇನೆ.",
        "en-IN": "Okay, I will connect you to a human colleague.",
    },
    "human_request_deferred": {
        "hi-IN": (
            "मैं आपकी समस्या हल करने की कोशिश कर सकती हूँ। बताइए, आपको "
            "किस चीज़ में मदद चाहिए?"
        ),
        "kn-IN": (
            "ನಿಮ್ಮ ಸಮಸ್ಯೆಯನ್ನು ಪರಿಹರಿಸಲು ನಾನು ಪ್ರಯತ್ನಿಸಬಹುದು. ಯಾವ ವಿಷಯದಲ್ಲಿ "
            "ಸಹಾಯ ಬೇಕು ಎಂದು ಹೇಳಿ?"
        ),
        "en-IN": (
            "I can try to resolve your issue. What do you need help with?"
        ),
    },
    "human_request_escalated": {
        "hi-IN": (
            "ठीक है, मैं इस कॉल को वरिष्ठ सहयोगी के पास आगे बढ़ा रही हूँ। "
            "आपकी समस्या पर मानवीय सहायता के लिए ध्यान दिया जाएगा।"
        ),
        "kn-IN": (
            "ಸರಿ, ಈ ಕರೆಯನ್ನು ಹಿರಿಯ ಸಹೋದ್ಯೋಗಿಗೆ ಮುಂದಕ್ಕೆ ಕಳುಹಿಸುತ್ತಿದ್ದೇನೆ. "
            "ನಿಮ್ಮ ಸಮಸ್ಯೆಗೆ ಮಾನವ ಸಹಾಯಕ್ಕಾಗಿ ಗಮನ ನೀಡಲಾಗುತ್ತದೆ."
        ),
        "en-IN": (
            "Understood. I'm escalating this call for a senior colleague "
            "to follow up."
        ),
    },
    "refund_approval_request": {
        "hi-IN": (
            "मुझे TXN004 का ₹2,400 का भुगतान मिला है। रिफंड आगे बढ़ाने से "
            "पहले आपकी पुष्टि चाहिए। क्या मैं इसे मानवीय स्वीकृति के लिए भेजूँ?"
        ),
        "kn-IN": (
            "TXN004 ರ ₹2,400 ಪಾವತಿ ಕಂಡುಬಂದಿದೆ. ಮರುಪಾವತಿಯನ್ನು ಮುಂದುವರಿಸುವ "
            "ಮೊದಲು ನಿಮ್ಮ ದೃಢೀಕರಣ ಬೇಕು. ಮಾನವ ಅನುಮೋದನೆಗೆ ಕಳುಹಿಸಬೇಕೇ?"
        ),
        "en-IN": (
            "I found payment TXN004 for 2,400 rupees. Before taking any "
            "refund action, please confirm: should I send this request for "
            "human approval?"
        ),
    },
    "refund_approval_submitted": {
        "hi-IN": (
            "आपका ₹2,400 का रिफंड अनुरोध दर्ज कर दिया है। इस पर ध्यान देना "
            "ज़रूरी है और मानवीय स्वीकृति आवश्यक है। अभी रिफंड शुरू नहीं हुआ है।"
        ),
        "kn-IN": (
            "ನಿಮ್ಮ ₹2,400 ಮರುಪಾವತಿ ವಿನಂತಿಯನ್ನು ದಾಖಲಿಸಿದ್ದೇನೆ. ಇದಕ್ಕೆ ಗಮನ "
            "ಅಗತ್ಯವಿದೆ ಮತ್ತು ಮಾನವ ಅನುಮೋದನೆ ಬೇಕು. ಮರುಪಾವತಿ ಇನ್ನೂ ಪ್ರಾರಂಭವಾಗಿಲ್ಲ."
        ),
        "en-IN": (
            "Your 2,400-rupee refund request is recorded for attention and "
            "requires human approval. The refund has not been initiated."
        ),
    },
    "refund_approval_declined": {
        "hi-IN": "ठीक है, मैंने रिफंड अनुरोध आगे नहीं भेजा है।",
        "kn-IN": "ಸರಿ, ಮರುಪಾವತಿ ವಿನಂತಿಯನ್ನು ಮುಂದಕ್ಕೆ ಕಳುಹಿಸಿಲ್ಲ.",
        "en-IN": "Okay, I have not submitted the refund request.",
    },
    "transaction_id_required": {
        "hi-IN": "कृपया वह ट्रांज़ैक्शन आईडी बताइए, जिसके बारे में आप पूछ रहे हैं।",
        "kn-IN": "ದಯವಿಟ್ಟು ನೀವು ಕೇಳುತ್ತಿರುವ ವಹಿವಾಟಿನ ಐಡಿ ತಿಳಿಸಿ.",
        "en-IN": "Please tell me the transaction ID you want me to check.",
    },
    "refund_transaction_not_found": {
        "hi-IN": "मुझे यह ट्रांज़ैक्शन नहीं मिला। कृपया आईडी जाँचकर फिर से बताइए।",
        "kn-IN": "ಈ ವಹಿವಾಟು ಕಂಡುಬಂದಿಲ್ಲ. ದಯವಿಟ್ಟು ಐಡಿಯನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತೆ ತಿಳಿಸಿ.",
        "en-IN": "I couldn't find that transaction. Please check the ID and tell me again.",
    },
    "refund_amount_unavailable": {
        "hi-IN": "मुझे इस ट्रांज़ैक्शन की राशि की पुष्टि नहीं हो पाई, इसलिए मैंने रिफंड अनुरोध नहीं भेजा है।",
        "kn-IN": "ಈ ವಹಿವಾಟಿನ ಮೊತ್ತವನ್ನು ಖಚಿತಪಡಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ, ಆದ್ದರಿಂದ ಮರುಪಾವತಿ ವಿನಂತಿಯನ್ನು ಕಳುಹಿಸಿಲ್ಲ.",
        "en-IN": "I couldn't verify the transaction amount, so I have not submitted a refund request.",
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
    "settlement_priority_declined": {
        "hi-IN": "ठीक है, मैंने प्राथमिकता टिकट नहीं बनाया है।",
        "kn-IN": "ಸರಿ, ಆದ್ಯತೆಯ ಟಿಕೆಟ್ ರಚಿಸಿಲ್ಲ.",
        "en-IN": "Okay, I have not created a priority ticket.",
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

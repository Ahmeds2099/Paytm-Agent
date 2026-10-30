"""Intent classification for merchant telecalling.

Two paths:

* a deterministic rule fast path for the labels where a mistake is costly
  (opt-out, human request, callback, language choice, yes/no), and
* one JSON call to the reply model for everything else.

Rules run first and win. They are deliberately narrow: a rule only fires on
phrases that mean one thing in a collections call, so a miss falls through to
the model instead of producing a confident wrong label.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

INTENTS: tuple[str, ...] = (
    "settlement_query",
    "transaction_issue",
    "qr_code_issue",
    "device_issue",
    "refund_query",
    "loan_interest",
    "soundbox_issue",
    "charges_query",
    "onboarding_kyc",
    "language_choice",
    "confirmation_yes",
    "confirmation_no",
    "human_request",
    "callback_request",
    "opt_out",
    "objection",
    "other",
)

SAFETY_INTENTS: tuple[str, ...] = (
    "opt_out",
    "human_request",
    "callback_request",
    "language_choice",
    "confirmation_yes",
    "confirmation_no",
)

INTENT_DESCRIPTIONS = {
    "settlement_query": "when or how settlement money will arrive",
    "transaction_issue": "a payment that failed, is stuck or shows the wrong status",
    "qr_code_issue": "a Paytm QR code that does not scan, display or work",
    "device_issue": "a device that is not powering on, connecting or working",
    "refund_query": "a refund that has not arrived or its status",
    "loan_interest": "interest in a merchant loan, eligibility or EMI",
    "soundbox_issue": "a soundbox that is silent, wrong or offline",
    "charges_query": "fees, deductions or charges on a transaction",
    "onboarding_kyc": "signing up, KYC, documents or account setup",
    "language_choice": "the merchant names the language they want",
    "confirmation_yes": "a clear yes, agreement or confirmation",
    "confirmation_no": "a clear no, refusal or disagreement",
    "human_request": "a request to speak to a person or support agent",
    "callback_request": "a request to be called back or called later",
    "opt_out": "a request to stop calling, not interested, remove the number",
    "objection": "a doubt, hesitation, price concern or pushback",
    "other": "anything else, including greetings and small talk",
}

_LANGUAGE_PATTERNS = (
    (
        "hi-IN",
        re.compile(r"\bhindi\b|हिंदी|हिन्दी|ಹಿಂದಿ", re.I),
    ),
    (
        "kn-IN",
        re.compile(r"\bkannada\b|ಕನ್ನಡ|कन्नड़|कन्नड", re.I),
    ),
    (
        "en-IN",
        re.compile(r"\benglish\b|अंग्रेजी|इंग्लिश|ಇಂಗ್ಲಿಷ್|ಆಂಗ್ಲ", re.I),
    ),
)

_LANGUAGE_CONTEXT = re.compile(
    r"\b(?:language|speak|talk|bol)\b|बोल|भाषा|ಮಾತನಾಡ|ಭಾಷೆ",
    re.I,
)

# Ordered: earlier rules win. Opt-out and human requests are checked before a
# bare yes/no so "no, stop calling me" is an opt-out, not a confirmation.
_RULES: tuple[tuple[str, tuple[re.Pattern, ...]], ...] = (
    (
        "opt_out",
        (
            re.compile(
                r"\b(?:stop calling|don'?t call|do not call|never call|"
                r"remove (?:my|this) number|unsubscribe|opt out|"
                r"not interested|no interest)\b",
                re.I,
            ),
            re.compile(
                r"(?:कॉल मत करो|कॉल मत करें|फोन मत करो|मुझे कॉल न करें|"
                r"बंद करो|दिलचस्पी नहीं|इंटरेस्ट नहीं|नंबर हटाओ)"
            ),
            re.compile(
                r"(?:ಕರೆ ಮಾಡಬೇಡಿ|ಕರೆ ಮಾಡಬೇಡ|ಫೋನ್ ಮಾಡಬೇಡಿ|ನಿಲ್ಲಿಸಿ|"
                r"ಆಸಕ್ತಿ ಇಲ್ಲ|ಇಷ್ಟ ಇಲ್ಲ|ನಂಬರ್ ತೆಗೆಯಿರಿ)"
            ),
        ),
    ),
    (
        "human_request",
        (
            re.compile(
                r"\b(?:human|real person|representative|customer care|"
                r"customer support|support agent|talk to (?:an|a) agent)\b",
                re.I,
            ),
            re.compile(r"(?:इंसान|व्यक्ति से बात|एजेंट|कस्टमर केयर|ग्राहक सेवा)"),
            re.compile(
                r"(?:ಮನುಷ್ಯ|ಮಾನವ|ವ್ಯಕ್ತಿ ಜೊತೆ|ಏಜೆಂಟ್|ಗ್ರಾಹಕ ಸೇವೆ)"
            ),
        ),
    ),
    (
        "callback_request",
        (
            re.compile(
                r"\b(?:call me back|call back|call later|call me later|"
                r"call me tomorrow|call me after|call after)\b",
                re.I,
            ),
            re.compile(r"(?:बाद में कॉल|फिर कॉल|कल कॉल|कॉल करना)"),
            re.compile(r"(?:ನಂತರ ಕರೆ|ಮತ್ತೆ ಕರೆ|ನಾಳೆ ಕರೆ|ಕರೆ ಮಾಡಿ)"),
        ),
    ),
    (
        "confirmation_no",
        (
            re.compile(
                r"^\s*(?:no|nope|nah|not now|not really)\b",
                re.I,
            ),
            re.compile(r"^\s*(?:नहीं|नहि|ना)"),
            re.compile(r"^\s*(?:ಇಲ್ಲ|ಬೇಡ)"),
        ),
    ),
    (
        "confirmation_yes",
        (
            re.compile(
                r"^\s*(?:yes|yeah|yep|ok|okay|sure|haan|han|ha|"
                r"sahi|theek|thik)\b",
                re.I,
            ),
            re.compile(r"^\s*(?:हाँ|हां|जी|ठीक|सही)"),
            re.compile(r"^\s*(?:ಹೌದು|ಸರಿ|ಆಗಲಿ)"),
        ),
    ),
)

_AMOUNT = re.compile(
    r"(?:₹|rs\.?|inr|rupees?|रुपये|ರೂಪಾಯಿ|ರೂ\.?)\s*"
    r"([\d][\d,]*(?:\.\d+)?)"
    r"|([\d][\d,]*(?:\.\d+)?)\s*"
    r"(?:rupees?|रुपये|ರೂಪಾಯಿ)",
    re.I,
)
_TXN_ID = re.compile(
    r"\b(?:txn|transaction|utr|order|ref(?:erence)?)\s*"
    r"(?:id|no|number)?\s*[:\-]?\s*([a-z0-9]{6,})\b",
    re.I,
)
_DATE = re.compile(
    r"\b(today|tomorrow|yesterday|this week|next week|"
    r"kal|aaj|आज|कल|इस हफ्ते|ಇಂದು|ನಾಳೆ|ನಿನ್ನೆ)\b",
    re.I,
)
_PHONE = re.compile(r"(?:\+91[\s-]?)?\b([6-9]\d{9})\b")
_TIME = re.compile(
    r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje|बजे|ಗಂಟೆ)\b",
    re.I,
)
_PRODUCT = re.compile(
    r"\b(qr|soundbox|sound box|speaker|device|machine|loan|settlement)\b",
    re.I,
)


@dataclass
class IntentResult:
    label: str
    confidence: float = 0.0
    slots: dict[str, Any] = field(default_factory=dict)
    source: str = "fallback"
    raw: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.label,
            "confidence": self.confidence,
            "slots": self.slots,
            "source": self.source,
        }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def extract_language(text: str) -> str | None:
    for code, pattern in _LANGUAGE_PATTERNS:
        if pattern.search(text):
            return code
    return None


def extract_slots(text: str) -> dict[str, Any]:
    """Pull the few slots a collections turn actually needs."""

    slots: dict[str, Any] = {}
    normalized = _normalize(text)

    amount = _AMOUNT.search(normalized)
    if amount:
        value = amount.group(1) or amount.group(2)
        slots["amount"] = value.replace(",", "")

    txn = _TXN_ID.search(normalized)
    if txn:
        slots["transaction_id"] = txn.group(1)

    date = _DATE.search(normalized)
    if date:
        slots["date"] = date.group(1)

    phone = _PHONE.search(normalized)
    if phone:
        slots["phone"] = phone.group(1)

    time_match = _TIME.search(normalized)
    if time_match:
        hour, minute, marker = time_match.groups()
        slots["time"] = f"{hour}:{minute or '00'} {marker.lower()}"

    product = _PRODUCT.search(normalized)
    if product:
        slots["product"] = product.group(1).lower().replace(" ", "_")

    language = extract_language(normalized)
    if language:
        slots["language"] = language

    return slots


def classify_rule(transcript: str) -> IntentResult | None:
    """Return a high-precision rule match, or ``None`` to ask the model."""

    text = _normalize(transcript)
    if not text:
        return IntentResult(label="other", confidence=0.0, source="rule")

    for label, patterns in _RULES:
        if any(pattern.search(text) for pattern in patterns):
            slots = extract_slots(text)
            if label == "language_choice" or "language" in slots:
                slots.setdefault("language", extract_language(text))
            return IntentResult(
                label=label,
                confidence=0.95,
                slots={k: v for k, v in slots.items() if v is not None},
                source="rule",
            )

    language = extract_language(text)
    if language:
        words = text.split()
        if len(words) <= 6 or _LANGUAGE_CONTEXT.search(text):
            return IntentResult(
                label="language_choice",
                confidence=0.9,
                slots={"language": language},
                source="rule",
            )

    return None


def _classifier_system_prompt() -> str:
    labels = "\n".join(
        f"- {label}: {description}"
        for label, description in INTENT_DESCRIPTIONS.items()
    )
    return (
        "Classify one turn from a Paytm merchant telecalling call. "
        "Return JSON only, shaped exactly as "
        '{"intent": "<label>", "confidence": <0 to 1>}. '
        "Choose exactly one label from this list:\n"
        f"{labels}\n"
        "Use other when nothing fits. Do not explain."
    )


def classify(
    transcript: str,
    language: str | None = None,
    llm: Any | None = None,
) -> IntentResult:
    """Classify a turn, preferring the deterministic rules."""

    rule = classify_rule(transcript)
    if rule is not None:
        return rule

    slots = extract_slots(transcript)

    if llm is None:
        return IntentResult(
            label="other",
            confidence=0.0,
            slots=slots,
            source="fallback",
        )

    try:
        payload = llm.complete_json(
            system=_classifier_system_prompt(),
            user=transcript,
            max_tokens=80,
        )
    except Exception:
        payload = None

    if not isinstance(payload, dict):
        return IntentResult(
            label="other",
            confidence=0.0,
            slots=slots,
            source="fallback",
        )

    label = str(payload.get("intent") or "").strip()
    if label not in INTENTS:
        return IntentResult(
            label="other",
            confidence=0.0,
            slots=slots,
            source="fallback",
            raw=payload,
        )

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return IntentResult(
        label=label,
        confidence=max(0.0, min(1.0, confidence)),
        slots=slots,
        source="llm",
        raw=payload,
    )

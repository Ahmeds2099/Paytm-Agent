"""Intent classification for merchant telecalling.

The label set is the one in the brief (section 5.3), one label per merchant
turn with a confidence value. Alongside the label the classifier returns a
``topic``: the concrete merchant issue, when the turn names one. The label
decides what Phase 4 is allowed to do; the topic decides what the answer is
about. Keeping them apart means a stuck payment and a late settlement are
still one label (the brief only has one money-movement label) without losing
the detail needed to answer.

Two classification paths:

* a deterministic rule fast path for the turns where a mistake is costly
  (opt-out, human request, callback, language choice, yes/no, ticket request,
  repeat complaint), and
* one JSON call to the reply model for everything else.

Rules run first and win. They are deliberately narrow: a rule only fires on
phrases that mean one thing in a collections call, so a miss falls through to
the model instead of producing a confident wrong label.

Topic to usual label, for callers that need a hint:

| topic             | usual label      | why |
| ----------------- | ---------------- | --- |
| soundbox_issue    | device_issue     | the brief's device fault |
| qr_code_issue     | policy_question  | answered from troubleshooting policy |
| charges_query     | policy_question  | answered from the fee policy |
| onboarding_kyc    | policy_question  | answered from the KYC policy |
| refund_query      | out_of_scope     | money-related, escalate to a human |
| transaction_issue | out_of_scope     | money-related, escalate to a human |

``out_of_scope`` is also the safe fallback when the model fails, because Phase
4 escalates on it rather than guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Brief section 5.3, exactly: one label per turn.
INTENTS: tuple[str, ...] = (
    "language_choice",
    "settlement_query",
    "device_issue",
    "ticket_request",
    "loan_interest",
    "device_offer_interest",
    "policy_question",
    "callback_request",
    "human_request",
    "repeat_complaint",
    "objection",
    "opt_out",
    "confirmation_yes",
    "confirmation_no",
    "smalltalk",
    "out_of_scope",
)

# Labels that must never depend on the model: a wrong answer here costs the
# merchant money, their consent, or a promised ticket.
CRITICAL_INTENTS: tuple[str, ...] = (
    "opt_out",
    "human_request",
    "callback_request",
    "language_choice",
    "confirmation_yes",
    "confirmation_no",
    "ticket_request",
    "repeat_complaint",
)

# Kept under the old name so existing imports keep working.
SAFETY_INTENTS = CRITICAL_INTENTS

# Concrete merchant issue, carried next to the label. Not every turn has one.
TOPICS: tuple[str, ...] = (
    "transaction_issue",
    "qr_code_issue",
    "refund_query",
    "soundbox_issue",
    "charges_query",
    "onboarding_kyc",
)

EXPECTED_INTENT_FOR_TOPIC = {
    "transaction_issue": "out_of_scope",
    "refund_query": "out_of_scope",
    "qr_code_issue": "policy_question",
    "charges_query": "policy_question",
    "onboarding_kyc": "policy_question",
    "soundbox_issue": "device_issue",
}

INTENT_DESCRIPTIONS = {
    "language_choice": "the merchant states a language preference",
    "settlement_query": "settlement delay, amount, date or reason",
    "device_issue": "soundbox or card machine fault",
    "ticket_request": "the merchant wants a complaint or ticket raised",
    "loan_interest": "interest in or questions about a merchant loan",
    "device_offer_interest": "interest in another device or plan",
    "policy_question": "a question answered from approved policy text",
    "callback_request": "the merchant wants a call later",
    "human_request": "the merchant asks for a person",
    "repeat_complaint": "the problem is not fixed or has happened before",
    "objection": "a concern about a sales offer: cost, trust or timing",
    "opt_out": "the merchant does not want sales calls or offers",
    "confirmation_yes": "a clear yes, agreement or confirmation",
    "confirmation_no": "a clear no, refusal or disagreement",
    "smalltalk": "a greeting or small talk, no request",
    "out_of_scope": "anything not handled here, including money-related asks",
}

TOPIC_DESCRIPTIONS = {
    "transaction_issue": "a payment that failed, is stuck or shows the wrong status",
    "qr_code_issue": "a Paytm QR code that does not scan, display or work",
    "refund_query": "a refund that has not arrived or its status",
    "soundbox_issue": "a soundbox that is silent, wrong or offline",
    "charges_query": "fees, deductions or charges on a transaction",
    "onboarding_kyc": "signing up, KYC, documents or account setup",
}

_LANGUAGE_PATTERNS = (
    (
        "hi-IN",
        re.compile(
            r"(?<![a-z])(?:hindi|hindhi|hindee)(?![a-z])|हिंदी|हिन्दी|ಹಿಂದಿ",
            re.I,
        ),
    ),
    (
        "kn-IN",
        re.compile(
            r"(?<![a-z])(?:kannada|kannad|kannadam)(?![a-z])|ಕನ್ನಡ|कन्नड़|कन्नड",
            re.I,
        ),
    ),
    (
        "en-IN",
        re.compile(
            r"(?<![a-z])(?:english|inglish|angrezi|angreji)(?![a-z])|"
            r"अंग्रेजी|इंग्लिश|ಇಂಗ್ಲಿಷ್|ಆಂಗ್ಲ",
            re.I,
        ),
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
        "ticket_request",
        (
            re.compile(
                r"\b(?:raise|file|create|open|register|lodge|book)\b"
                r"[^.!?]{0,24}\b(?:complaint|ticket)\b"
                r"|\b(?:complaint|ticket)\s+(?:number|id)\b",
                re.I,
            ),
            re.compile(
                r"(?:शिकायत|कंप्लेंट|टिकट)[^.!?।]{0,14}"
                r"(?:दर्ज|बनाइए|बनवाइए|नंबर|चाहिए)"
            ),
            re.compile(
                r"(?:ದೂರು|ಕಂಪ್ಲೇಂಟ್|ಟಿಕೆಟ್)[^.!?।]{0,16}"
                r"(?:ದಾಖಲಿಸ|ಮಾಡಿ|ನೀಡಿ|ಸಂಖ್ಯೆ|ಬೇಕು)"
            ),
        ),
    ),
    (
        "repeat_complaint",
        (
            re.compile(
                r"\b(?:still not (?:fixed|resolved|working)|"
                r"not (?:fixed|resolved) yet|"
                r"same (?:problem|issue)[^.!?]{0,20}again|"
                r"happened again|again and again|"
                r"(?:second|third|fourth) time|"
                r"called before|open for (?:a|\d+) week)\b",
                re.I,
            ),
            re.compile(
                r"(?:अभी भी ठीक नहीं|अभी तक ठीक नहीं|पहले भी (?:कॉल|शिकायत)|"
                r"फिर से वही|तीसरी बार|दूसरी बार|हफ्ते से)"
            ),
            re.compile(
                r"(?:ಇನ್ನೂ ಸರಿ ಆಗಿಲ್ಲ|ಮೊದಲು ಕೂಡ ಕರೆ|ಮತ್ತೆ ಅದೇ|"
                r"ಮೂರನೇ ಬಾರಿ|ಎರಡನೇ ಬಾರಿ|ವಾರದಿಂದ)"
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
    (
        "device_offer_interest",
        (
            re.compile(
                r"\b(?:interested in|want|need|looking for)\s+"
                r"(?:a\s+|the\s+|your\s+)?(?:soundbox|sound box|new machine|"
                r"new device|second device|device offer)\b"
                r"|\b(?:send|share)\s+(?:me\s+)?(?:the\s+)?(?:offer|details|plan)\b",
                re.I,
            ),
            re.compile(
                r"(?:साउंडबॉक्स|नया मशीन|नया डिवाइस|ऑफर)[^.!?।]{0,16}"
                r"(?:चाहिए|दीजिए|भेजिए|बताइए)"
            ),
            re.compile(
                r"(?:ಸೌಂಡ್‌ಬಾಕ್ಸ್|ಹೊಸ ಮಷೀನ್|ಹೊಸ ಡಿವೈಸ್|ಆಫರ್)[^.!?।]{0,16}"
                r"(?:ಬೇಕು|ಕಳುಹಿಸಿ|ತಿಳಿಸಿ)"
            ),
        ),
    ),
    (
        "smalltalk",
        (
            re.compile(
                r"^\s*(?:hi|hello|hey|namaste|namaskar|"
                r"good (?:morning|afternoon|evening)|"
                r"who (?:is|'s) (?:this|it)|"
                r"thank you|thanks|bye)\s*[.!?।]*\s*$",
                re.I,
            ),
            re.compile(
                r"^\s*(?:नमस्ते|नमस्कार|हैलो|धन्यवाद|शुक्रिया|"
                r"कौन बोल रहा)\s*[.!?।]*\s*$"
            ),
            re.compile(
                r"^\s*(?:ನಮಸ್ಕಾರ|ನಮಸ್ತೆ|ಹಲೋ|ಧನ್ಯವಾದ|"
                r"ಯಾರು ಮಾತನಾಡುತ್ತ)\s*[.!?।]*\s*$"
            ),
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

# Topic patterns are independent of the label: a turn can be an objection
# *about* charges, or a policy question *about* charges.
_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    (
        "refund_query",
        re.compile(r"\brefund|रिफंड|ರಿಫಂಡ್", re.I),
    ),
    (
        "qr_code_issue",
        re.compile(r"\bqr\b|q\.r\.|क्यूआर|क्यू आर|ಕ್ಯೂಆರ್", re.I),
    ),
    (
        "soundbox_issue",
        re.compile(
            r"\bsound\s?box\b|साउंडबॉक्स|साउंड बॉक्स|ಸೌಂಡ್‌ಬಾಕ್ಸ್|ಸೌಂಡ್ ಬಾಕ್ಸ್",
            re.I,
        ),
    ),
    (
        "charges_query",
        re.compile(
            r"\bcharges?\b|\bfees?\b|\bdeduct(?:ed|ion)?\b|\bfee\b|"
            r"चार्ज|शुल्क|कटौती|ಚಾರ್ಜ್|ಶುಲ್ಕ|ಕಡಿತ",
            re.I,
        ),
    ),
    (
        "onboarding_kyc",
        re.compile(
            r"\bkyc\b|\bonboard|\bsign ?up\b|\bregister(?:ed)? as\b|"
            r"केवाईसी|रजिस्टर|ಕೆವೈಸಿ|ನೋಂದಣಿ|ನೋಂದಾಯಿಸ",
            re.I,
        ),
    ),
    (
        "transaction_issue",
        re.compile(
            r"\btransaction\b|\btxn\b|\bpayment (?:failed|stuck|pending)\b|"
            r"\bpayment (?:did not|didn'?t) (?:come|arrive)\b|"
            r"\bcustomer (?:paid|says)\b|\bamount (?:is|was) (?:wrong|incorrect|missing)\b|"
            r"\bdouble (?:payment|deduct\w*)\b|"
            r"पेमेंट फेल|ट्रांजैक्शन|पेमेंट पेंडिंग|ग्राहक.{0,10}(?:पेमेंट|भुगतान)|"
            r"रकम गलत|पैसे कट|"
            r"ಟ್ರಾನ್ಸಾಕ್ಷನ್|ಪೇಮೆಂಟ್ ಫೇಲ್|ಗ್ರಾಹಕ.{0,10}(?:ಪೇಮೆಂಟ್|ಪಾವತಿ)|"
            r"ಮೊತ್ತ ತಪ್ಪು|ಹಣ ಕಟ್ಟ",
            re.I,
        ),
    ),
)


@dataclass
class IntentResult:
    label: str
    confidence: float = 0.0
    slots: dict[str, Any] = field(default_factory=dict)
    source: str = "fallback"
    topic: str | None = None
    raw: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.label,
            "confidence": self.confidence,
            "slots": self.slots,
            "topic": self.topic,
            "source": self.source,
        }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def extract_language(text: str) -> str | None:
    for code, pattern in _LANGUAGE_PATTERNS:
        if pattern.search(text):
            return code
    return None


def extract_topic(text: str) -> str | None:
    """Return the concrete merchant issue named in the turn, if any."""

    for topic, pattern in _TOPIC_PATTERNS:
        if pattern.search(text or ""):
            return topic
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

    topic = extract_topic(normalized)
    if topic:
        slots["topic"] = topic

    return slots


def classify_rule(transcript: str) -> IntentResult | None:
    """Return a high-precision rule match, or ``None`` to ask the model."""

    text = _normalize(transcript)
    topic = extract_topic(text)

    if not text:
        return IntentResult(
            label="smalltalk",
            confidence=0.0,
            source="rule",
            topic=topic,
        )

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
                topic=topic,
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
                topic=topic,
            )

    return None


def _classifier_system_prompt() -> str:
    labels = "\n".join(
        f"- {label}: {description}"
        for label, description in INTENT_DESCRIPTIONS.items()
    )
    topics = ", ".join(TOPICS)
    return (
        "Classify one turn from a Paytm merchant telecalling call. "
        "Return JSON only, shaped exactly as "
        '{"intent": "<label>", "confidence": <0 to 1>, "topic": "<topic or null>"}. '
        "Choose exactly one intent from this list:\n"
        f"{labels}\n"
        "Set topic to the concrete issue only when the turn names one; "
        f"allowed topics are: {topics}. Otherwise use null. "
        "Money-related asks such as refunds, loan approval or limit changes "
        "are out_of_scope. Use other labels only when they fit. Do not explain."
    )


def _safe_fallback(slots: dict[str, Any], topic: str | None, raw: Any = None):
    return IntentResult(
        label="out_of_scope",
        confidence=0.0,
        slots=slots,
        source="fallback",
        topic=topic,
        raw=raw if isinstance(raw, dict) else None,
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
    topic = extract_topic(transcript)

    if llm is None:
        return _safe_fallback(slots, topic)

    try:
        payload = llm.complete_json(
            system=_classifier_system_prompt(),
            user=transcript,
            max_tokens=80,
        )
    except Exception:
        payload = None

    if not isinstance(payload, dict):
        return _safe_fallback(slots, topic)

    label = str(payload.get("intent") or "").strip()
    if label not in INTENTS:
        return _safe_fallback(slots, topic, payload)

    model_topic = str(payload.get("topic") or "").strip()
    if model_topic not in TOPICS:
        model_topic = None

    try:
        confidence = float(payload.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    return IntentResult(
        label=label,
        confidence=max(0.0, min(1.0, confidence)),
        slots=slots,
        source="llm",
        topic=topic or model_topic,
        raw=payload,
    )

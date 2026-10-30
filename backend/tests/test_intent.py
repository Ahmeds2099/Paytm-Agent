import unittest

from app.services.intent import (
    CRITICAL_INTENTS,
    EXPECTED_INTENT_FOR_TOPIC,
    INTENTS,
    SAFETY_INTENTS,
    TOPICS,
    classify,
    classify_rule,
    extract_language,
    extract_slots,
    extract_topic,
)
from tests.data.intent_examples import EXAMPLES, LANGUAGES


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def complete_json(self, system, user, max_tokens=80):
        self.calls.append({"system": system, "user": user, "max_tokens": max_tokens})
        return self.payload


class RaisingLLM:
    def complete_json(self, **kwargs):
        raise RuntimeError("classifier unavailable")


class IntentTaxonomyTests(unittest.TestCase):
    def test_sixteen_unique_labels_matching_the_brief(self):
        self.assertEqual(len(INTENTS), 16)
        self.assertEqual(len(set(INTENTS)), 16)
        self.assertEqual(
            set(INTENTS),
            {
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
            },
        )

    def test_no_other_label_and_no_issue_labels(self):
        self.assertNotIn("other", INTENTS)
        for topic in TOPICS:
            self.assertNotIn(topic, INTENTS)

    def test_safety_alias_still_points_at_critical_labels(self):
        self.assertEqual(SAFETY_INTENTS, CRITICAL_INTENTS)
        for label in CRITICAL_INTENTS:
            self.assertIn(label, INTENTS)

    def test_topic_mapping_is_documented_and_valid(self):
        self.assertEqual(set(EXPECTED_INTENT_FOR_TOPIC), set(TOPICS))
        for topic, label in EXPECTED_INTENT_FOR_TOPIC.items():
            self.assertIn(label, INTENTS, topic)

    def test_dataset_has_five_examples_per_intent_per_language(self):
        self.assertEqual(set(EXAMPLES), set(INTENTS))
        for label, by_language in EXAMPLES.items():
            self.assertEqual(set(by_language), set(LANGUAGES), label)
            for language, examples in by_language.items():
                self.assertEqual(len(examples), 5, f"{label}/{language}")
                self.assertTrue(all(example.strip() for example in examples))


class CriticalRuleTests(unittest.TestCase):
    def test_every_critical_example_is_caught_by_a_rule(self):
        for label in CRITICAL_INTENTS:
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    with self.subTest(label=label, language=language, text=example):
                        result = classify_rule(example)
                        self.assertIsNotNone(result, example)
                        self.assertEqual(result.label, label)
                        self.assertEqual(result.source, "rule")

    def test_critical_examples_do_not_need_the_model(self):
        llm = RaisingLLM()
        for label in CRITICAL_INTENTS:
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    with self.subTest(label=label, text=example):
                        self.assertEqual(classify(example, llm=llm).label, label)

    def test_non_critical_examples_do_not_hit_a_critical_rule(self):
        for label in set(INTENTS) - set(CRITICAL_INTENTS):
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    result = classify_rule(example)
                    with self.subTest(label=label, text=example):
                        if result is not None:
                            self.assertNotIn(result.label, CRITICAL_INTENTS)


class LanguageChoiceTests(unittest.TestCase):
    def test_language_names_in_all_three_scripts(self):
        cases = {
            "हिंदी": "hi-IN",
            "ಕನ್ನಡ": "kn-IN",
            "English": "en-IN",
            "हिंदी में बात करें": "hi-IN",
            "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ": "kn-IN",
            "इंग्लिश में बोलिए": "en-IN",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(extract_language(text), expected)
                result = classify_rule(text)
                self.assertIsNotNone(result)
                self.assertEqual(result.label, "language_choice")
                self.assertEqual(result.slots.get("language"), expected)

    def test_language_word_inside_a_long_turn_is_not_a_choice(self):
        text = (
            "I was reading about Hindi newspapers and I want to know when my "
            "settlement for last Friday will arrive in my bank account"
        )
        self.assertIsNone(classify_rule(text))


class TopicTests(unittest.TestCase):
    def test_topic_is_extracted_next_to_the_label(self):
        cases = {
            "My Paytm QR code is not working.": "qr_code_issue",
            "My soundbox is not announcing payments.": "soundbox_issue",
            "The refund is still pending after five days.": "refund_query",
            "Why was a fee deducted from my payment?": "charges_query",
            "Which documents do I need for KYC?": "onboarding_kyc",
            "My transaction is stuck on pending.": "transaction_issue",
            "मेरा क्यूआर कोड काम नहीं कर रहा।": "qr_code_issue",
            "ನನ್ನ ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಆಫ್‌ಲೈನ್ ಇದೆ.": "soundbox_issue",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(extract_topic(text), expected)

    def test_topic_absent_when_the_turn_names_no_issue(self):
        self.assertIsNone(extract_topic("When will my settlement come?"))
        self.assertIsNone(extract_topic("Hello."))

    def test_topic_rides_along_with_a_rule_label(self):
        result = classify_rule("I'm not interested, my QR is useless anyway.")
        self.assertIsNotNone(result)
        self.assertEqual(result.label, "opt_out")
        self.assertEqual(result.topic, "qr_code_issue")

    def test_topic_is_a_slot_too(self):
        self.assertEqual(
            extract_slots("ರೂ. 2500 ಸೌಂಡ್‌ಬಾಕ್ಸ್ ಬಾಕಿ")["topic"],
            "soundbox_issue",
        )


class SlotTests(unittest.TestCase):
    def test_amount_from_digits_and_currency_words(self):
        self.assertEqual(extract_slots("Rs. 1,500 was deducted")["amount"], "1500")
        self.assertEqual(extract_slots("500 rupees refund")["amount"], "500")
        self.assertEqual(extract_slots("ರೂ. 2500 ಬಾಕಿ")["amount"], "2500")

    def test_transaction_id(self):
        slots = extract_slots("check txn id ABCD123456 please")
        self.assertEqual(slots["transaction_id"], "ABCD123456")

    def test_date_phone_and_time(self):
        slots = extract_slots("call me tomorrow at 5 pm on 9876543210")
        self.assertEqual(slots["date"], "tomorrow")
        self.assertEqual(slots["phone"], "9876543210")
        self.assertEqual(slots["time"], "5:00 pm")

    def test_product_keyword(self):
        self.assertEqual(
            extract_slots("my soundbox is silent")["product"],
            "soundbox",
        )

    def test_empty_text_has_no_slots(self):
        self.assertEqual(extract_slots(""), {})


class ClassifierFallbackTests(unittest.TestCase):
    def test_model_label_is_used_for_non_critical_turns(self):
        llm = FakeLLM({"intent": "settlement_query", "confidence": 0.82})
        result = classify("money has not reached my bank account yet", llm=llm)
        self.assertEqual(result.label, "settlement_query")
        self.assertEqual(result.source, "llm")
        self.assertAlmostEqual(result.confidence, 0.82)
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("settlement_query", llm.calls[0]["system"])
        self.assertIn("out_of_scope", llm.calls[0]["system"])

    def test_model_topic_is_used_when_rules_find_none(self):
        llm = FakeLLM(
            {
                "intent": "device_issue",
                "confidence": 0.8,
                "topic": "soundbox_issue",
            }
        )
        result = classify("the speaker stopped talking since morning", llm=llm)
        self.assertEqual(result.label, "device_issue")
        self.assertEqual(result.topic, "soundbox_issue")

    def test_rule_topic_wins_over_the_model(self):
        llm = FakeLLM(
            {
                "intent": "policy_question",
                "confidence": 0.8,
                "topic": "charges_query",
            }
        )
        result = classify("how can I get my QR print replaced", llm=llm)
        self.assertEqual(result.topic, "qr_code_issue")

    def test_unknown_label_falls_back_to_out_of_scope(self):
        llm = FakeLLM({"intent": "weather", "confidence": 0.9})
        result = classify("something odd happened", llm=llm)
        self.assertEqual(result.label, "out_of_scope")
        self.assertEqual(result.source, "fallback")

    def test_unknown_topic_is_dropped(self):
        llm = FakeLLM({"intent": "policy_question", "topic": "weather"})
        result = classify("something odd happened", llm=llm)
        self.assertEqual(result.label, "policy_question")
        self.assertIsNone(result.topic)

    def test_model_failure_falls_back_to_out_of_scope(self):
        result = classify("something odd happened", llm=RaisingLLM())
        self.assertEqual(result.label, "out_of_scope")
        self.assertEqual(result.source, "fallback")

    def test_no_model_returns_out_of_scope(self):
        result = classify("something odd happened")
        self.assertEqual(result.label, "out_of_scope")
        self.assertEqual(result.source, "fallback")

    def test_slots_survive_the_model_path(self):
        llm = FakeLLM({"intent": "settlement_query", "confidence": 0.7})
        result = classify("my Rs. 2,000 settlement is late", llm=llm)
        self.assertEqual(result.slots.get("amount"), "2000")

    def test_result_serializes_with_topic(self):
        result = classify("Yes.")
        payload = result.as_dict()
        self.assertEqual(payload["intent"], "confirmation_yes")
        self.assertIn("slots", payload)
        self.assertIn("source", payload)
        self.assertIn("topic", payload)


if __name__ == "__main__":
    unittest.main()

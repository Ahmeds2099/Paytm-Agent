import unittest

from app.services.intent import (
    INTENTS,
    SAFETY_INTENTS,
    classify,
    classify_rule,
    extract_language,
    extract_slots,
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
    def test_seventeen_unique_labels(self):
        self.assertEqual(len(INTENTS), 17)
        self.assertEqual(len(set(INTENTS)), 17)

    def test_safety_labels_are_part_of_the_taxonomy(self):
        for label in SAFETY_INTENTS:
            self.assertIn(label, INTENTS)

    def test_dataset_has_five_examples_per_intent_per_language(self):
        self.assertEqual(set(EXAMPLES), set(INTENTS))
        for label, by_language in EXAMPLES.items():
            self.assertEqual(set(by_language), set(LANGUAGES), label)
            for language, examples in by_language.items():
                self.assertEqual(len(examples), 5, f"{label}/{language}")
                self.assertTrue(all(example.strip() for example in examples))


class SafetyRuleTests(unittest.TestCase):
    def test_every_safety_example_is_caught_by_a_rule(self):
        for label in SAFETY_INTENTS:
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    with self.subTest(label=label, language=language, text=example):
                        result = classify_rule(example)
                        self.assertIsNotNone(result, example)
                        self.assertEqual(result.label, label)
                        self.assertEqual(result.source, "rule")

    def test_safety_examples_do_not_need_the_model(self):
        llm = RaisingLLM()
        for label in SAFETY_INTENTS:
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    with self.subTest(label=label, text=example):
                        self.assertEqual(classify(example, llm=llm).label, label)

    def test_non_safety_examples_do_not_hit_a_safety_rule(self):
        for label in set(INTENTS) - set(SAFETY_INTENTS):
            for language in LANGUAGES:
                for example in EXAMPLES[label][language]:
                    result = classify_rule(example)
                    with self.subTest(label=label, text=example):
                        if result is not None:
                            self.assertNotIn(result.label, SAFETY_INTENTS)


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
    def test_model_label_is_used_for_non_safety_turns(self):
        llm = FakeLLM({"intent": "settlement_query", "confidence": 0.82})
        result = classify("money has not reached my bank account yet", llm=llm)
        self.assertEqual(result.label, "settlement_query")
        self.assertEqual(result.source, "llm")
        self.assertAlmostEqual(result.confidence, 0.82)
        self.assertEqual(len(llm.calls), 1)
        self.assertIn("settlement_query", llm.calls[0]["system"])

    def test_unknown_label_falls_back_to_other(self):
        llm = FakeLLM({"intent": "weather", "confidence": 0.9})
        result = classify("something odd happened", llm=llm)
        self.assertEqual(result.label, "other")
        self.assertEqual(result.source, "fallback")

    def test_model_failure_falls_back_to_other(self):
        result = classify("something odd happened", llm=RaisingLLM())
        self.assertEqual(result.label, "other")
        self.assertEqual(result.source, "fallback")

    def test_no_model_returns_other(self):
        result = classify("something odd happened")
        self.assertEqual(result.label, "other")
        self.assertEqual(result.source, "fallback")

    def test_slots_survive_the_model_path(self):
        llm = FakeLLM({"intent": "settlement_query", "confidence": 0.7})
        result = classify("my Rs. 2,000 settlement is late", llm=llm)
        self.assertEqual(result.slots.get("amount"), "2000")

    def test_result_serializes(self):
        result = classify("Yes.")
        payload = result.as_dict()
        self.assertEqual(payload["intent"], "confirmation_yes")
        self.assertIn("slots", payload)
        self.assertIn("source", payload)


if __name__ == "__main__":
    unittest.main()

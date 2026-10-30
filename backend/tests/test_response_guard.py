import unittest

from app.services.voice.response_guard import (
    VoiceReplyGuard,
    apology_line,
    apply_reply_budget,
    closing_question,
    count_sentences,
    split_sentences,
    strip_voice_markup,
)


class MarkupTests(unittest.TestCase):
    def test_numbered_list_is_removed(self):
        text = "1. Check the app.\n2. Restart the device."
        self.assertEqual(
            strip_voice_markup(text),
            "Check the app. Restart the device.",
        )

    def test_bullets_headers_and_bold_are_removed(self):
        text = "## Steps\n- **First** check the cable\n- Then restart"
        self.assertEqual(
            strip_voice_markup(text),
            "Steps First check the cable Then restart",
        )

    def test_links_and_tables_are_removed(self):
        text = "See [the help page](https://paytm.com) | call support"
        self.assertEqual(
            strip_voice_markup(text),
            "See the help page call support",
        )

    def test_code_fence_is_removed(self):
        self.assertEqual(
            strip_voice_markup("```json\n{}\n```"),
            "",
        )


class SentenceTests(unittest.TestCase):
    def test_english_sentences(self):
        self.assertEqual(
            split_sentences("One. Two? Three!"),
            ["One.", "Two?", "Three!"],
        )

    def test_devanagari_danda(self):
        self.assertEqual(
            split_sentences("पहला वाक्य। दूसरा वाक्य।"),
            ["पहला वाक्य।", "दूसरा वाक्य।"],
        )

    def test_numbered_marker_is_not_a_sentence(self):
        self.assertEqual(
            split_sentences("1. Check the app. 2. Restart."),
            ["Check the app.", "Restart."],
        )

    def test_abbreviation_is_not_a_sentence_break(self):
        self.assertEqual(
            split_sentences("Rs. 500 was deducted."),
            ["Rs. 500 was deducted."],
        )

    def test_count(self):
        self.assertEqual(count_sentences("One. Two. Three."), 3)


class BudgetTests(unittest.TestCase):
    def test_short_reply_is_unchanged(self):
        text = "Your settlement will arrive tomorrow."
        self.assertEqual(apply_reply_budget(text, "en-IN"), text)

    def test_three_sentences_are_kept(self):
        text = "One. Two. Three."
        self.assertEqual(apply_reply_budget(text, "en-IN"), text)

    def test_fourth_statement_is_replaced_with_an_offer(self):
        text = "One. Two. Three. Four."
        self.assertEqual(
            apply_reply_budget(text, "en-IN"),
            "One. Two. Three. Would you like to know more?",
        )

    def test_fourth_question_is_allowed(self):
        text = "One. Two. Three. Is that okay?"
        self.assertEqual(apply_reply_budget(text, "en-IN"), text)

    def test_hard_cap_of_five(self):
        text = "One. Two. Three. Four? Five. Six. Seven."
        result = apply_reply_budget(text, "en-IN")
        self.assertEqual(count_sentences(result), 5)
        self.assertNotIn("Six", result)
        self.assertNotIn("Seven", result)

    def test_offer_is_localized(self):
        self.assertEqual(
            apply_reply_budget("One. Two. Three. Four.", "hi-IN"),
            "One. Two. Three. " + closing_question("hi-IN"),
        )
        self.assertEqual(
            apply_reply_budget("One. Two. Three. Four.", "kn-IN"),
            "One. Two. Three. " + closing_question("kn-IN"),
        )

    def test_auto_language_does_not_add_an_offer(self):
        self.assertEqual(
            apply_reply_budget("One. Two. Three. Four.", "auto"),
            "One. Two. Three.",
        )

    def test_markup_never_reaches_speech(self):
        text = "**Good news.**\n\n1. Money is on the way.\n2. Check tomorrow."
        result = apply_reply_budget(text, "en-IN")
        self.assertNotIn("*", result)
        self.assertNotIn("1.", result)
        self.assertIn("Good news.", result)

    def test_streaming_guard_matches_the_batch_result(self):
        guard = VoiceReplyGuard(language="en-IN")
        parts = []
        for token in ["One. ", "Two. ", "Three. ", "Four."]:
            parts.extend(guard.feed(token))
        parts.extend(guard.flush())
        self.assertEqual(
            " ".join(parts),
            "One. Two. Three. Would you like to know more?",
        )

    def test_streaming_guard_stops_accepting_tokens(self):
        guard = VoiceReplyGuard(language="en-IN")
        guard.feed("One. Two. Three. Four.")
        self.assertTrue(guard.finished)
        self.assertEqual(guard.feed(" Five."), [])

    def test_long_unpunctuated_chunk_is_released(self):
        guard = VoiceReplyGuard(language="en-IN")
        parts = guard.feed("a" * 160)
        self.assertTrue(parts)
        self.assertEqual(len(parts[0]), 140)
        self.assertEqual(guard.units, 0)

    def test_long_sentence_counts_once(self):
        guard = VoiceReplyGuard(language="en-IN")
        long_sentence = ("word " * 40).strip() + "."
        parts = []
        for token in long_sentence:
            parts.extend(guard.feed(token))
        parts.extend(guard.flush())
        self.assertGreater(len(parts), 1)
        self.assertEqual(guard.units, 1)

    def test_apology_exists_for_each_language(self):
        for language in ("hi-IN", "kn-IN", "en-IN"):
            self.assertTrue(apology_line(language).strip())
        self.assertTrue(apology_line(None).strip())


if __name__ == "__main__":
    unittest.main()

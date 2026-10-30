import struct
import tempfile
import unittest
from pathlib import Path

from app.services.voice.language_gate import (
    MAX_LANGUAGE_ATTEMPTS,
    detect_language_change,
    detect_language_choice,
    resolve_language_gate,
)
from app.services.voice.phrases import (
    GREETING_ORDER,
    LANGUAGE_NAMES,
    PHRASES,
    phrase_text,
    required_clips,
)
from app.services.voice.prerender import PhraseCache, strip_wav


class LanguageGateTests(unittest.TestCase):
    def test_each_language_name_in_each_script_locks(self):
        cases = {
            "Hindi.": "hi-IN",
            "हिंदी।": "hi-IN",
            "हिंदी में बात करें।": "hi-IN",
            "Kannada please.": "kn-IN",
            "ಕನ್ನಡ.": "kn-IN",
            "ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ.": "kn-IN",
            "English.": "en-IN",
            "इंग्लिश में बोलिए।": "en-IN",
            "ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಮಾತನಾಡಿ.": "en-IN",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                result = resolve_language_gate(text, attempts=0)
                self.assertEqual(result.action, "lock")
                self.assertEqual(result.language, expected)
                self.assertEqual(result.attempts, 0)

    def test_common_spellings_are_accepted(self):
        cases = {
            "hindhi": "hi-IN",
            "kannad": "kn-IN",
            "inglish": "en-IN",
            "angrezi": "en-IN",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_language_choice(text), expected)

    def test_code_mixed_transcript_still_finds_the_language(self):
        # Sarvam sometimes returns a Latin language name glued to the rest of
        # an Indic word, so a trailing word boundary is too strict.
        cases = {
            "Kannadaದಲ್ಲಿ ಮಾತನಾಡಿ": "kn-IN",
            "English ಪ್ಲೀಸ್": "en-IN",
            "Hindi में बात करें": "hi-IN",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(detect_language_choice(text), expected)

    def test_single_word_answer_is_enough(self):
        self.assertEqual(resolve_language_gate("Kannada", 0).action, "lock")
        self.assertEqual(resolve_language_gate("हिंदी", 0).action, "lock")
        self.assertEqual(resolve_language_gate("English", 0).action, "lock")

    def test_unclear_first_answer_asks_once_more(self):
        result = resolve_language_gate("hmm what is this", attempts=0)
        self.assertEqual(result.action, "retry")
        self.assertIsNone(result.language)
        self.assertEqual(result.attempts, 1)

    def test_unclear_second_answer_defaults_to_english(self):
        result = resolve_language_gate("I still do not understand", attempts=1)
        self.assertEqual(result.action, "default")
        self.assertEqual(result.language, "en-IN")
        self.assertEqual(result.attempts, MAX_LANGUAGE_ATTEMPTS)

    def test_bare_yes_is_not_a_language(self):
        result = resolve_language_gate("Yes.", attempts=0)
        self.assertEqual(result.action, "retry")

    def test_a_long_turn_is_not_a_language_choice(self):
        result = resolve_language_gate(
            "My settlement from last Friday has still not reached my bank account",
            attempts=0,
        )
        self.assertEqual(result.action, "retry")
        self.assertIsNone(detect_language_choice(
            "My settlement from last Friday has still not reached my bank account"
        ))

    def test_opt_out_is_respected_before_a_language_is_chosen(self):
        result = resolve_language_gate("Stop calling me.", attempts=1)
        self.assertEqual(result.action, "opt_out")
        self.assertEqual(result.attempts, 1)

    def test_human_request_is_recognised_before_a_language_is_chosen(self):
        result = resolve_language_gate(
            "I want to talk to a human.",
            attempts=0,
        )
        self.assertEqual(result.action, "human_request")

    def test_configured_fallback_language_is_used(self):
        result = resolve_language_gate(
            "no idea",
            attempts=1,
            default_language="hi-IN",
        )
        self.assertEqual(result.action, "default")
        self.assertEqual(result.language, "hi-IN")

    def test_auto_is_never_a_locked_language(self):
        result = resolve_language_gate(
            "no idea",
            attempts=1,
            default_language="auto",
        )
        self.assertEqual(result.language, "en-IN")


class LanguageChangeTests(unittest.TestCase):
    def test_explicit_request_changes_the_language(self):
        self.assertEqual(detect_language_change("Please speak in Kannada", "hi-IN"), "kn-IN")
        self.assertEqual(detect_language_change("कन्नड़ में बात करें।", "en-IN"), "kn-IN")
        self.assertEqual(detect_language_change("English please", "hi-IN"), "en-IN")

    def test_same_language_is_not_a_change(self):
        self.assertIsNone(detect_language_change("Hindi.", "hi-IN"))

    def test_a_language_word_inside_a_sentence_does_not_switch(self):
        text = (
            "मैं हिंदी अखबार पढ़ता हूँ और मेरा सेटलमेंट कल आना चाहिए था"
        )
        self.assertIsNone(detect_language_change(text, "en-IN"))

    def test_a_normal_turn_never_switches(self):
        self.assertIsNone(
            detect_language_change("When will my settlement arrive?", "kn-IN")
        )


class PhraseTableTests(unittest.TestCase):
    def test_greeting_exists_in_all_three_languages(self):
        self.assertEqual(set(PHRASES["greeting"]), {"hi-IN", "kn-IN", "en-IN"})
        self.assertEqual(set(GREETING_ORDER), {"hi-IN", "kn-IN", "en-IN"})

    def test_greeting_has_the_recording_notice(self):
        markers = {
            "hi-IN": "रिकॉर्ड",
            "kn-IN": "ರೆಕಾರ್ಡ್",
            "en-IN": "recorded",
        }
        for language, marker in markers.items():
            with self.subTest(language=language):
                self.assertIn(marker, PHRASES["greeting"][language])

    def test_greeting_offers_all_three_language_names(self):
        self.assertIn("हिंदी", PHRASES["greeting"]["hi-IN"])
        self.assertIn("ಕನ್ನಡ", PHRASES["greeting"]["kn-IN"])
        self.assertIn("English", PHRASES["greeting"]["en-IN"])

    def test_every_phrase_falls_back_to_english(self):
        for phrase_id in PHRASES:
            with self.subTest(phrase_id=phrase_id):
                self.assertTrue(phrase_text(phrase_id, "en-IN"))
                self.assertEqual(
                    phrase_text(phrase_id, "xx-XX"),
                    phrase_text(phrase_id, "en-IN"),
                )

    def test_language_names_cover_the_supported_set(self):
        self.assertEqual(
            set(LANGUAGE_NAMES),
            {"hi-IN", "kn-IN", "en-IN"},
        )

    def test_required_clips_match_the_phrase_table(self):
        clips = required_clips("greeting")
        self.assertEqual(
            set(clips),
            {
                ("greeting", "hi-IN"),
                ("greeting", "kn-IN"),
                ("greeting", "en-IN"),
            },
        )


def _wav(payload: bytes) -> bytes:
    header = b"RIFF" + struct.pack("<I", 36 + len(payload))
    header += b"WAVE"
    header += b"fmt " + struct.pack("<I", 16)
    header += struct.pack("<HHIIHH", 1, 1, 16000, 64000, 4, 32)
    header += b"data" + struct.pack("<I", len(payload))
    return header + payload


class WavStripTests(unittest.TestCase):
    def test_header_is_removed(self):
        pcm = bytes(range(16))
        self.assertEqual(strip_wav(_wav(pcm)), pcm)

    def test_non_wav_is_returned_unchanged(self):
        self.assertEqual(strip_wav(b"not a wav"), b"not a wav")

    def test_empty_data_chunk_returns_empty(self):
        self.assertEqual(strip_wav(_wav(b"")), b"")


class PhraseCacheTests(unittest.TestCase):
    def test_missing_clip_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = PhraseCache(Path(directory))
            self.assertIsNone(cache.get("greeting", "hi-IN"))

    def test_path_is_stable_and_language_specific(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = PhraseCache(Path(directory))
            first = cache.path_for("greeting", "hi-IN")
            second = cache.path_for("greeting", "hi-IN")
            other = cache.path_for("greeting", "kn-IN")
            self.assertEqual(first, second)
            self.assertNotEqual(first, other)
            self.assertIn("greeting", first.name)
            self.assertTrue(str(first).endswith(".pcm"))


if __name__ == "__main__":
    unittest.main()

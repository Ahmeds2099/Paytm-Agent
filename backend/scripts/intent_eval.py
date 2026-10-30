"""Live intent accuracy run against the configured model.

Owner-run because it spends Groq credits: one classification call per example
that the rule fast path does not catch.

    .venv\\Scripts\\python.exe scripts\\intent_eval.py
    .venv\\Scripts\\python.exe scripts\\intent_eval.py --language hi-IN
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.intent import SAFETY_INTENTS, classify  # noqa: E402
from app.services.llm import LLMService  # noqa: E402
from tests.data.intent_examples import EXAMPLES, LANGUAGES  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--language",
        choices=LANGUAGES,
        action="append",
        help="limit to one language; repeatable",
    )
    args = parser.parse_args()

    languages = tuple(args.language) if args.language else LANGUAGES
    llm = LLMService()

    totals: Counter[str] = Counter()
    correct: Counter[str] = Counter()
    by_source: Counter[str] = Counter()
    mistakes: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for expected, by_language in EXAMPLES.items():
        for language in languages:
            for text in by_language[language]:
                result = classify(text, language=language, llm=llm)
                totals[language] += 1
                by_source[result.source] += 1
                if result.label == expected:
                    correct[language] += 1
                else:
                    mistakes[language].append(
                        (f"{expected} -> {result.label}", text)
                    )

    print("\nIntent accuracy")
    print("-" * 60)
    for language in languages:
        total = totals[language]
        hits = correct[language]
        rate = (hits / total * 100) if total else 0.0
        print(f"{language}: {hits}/{total} ({rate:.1f}%)")

    print("\nResolved by")
    print("-" * 60)
    for source, count in sorted(by_source.items()):
        print(f"{source}: {count}")

    safety = sum(
        1
        for label in SAFETY_INTENTS
        for language in languages
        for text in EXAMPLES[label][language]
        if classify(text, language=language).label == label
    )
    safety_total = len(SAFETY_INTENTS) * len(languages) * 5
    print(f"\nSafety rules: {safety}/{safety_total}")

    for language, rows in mistakes.items():
        if not rows:
            continue
        print(f"\nMistakes ({language})")
        print("-" * 60)
        for label, text in rows:
            print(f"{label:45} {text}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

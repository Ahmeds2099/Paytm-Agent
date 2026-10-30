"""Live intent accuracy run against the configured model.

Owner-run because it spends Groq credits: one classification call per example
that the rule fast path does not catch.

    .venv\\Scripts\\python.exe scripts\\intent_eval.py
    .venv\\Scripts\\python.exe scripts\\intent_eval.py --language hi-IN

Reports three things:

* intent accuracy per language, against the brief's 16 labels,
* how many turns each path resolved (rule, model, fallback),
* the critical-intent rate, which must stay at 100% because those rules are
  deterministic and never call the model.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.intent import (  # noqa: E402
    CRITICAL_INTENTS,
    EXPECTED_INTENT_FOR_TOPIC,
    TOPICS,
    classify,
)
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

    topic_total = 0
    topic_agrees = 0
    topic_mistakes: list[tuple[str, str, str]] = []

    for expected, by_language in EXAMPLES.items():
        for language in languages:
            for text in by_language[language]:
                result = classify(text, language=language, llm=llm)
                totals[language] += 1
                by_source[result.source] += 1
                if result.label == expected:
                    correct[language] += 1
                else:
                    mistakes[language].append((f"{expected} -> {result.label}", text))

                if result.topic:
                    topic_total += 1
                    expected_label = EXPECTED_INTENT_FOR_TOPIC.get(result.topic)
                    if expected_label == result.label:
                        topic_agrees += 1
                    else:
                        topic_mistakes.append(
                            (result.topic, result.label, text)
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

    critical = sum(
        1
        for label in CRITICAL_INTENTS
        for language in languages
        for text in EXAMPLES[label][language]
        if classify(text, language=language).label == label
    )
    critical_total = len(CRITICAL_INTENTS) * len(languages) * 5
    print(f"\nCritical rules: {critical}/{critical_total}")

    if topic_total:
        rate = topic_agrees / topic_total * 100
        print(
            f"Topic carries the expected label: "
            f"{topic_agrees}/{topic_total} ({rate:.1f}%)"
        )
        print(f"Topics seen: {', '.join(sorted({t for t, _, _ in topic_mistakes})) or 'none off-pattern'}")

    for language, rows in mistakes.items():
        if not rows:
            continue
        print(f"\nLabel mistakes ({language})")
        print("-" * 60)
        for label, text in rows:
            print(f"{label:45} {text}")

    if topic_mistakes:
        print("\nTopic/label mismatches")
        print("-" * 60)
        for topic, label, text in topic_mistakes:
            expected = EXPECTED_INTENT_FOR_TOPIC.get(topic)
            print(f"{topic:18} expected {expected:15} got {label:15} {text}")

    print(f"\nAllowed topics: {', '.join(TOPICS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

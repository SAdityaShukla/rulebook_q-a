import json
import sys
from pathlib import Path


sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1] / "src"
    ),
)

from reasoner import Reasoner


EVAL_FILE = (
    Path(__file__).resolve().parents[1]
    / "data/eval_questions.jsonl"
)


def main():

    reasoner = Reasoner()

    rows = [
        json.loads(line)
        for line in EVAL_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
    ]

    results = []

    for item in rows:

        result = reasoner.ask(
            item["question"]
        )

        state_ok = (
            result.state
            == item["expected_state"]
        )

        expected_citations = set(
            item.get(
                "expected_citations",
                [],
            )
        )

        actual_citations = set(
            result.citations
        )

        citation_ok = (
            expected_citations
            .issubset(actual_citations)
        )

        full_ok = (
            state_ok
            and citation_ok
        )

        results.append(
            {
                "item": item,
                "result": result,
                "state_ok": state_ok,
                "citation_ok": citation_ok,
                "full_ok": full_ok,
            }
        )

        print(
            f"{item['id']} | "
            f"expected={item['expected_state']:<13} "
            f"got={result.state:<13} "
            f"state={'PASS' if state_ok else 'FAIL'} "
            f"citations={'PASS' if citation_ok else 'FAIL'} "
            f"full={'PASS' if full_ok else 'FAIL'}"
        )

    total = len(results)

    state_correct = sum(
        r["state_ok"]
        for r in results
    )

    full_correct = sum(
        r["full_ok"]
        for r in results
    )

    citation_correct = sum(
        r["citation_ok"]
        for r in results
    )

    print()
    print("=" * 50)
    print("POLICY PROOF EVALUATION")
    print("=" * 50)

    print(f"Total questions : {total}")

    print()

    for state in (
        "answers",
        "silent",
        "contradiction",
    ):

        subset = [
            r
            for r in results
            if r["item"]["expected_state"]
            == state
        ]

        correct = sum(
            r["state_ok"]
            for r in subset
        )

        percentage = (
            correct / len(subset) * 100
            if subset
            else 0
        )

        label = {
            "answers": "Answered",
            "silent": "Not Covered",
            "contradiction": "Contradiction",
        }[state]

        print(
            f"{label:<15}: "
            f"{correct}/{len(subset)} "
            f"({percentage:.2f}%)"
        )

    print()

    print(
        f"State accuracy  : "
        f"{state_correct}/{total} "
        f"({state_correct / total:.2%})"
    )

    print(
        f"Citation score  : "
        f"{citation_correct}/{total} "
        f"({citation_correct / total:.2%})"
    )

    print(
        f"Full score      : "
        f"{full_correct}/{total} "
        f"({full_correct / total:.2%})"
    )

    print("=" * 50)


if __name__ == "__main__":
    main()

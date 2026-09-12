import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from reasoner import Reasoner

EVAL_FILE = Path(__file__).resolve().parents[1] / "data/eval_questions.jsonl"

def main():
    reasoner = Reasoner()
    rows = [json.loads(x) for x in EVAL_FILE.read_text(encoding="utf-8").splitlines() if x.strip()]
    results = []
    for item in rows:
        got = reasoner.ask(item["question"])
        state_ok = got.state == item["expected_state"]
        expected = set(item.get("expected_citations", []))
        actual = set(got.citations)
        citation_ok = expected.issubset(actual)
        full_ok = state_ok and citation_ok
        results.append((item, got, state_ok, full_ok))
        print(f"{item['id']} | expected={item['expected_state']:<13} got={got.state:<13} state={'PASS' if state_ok else 'FAIL'} full={'PASS' if full_ok else 'FAIL'}")

    total = len(results)
    state_score = sum(x[2] for x in results)
    full_score = sum(x[3] for x in results)
    print("\n=== POLICY PROOF EVALUATION ===")
    print(f"Questions:      {total}")
    print(f"State accuracy: {state_score}/{total} = {state_score/total:.1%}")
    print(f"Full score:     {full_score}/{total} = {full_score/total:.1%}")
    for state in ("answers", "silent", "contradiction"):
        subset = [x for x in results if x[0]["expected_state"] == state]
        correct = sum(x[2] for x in subset)
        print(f"{state:<14}: {correct}/{len(subset)} = {correct/len(subset):.1%}")

if __name__ == "__main__": main()

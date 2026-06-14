"""Two-layer evaluation.

1) certify_judge(): run the judge on the human-labeled golden rows and measure
   how often the judge's verdict MATCHES human judgment. This is the judge's
   trust score. If it can't match humans, we can't trust it at scale.

2) evaluate_sample(): run the certified judge over a random sample of all data
   to estimate TYPE accuracy at scale — no extra human labeling needed.
"""
import argparse
import csv
import time
from pathlib import Path

from src.db import get_conn
from src.eval.judge import judge_one

GOLDEN = Path("data/golden_set.csv")


def certify_judge() -> None:
    conn = get_conn()
    rows = list(csv.DictReader(GOLDEN.open(encoding="utf-8")))
    labeled = [r for r in rows if r.get("gold_type", "").strip()]
    print(f"Certifying judge on {len(labeled)} human-labeled rows "
          f"(of {len(rows)} total)\n")

    agree = counted = 0
    for r in labeled:
        item = conn.execute(
            "SELECT fb_type FROM feedback_items WHERE id = ?", (r["id"],)
        ).fetchone()
        if not item:
            continue
        predicted = item["fb_type"]
        human_says_correct = (r["gold_type"].strip() == predicted)   # did the human keep Llama's type?
        verdict = judge_one(r["body"], predicted)
        if verdict["type_correct"] is None:                          # judge errored -> skip
            continue
        judge_says_correct = verdict["type_correct"]
        match = (judge_says_correct == human_says_correct)           # judge agrees with human?
        counted += 1
        agree += int(match)
        human_str = "correct" if human_says_correct else f"WRONG(should be {r['gold_type'].strip()})"
        judge_str = "correct" if judge_says_correct else "WRONG"
        print(f"#{r['id']:>3}  Llama={predicted:<15} human:{human_str:<28} "
              f"judge:{judge_str:<8} {'MATCH' if match else 'MISMATCH'}")

    print()
    if counted:
        print(f"JUDGE-HUMAN AGREEMENT: {agree}/{counted} = {agree / counted:.0%}")
        print("(This is the judge's trust score. Higher = safe to use at scale.)")
    else:
        print("No comparable labeled rows yet — label some golden rows first.")


def evaluate_sample(n: int = 20, pause: float = 1.0) -> None:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, body, fb_type FROM feedback_items "
        "WHERE status = 'classified' ORDER BY RANDOM() LIMIT ?",
        (n,),
    ).fetchall()

    correct = wrong = errors = 0
    for i, r in enumerate(rows, start=1):
        v = judge_one(r["body"], r["fb_type"])
        if v["type_correct"] is True:
            correct += 1
            note = "ok"
        elif v["type_correct"] is False:
            wrong += 1
            note = f"FLAG -> suggests {v['suggested_type']}"
        else:
            errors += 1
            note = f"judge error: {v['reasoning'][:50]}"
        # print EVERY item so progress is always visible (never looks frozen)
        print(f"  [{i}/{len(rows)}] #{r['id']:>3}  Llama={r['fb_type']:<15} {note}")
        time.sleep(pause)   # stay under Groq's free per-minute limit

    judged = correct + wrong
    print()
    if judged:
        print(f"JUDGE-ESTIMATED TYPE ACCURACY on {judged} items: "
              f"{correct}/{judged} = {correct / judged:.0%}  (judge errors: {errors})")
    else:
        print("Nothing judged.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["certify", "sample"])
    parser.add_argument("--n", type=int, default=50)
    args = parser.parse_args()
    if args.mode == "certify":
        certify_judge()
    else:
        evaluate_sample(args.n)
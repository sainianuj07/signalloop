"""Classify every unclassified review, batch by batch.

Resumable AND self-healing: on a rate limit (429) it prints a message, waits a
cooldown, and retries the SAME item — nothing is marked failed or lost.
Safe to re-run anytime.
"""
import time

from src.classify.classifier import classify_one
from src.db import get_conn, get_unclassified_batch, mark_failed, save_label

RATE_LIMIT_HINTS = ("429", "rate limit", "rate_limit", "resource_exhausted",
                    "too many requests", "tokens per")


def _is_rate_limit(err: str) -> bool:
    return any(h in err.lower() for h in RATE_LIMIT_HINTS)


def run(batch_size: int = 15, cooldown: int = 60, max_waits: int = 3) -> None:
    conn = get_conn()
    classified = failed = 0

    while True:
        batch = get_unclassified_batch(conn, limit=batch_size)
        if not batch:                      # nothing left as 'new' -> done
            break

        for row in batch:
            # Keep retrying THIS item through rate-limit cooldowns until it resolves.
            waits = 0
            while True:
                label = classify_one(row["body"])
                if "error" in label and _is_rate_limit(label["error"]):
                    waits += 1
                    if waits > max_waits:
                        print(f"  #{row['id']}: still limited after {max_waits} waits — likely a DAILY cap. "
                              f"Stopping (resumable). Re-run later or use another model.")
                        return            # stop cleanly; item stays 'new', nothing lost
                    print(f"  rate limit (429) — waiting {cooldown}s ({waits}/{max_waits}), retrying #{row['id']}...")
                    time.sleep(cooldown)
                    continue
                break

            if "error" in label:           # a real, non-rate-limit error (e.g. bad JSON)
                mark_failed(conn, row["id"])
                failed += 1
                print(f"  FAILED #{row['id']}: {label['error'][:60]}")
            else:
                save_label(conn, row["id"], label)
                classified += 1
                print(f"  [{classified}] #{row['id']} -> {label['type']:<15} sev {label['severity']}  conf {label['confidence']}")

    print(f"\nDone. Classified {classified}, failed {failed}.")


if __name__ == "__main__":
    run()
"""Classify every unclassified review, batch by batch.

Resumable by design: only touches status='new' items, and marks each
'classified' (or 'failed') only AFTER processing. Safe to re-run anytime.
"""
from src.classify.classifier import classify_one
from src.db import get_conn, get_unclassified_batch, mark_failed, save_label


def run(batch_size: int = 15) -> None:
    conn = get_conn()
    classified = 0
    failed = 0

    while True:
        batch = get_unclassified_batch(conn, limit=batch_size)
        if not batch:           # nothing left marked 'new' -> we're done
            break

        for row in batch:
            label = classify_one(row["body"])
            if "error" in label:                 # the AI call failed
                mark_failed(conn, row["id"])
                failed += 1
                print(f"  FAILED #{row['id']}: {label['error'][:60]}")
            else:
                save_label(conn, row["id"], label)
                classified += 1
                print(f"  [{classified}] #{row['id']} -> {label['type']:<15} "
                      f"sev {label['severity']}  conf {label['confidence']}")

    print(f"\nDone. Classified {classified}, failed {failed}.")


if __name__ == "__main__":
    run()
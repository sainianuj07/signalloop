"""Universal CSV import — the path real customers use for their own tickets/NPS/etc.

Expected columns (only `body` is required): body, author, rating, created_at, external_id
Usage:
    python -m src.ingest.csv_import path/to/feedback.csv
"""
import argparse

import pandas as pd

from src.db import get_conn, insert_items


def import_csv(path: str) -> int:
    df = pd.read_csv(path)
    if "body" not in df.columns:
        raise ValueError(f"CSV must have a 'body' column; found: {list(df.columns)}")

    items = []
    for i, row in df.iterrows():
        body = str(row["body"]).strip()
        if len(body) < 20:
            continue
        items.append(
            {
                "source": "csv",
                "external_id": str(row.get("external_id", f"csv-{i}")),
                "author": str(row.get("author", "anonymous")),
                "body": body,
                "rating": int(row["rating"]) if pd.notna(row.get("rating")) else None,
                "created_at": str(row.get("created_at")) if pd.notna(row.get("created_at")) else None,
            }
        )
    return insert_items(get_conn(), items)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    args = parser.parse_args()
    print(f"Inserted {import_csv(args.csv_path)} items")


if __name__ == "__main__":
    main()

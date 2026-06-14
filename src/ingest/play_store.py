"""Ingest Google Play reviews (no API key needed).

Usage:
    python -m src.ingest.play_store notion.id --count 300
"""
import argparse

from google_play_scraper import Sort, reviews

from src.db import get_conn, insert_items


def fetch_reviews(app_id: str, count: int = 300) -> list[dict]:
    raw, _ = reviews(app_id, lang="en", country="us", sort=Sort.NEWEST, count=count)
    return [
        {
            "source": "play_store",
            "external_id": r["reviewId"],
            "author": r.get("userName") or "anonymous",
            "body": (r.get("content") or "").strip(),
            "rating": r.get("score"),
            "created_at": r["at"].isoformat() if r.get("at") else None,
        }
        for r in raw
        # Drop empty / ultra-short reviews: "good app" carries no roadmap signal
        if r.get("content") and len(r["content"].strip()) >= 20
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("app_id", help="Play Store package id, e.g. notion.id")
    parser.add_argument("--count", type=int, default=300)
    args = parser.parse_args()

    items = fetch_reviews(args.app_id, args.count)
    conn = get_conn()
    inserted = insert_items(conn, items)
    total = conn.execute("SELECT COUNT(*) FROM feedback_items").fetchone()[0]
    print(f"Fetched {len(items)} usable reviews, inserted {inserted} new (db total: {total})")


if __name__ == "__main__":
    main()

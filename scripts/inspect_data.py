"""Quick data sanity check: distribution + samples. Run: python scripts/inspect_data.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.db import get_conn, get_unclassified_batch

conn = get_conn()
print("Rating distribution:")
for row in conn.execute("SELECT rating, COUNT(*) FROM feedback_items GROUP BY rating ORDER BY rating"):
    print(f"  {row[0]} stars: {row[1]}")

print("\nPipeline status:")
for row in conn.execute("SELECT status, COUNT(*) FROM feedback_items GROUP BY status"):
    print(f"  {row[0]}: {row[1]}")

print("\nSample low-rating reviews (signal-rich):")
for row in conn.execute("SELECT rating, substr(body,1,160) FROM feedback_items WHERE rating <= 2 LIMIT 5"):
    print(f"  [{row[0]}*] {row[1]}")

print("\nFirst unclassified batch:")
batch = get_unclassified_batch(conn, limit=5)

print("  ids:", [row["id"] for row in batch])
again = get_unclassified_batch(conn, limit=5)

print("  stable across calls?", [r["id"] for r in again] == [r["id"] for r in batch])
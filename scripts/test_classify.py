import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import get_conn, get_unclassified_batch
from src.classify.classifier import classify_one

conn = get_conn()
batch = get_unclassified_batch(conn, limit=3)   # grab 3 real reviews

for row in batch:
    label = classify_one(row["body"])
    print(f"\nReview: {row['body'][:80]}")
    print(f"  -> {label}")
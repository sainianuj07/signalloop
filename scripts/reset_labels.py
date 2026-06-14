"""Reset items to 'new' so the classifier re-runs them after a prompt change.
Skips human-corrected items so we never overwrite ground-truth human labels."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import get_conn

conn = get_conn()
cur = conn.execute(
    """UPDATE feedback_items
       SET status = 'new', fb_type = NULL, product_area = NULL,
           sentiment = NULL, severity = NULL, confidence = NULL
       WHERE human_corrected = 0"""
)
conn.commit()
print(f"Reset {cur.rowcount} items to 'new'. Now run the pipeline to re-classify.")
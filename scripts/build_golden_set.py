"""Export a stratified sample for FAST human review (the 'golden set').

Time-saver: each gold_* column is pre-filled with the AI's prediction.
You only CORRECT the wrong cells instead of labeling from scratch.
Trade-off: measures human-AI agreement / correction rate (slightly
optimistic due to anchoring bias), not fully-blind accuracy. Documented.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from src.db import get_conn

PER_TYPE = 25  # up to this many per predicted type -> ~40 items total

conn = get_conn()
rows = conn.execute(
    "SELECT id, body, fb_type, severity FROM feedback_items WHERE status = 'classified'"
).fetchall()

df = pd.DataFrame(rows, columns=["id", "body", "predicted_type", "predicted_severity"])
sample = df.groupby("predicted_type").head(PER_TYPE)

out = sample[["id", "body"]].copy()
out["gold_type"] = sample["predicted_type"].values         # pre-filled AI guess — fix if wrong
out["gold_severity"] = sample["predicted_severity"].values # pre-filled AI guess — fix if wrong
out["gold_notes"] = ""                                      # optional: note tricky ones

path = Path("data/golden_set.csv")
out.to_csv(path, index=False)
print(f"Wrote {len(out)} items to {path}.")
print("Skim each row. Only EDIT gold_type / gold_severity where the AI got it wrong, then save.")
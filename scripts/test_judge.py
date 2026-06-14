import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import get_conn
from src.eval.judge import judge_one

conn = get_conn()
rows = conn.execute(
    "SELECT id, body, fb_type FROM feedback_items WHERE status = 'classified' LIMIT 5"
).fetchall()

for r in rows:
    v = judge_one(r["body"], r["fb_type"])
    if v["type_correct"] is True:
        mark = "AGREE"
    elif v["type_correct"] is False:
        mark = "DISAGREE"
    else:
        mark = "ERROR"
    print(f"\n#{r['id']}  Llama said: {r['fb_type']}  ->  Judge: {mark} (suggests {v['suggested_type']})")
    print(f"   reason: {v['reasoning']}")
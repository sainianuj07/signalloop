"""Cluster actionable feedback into named themes: embed -> KMeans -> name.

Pipeline:
  1. embed each review (meaning -> vector) with Gemini
  2. group nearby vectors with KMeans (semantic clusters)
  3. ask the LLM to NAME each cluster from its member reviews
  4. save themes and link items to them
"""
from collections import Counter
import json
import os
import pickle
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from sklearn.cluster import KMeans

from src.db import assign_theme, clear_themes, get_conn, save_theme
from src.llm import complete

load_dotenv()
EMBED_MODEL = "gemini-embedding-001"
CACHE_PATH = Path("data/embeddings.pkl")


def _load_cache() -> dict:
    """Load the {review_text: vector} cache from disk (empty if none yet)."""
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "rb") as f:
            return pickle.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "wb") as f:
        pickle.dump(cache, f)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed texts into unit vectors, CACHING each to disk so we never pay to
    embed the same review twice. Survives the per-minute rate limit by waiting
    and retrying the current batch."""
    cache = _load_cache()
    todo = [t for t in texts if t not in cache]            # only embed what we haven't already

    if todo:
        print(f"  embedding {len(todo)} new items ({len(texts) - len(todo)} from cache)...")
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        BATCH = 20
        i = 0
        while i < len(todo):
            chunk = todo[i:i + BATCH]
            try:
                resp = client.models.embed_content(model=EMBED_MODEL, contents=chunk)
                for t, e in zip(chunk, resp.embeddings):
                    cache[t] = e.values
                _save_cache(cache)         # save after each batch -> resumable if interrupted
                i += BATCH
                time.sleep(1)              # gentle pacing under the per-minute limit
            except Exception as ex:
                if "429" in str(ex) or "RESOURCE_EXHAUSTED" in str(ex):
                    print("  embedding rate limit reached — waiting 60s, then resuming...")
                    time.sleep(60)
                    continue               # retry the SAME chunk after the window resets
                raise
    else:
        print(f"  all {len(texts)} embeddings loaded from cache (0 API calls)")

    X = np.array([cache[t] for t in texts])                # build matrix in original order
    return X / np.linalg.norm(X, axis=1, keepdims=True)    # normalize -> cosine-style clustering


def name_cluster(reviews: list[str], areas: list[str]) -> tuple[str, str]:
    """LLM name + one-line summary for a cluster. Falls back to the cluster's
    dominant product area if the LLM is unavailable (rate limits etc.)."""
    try:
        sample = "\n".join(f"- {r[:160]}" for r in reviews[:12])
        prompt = f"""These user reviews were grouped into ONE theme. Give the theme a short,
specific name (e.g. "Offline sync failures") and a one-sentence summary.

Reviews:
{sample}

Reply with ONLY this JSON: {{"name": "...", "summary": "..."}}"""
        raw = complete(prompt, provider="gemini")
        s, e = raw.find("{"), raw.rfind("}")
        d = json.loads(raw[s:e + 1])
        return str(d.get("name", "Unnamed"))[:60], str(d.get("summary", ""))[:200]
    except Exception:
        top_area = Counter(areas).most_common(1)[0][0]
        return f"{top_area.title()} issues", "(auto-named by product area — LLM naming unavailable)"

def run(k: int | None = None) -> None:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, body, product_area FROM feedback_items "
        "WHERE status = 'classified' AND fb_type != 'praise'"
    ).fetchall()
    ids = [r["id"] for r in rows]
    texts = [r["body"] for r in rows]
    areas = [(r["product_area"] or "general") for r in rows]
    print(f"Clustering {len(texts)} actionable items...")

    X = embed_texts(texts)
    if k is None:
        k = max(4, min(8, round(len(texts) / 18)))  # fewer, broader themes (data is a continuum)
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)

    clear_themes(conn)
    for c in range(k):
        members = [i for i, lab in enumerate(labels) if lab == c]
        member_ids = [ids[i] for i in members]
        member_texts = [texts[i] for i in members]
        member_areas = [areas[i] for i in members]
        name, summary = name_cluster(member_texts, member_areas)
        theme_id = save_theme(conn, name, summary)
        assign_theme(conn, member_ids, theme_id)
        print(f"  [{len(member_ids):>3} items] {name}")
    print(f"\nDone. Created {k} themes.")


if __name__ == "__main__":
    import sys
    k = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run(k)
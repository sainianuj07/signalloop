"""Cluster actionable feedback into named themes: embed -> KMeans -> name.

Pipeline:
  1. embed each review (meaning -> vector) with Gemini
  2. group nearby vectors with KMeans (semantic clusters)
  3. ask the LLM to NAME each cluster from its member reviews
  4. save themes and link items to them
"""
import json
import os

import numpy as np
from dotenv import load_dotenv
from google import genai
from sklearn.cluster import KMeans

from src.db import assign_theme, clear_themes, get_conn, save_theme
from src.llm import complete

load_dotenv()
EMBED_MODEL = "gemini-embedding-001"


def embed_texts(texts: list[str]) -> np.ndarray:
    """Turn a list of texts into a matrix of unit-length vectors."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    vectors = []
    BATCH = 50  # embed 50 at a time -> few API calls, no rate-limit pain
    for start in range(0, len(texts), BATCH):
        chunk = texts[start:start + BATCH]
        resp = client.models.embed_content(model=EMBED_MODEL, contents=chunk)
        vectors.extend(e.values for e in resp.embeddings)
    X = np.array(vectors)
    # normalize to unit length so KMeans groups by *direction* (cosine), not magnitude
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def name_cluster(reviews: list[str]) -> tuple[str, str]:
    """Ask the LLM for a short name + one-line summary of a cluster."""
    sample = "\n".join(f"- {r[:160]}" for r in reviews[:12])
    prompt = f"""These user reviews were grouped into ONE theme. Give the theme a short,
specific name (e.g. "Offline sync failures") and a one-sentence summary.

Reviews:
{sample}

Reply with ONLY this JSON: {{"name": "...", "summary": "..."}}"""
    raw = complete(prompt)  # classifier model (Groq) is fine for naming
    s, e = raw.find("{"), raw.rfind("}")
    d = json.loads(raw[s:e + 1])
    return str(d.get("name", "Unnamed"))[:60], str(d.get("summary", ""))[:200]


def run(k: int | None = None) -> None:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, body FROM feedback_items "
        "WHERE status = 'classified' AND fb_type != 'praise'"
    ).fetchall()
    ids = [r["id"] for r in rows]
    texts = [r["body"] for r in rows]
    print(f"Clustering {len(texts)} actionable items...")

    X = embed_texts(texts)
    if k is None:
        k = max(5, min(15, len(texts) // 10))  # heuristic: ~1 theme per 10 items
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X)

    clear_themes(conn)
    for c in range(k):
        members = [i for i, lab in enumerate(labels) if lab == c]
        member_ids = [ids[i] for i in members]
        member_texts = [texts[i] for i in members]
        name, summary = name_cluster(member_texts)
        theme_id = save_theme(conn, name, summary)
        assign_theme(conn, member_ids, theme_id)
        print(f"  [{len(member_ids):>3} items] {name}")
    print(f"\nDone. Created {k} themes.")


if __name__ == "__main__":
    run()
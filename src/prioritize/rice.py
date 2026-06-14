"""Score every theme with RICE -> a ranked roadmap. Pure math, no LLM."""
from src.db import clear_opportunities, get_conn, save_opportunity

DEFAULT_EFFORT = 2.0  # person-weeks; humans adjust this per theme in the dashboard


def compute() -> None:
    conn = get_conn()
    themes = conn.execute("SELECT id, name FROM themes").fetchall()
    clear_opportunities(conn)

    results = []
    for t in themes:
        s = conn.execute(
            """SELECT COUNT(*) AS n, AVG(severity) AS sev, AVG(confidence) AS conf
               FROM feedback_items WHERE theme_id = ?""",
            (t["id"],),
        ).fetchone()

        reach = s["n"]
        impact = round(s["sev"] or 0, 2)         # avg severity 1-4 = how badly it hurts
        confidence = round(s["conf"] or 0, 2)    # avg model confidence 0-1
        effort = DEFAULT_EFFORT
        rice = round((reach * impact * confidence) / effort, 1)

        save_opportunity(conn, t["id"], reach, impact, confidence, effort, rice)
        results.append((rice, t["name"], reach, impact, confidence))

    results.sort(reverse=True)  # highest RICE first
    print(f"{'RICE':>7}  {'Reach':>5} {'Impact':>6} {'Conf':>5}  Theme")
    print("-" * 70)
    for rice, name, reach, impact, conf in results:
        print(f"{rice:>7}  {reach:>5} {impact:>6} {conf:>5}  {name}")


if __name__ == "__main__":
    compute()
"""Theme drift monitoring + auto-published "State of Feedback" brief.

Static dashboards show *what* the feedback is. This shows *what's changing* —
which themes are rising or cooling week over week (theme velocity) — and writes
a short brief a founder could read every Monday. In production this would run on
a schedule (cron / GitHub Action); here it runs on demand and feeds the dashboard.

Usage:
  python -m src.drift.monitor          # print drift table
  python -m src.drift.monitor brief    # generate the weekly brief
"""
import sys
from pathlib import Path

from src.db import get_conn, get_top_opportunity
from src.llm import complete

OUT = Path("docs/generated/weekly_brief.md")
WINDOW = 7  # days per period: "this week" vs "the week before"


def _ask(prompt: str) -> str:
    """Prose completion with provider fallback (Groq -> Gemini)."""
    last = None
    for provider in ("groq", "gemini"):
        try:
            return complete(prompt, provider=provider, json_mode=False).strip()
        except Exception as e:
            last = e
    raise RuntimeError(f"All providers failed: {last}")


def compute_drift(window_days: int = WINDOW):
    """For each theme, count items in the most recent window vs the prior window.
    Returns (anchor_date, [ {theme, recent, previous, change} ... ] sorted by change)."""
    conn = get_conn()
    anchor = conn.execute(
        "SELECT MAX(date(created_at)) FROM feedback_items WHERE created_at IS NOT NULL"
    ).fetchone()[0]
    recent_mod = f"-{window_days} days"
    prev_mod = f"-{2 * window_days} days"

    rows = conn.execute(
        """SELECT t.name AS theme,
                  SUM(CASE WHEN date(f.created_at) > date(?, ?) THEN 1 ELSE 0 END) AS recent,
                  SUM(CASE WHEN date(f.created_at) <= date(?, ?)
                            AND date(f.created_at) >  date(?, ?) THEN 1 ELSE 0 END) AS previous
           FROM themes t JOIN feedback_items f ON f.theme_id = t.id
           GROUP BY t.id, t.name""",
        (anchor, recent_mod, anchor, recent_mod, anchor, prev_mod),
    ).fetchall()

    drift = [{"theme": r["theme"], "recent": r["recent"], "previous": r["previous"],
              "change": r["recent"] - r["previous"]} for r in rows]
    drift.sort(key=lambda d: d["change"], reverse=True)
    return anchor, drift


def generate_brief(window_days: int = WINDOW) -> str:
    conn = get_conn()
    anchor, drift = compute_drift(window_days)
    total_recent = sum(d["recent"] for d in drift)
    rising = [d for d in drift if d["change"] > 0]
    cooling = [d for d in drift if d["change"] < 0]
    top = get_top_opportunity(conn)

    movement = "\n".join(
        f"- {d['theme']}: {d['previous']} → {d['recent']} ({'+' if d['change'] >= 0 else ''}{d['change']})"
        for d in drift
    )
    prompt = f"""You are a product analyst writing a short weekly "State of Feedback" brief for the team.
Week ending {anchor}. {total_recent} actionable feedback items came in this week.

Theme movement (previous week → this week, with change):
{movement}

Top RICE opportunity right now: {top['name']} (RICE {top['rice_score']}).

Write a punchy 4-6 sentence brief in first person: what's rising, what's cooling, and the
ONE thing we should act on this week. Crisp and concrete — no fluff, no AI clichés."""
    narrative = _ask(prompt)

    def _bullets(items):
        return "\n".join(f"- **{d['theme']}** ({'+' if d['change'] >= 0 else ''}{d['change']})"
                         for d in items) or "- (none)"

    md = (f"# State of Feedback — week ending {anchor}\n\n"
          f"*{total_recent} actionable items this week.*\n\n"
          f"## Summary\n{narrative}\n\n"
          f"## Rising themes\n{_bullets(rising)}\n\n"
          f"## Cooling themes\n{_bullets(cooling)}\n\n"
          f"## Movement (prev week → this week)\n{movement}\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    return md


def _print_table():
    anchor, drift = compute_drift()
    print(f"Theme velocity (week ending {anchor}):  prev -> recent (change)")
    for d in drift:
        arrow = "UP  " if d["change"] > 0 else ("DOWN" if d["change"] < 0 else "flat")
        print(f"  [{arrow}] {d['theme']:<42} {d['previous']:>2} -> {d['recent']:>2}  ({d['change']:+d})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "brief":
        generate_brief()
        print(f"Saved -> {OUT}")
    else:
        _print_table()

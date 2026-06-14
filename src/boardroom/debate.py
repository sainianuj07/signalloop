"""The Prioritization Boardroom — a multi-agent debate over the roadmap.

Three role-agents (Growth, Engineering, Finance) argue priorities from their own
incentives; a Head-of-Product agent synthesizes a DECISION MEMO that records the
recommendation AND the dissent. The product insight: real prioritization is a
negotiation between competing interests, not a single formula. RICE ranks; the
boardroom *decides*.

Usage:  python -m src.boardroom.debate
"""
from pathlib import Path

from src.db import get_conn
from src.llm import complete

OUT = Path("docs/generated/boardroom_memo.md")

AGENTS = {
    "Growth PM": "You optimize for reach, activation, retention, and churn reduction. "
                 "You favor work that touches the most users and stops them from leaving.",
    "Engineering Lead": "You weigh implementation effort, technical risk, reliability, and tech debt. "
                        "You favor high-impact fixes that are feasible and reduce instability.",
    "Finance (CFO)": "You weigh cost, ROI, and revenue/retention impact per unit of effort. "
                     "You are skeptical of expensive work with diffuse payoff.",
}


def _ask(prompt: str) -> str:
    """Prose completion with provider fallback so one rate limit can't block us."""
    last = None
    for provider in ("groq", "gemini"):
        try:
            return complete(prompt, provider=provider, json_mode=False).strip()
        except Exception as e:
            last = e
            print(f"    {provider} failed ({str(e)[:50]}) — trying next...")
    raise RuntimeError(f"All providers failed: {last}")


def _roadmap_context(conn) -> str:
    rows = conn.execute(
        """SELECT t.name, o.reach, o.impact, o.confidence, o.effort, o.rice_score
           FROM opportunities o JOIN themes t ON t.id=o.theme_id
           ORDER BY o.rice_score DESC"""
    ).fetchall()
    return "\n".join(
        f"{i+1}. {r['name']} — reach {r['reach']}, impact {r['impact']}/4, "
        f"effort {r['effort']}w, RICE {r['rice_score']}"
        for i, r in enumerate(rows)
    )


def _opinion(role: str, mandate: str, roadmap: str) -> str:
    prompt = f"""You are the {role} on a product leadership team. {mandate}

RICE-ranked roadmap:
{roadmap}

In 4-5 sentences, argue from YOUR perspective: which 1-2 opportunities to prioritize
first, which you'd deprioritize, and why. Be opinionated and specific."""
    return _ask(prompt)


def _synthesize(roadmap: str, opinions: dict) -> str:
    panel = "\n\n".join(f"### {role}\n{op}" for role, op in opinions.items())
    prompt = f"""You are the Head of Product. Three leaders debated the roadmap below.
Write the decision memo in YOUR OWN voice — first person, direct, decisive, the way a real
product leader writes to their team. No corporate filler, no AI clichés, no hedging.

ROADMAP:
{roadmap}

PANEL OPINIONS:
{panel}

Write a markdown decision memo with these sections:
## Decision
The top 3 priorities, in order. For each, ONE sharp sentence of rationale in your own words.
## Dissent
Name exactly where the leaders disagreed, and whose concern you are knowingly setting aside —
and say in one line why you're comfortable carrying that risk.
## Next step
Write this in first person as a concrete commitment, as if I am writing it myself: what I will
do next sprint, who I'll pull in, and what I expect to see. Make it sound owned and specific
(e.g. "I'm putting two engineers on the crash cluster this sprint and asking design to..."),
NOT a generic recommendation."""
    return _ask(prompt)


def run() -> None:
    conn = get_conn()
    roadmap = _roadmap_context(conn)
    if not roadmap:
        print("No roadmap found. Run: python -m src.prioritize.rice")
        return

    print("Convening the boardroom...\n")
    opinions = {}
    for role, mandate in AGENTS.items():
        print(f"  {role} is weighing in...")
        opinions[role] = _opinion(role, mandate, roadmap)
    print("  Head of Product is synthesizing the decision...")
    memo = _synthesize(roadmap, opinions)

    panel_md = "\n\n".join(f"## {role}\n{op}" for role, op in opinions.items())
    full = (f"# Prioritization Boardroom — Decision Memo\n\n"
            f"## Roadmap considered\n{roadmap}\n\n"
            f"# Panel debate\n{panel_md}\n\n---\n{memo}\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(full, encoding="utf-8")
    print(f"\nSaved -> {OUT}")


if __name__ == "__main__":
    run()

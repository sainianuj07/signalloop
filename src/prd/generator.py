"""Citation-verified PRD generator (the centerpiece differentiator).

Takes the top-ranked opportunity (or a given theme), drafts a PRD grounded in
the theme's ACTUAL reviews, then VERIFIES that every [#id] citation points to a
real review in that theme. The verbatim "Evidence" appendix is rendered by US
from the database — so quotes can't be hallucinated, only IDs can, and we catch
those.

Usage:
  python -m src.prd.generator          # top RICE opportunity
  python -m src.prd.generator 5        # a specific theme id
"""
import re
import sys
from pathlib import Path

from src.db import (get_conn, get_opportunity, get_theme_items,
                    get_top_opportunity, save_prd)
from src.llm import complete

OUT_DIR = Path("docs/generated")
MAX_REVIEWS_IN_PROMPT = 30   # cap context size; items are pre-sorted worst-first


def _build_prompt(opp, items) -> str:
    reviews = "\n".join(
        f"[#{r['id']}] ({r['fb_type']}, sev {r['severity']}): {r['body'][:300]}"
        for r in items
    )
    return f"""You are a senior product manager at a B2B SaaS company writing a thorough,
decision-ready PRD that your CEO and engineering lead will actually read and act on.
Write with depth, precision, and a confident first-person product voice — NOT generic
AI filler. Quantify wherever the data allows.

OPPORTUNITY: {opp['name']}
Theme summary: {opp['summary']}
Quantified evidence base: {opp['reach']} user reports, average severity {opp['impact']}/4, RICE {opp['rice_score']}.

ACTUAL user reviews behind this opportunity (cite by their [#id]):
{reviews}

Write a COMPREHENSIVE PRD in markdown. Use EXACTLY these sections, and make each one
substantive (several sentences or a real list — never a single throwaway line):

# PRD: {opp['name']}
**Status:** Draft · **Priority:** <choose P0/P1/P2 and justify in one line> · **Evidence:** {opp['reach']} reports

## 1. Background & Context
Why this surfaced now and what the data shows (counts, severity, churn signals). Cite reviews [#id].

## 2. Problem Statement
Break the core problem into 2–4 distinct sub-problems. For each: what specifically breaks,
who it affects, and the cited evidence [#id]. Be concrete — name the exact failures users describe.

## 3. Goals & Non-Goals
- **Goals:** 3–5 concrete, outcome-oriented goals.
- **Non-Goals:** 2–3 things explicitly out of scope (this shows product judgment).

## 4. Requirements
A numbered list of specific requirements. For EACH requirement give: a **priority** (P0/P1/P2),
what it does in concrete terms, and the cited evidence [#id] that motivates it.

## 5. Success Metrics
3–5 measurable metrics, each with a direction and a TARGET and a timeframe
(e.g. "cut crash-related 1-star reviews by 50% within two releases"). Tie each to a problem above.

## 6. Risks & Open Questions
Real technical/UX/scope risks and the honest open questions a team would actually argue about.

STRICT RULES:
- Every claim about user pain MUST cite one or more review IDs in [#id] form.
- Cite ONLY ids that appear in the list above. NEVER invent an id or a quote.
- Be specific, structured, and confident. Ban hedging and AI clichés
  ("in today's fast-paced world", "it is important to note", "leverage synergies")."""


def _draft(prompt: str) -> str:
    """Draft as prose; try Groq then Gemini so one rate limit can't block us."""
    last = None
    for provider in ("groq", "gemini"):
        try:
            return complete(prompt, provider=provider, json_mode=False)
        except Exception as e:
            last = e
            print(f"  {provider} drafting failed ({str(e)[:70]}) — trying next provider...")
    raise RuntimeError(f"All providers failed for PRD drafting: {last}")


def _verify_citations(prd_text: str, valid_ids: set[int]):
    """Find every #id cited and split into valid vs hallucinated."""
    cited = {int(m) for m in re.findall(r"#(\d+)", prd_text)}
    return cited, (cited & valid_ids), (cited - valid_ids)


def generate(theme_id: int | None = None) -> None:
    conn = get_conn()
    opp = get_opportunity(conn, theme_id) if theme_id else get_top_opportunity(conn)
    if not opp:
        print("No opportunity found. Run RICE first: python -m src.prioritize.rice")
        return

    all_items = get_theme_items(conn, opp["theme_id"])
    prompt_items = all_items[:MAX_REVIEWS_IN_PROMPT]
    valid_ids = {r["id"] for r in prompt_items}     # only ids the model was shown are citeable
    print(f"Drafting PRD for: {opp['name']} (theme {opp['theme_id']}, {len(prompt_items)} reviews shown)...")

    prd = _draft(_build_prompt(opp, prompt_items))
    cited, valid, hallucinated = _verify_citations(prd, valid_ids)

    # Verification report
    report = [
        "\n---\n## Citation Verification (automated guardrail)",
        f"- Citations found: **{len(cited)}**",
        f"- Valid (point to a real review in this theme): **{len(valid)}**",
        f"- Hallucinated (id not in this theme): **{len(hallucinated)}**"
        + (f" — flagged: {sorted(hallucinated)}" if hallucinated else " — none"),
    ]

    # Verbatim evidence — rendered by US from the DB, so quotes are ground-truth
    by_id = {r["id"]: r for r in all_items}
    evidence = ["\n## Evidence — verbatim from source (rendered from DB, not the model)"]
    for cid in sorted(valid):
        r = by_id[cid]
        evidence.append(f'- **[#{cid}]** ({r["fb_type"]}, sev {r["severity"]}): "{r["body"][:280]}"')

    full = prd.strip() + "\n" + "\n".join(report) + "\n" + "\n".join(evidence) + "\n"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"PRD_theme_{opp['theme_id']}.md"
    out_path.write_text(full, encoding="utf-8")
    save_prd(conn, opp["theme_id"], full)

    print(f"\nSaved -> {out_path}")
    print(f"Citations: {len(cited)} total | {len(valid)} valid | {len(hallucinated)} hallucinated")
    print("  [OK] every citation points to a real review"
          if not hallucinated else f"  [WARN] verifier caught hallucinated ids: {sorted(hallucinated)}")


if __name__ == "__main__":
    tid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    generate(tid)

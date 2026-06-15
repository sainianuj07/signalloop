"""Citation-verified PRD generator.

Two workflows:
  - generate(theme_id, suggestions)        -> PRD for a whole theme CLUSTER
  - generate_from_review(review_id, ...)   -> PRD speccing ONE specific REVIEW (bug/feature)

Both accept an optional manager `suggestions` string that is injected into the prompt
to steer the output, verify every [#id] citation against the real source IDs, and append
a verbatim evidence block rendered from the database (so quotes can't be hallucinated).

CLI:
  python -m src.prd.generator                # top-ranked theme
  python -m src.prd.generator theme 35       # a specific theme
  python -m src.prd.generator review 149     # a specific review id
"""
import re
import sys
from pathlib import Path

from src.db import (get_conn, get_opportunity, get_review, get_theme_items,
                    get_top_opportunity, save_prd)
from src.llm import complete

OUT_DIR = Path("docs/generated")
MAX_REVIEWS_IN_PROMPT = 30


# ---------- shared helpers ----------
def _suggestions_block(suggestions: str) -> str:
    """Inject the manager's optional guidance into the prompt (empty if none given)."""
    s = (suggestions or "").strip()
    if not s:
        return ""
    return ("\n\nThe product manager added these guidelines to steer this PRD. "
            "Treat them as priorities and reflect them in the relevant sections:\n"
            f"{s}\n")


def _draft(prompt: str) -> str:
    """Draft prose with provider fallback (Groq -> Gemini), temperature=0 (deterministic)."""
    last = None
    for provider in ("groq", "gemini"):
        try:
            return complete(prompt, provider=provider, json_mode=False)
        except Exception as e:
            last = e
            print(f"  {provider} drafting failed ({str(e)[:70]}) - trying next provider...")
    raise RuntimeError(f"All providers failed for PRD drafting: {last}")


def _verify_citations(prd_text: str, valid_ids: set) -> tuple:
    cited = {int(m) for m in re.findall(r"#(\d+)", prd_text)}
    return cited, (cited & valid_ids), (cited - valid_ids)


def _assemble(prd: str, cited: set, valid: set, hallucinated: set, by_id: dict) -> str:
    """PRD prose + the verification report + verbatim evidence pulled from the DB."""
    report = [
        "\n---\n## Citation Verification (automated guardrail)",
        f"- Citations found: **{len(cited)}**",
        f"- Valid (point to a real review): **{len(valid)}**",
        f"- Hallucinated: **{len(hallucinated)}**"
        + (f" - flagged: {sorted(hallucinated)}" if hallucinated else " - none"),
    ]
    evidence = ["\n## Evidence - verbatim from source (rendered from the database, not the model)"]
    for cid in sorted(valid):
        r = by_id.get(cid)
        if r is not None:
            evidence.append(f'- **[#{cid}]** ({r["fb_type"]}, sev {r["severity"]}): "{str(r["body"])[:280]}"')
    return prd.strip() + "\n" + "\n".join(report) + "\n" + "\n".join(evidence) + "\n"


# ---------- workflow 1: theme cluster ----------
def _build_theme_prompt(opp, items, suggestions: str) -> str:
    reviews = "\n".join(
        f"[#{r['id']}] ({r['fb_type']}, sev {r['severity']}): {str(r['body'])[:300]}"
        for r in items)
    return f"""You are a senior product manager writing a thorough, decision-ready PRD that your
CEO and engineering lead will act on. Depth, precision, a confident first-person voice, no AI filler.

OPPORTUNITY: {opp['name']}
Theme summary: {opp['summary']}
Evidence base: {opp['reach']} reports, avg severity {opp['impact']}/4, RICE {opp['rice_score']}.

ACTUAL user reviews behind this opportunity (cite by their [#id]):
{reviews}
{_suggestions_block(suggestions)}
Write a COMPREHENSIVE PRD in markdown with EXACTLY these sections, each substantive:

# PRD: {opp['name']}
**Status:** Draft · **Priority:** <P0/P1/P2 + one-line justification> · **Evidence:** {opp['reach']} reports

## 1. Background & Context
## 2. Problem Statement   (break into 2-4 cited sub-problems)
## 3. Goals & Non-Goals
## 4. Requirements         (numbered; each with a P0/P1/P2 tag and cited evidence [#id])
## 5. Success Metrics      (each with a direction, target and timeframe)
## 6. Risks & Open Questions

STRICT RULES:
- Every claim about user pain MUST cite review IDs in [#id] form.
- Cite ONLY ids from the list above. NEVER invent an id or a quote.
- Be specific and confident. No marketing fluff or AI clichés."""


def generate(theme_id: int = None, suggestions: str = "") -> str:
    conn = get_conn()
    opp = get_opportunity(conn, theme_id) if theme_id else get_top_opportunity(conn)
    if not opp:
        return "No opportunity found. Run RICE first: python -m src.prioritize.rice"
    all_items = get_theme_items(conn, opp["theme_id"])
    prompt_items = all_items[:MAX_REVIEWS_IN_PROMPT]
    valid_ids = {r["id"] for r in prompt_items}

    prd = _draft(_build_theme_prompt(opp, prompt_items, suggestions))
    cited, valid, hallucinated = _verify_citations(prd, valid_ids)
    by_id = {r["id"]: r for r in all_items}
    full = _assemble(prd, cited, valid, hallucinated, by_id)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"PRD_theme_{opp['theme_id']}.md").write_text(full, encoding="utf-8")
    save_prd(conn, opp["theme_id"], full)
    print(f"[theme] {opp['name']}: citations {len(cited)} | valid {len(valid)} | hallucinated {len(hallucinated)}")
    return full


# ---------- workflow 2: specific review id ----------
def _build_review_prompt(review, siblings, suggestions: str) -> str:
    related = ""
    if siblings:
        lines = "\n".join(
            f"[#{r['id']}] ({r['fb_type']}, sev {r['severity']}): {str(r['body'])[:200]}"
            for r in siblings)
        related = ("\n\nRelated feedback from the SAME theme (supporting evidence you may also "
                   f"cite, to show this is not a one-off):\n{lines}\n")
    return f"""You are a senior product manager turning ONE specific user review into a focused,
buildable PRD. Treat the TARGET review as a concrete bug report or feature request, and use the
related feedback only to corroborate how widespread the issue is. Keep the spec scoped to this issue.

TARGET REVIEW [#{review['id']}]  (type: {review['fb_type']}, severity: {review['severity']}/4):
\"\"\"{str(review['body'])}\"\"\"
{related}{_suggestions_block(suggestions)}
Write a focused PRD in markdown with EXACTLY these sections:

# PRD: <a short, specific title for this issue>
**Source:** review [#{review['id']}] · **Type:** {review['fb_type']} · **Severity:** {review['severity']}/4

## 1. Problem
What exactly is broken or missing, grounded in the target review [#{review['id']}]. Where the
related feedback backs it up, cite those ids too to show it is not a one-off.

## 2. Proposed Solution & Requirements
Numbered requirements, each with a priority tag (P0/P1/P2).

## 3. Acceptance Criteria
Testable bullet conditions that mean this is done.

## 4. Success Metric
One measurable metric with a target and a timeframe.

## 5. Risks & Open Questions

STRICT RULES:
- Always cite the target review [#{review['id']}]; you MAY also cite the related ids listed above.
- Do NOT invent any other review ids or quotes.
- Be specific and buildable. No fluff or AI clichés."""


def generate_from_review(review_id: int, suggestions: str = "") -> str:
    conn = get_conn()
    review = get_review(conn, review_id)
    if review is None:
        return f"No review found with id {review_id}."

    # pull a few sibling reviews from the same theme for corroboration
    siblings = []
    if review["theme_id"] is not None:
        siblings = [r for r in get_theme_items(conn, review["theme_id"])
                    if r["id"] != review_id][:6]

    prd = _draft(_build_review_prompt(review, siblings, suggestions))
    valid_ids = {review["id"]} | {r["id"] for r in siblings}
    cited, valid, hallucinated = _verify_citations(prd, valid_ids)
    by_id = {review["id"]: review}
    by_id.update({r["id"]: r for r in siblings})
    full = _assemble(prd, cited, valid, hallucinated, by_id)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"PRD_review_{review_id}.md").write_text(full, encoding="utf-8")
    print(f"[review #{review_id}] siblings {len(siblings)} | citations {len(cited)} "
          f"| valid {len(valid)} | hallucinated {len(hallucinated)}")
    return full


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "review":
        generate_from_review(int(args[1]))
    elif args and args[0] == "theme":
        generate(int(args[1]) if len(args) > 1 else None)
    else:
        generate()

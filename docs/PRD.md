# PRD — SignalLoop: Feedback-to-Roadmap Intelligence Engine

**Author:** Anuj Kumar · **Status:** Draft v1 · **Date:** 2026-06-11 · **Target ship:** 2026-06-14

---

## 1. Problem

Early-stage B2B SaaS teams (pre-seed → Series A) drown in unstructured feedback — support tickets, app-store reviews, sales call notes, NPS verbatims — scattered across 5+ tools. Nobody has time to read it all, so roadmap decisions default to **the loudest customer, the founder's gut, or the most recent complaint**.

The cost is concrete: churned customers whose complaints were never aggregated, weeks of engineering spent on features nobody asked for, and investor updates that say "customers love it" with no evidence.

**Why existing tools don't solve this for our segment:**

| Tool | Why it fails early-stage teams |
|---|---|
| Productboard, Aha! | $20–60/seat/mo, built for PM teams that already exist; weeks of setup |
| Enterpret, Unwrap.ai | Enterprise pricing ($1k+/mo), sales-led, overkill at <500 feedback items/mo |
| Canny | Captures feature requests users *submit*; doesn't mine the feedback you *already have* |
| Spreadsheet + intern | What everyone actually does; doesn't scale past week 2 |

**The wedge:** zero-setup, AI-first, founder-priced. Drop in a CSV or connect a source, get a prioritized roadmap brief in minutes — no taxonomy setup, no tagging, no onboarding call.

## 2. Target user (ICP)

- **Who:** Founder or first PM at a B2B SaaS startup, 2–30 employees, 50–5,000 users.
- **Trigger moment:** feedback volume crosses ~100 items/month — too much to read, too little to justify Productboard.
- **Jobs to be done:**
  1. *"When I plan the next sprint/quarter, I want to know which problems hurt the most customers the worst, so I can defend roadmap choices with evidence."*
  2. *"When a churned customer asks 'did you even read my feedback?', I want to prove we systematically process every item."*
  3. *"When I write the investor update, I want quantified voice-of-customer themes, not anecdotes."*

## 3. Solution overview

A pipeline + dashboard with four stages:

```
INGEST → UNDERSTAND → PRIORITIZE → ACT
```

1. **Ingest** — pull feedback from sources (v1: app-store reviews + CSV import covering tickets/NPS/anything).
2. **Understand (AI)** — every item is classified by an LLM into: feedback type (bug / feature request / UX friction / pricing / praise / churn risk), product area, sentiment, and severity. Items are then clustered into named themes ("Export to PDF broken on mobile" — 47 items).
3. **Prioritize** — themes are scored with RICE (Reach from item counts, Impact from severity, Confidence from cluster coherence, Effort estimated + human-editable). Output: a ranked opportunity list.
4. **Act** — one click generates (a) a weekly insight brief and (b) a draft PRD for any top opportunity, grounded in the actual customer quotes. **Human-in-the-loop:** every AI label is reviewable/correctable, and corrections feed the eval set.

## 4. MVP scope (4-day build)

**In:**
- Google Play review ingestion (live scraping, no API key) + universal CSV import
- LLM classification pipeline with structured JSON output, batching, retry, and a deterministic mock mode
- Theme clustering and naming
- RICE-scored opportunity board
- Insight brief + draft-PRD generation
- Eval harness: golden labeled set, accuracy report per label dimension
- Streamlit dashboard (review queue, themes, opportunities, evals tab)
- Free-tier LLMs only (Groq / Gemini), graceful rate-limit handling

**Out (v2+):**
- Intercom/Zendesk/Slack native integrations
- Multi-tenant auth & billing
- Fine-tuning; vector database
- Automatic effort estimation from codebase

## 5. Success metrics

- **North star:** *% of ingested feedback items that reach a prioritized theme* (target ≥ 85%) — measures whether the engine turns raw noise into decision-ready signal.
- **Quality:** classification accuracy vs. golden set ≥ 80% on type, ≥ 75% on severity (measured by eval harness, not vibes).
- **Activation (product):** time from CSV upload → first prioritized opportunity ≤ 5 minutes.
- **Trust:** % of AI labels corrected by human review ≤ 15% (rising corrections = model or taxonomy drift).
- **Cost guardrail:** ≤ $0 (free tier) at demo scale; modeled cost ≤ $0.02 per 100 items at paid scale.

## 6. Risks & mitigations

| Risk | Type | Mitigation |
|---|---|---|
| LLM mislabels feedback → wrong priorities | AI quality | Golden eval set before trusting output; human review queue; confidence thresholds route low-confidence items to humans |
| Free-tier rate limits block pipeline | Technical | Batch 15–20 items per call; exponential backoff; resumable runs (SQLite state) |
| Hallucinated quotes in generated PRDs | AI safety | PRD generator only quotes verbatim items passed in context; post-check that quotes exist in source |
| Themes too generic ("improve UX") to act on | Product | Cluster naming prompt requires specificity + example items; minimum cluster size |
| Demo data ≠ B2B reality | GTM | CSV import means any startup can use their real tickets day one |

## 7. Milestones

- **Day 1 (Thu):** PRD, repo, data layer, real reviews ingested 
- **Day 2 (Fri):** Classification pipeline + golden set + eval harness
- **Day 3 (Sun):** Clustering, RICE board, report/PRD generation, dashboard, Human-in-the-loop polish, scheduled ingestion, deploy (Streamlit Cloud), case-study README

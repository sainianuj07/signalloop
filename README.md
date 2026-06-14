# SignalLoop — Feedback-to-Roadmap Intelligence Engine

Turn raw user feedback (app reviews, support tickets, NPS) into a **prioritized,
evidence-backed roadmap** — built for early-stage B2B SaaS teams who have too much
feedback to read and no PM team to read it.

```
INGEST  →  UNDERSTAND (LLM)  →  PRIORITIZE (RICE)  →  ACT (PRDs, decisions, briefs)
```

> **Why this exists:** roadmap calls at early-stage startups default to the loudest
> customer or the founder's gut. SignalLoop reads *every* item, groups it into themes,
> ranks them with RICE, and produces decision-ready artifacts — with a measurable
> evaluation layer and a human-in-the-loop behind every AI label.

*(Add a screenshot/GIF of the dashboard here.)*

---

## What it does

1. **Ingest** — live Google Play reviews (no API key) + universal CSV import for any team's own data.
2. **Understand** — an LLM labels every item (type · product area · sentiment · severity) with structured JSON, batching, retries, and a deterministic mock mode.
3. **Prioritize** — items are clustered into named **themes** (embeddings + KMeans), then scored with **RICE** into a ranked opportunity board.
4. **Act** —
   - **Citation-verified PRD generator** — drafts a PRD for the top opportunity where *every claim cites a real review ID*, with an automated checker for hallucinated citations and a verbatim evidence appendix rendered from the database.
   - **Prioritization Boardroom** — Growth / Engineering / Finance agents debate the roadmap; a Head-of-Product agent writes a decision memo *with recorded dissent*.
   - **Drift monitoring + weekly brief** — detects which themes are rising/cooling week-over-week and auto-writes a "State of Feedback" brief.
5. **Trust** — a **two-layer evaluation** system and a human-in-the-loop **review queue**.

## What makes it more than a demo

| Layer | Most portfolio projects | SignalLoop |
|---|---|---|
| Evaluation | "looks right" | **Human golden set + independent cross-vendor LLM judge**, certified before trust; 96% judge-estimated type accuracy; a real classifier bias caught *and fixed* |
| Generation | hope it's grounded | **Citations verified against source; quotes rendered from the DB** (hallucinated quotes are structurally impossible) |
| Prioritization | a RICE table | **Multi-agent debate → decision memo with explicit dissent** |
| Lifecycle | a static snapshot | **Drift monitoring + auto-published brief** |
| Engineering | one happy path | provider fallback, rate-limit cooldowns, resumable pipeline, embedding cache, graceful degradation |

## The PM thinking (read these)

- **[docs/PRD.md](docs/PRD.md)** — problem, ICP, the competitive wedge, success metrics, AI-risk table.
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — 6 ADRs (architecture decision records), incl. the two-layer eval design.
- **[docs/MODEL_MEMO.md](docs/MODEL_MEMO.md)** — data-driven model selection (accuracy / cost / rate-limit trade-offs).
- **Sample outputs:** [a generated PRD](docs/generated/PRD_theme_35.md) · [a boardroom memo](docs/generated/boardroom_memo.md) · [a weekly brief](docs/generated/weekly_brief.md).

## Architecture

```
src/
  ingest/      play_store + csv  -> SQLite
  classify/    prompt · llm client (Groq/Gemini/mock) · classifier · pipeline
  eval/        judge (independent model) · run_eval (certify + scale)
  cluster/     embeddings (cached) -> KMeans -> LLM-named themes
  prioritize/  RICE scoring -> opportunity board
  prd/         citation-verified PRD generator
  boardroom/   multi-agent prioritization debate
  drift/       theme velocity + weekly brief
app/dashboard.py   Streamlit product surface (7 tabs, Plotly visuals)
```

## Run it locally

```bash
pip install -r requirements.txt
copy .env.example .env          # add a free Groq and/or Gemini key (see file)

python -m src.ingest.play_store notion.id --count 300   # ingest demo data
python -m src.classify.pipeline                          # label everything
python -m src.cluster.themes                             # themes
python -m src.prioritize.rice                            # RICE roadmap
python -m src.prd.generator                              # citation-verified PRD
python -m src.boardroom.debate                           # boardroom memo
python -m src.drift.monitor brief                        # weekly brief

streamlit run app/dashboard.py                           # the dashboard
```

Free-tier only: **Groq** (console.groq.com) and **Google AI Studio** (aistudio.google.com),
no credit card. A deterministic `mock` provider runs the whole pipeline offline.

## Results & honest limitations

- 216 real reviews → 102 actionable → 6 themes → ranked roadmap → generated PRD + decision memo.
- Judge-estimated **96%** type accuracy (independent model, sampled).
- **Limitations I'd fix next:** feedback doesn't cluster crisply (silhouette ~0.04 → cluster
  count is a judgment call); classifier confidence is uncalibrated; free-tier rate limits were
  the real constraint (production = paid tier). Details in [MODEL_MEMO.md](docs/MODEL_MEMO.md).

## Tech

Python · SQLite · Streamlit · Plotly · scikit-learn · Groq (Llama-3.3-70B, GPT-OSS-20B) ·
Google (Gemini, embeddings). Provider-agnostic LLM layer; swap models in one line.

# SignalLoop — Feedback-to-Roadmap Intelligence Engine

Turn raw user feedback (app reviews, support tickets, NPS verbatims) into a prioritized, evidence-backed roadmap — built for early-stage B2B SaaS teams that have too much feedback to read and no PM team to read it.

```
INGEST  →  UNDERSTAND (LLM)  →  PRIORITIZE (RICE)  →  ACT (briefs + draft PRDs)
```

## Why this exists

Roadmap decisions at early-stage startups default to the loudest customer or the founder's gut. SignalLoop processes every feedback item: classifies it (type, product area, sentiment, severity), clusters items into named themes, scores themes with RICE, and generates insight briefs and draft PRDs grounded in verbatim customer quotes — with a human-in-the-loop review queue and a measurable eval harness behind every AI label.

Full product thinking: [docs/PRD.md](docs/PRD.md) · Decisions: [docs/DECISIONS.md](docs/DECISIONS.md)

## Quickstart

```bash
pip install -r requirements.txt
copy .env.example .env          # add a free Groq or Gemini key (see file)

# Ingest demo data (live Google Play reviews, no key needed)
python -m src.ingest.play_store notion.id --count 300
# ...or your own data
python -m src.ingest.csv_import path/to/feedback.csv

# Classify + cluster + prioritize (Day 2-3, coming)
# Launch dashboard (Day 3, coming)
streamlit run app/dashboard.py
```

## Status

- [x] Day 1 — PRD, data layer, ingestion (Play Store + CSV)
- [ ] Day 2 — LLM classification pipeline, golden set, eval harness
- [ ] Day 3 — Theme clustering, RICE board, report/PRD generation, dashboard
- [ ] Day 4 — Human-in-the-loop, automation, deploy, case study

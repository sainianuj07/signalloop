# SignalLoop: Feedback-to-Roadmap Intelligence Engine

# SignalLoop

**Live demo:** https://signalloop.streamlit.app/  ·  **Code:** this repo

SignalLoop reads raw user feedback — app-store reviews, support tickets, NPS notes — and turns it into a prioritized, evidence-backed roadmap. I built it to answer a question I kept hitting while learning product management: *how does a small team decide what to build when they're drowning in feedback and don't have a PM team to read it all?*

<img width="2648" height="1562" alt="dashboard" src="https://github.com/user-attachments/assets/1425bf55-9930-4de5-baf2-bdb3bec75651" />


## Why I built it

I'm moving into AI PM, and I wanted to build an AI workflow end to end — not just talk about one in an interview. The interesting stuff isn't "call an LLM and render a chart." It's the boring-but-load-bearing parts: proving the model is actually right, surviving free-tier rate limits, and writing my decisions down so they're defensible. That's where most demos quietly skip; so that's where I spent my time.

## How it works

1. **Ingest** — live Play Store reviews (no API key needed) or a CSV of your own tickets.
2. **Understand** — an LLM labels every item: type, product area, sentiment, severity (structured JSON, with batching, retries, and an offline mock mode).
3. **Prioritize** — items get embedded and clustered into named themes, then scored with RICE into a ranked opportunity board.
4. **Act** — generate a citation-verified PRD for the top opportunity, run the prioritization boardroom, or publish the weekly brief.

## The parts I cared most about

**Evaluation, done honestly.** Anyone can call an LLM and show a chart. The harder question is *how do you know it's right?* I hand-labeled a small golden set, then built an **independent LLM judge** (OpenAI's model grading Meta's Llama, so it doesn't just agree with itself) and only trusted it after checking it against my human labels. It estimated ~96% type accuracy — and more importantly, it **caught a real bias**: my classifier was labeling *angry* reviews as "churn risk" even when the user never said they'd leave. I tightened the prompt, re-ran the eval, and watched the bad labels move. Measure → diagnose → fix → measure again.

**PRDs that can't make things up.** The PRD generator drafts each section grounded in actual reviews, and every claim has to cite a review ID. A checker then verifies those citations are real, and the evidence quotes are pulled straight from the database — not from the model — so a hallucinated quote is impossible by construction.

**Prioritization as a negotiation, not a formula.** RICE gives you a number, but real roadmap calls are arguments between people who want different things. So I built a "boardroom": a Growth, an Engineering, and a Finance agent debate the roadmap from their own incentives, and a Head-of-Product agent writes the decision — including where they disagreed and whose risk it's accepting.

**Watching what changes, not just what is.** A static dashboard tells you the state of feedback. Drift monitoring tells you the *movement* — it compares this week to last and flags themes that are spiking. On my data it caught "offline status" complaints jumping 1 → 6 in a week, which a RICE table would have buried.

## What I learned (the honest part)

- **Free-tier rate limits were the real boss fight,** not model quality. I hit Groq's daily token cap and Gemini's per-minute limits repeatedly, and ended up building provider fallback, visible cooldowns, a resumable pipeline, and an embedding cache so I never pay to embed the same review twice.
- **Not everything clusters cleanly.** I validated cluster quality with a silhouette score and found the feedback is more of a continuum than neat topics (~0.04). So I treated "how many themes" as a product judgment, not something a metric handed me — and said so instead of pretending.
- **Models sound more confident than they are.** Every label came back 80–100% confident, including the wrong ones. That's exactly why an independent eval matters.

## Run it yourself

```bash
pip install -r requirements.txt
copy .env.example .env        # add a free Groq and/or Gemini key (links in the file)

python -m src.ingest.play_store notion.id --count 300   # ingest demo data
python -m src.classify.pipeline                          # label everything
python -m src.cluster.themes                             # build themes
python -m src.prioritize.rice                            # rank with RICE
python -m src.prd.generator                              # citation-verified PRD
python -m src.boardroom.debate                           # boardroom memo
python -m src.drift.monitor brief                        # weekly brief

streamlit run app/dashboard.py                           # the dashboard

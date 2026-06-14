# Decision Log

Short records of consequential choices — what we picked, what we rejected, and why. (PM hygiene: decisions are products too.)

## ADR-001: Free-tier LLM strategy 
**Decision:** Provider-agnostic client with three backends: Groq (`llama-3.3-70b-versatile`, free ~14k req/day), Google Gemini (`gemini-2.5-flash` free tier), and a deterministic **mock mode** for development/tests.
**Rejected:** Anthropic/OpenAI (no free tier — budget constraint); local models via Ollama (setup burden, slow on laptop, hurts 4-day deadline).
**Consequence:** prompts must stay model-portable (plain JSON-schema instructions, no provider-specific tool calling in v1).

## ADR-002: SQLite over Postgres 
**Decision:** SQLite single-file DB.
**Why:** zero setup, ships inside the repo, resumable pipeline state for free. At demo scale (<10k items) performance is a non-issue.
**Revisit when:** multi-tenant or concurrent writers.

## ADR-003: Streamlit over FastAPI+React 
**Decision:** Streamlit for the entire UI.
**Why:** 4-day deadline; intermediate-Python builder; free deployment on Streamlit Community Cloud; dashboards are Streamlit's home turf.
**Trade-off accepted:** less UI control, no real auth in v1.

## ADR-004: Demo dataset = Google Play reviews 
**Decision:** Scrape public Google Play reviews of a well-known SaaS app (Notion) as the live demo dataset; CSV import is the path for real customers' own data.
**Why:** real, messy, public, free, no API key; reviewers genuinely report bugs/feature requests, so the classification problem is authentic.


## ADR-005: Added `question` to the feedback taxonomy (Anuj)
**Decision:** Add an 8th feedback type, `question` — the user is asking how to do something or is confused about existing functionality (a how-to / support request).
**Why:** Spotted a real gap — feedback like *"how do I use this for maximum productivity?"* is neither a bug nor a feature request; it signals a **docs/onboarding** problem, not a product defect. Different signal → different action (improve docs, not build features).
**Consequence:** The classification prompt and the golden eval set must both include `question` as a valid label.


## ADR-006: Two-layer evaluation — human golden set + independent LLM-as-judge (Anuj)
**Decision:** Evaluate classification in two layers: (1) a small (~50), fixed, human-labeled golden set as ground truth; (2) an LLM-as-judge (Gemini) that grades the classifier (Llama) automatically and scales to any data volume. The judge is certified by measuring its agreement with the human golden set before being trusted at scale.
**Why:** Hand-labeling every item doesn't scale to thousands/millions (the real production problem). A pure LLM-judge with no human anchor can't be trusted ("who grades the grader?"). Stacking them keeps human effort flat and small while scaling evaluation infinitely, still anchored to human judgment.
**Independence:** Judge model (Gemini) differs from classifier model (Llama) so the judge doesn't share the classifier's blind spots / rubber-stamp its own style.
**Consequence:** Need a free Gemini API key. Must report judge-human agreement % as the judge's trust score.

**Update (judge model):** Gemini free tier rate-limited bulk eval (~20 req/min → 429s). Switched the judge to OpenAI `gpt-oss-20b` on Groq — still cross-vendor independent (OpenAI judging Meta's Llama) but fast with generous free limits. First result: judge–human agreement 4/4 (easy cases; needs labeled disagreements); judge-estimated type accuracy 96% on a 50-item sample, 2 flags — both over-applied `churn_risk`.
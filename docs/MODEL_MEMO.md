# Model-Selection Memo — SignalLoop

**Author:** Anuj Kumar · **Updated:** 2026-06 · **Audience:** eng + leadership

A record of *which* models do *what* in the pipeline, *why*, and the accuracy / cost /
throughput trade-offs behind each call. The point: model choice is a product decision,
made against evals and constraints — not a default.

## The jobs, and the model assigned to each

| Stage | Job | Model | Why this one |
|---|---|---|---|
| Classify | Label each review (type / severity / sentiment) | **Llama-3.3-70B** (Groq) | Strong instruction-following + native JSON mode; fast on Groq; generous free tier |
| Judge (eval) | Grade the classifier's labels | **GPT-OSS-20B** (Groq) | **Cross-vendor independence** (OpenAI grading Meta) so the judge doesn't share the classifier's blind spots |
| Embed | Vectorize reviews for clustering | **gemini-embedding-001** (Google) | Free, batchable (few calls), 3072-dim captures semantics well |
| Name / Draft | Theme names, PRD, boardroom, brief | **Llama-3.3-70B → Gemini fallback** | Quality prose; fallback survives rate limits |

## Why an *independent* judge (the key eval decision)

If the classifier grades itself, it rubber-stamps its own style and biases (we measured
this: a same-style judge agreed with everything). Using a **different model family** as the
judge is what makes "96% type accuracy" a credible number rather than a model flattering
itself. This is the standard production pattern (model-graded eval, validated against a
human golden set). See [DECISIONS.md ADR-006](DECISIONS.md).

## Evidence base (from our own eval harness)

- **Judge ↔ human agreement:** anchored on a hand-labeled golden set (the judge is only
  trusted because it matches human labels first).
- **Judge-estimated type accuracy:** **96%** on a 50-item sample; the judge flagged real
  disagreements (it discriminates — not a rubber stamp).
- **A real bias caught & fixed:** the classifier over-applied `churn_risk` to *angry* reviews
  that never said they'd leave. We tightened the prompt definition (anger ≠ churn) and the
  bias dropped (`churn_risk` 14 → 9; the exact flagged reviews moved to `bug`/`ux_friction`).
  Measure → diagnose → fix → re-measure.

## Cost / throughput / latency trade-offs

- **The binding constraint during the build was free-tier rate limits, not model quality.**
  We hit Groq's daily token cap (100k TPD) and Gemini's per-minute embedding cap (100 RPM).
- **Mitigations built in:** provider fallback (Groq↔Gemini), visible 429 cooldowns with
  bounded retries (resumable pipeline), and an **on-disk embedding cache** (never embed the
  same review twice — re-clustering is then free).
- **Production economics:** on a paid tier (e.g. Groq Dev, or a small hosted model) the rate
  limits vanish. Modeled cost at scale is well under **$0.02 per 100 items** for
  classification — cheap enough that the bottleneck becomes review quality, not spend.

## What I'd change at larger scale

- Swap KMeans for HDBSCAN (auto cluster count + outlier handling); our silhouette analysis
  showed the feedback is a *continuum* (~0.04), so cluster count is a judgment call today.
- Calibrate the classifier's confidence (currently 0.8–1.0 on everything) so the review
  queue can route by *true* uncertainty.
- Move embeddings to a paid/batch endpoint or a local model to remove the per-minute ceiling.

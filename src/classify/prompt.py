"""Builds the classification prompt we send to the LLM.

The prompt is a *product decision*: the type DEFINITIONS below (not just the
names) are what the model actually reads. Bare names -> the model invents its
own meaning; precise definitions -> consistent, intended labels.
"""

# Each type's DEFINITION is sent to the model. (Comments aren't — only the
# prompt string reaches the AI.) churn_risk is deliberately strict: anger is
# NOT churn; we require an explicit exit signal.
TYPE_DEFINITIONS = {
    "bug": "something is broken: crashes, errors, freezes, data loss, or it doesn't work as intended",
    "feature_request": "the user wants a capability that doesn't exist yet",
    "ux_friction": "it works, but it's confusing, clunky, slow, or harder to use than it should be",
    "pricing": "about cost, plans, billing, paywalls, or value-for-money",
    "praise": "positive feedback with no problem to fix",
    "churn_risk": ("the user EXPLICITLY signals they are leaving: canceling, uninstalling, "
                   "switching to a competitor, or demanding a refund. Anger or frustration "
                   "ALONE is NOT churn_risk — there must be a clear exit signal"),
    "question": "the user asks how to do something, or is confused about an existing feature (a docs/onboarding gap)",
    "other": "genuinely none of the above",
}

# Single source of truth: the allowed labels are exactly the defined ones.
FEEDBACK_TYPES = list(TYPE_DEFINITIONS.keys())

SEVERITY_SCALE = """1 = minor (cosmetic, mild annoyance)
2 = moderate (slows the user down, has a workaround)
3 = major (blocks an important task, no easy workaround)
4 = critical (app unusable, data loss, or user is explicitly churning)"""


def _format_type_definitions() -> str:
    return "\n".join(f"- {name}: {desc}" for name, desc in TYPE_DEFINITIONS.items())


def build_prompt(review_text: str) -> str:
    """Return the full instruction text for classifying one review."""
    return f"""You are an expert product analyst for a B2B SaaS company.
Classify the user feedback below into a structured label.

Choose `type` as exactly ONE of these. Follow the definitions strictly:
{_format_type_definitions()}

Rate `severity` on this scale:
{SEVERITY_SCALE}

Also identify:
- `area`: the product area in 1-3 words (e.g. "sync", "mobile editor", "billing")
- `sentiment`: one of positive, neutral, negative
- `confidence`: your confidence from 0.0 to 1.0 that this label is correct

Respond with ONLY a JSON object in exactly this shape, nothing else:
{{"type": "...", "area": "...", "sentiment": "...", "severity": 0, "confidence": 0.0}}

USER FEEDBACK:
\"\"\"{review_text}\"\"\"
"""
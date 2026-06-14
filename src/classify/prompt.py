"""Builds the classification prompt we send to the LLM.

The prompt is a *product decision*, not just code: the categories and the
severity scale below define what SignalLoop can 'see' in feedback.
"""

# The 8 feedback types the model is allowed to choose from.
# Constraining the choices is what keeps our data clean and countable.
FEEDBACK_TYPES = [
    "bug",            # something is broken / not working
    "feature_request",# user wants something that doesn't exist yet
    "ux_friction",    # it works, but it's confusing or hard to use
    "pricing",        # cost, plans, billing, value-for-money
    "praise",         # positive feedback, no action needed
    "churn_risk",     # user is leaving or threatening to leave
    "question",       # user asking how to do something (docs/onboarding gap)
    "other",          # genuinely none of the above
]

SEVERITY_SCALE = """1 = minor (cosmetic, mild annoyance)
2 = moderate (slows the user down, has a workaround)
3 = major (blocks an important task, no easy workaround)
4 = critical (app unusable, data loss, or user is churning)"""


def build_prompt(review_text: str) -> str:
    """Return the full instruction text for classifying one review."""
    types_list = ", ".join(FEEDBACK_TYPES)
    return f"""You are an expert product analyst for a B2B SaaS company.
Classify the user feedback below into a structured label.

Choose `type` from exactly one of: {types_list}

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
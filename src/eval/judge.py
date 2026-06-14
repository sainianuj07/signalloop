"""LLM-as-judge: an INDEPENDENT model (Gemini) grades the classifier's labels.

judge_one(review, assigned_type) -> {type_correct, suggested_type, reasoning}
Used to (a) certify the judge against the human golden set, then
(b) evaluate all data at scale — no extra human labeling needed.
"""
import json

from src.classify.prompt import FEEDBACK_TYPES
from src.llm import complete

JUDGE_PROVIDER = "groq"               # fast, generous free limits
JUDGE_MODEL = "openai/gpt-oss-20b"    # OpenAI's model judging Meta's Llama = cross-vendor independence


def _build_judge_prompt(review_text: str, assigned_type: str) -> str:
    types_list = ", ".join(FEEDBACK_TYPES)
    return f"""You are a strict QA reviewer for a feedback-classification system.
Decide whether the TYPE a classifier assigned to a user review is correct.

Allowed types: {types_list}

User review:
\"\"\"{review_text}\"\"\"

Classifier assigned type: {assigned_type}

Reply with ONLY this JSON, nothing else:
{{"type_correct": true, "suggested_type": "...", "reasoning": "..."}}
"""


def judge_one(review_text: str, assigned_type: str) -> dict:
    """Ask the independent judge whether `assigned_type` fits the review."""
    prompt = _build_judge_prompt(review_text, assigned_type)
    try:
        raw = complete(prompt, provider=JUDGE_PROVIDER, model=JUDGE_MODEL)
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end + 1])
        return {
            "type_correct": bool(data.get("type_correct", False)),
            "suggested_type": str(data.get("suggested_type", assigned_type)),
            "reasoning": str(data.get("reasoning", ""))[:300],
        }
    except Exception as e:
        # judge itself failed (e.g. quota) — return 'unknown', don't crash
        return {"type_correct": None, "suggested_type": assigned_type,
                "reasoning": f"judge error: {e}", "error": str(e)}
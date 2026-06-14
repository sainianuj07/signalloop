"""Turn one raw review into a clean, VALIDATED label dictionary.

Layer 2: hardened. Survives the AI adding chatter, returning broken
JSON, or inventing categories. Always returns a usable dict.
"""
import json

from src.classify.prompt import FEEDBACK_TYPES, build_prompt
from src.llm import complete

VALID_SENTIMENTS = {"positive", "neutral", "negative"}


def classify_one(review_text: str) -> dict:
    """Classify a single review. Always returns a valid label dict —
    even if the AI misbehaves (then we fall back to a safe 'needs review' label)."""
    prompt = build_prompt(review_text)
    try:
        raw_reply = complete(prompt)
        data = _extract_json(raw_reply)
    except Exception as e:
        # The AI failed us. Don't crash the pipeline — flag for a human.
        return {
            "type": "other", "area": "unknown", "sentiment": "neutral",
            "severity": 2, "confidence": 0.0, "error": str(e),
        }
    return _validate(data)


def _extract_json(text: str) -> dict:
    """Grab the JSON object from the reply, even if wrapped in chatter.
    Takes everything from the first '{' to the last '}'."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in AI reply")
    return json.loads(text[start:end + 1])


def _validate(data: dict) -> dict:
    """Force the AI's output into our allowed values. Anything weird
    gets replaced with a safe default instead of poisoning our data."""
    fb_type = data.get("type", "other")
    if fb_type not in FEEDBACK_TYPES:
        fb_type = "other"

    sentiment = data.get("sentiment", "neutral")
    if sentiment not in VALID_SENTIMENTS:
        sentiment = "neutral"

    severity = _to_int(data.get("severity"), default=2)
    severity = max(1, min(4, severity))            # clamp into 1..4

    confidence = _to_float(data.get("confidence"), default=0.5)
    confidence = max(0.0, min(1.0, confidence))    # clamp into 0.0..1.0

    return {
        "type": fb_type,
        "area": str(data.get("area", "unknown"))[:50],
        "sentiment": sentiment,
        "severity": severity,
        "confidence": confidence,
    }


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default                       # 4. hand back the usable dict
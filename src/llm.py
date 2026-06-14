"""The 'waiter': sends a prompt to an AI and returns its text reply.

complete(prompt, provider=None) hides which model we use. The default
provider comes from LLM_PROVIDER in .env, but a caller can OVERRIDE it —
e.g. the evaluator forces provider='gemini' so an INDEPENDENT model judges
the classifier (Llama).

Real API calls are wrapped with retry + backoff, so transient failures
(HTTP 503 overloaded, 429 rate-limit) wait and retry instead of crashing.
"""
import os

from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

load_dotenv()

DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()
PROVIDER = DEFAULT_PROVIDER  # kept for older imports


def _is_transient(exc: Exception) -> bool:
    """Retry only genuine transient SERVER errors (5xx / overload / timeout).
    Rate limits (429) are deliberately NOT retried here — the pipeline handles
    those visibly with a cooldown, instead of freezing silently."""
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (500, 502, 503, 504):
        return True
    msg = str(exc).lower()
    return any(s in msg for s in ("500", "502", "503", "504", "overloaded", "unavailable", "timeout"))



# Shared retry policy: wait 5s, 10s, 20s, 40s, 60s... up to 6 tries, then give up.
# Only retries _is_transient errors (server blips) — NOT rate limits.
_retry = retry(
    retry=retry_if_exception(_is_transient),
    wait=wait_exponential(multiplier=5, min=5, max=60),
    stop=stop_after_attempt(6),
    reraise=True,
)

def complete(prompt: str, provider: str | None = None, model: str | None = None,
             json_mode: bool = True) -> str:
    """Send `prompt` to an AI, return the raw text reply.
    provider: 'groq' | 'gemini' | 'mock'. model: optional model-id override.
    json_mode: True (default) asks Groq for strict JSON. Set False for free-form
    prose, e.g. drafting a PRD."""
    provider = (provider or DEFAULT_PROVIDER).lower()
    if provider == "groq":
        return _groq_complete(prompt, model, json_mode)
    elif provider == "gemini":
        return _gemini_complete(prompt, model)
    elif provider == "mock":
        return _mock_complete(prompt)
    else:
        raise ValueError(f"Unknown provider: {provider!r}. Use groq, gemini, or mock.")


@_retry
def _groq_complete(prompt: str, model: str | None = None, json_mode: bool = True) -> str:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    response = client.chat.completions.create(
        model=model or "llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        **kwargs,
    )
    return response.choices[0].message.content


@_retry
def _gemini_complete(prompt: str, model: str | None = None) -> str:
    from google import genai

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=model or "gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def _mock_complete(prompt: str) -> str:
    """A fake AI for offline dev. Returns valid JSON by guessing from keywords."""
    text = prompt.lower()
    if "not opening" in text or "crash" in text or "bug" in text or "laggy" in text:
        return '{"type": "bug", "area": "general", "sentiment": "negative", "severity": 3, "confidence": 0.6}'
    if "how to" in text or "how do" in text:
        return '{"type": "question", "area": "onboarding", "sentiment": "neutral", "severity": 1, "confidence": 0.6}'
    if "love" in text or "great" in text or "best" in text:
        return '{"type": "praise", "area": "general", "sentiment": "positive", "severity": 1, "confidence": 0.7}'
    return '{"type": "other", "area": "general", "sentiment": "neutral", "severity": 2, "confidence": 0.4}'
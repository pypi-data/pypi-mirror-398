# src/emotionics/lite.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .schema import LiteResult
from .errors import ProviderResponseError

VERSION = "0.1.0"

def _clamp01(x: Any) -> float:
    try:
        v = float(x)
    except Exception:
        return 0.0
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v

def analyze_lite(
    text: str,
    actor: Optional[str] = None,
    language: str = "auto",
    provider: Optional[object] = None,
    model: str = "auto",
    **kwargs: Any,
) -> Dict[str, Any]:
    if provider is None:
        res: LiteResult = {
            "mode": "lite",
            "version": VERSION,
            "trust": 0.5,
            "surprise": 0.0,
            "joy": 0.0,
            "fear": 0.0,
            "confidence": 0.5,
        }
        return res

    prompt = f"""You are Emotionics Lite.
Return ONLY valid JSON (no markdown, no code fences, no extra text).
Keys: trust, surprise, joy, fear, confidence. Values: numbers in [0,1].

Text: {text}
"""

    raw = provider.generate(prompt=prompt, model=model, **kwargs)

    # Parse JSON strictly
    try:
        data = json.loads(raw)
    except Exception as e:
        raise ProviderResponseError(
            "LLM response was not valid JSON.",
            hint="Make sure the provider returns JSON only.",
            details={"raw": raw[:4000]},
            cause=e,
        )

    if not isinstance(data, dict):
        raise ProviderResponseError(
            "LLM response JSON must be an object.",
            hint="Expected: {trust:..., surprise:..., joy:..., fear:..., confidence:...}",
            details={"type": type(data).__name__},
        )

    # Normalize and clamp
    res: LiteResult = {
        "mode": "lite",
        "version": VERSION,
        "trust": _clamp01(data.get("trust")),
        "surprise": _clamp01(data.get("surprise")),
        "joy": _clamp01(data.get("joy")),
        "fear": _clamp01(data.get("fear")),
        "confidence": _clamp01(data.get("confidence")),
    }
    return res
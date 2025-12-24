# src/emotionics/core.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional, Protocol

from .errors import EmotionicsError, NotActivatedError, InvalidModeError,  ValidationError
from .lite import analyze_lite

Mode = Literal["lite", "full"]
LLMName = Literal["openai"]  # for now

class LLMProvider(Protocol):
    def generate(self, *, prompt: str, model: str, **kwargs: Any) -> str: ...

@dataclass(frozen=True)
class EmotionicsConfig:
    provider: Optional[LLMProvider] = None
    model: str = "auto"

_DEFAULT_CONFIG: Optional[EmotionicsConfig] = None


def activate(
    *,
    provider: Optional[LLMProvider] = None,
    model: str = "auto",
    # thin wrapper options
    llm: Optional[LLMName] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """
    Activate Emotionics.

    Simple (recommended):
        emotionics.activate(llm="openai", api_key="...", model="...")

    Advanced (explicit):
        emotionics.activate(provider=MyProvider(...), model="...")
    """
    global _DEFAULT_CONFIG

    # Prevent ambiguous responsibility boundary.
    if provider is not None and (llm is not None or api_key is not None):
        raise ValidationError(
            "activate() received both 'provider' and ('llm'/'api_key').",
            hint="Use either provider=... OR llm=... + api_key=..., not both.",
            details={"has_provider": True, "has_llm": llm is not None, "has_api_key": api_key is not None},
        )

    # Factory path
    if provider is None and llm is not None:
        if llm != "openai":
            raise ValidationError(
                f"Unsupported llm: {llm!r}",
                hint="Currently supported: 'openai'",
                details={"llm": llm, "supported": ["openai"]},
            )
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise ValidationError(
                "api_key must be a non-empty string",
                hint="Pass your OpenAI API key: emotionics.activate(llm='openai', api_key='...')",
            )

        from .providers import OpenAIProvider
        provider = OpenAIProvider(
            api_key=api_key,
            base_url=kwargs.pop("base_url", None),
            organization=kwargs.pop("organization", None),
            project=kwargs.pop("project", None),
        )

        # Keep wrapper strict (to avoid silently ignored params)
        if kwargs:
            unknown = ", ".join(sorted(kwargs.keys()))
            raise ValidationError(
                f"Unknown activate() parameters for llm='openai': {unknown}",
                hint="Allowed: base_url, organization, project",
                details={"unknown": sorted(kwargs.keys()), "allowed": ["base_url", "organization", "project"]},
            )

    _DEFAULT_CONFIG = EmotionicsConfig(provider=provider, model=model)


def _require_config() -> EmotionicsConfig:
    if _DEFAULT_CONFIG is None:
        raise NotActivatedError(
            "Emotionics is not activated.",
            hint="Call emotionics.activate(llm='openai', api_key='...', model='...') first "
                 "or emotionics.activate(provider=..., model=...).",
        )
    return _DEFAULT_CONFIG


def estimate(
    text: str,
    mode: Mode = "lite",
    actor: Optional[str] = None,
    language: str = "auto",
    **kwargs: Any,
) -> Dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        raise EmotionicsError("text must be a non-empty string")

    cfg = _require_config()

    if mode == "lite":
        return analyze_lite(
            text=text,
            actor=actor,
            language=language,
            provider=cfg.provider,
            model=cfg.model,
            **kwargs,
        )

    if mode == "full":
        raise EmotionicsError("mode='full' is not available in this build")

    raise InvalidModeError(f"Unknown mode: {mode}")
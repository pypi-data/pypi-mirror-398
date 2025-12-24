# src/emotionics/errors.py
from __future__ import annotations
from typing import Any, Dict, Optional


class EmotionicsError(Exception):
    """
    Base exception for emotionics.

    - code: machine-readable error code (stable)
    - message: human-readable summary
    - hint: actionable next step
    - details: debug-friendly structured metadata
    """

    default_code: str = "EMO000"
    default_message: str = "Emotionics error"

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        hint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[BaseException] = None,
    ) -> None:
        msg = message or self.default_message
        super().__init__(msg)

        self.code: str = code or self.default_code
        self.hint: Optional[str] = hint
        self.details: Dict[str, Any] = details or {}

        # Keep native exception chaining useful
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> Dict[str, Any]:
        """Serializable form (e.g., for API responses)."""
        payload: Dict[str, Any] = {
            "error": {
                "code": self.code,
                "message": str(self.args[0]) if self.args else self.default_message,
            }
        }
        if self.hint:
            payload["error"]["hint"] = self.hint
        if self.details:
            payload["error"]["details"] = self.details
        return payload

    def __str__(self) -> str:
        base = f"[{self.code}] {self.args[0] if self.args else self.default_message}"
        if self.hint:
            return f"{base} (hint: {self.hint})"
        return base


# ---- Common / user-facing errors ----

class NotActivatedError(EmotionicsError):
    default_code = "EMO101"
    default_message = "Emotionics is not activated."

    def __init__(self, message: Optional[str] = None, **kwargs: Any) -> None:
        super().__init__(
            message or self.default_message,
            hint=kwargs.pop("hint", "Call emotionics.activate(provider=..., model=...) first."),
            **kwargs,
        )


class InvalidModeError(EmotionicsError):
    default_code = "EMO102"
    default_message = "Invalid mode."

    def __init__(self, mode: Optional[str] = None, *, allowed: Optional[list[str]] = None, **kwargs: Any) -> None:
        allowed = allowed or ["lite", "full"]
        msg = self.default_message if mode is None else f"Unknown mode: {mode}"
        super().__init__(
            msg,
            hint=kwargs.pop("hint", f"Use one of: {', '.join(allowed)}"),
            details=kwargs.pop("details", {"mode": mode, "allowed": allowed}),
            **kwargs,
        )


class ValidationError(EmotionicsError):
    default_code = "EMO201"
    default_message = "Invalid input."


class NotAvailableError(EmotionicsError):
    """Feature exists conceptually but is not available in this build/version."""
    default_code = "EMO202"
    default_message = "This feature is not available in this build."


# ---- Provider / LLM related ----

class ProviderError(EmotionicsError):
    default_code = "EMO301"
    default_message = "LLM provider error."


class ProviderAuthError(ProviderError):
    default_code = "EMO302"
    default_message = "LLM provider authentication failed."


class ProviderResponseError(ProviderError):
    default_code = "EMO303"
    default_message = "LLM provider returned an invalid response."


class ProviderRateLimitError(ProviderError):
    default_code = "EMO304"
    default_message = "LLM provider rate limit exceeded."


# ---- Internal / unexpected ----

class InternalError(EmotionicsError):
    default_code = "EMO900"
    default_message = "Internal error."
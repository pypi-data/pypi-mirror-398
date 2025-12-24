# src/emotionics/providers/openai.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..errors import ProviderError


@dataclass
class OpenAIProvider:
    api_key: str
    base_url: Optional[str] = None
    organization: Optional[str] = None
    project: Optional[str] = None

    def generate(self, *, prompt: str, model: str, **kwargs: Any) -> str:
        try:
            from openai import OpenAI  # type: ignore
        except Exception as e:
            raise ProviderError(
                "OpenAI provider requires the 'openai' package.",
                hint="Install it with: pip install openai",
                cause=e,
            )

        client_kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        if self.organization:
            client_kwargs["organization"] = self.organization
        if self.project:
            client_kwargs["project"] = self.project

        client = OpenAI(**client_kwargs)

        try:
            resp = client.responses.create(
                model=model,
                input=prompt,
                **kwargs,
            )
            return resp.output_text
        except Exception as e:
            raise ProviderError(
                "OpenAI request failed.",
                hint="Check your model name, API key, network, and OpenAI SDK version.",
                cause=e,
                details={"model": model},
            )
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .base import BaseProvider
from .local_echo import LocalEchoProvider


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    base_url: Optional[str] = None
    timeout_s: float = 60.0
    extra: Dict[str, Any] | None = None


def make_provider(cfg: ProviderConfig) -> BaseProvider:
    p = (cfg.provider or "").lower().strip()
    if p == "local_echo":
        return LocalEchoProvider()
    if p == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=cfg.api_key,
            default_model=cfg.default_model,
            base_url=cfg.base_url,
            timeout_s=cfg.timeout_s,
        )
    if p == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider(
            api_key=cfg.api_key,
            default_model=cfg.default_model,
            timeout_s=cfg.timeout_s,
        )

    raise ValueError(f"Unknown provider: {cfg.provider}")

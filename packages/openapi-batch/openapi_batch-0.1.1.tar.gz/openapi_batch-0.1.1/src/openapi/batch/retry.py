from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Optional


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_s: float = 0.5
    max_delay_s: float = 20.0
    jitter: float = 0.2
    retry_on_types: Optional[set[str]] = None

    @staticmethod
    def default() -> "RetryPolicy":
        return RetryPolicy(
            max_attempts=3,
            base_delay_s=0.5,
            max_delay_s=20.0,
            jitter=0.2,
            retry_on_types={"timeout", "rate_limit", "provider_5xx", "network"},
        )

    def should_retry(self, *, attempt: int, error_type: str, retryable: bool) -> bool:
        if attempt >= self.max_attempts:
            return False
        if not retryable:
            return False
        if self.retry_on_types is None:
            return True
        return error_type in self.retry_on_types

    def sleep(self, attempt: int) -> None:
        delay = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        jitter = delay * self.jitter * (random.random() * 2 - 1)
        time.sleep(max(0.0, delay + jitter))

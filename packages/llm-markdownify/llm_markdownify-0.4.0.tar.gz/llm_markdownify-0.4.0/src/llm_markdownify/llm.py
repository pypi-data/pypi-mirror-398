# Copyright (c) 2025 Sethu Pavan Venkata Reddy Pastula
# Licensed under the Apache License, Version 2.0. See LICENSE file for details.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from typing import List, Optional

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from .cache import get_cache
from .logging import get_logger
from .prompt_profiles import PromptProfile

# Soften LiteLLM's heavy logging/cold-storage features which can import proxy/apscheduler
# and cause shutdown-time errors on some Python versions.
os.environ.setdefault("LITELLM_LOGGING", "false")
os.environ.setdefault("LITELLM_DISABLE_COLD_STORAGE", "1")
os.environ.setdefault("LITELLM_LOG_LEVEL", "ERROR")

# Aggressively silence noisy third-party loggers
for logger_name in ("LiteLLM", "litellm", "litellm.proxy", "apscheduler"):
    try:
        _log = logging.getLogger(logger_name)
        _log.setLevel(logging.CRITICAL)
        _log.propagate = False
    except Exception:
        pass

logger = get_logger("llm_markdownify.llm")


# Rate limiter state
class RateLimiter:
    """Simple token bucket rate limiter for requests per minute."""

    def __init__(self, rpm: Optional[int] = None) -> None:
        self.rpm = rpm
        self.lock = threading.Lock()
        self.tokens = float(rpm) if rpm else float("inf")
        self.last_refill = time.monotonic()

    def acquire(self) -> None:
        """Block until a request slot is available."""
        if self.rpm is None:
            return

        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            # Refill tokens based on elapsed time
            self.tokens = min(float(self.rpm), self.tokens + elapsed * (self.rpm / 60.0))
            self.last_refill = now

            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return

            # Calculate wait time
            wait_time = (1.0 - self.tokens) / (self.rpm / 60.0)

        logger.debug("Rate limit: waiting %.2fs", wait_time)
        time.sleep(wait_time)

        with self.lock:
            self.tokens = 0.0
            self.last_refill = time.monotonic()


# Global rate limiter and retry config (configured at runtime)
_rate_limiter: Optional[RateLimiter] = None
_max_retries: int = 3
_retry_delay: float = 1.0


def configure_llm(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    rate_limit_rpm: Optional[int] = None,
) -> None:
    """Configure retry and rate limiting behavior."""
    global _rate_limiter, _max_retries, _retry_delay
    _max_retries = max_retries
    _retry_delay = retry_delay
    _rate_limiter = RateLimiter(rate_limit_rpm) if rate_limit_rpm else None
    logger.debug(
        "LLM configured: max_retries=%d, retry_delay=%.1fs, rpm=%s",
        max_retries,
        retry_delay,
        rate_limit_rpm,
    )


def _hash_content(content: str) -> str:
    """Create a short hash of content for caching."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


def _completion_with_retry(
    *, model: str, messages: list, temperature: float, max_tokens: int | None
):
    """Execute LLM completion with retry logic."""
    # Local import to allow env configuration above to take effect
    import litellm  # type: ignore
    from litellm import completion as _litellm_completion  # type: ignore

    # Drop unsupported params for strict models
    try:
        litellm.drop_params = True  # type: ignore[attr-defined]
    except Exception:
        pass

    # Apply rate limiting
    if _rate_limiter:
        _rate_limiter.acquire()

    # Build retry decorator dynamically based on config
    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(_max_retries + 1),  # +1 because first attempt isn't a retry
        wait=wait_exponential(multiplier=_retry_delay, min=_retry_delay, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _do_completion():
        kwargs = {"model": model, "messages": messages, "temperature": temperature}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return _litellm_completion(**kwargs)

    return _do_completion()


def _message_with_images(text: str, image_data_urls: List[str]) -> dict:
    """Build a message dict with text and images."""
    content = [{"type": "text", "text": text}]
    for url in image_data_urls:
        content.append({"type": "image_url", "image_url": {"url": url}})
    return {"role": "user", "content": content}


def assess_continuation(
    model: str,
    first_data_url: str,
    second_data_url: str | None,
    profile: PromptProfile,
) -> str:
    """Assess if pages should be merged (continuation detection)."""
    images = [first_data_url] + ([second_data_url] if second_data_url else [])
    messages = [
        {"role": "system", "content": profile.continuation_system},
        _message_with_images(profile.continuation_user, images),
    ]

    # Check cache
    cache = get_cache()
    prompt_hash = _hash_content(profile.continuation_system + profile.continuation_user)
    image_hashes = [_hash_content(url) for url in images]
    cached = cache.get(model, prompt_hash, image_hashes)
    if cached:
        return cached

    resp = _completion_with_retry(model=model, messages=messages, temperature=0.0, max_tokens=4)
    result = str(resp["choices"][0]["message"]["content"]).strip().upper()

    # Cache result
    cache.set(model, prompt_hash, image_hashes, result)
    return result


def generate_markdown(
    model: str,
    image_data_urls: List[str],
    profile: PromptProfile,
    temperature: float = 0.2,
    max_tokens: int = 2000,
) -> str:
    """Generate markdown from page images."""
    messages = [
        {"role": "system", "content": profile.markdown_system},
        _message_with_images(profile.markdown_user, image_data_urls),
    ]

    # Check cache
    cache = get_cache()
    prompt_hash = _hash_content(profile.markdown_system + profile.markdown_user)
    image_hashes = [_hash_content(url) for url in image_data_urls]
    cached = cache.get(model, prompt_hash, image_hashes)
    if cached:
        logger.info("Using cached markdown response")
        return cached

    resp = _completion_with_retry(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    result = str(resp["choices"][0]["message"]["content"]).strip()

    # Cache result
    cache.set(model, prompt_hash, image_hashes, result)
    return result

"""agents/client.py — Shared Anthropic client factory."""

import logging
import os
import threading

import anthropic

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None
_lock = threading.Lock()


def get_client() -> anthropic.Anthropic:
    """
    Return a module-level Anthropic client, creating it on first call.

    Thread-safe: uses a lock to prevent races during initialisation.
    """
    global _client
    if _client is None:
        with _lock:
            # Double-checked locking: another thread may have initialised
            # the client while we were waiting for the lock.
            if _client is None:
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                if not api_key:
                    raise EnvironmentError(
                        "ANTHROPIC_API_KEY environment variable is not set. "
                        "Export it before running: export ANTHROPIC_API_KEY='sk-ant-...'"
                    )
                _client = anthropic.Anthropic(api_key=api_key)
    return _client

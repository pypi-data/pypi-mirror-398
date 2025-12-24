"""
PromptGuard Python SDK

Drop-in security for AI applications.
Just change your base URL and add an API key.

Usage:
    from promptguard import PromptGuard

    pg = PromptGuard(api_key="pg_xxx")

    # Use as OpenAI drop-in replacement
    response = pg.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
"""

from promptguard.client import PromptGuard, PromptGuardAsync
from promptguard.config import Config

__version__ = "0.1.0"
__all__ = ["PromptGuard", "PromptGuardAsync", "Config"]

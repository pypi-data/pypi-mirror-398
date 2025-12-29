"""SDK client wrapper for ORQ CLI."""

from typing import Optional

from orq_ai_sdk import Orq

from orq.config import get_api_key, get_environment


def get_client(
    api_key: Optional[str] = None,
    environment: Optional[str] = None
) -> Orq:
    """Get an authenticated Orq client."""
    key = get_api_key(api_key)
    if not key:
        raise ValueError(
            "API key not found. Set it with:\n"
            "  orq config set api_key YOUR_KEY\n"
            "  or export ORQ_API_KEY=YOUR_KEY\n"
            "  or use --api-key flag"
        )

    env = get_environment(environment)
    return Orq(api_key=key, environment=env)

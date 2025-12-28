from __future__ import annotations

import secrets
import string
from typing import Final


_ID_ALPHABET: Final[str] = string.ascii_lowercase + string.digits


def generate_short_id(length: int = 6) -> str:
    """Return a cryptographically secure, url-safe short identifier.

    Microsoft Agent Framework examples prefer short identifiers for artifacts and
    workspace directories. The helper sticks to a predictable eight-character
    length unless the caller opts into a different size.
    """
    if length <= 0:
        raise ValueError("length must be positive")
    return "".join(secrets.choice(_ID_ALPHABET) for _ in range(length))


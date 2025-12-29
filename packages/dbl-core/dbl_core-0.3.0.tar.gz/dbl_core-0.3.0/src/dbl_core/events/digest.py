from __future__ import annotations

from typing import Any

from .canonical import json_dumps, digest_bytes


def digest_canonical(data: Any) -> str:
    return digest_bytes(json_dumps(data))

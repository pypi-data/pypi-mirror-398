from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping


def freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: freeze_value(v) for k, v in value.items()})
    if isinstance(value, tuple):
        return tuple(freeze_value(v) for v in value)
    if isinstance(value, list):
        return tuple(freeze_value(v) for v in value)
    if isinstance(value, set):
        return frozenset(freeze_value(v) for v in value)
    return value


def format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def canonicalize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_dt(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        items: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            items[str(key)] = canonicalize_value(value[key])
        return items
    if isinstance(value, (list, tuple)):
        return [canonicalize_value(v) for v in value]
    if isinstance(value, set):
        return sorted([canonicalize_value(v) for v in value], key=lambda k: str(k))
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"__non_serializable__": type(value).__name__}


def json_dumps(data: Any) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def digest_bytes(payload: str) -> str:
    return sha256(payload.encode("utf-8")).hexdigest()

from __future__ import annotations

import base64
import dataclasses
import datetime as dt
import json
from pathlib import Path
from typing import Any

_TYPE_KEY = "__tanu_type__"


def _default(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, dt.datetime):
        return {_TYPE_KEY: "datetime", "value": obj.isoformat()}
    if isinstance(obj, dt.date):
        return {_TYPE_KEY: "date", "value": obj.isoformat()}
    if isinstance(obj, Path):
        return {_TYPE_KEY: "path", "value": str(obj)}
    if isinstance(obj, bytes):
        return {_TYPE_KEY: "bytes", "base64": base64.b64encode(obj).decode("ascii")}
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _object_hook(obj: dict[str, Any]) -> Any:
    t = obj.get(_TYPE_KEY)
    if not t:
        return obj
    if t == "datetime":
        return dt.datetime.fromisoformat(str(obj["value"]))
    if t == "date":
        return dt.date.fromisoformat(str(obj["value"]))
    if t == "path":
        return Path(str(obj["value"]))
    if t == "bytes":
        return base64.b64decode(str(obj["base64"]))
    return obj


def encode_json(payload: Any) -> bytes:
    return json.dumps(payload, default=_default, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def decode_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_hook=_object_hook)

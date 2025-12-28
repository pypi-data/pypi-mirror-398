from __future__ import annotations

import dataclasses
import traceback as _traceback
from typing import Any

from .exceptions import RemoteErrorPayload

PROTOCOL_VERSION = 1


def build_request(method: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "v": PROTOCOL_VERSION,
        "method": method,
        "args": list(args),
        "kwargs": kwargs,
    }


def build_ok_response(result: Any) -> dict[str, Any]:
    return {"v": PROTOCOL_VERSION, "ok": True, "result": result}


def build_error_response(exc: BaseException, *, include_traceback: bool) -> dict[str, Any]:
    payload = RemoteErrorPayload(
        type=type(exc).__name__,
        message=str(exc),
        traceback=_traceback.format_exc() if include_traceback else None,
    )
    return {"v": PROTOCOL_VERSION, "ok": False, "error": dataclasses.asdict(payload)}

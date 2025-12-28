from __future__ import annotations

from dataclasses import dataclass


class TanukiError(Exception):
    pass


class TanukiTimeoutError(TanukiError):
    pass


class TanukiConnectionError(TanukiError):
    pass


@dataclass(frozen=True, slots=True)
class RemoteErrorPayload:
    type: str
    message: str
    traceback: str | None = None


class TanukiRemoteError(TanukiError):
    def __init__(self, payload: RemoteErrorPayload):
        self.payload = payload
        msg = payload.message
        if payload.traceback:
            msg = f"{msg}\n\nRemote traceback:\n{payload.traceback}"
        super().__init__(msg)

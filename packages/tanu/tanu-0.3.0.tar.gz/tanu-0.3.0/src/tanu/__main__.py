from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from typing import Any

from . import RabbitMQConfig, Tanuki
from .exceptions import TanukiConnectionError, TanukiRemoteError, TanukiTimeoutError


def _build_config_from_args(args: argparse.Namespace) -> RabbitMQConfig:
    cfg = RabbitMQConfig()
    updates: dict[str, Any] = {}
    for field in ("host", "port", "virtual_host", "username", "password"):
        val = getattr(args, field, None)
        if val is not None:
            updates[field] = val
    if updates:
        cfg = dataclasses.replace(cfg, **updates)
    return cfg


def _cmd_help(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="python -m tanu help", add_help=True)
    p.add_argument("worker_name", help="worker name (e.g. device-1 or device-1@lab)")
    p.add_argument("--host", default=None)
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--virtual-host", dest="virtual_host", default=None)
    p.add_argument("--username", default=None)
    p.add_argument("--password", default=None)
    p.add_argument("--timeout", type=float, default=None)
    p.add_argument("--json", action="store_true", help="print raw JSON")
    args = p.parse_args(argv)

    cfg = _build_config_from_args(args)
    try:
        with Tanuki(args.worker_name, cfg) as cli:
            payload = cli("__tanuki_help__", timeout=args.timeout)
    except TanukiTimeoutError as e:
        print(f"timeout: {e}", file=sys.stderr)
        return 2
    except TanukiConnectionError as e:
        print(f"connection error: {e}", file=sys.stderr)
        return 3
    except TanukiRemoteError as e:
        print(f"remote error: {e}", file=sys.stderr)
        return 4

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    worker = payload.get("worker", args.worker_name)
    realm = payload.get("realm") or "local"
    queue = payload.get("queue") or "-"
    req = payload.get("request_exchange") or "-"
    rep = payload.get("reply_exchange") or "-"

    print(f"Worker: {worker} (realm={realm})")
    print(f"Queue: {queue}")
    if realm != "local":
        print(f"Request exchange: {req}")
        print(f"Reply exchange: {rep}")

    cmds = payload.get("commands") or []
    if not cmds:
        print("Commands: -")
        return 0

    print("Commands:")
    for cmd in cmds:
        sig = cmd.get("signature") or cmd.get("name") or ""
        doc = cmd.get("doc")
        if doc:
            print(f"  - {sig}  # {doc}")
        else:
            print(f"  - {sig}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: python -m tanu help WORKER_NAME", file=sys.stderr)
        return 2

    cmd = argv.pop(0)
    if cmd == "help":
        return _cmd_help(argv)

    print(f"unknown command: {cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


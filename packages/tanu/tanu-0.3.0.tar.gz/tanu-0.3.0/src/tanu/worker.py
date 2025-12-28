from __future__ import annotations

import logging
import time
from collections.abc import Callable
from inspect import Parameter, Signature
from typing import Any

import pika

from .config import RabbitMQConfig
from .protocol import build_error_response, build_ok_response
from .rabbitmq import connect_blocking, declare_rpc_topology, declare_worker_queue
from .utils.object_encoder_decoder import decode_json, encode_json

logger = logging.getLogger("tanu.worker")

Handler = Callable[..., Any]


class TanukiWorker:
    def __init__(
        self,
        worker_name: str,
        config: RabbitMQConfig | None = None,
        *,
        worker_id: str | None = None,
    ) -> None:
        self._worker_name = worker_name
        self._config = config or RabbitMQConfig()
        self._worker_id = worker_id or f"tanuki-worker:{worker_name}"

        _, self._realm = self._config.split_worker_name(worker_name)
        self._request_exchange = self._config.request_exchange_name(worker_name)
        self._reply_exchange = self._config.reply_exchange_name(worker_name)
        self._routing_key = self._config.request_routing_key(worker_name)

        self._handlers: dict[str, Handler] = {}
        self.register("__tanuki_help__", self._tanuki_help)

        self._connection: pika.BlockingConnection | None = None
        self._consume_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._publish_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._queue_name: str | None = None

    @property
    def config(self) -> RabbitMQConfig:
        return self._config

    @property
    def worker_name(self) -> str:
        return self._worker_name

    def handler(self, method: str) -> Callable[[Handler], Handler]:
        def _decorator(fn: Handler) -> Handler:
            self._handlers[method] = fn
            return fn

        return _decorator

    def command(self, name: str) -> Callable[[Handler], Handler]:
        return self.handler(name)

    def register(self, method: str, fn: Handler) -> None:
        self._handlers[method] = fn

    def _tanuki_help(self) -> dict[str, Any]:
        import inspect

        def _ann_to_str(ann: Any) -> str | None:
            if ann is inspect._empty:
                return None
            if isinstance(ann, type):
                return ann.__name__
            return str(ann)

        def _param_to_dict(p: Parameter) -> dict[str, Any]:
            return {
                "name": p.name,
                "kind": p.kind.name,
                "annotation": _ann_to_str(p.annotation),
                "has_default": p.default is not inspect._empty,
                "default": None if p.default is inspect._empty else repr(p.default),
            }

        commands: list[dict[str, Any]] = []
        for name, fn in sorted(self._handlers.items(), key=lambda kv: kv[0]):
            if name.startswith("__tanuki_"):
                continue
            try:
                sig: Signature = inspect.signature(fn)
                sig_str = f"{name}{sig}"
                params = [_param_to_dict(p) for p in sig.parameters.values()]
                return_ann = _ann_to_str(sig.return_annotation)
            except Exception:
                sig_str = name
                params = []
                return_ann = None

            doc = getattr(fn, "__doc__", None) or None
            if isinstance(doc, str):
                doc = doc.strip().splitlines()[0] if doc.strip() else None

            commands.append(
                {
                    "name": name,
                    "signature": sig_str,
                    "params": params,
                    "return": return_ann,
                    "doc": doc,
                }
            )

        return {
            "worker": self._worker_name,
            "realm": self._realm,
            "queue": self._config.request_queue_name(self._worker_name),
            "request_exchange": self._request_exchange,
            "reply_exchange": self._reply_exchange,
            "commands": commands,
        }

    def close(self) -> None:
        if self._consume_ch and self._consume_ch.is_open:
            try:
                self._consume_ch.close()
            except Exception:
                logger.debug("ignore close(consume_ch) error", exc_info=True)
        if self._publish_ch and self._publish_ch.is_open:
            try:
                self._publish_ch.close()
            except Exception:
                logger.debug("ignore close(publish_ch) error", exc_info=True)
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                logger.debug("ignore close(connection) error", exc_info=True)
        self._connection = None
        self._consume_ch = None
        self._publish_ch = None
        self._queue_name = None

    def stop(self) -> None:
        if self._consume_ch and self._consume_ch.is_open:
            try:
                self._consume_ch.stop_consuming()
            except Exception:
                logger.debug("ignore stop_consuming error", exc_info=True)
        self.close()

    def purge(self) -> int:
        self._ensure_connected()
        assert self._consume_ch and self._queue_name
        result = self._consume_ch.queue_purge(queue=self._queue_name)
        return int(result.method.message_count)

    def _ensure_connected(self) -> None:
        if self._connection and self._connection.is_open and self._consume_ch and self._publish_ch and self._queue_name:
            return

        self.close()

        self._connection = connect_blocking(self._config, connection_name=self._worker_id, max_retries=0)
        self._consume_ch = self._connection.channel()
        self._publish_ch = self._connection.channel()

        declare_rpc_topology(self._consume_ch, self._config, worker_name=self._worker_name)
        self._queue_name = declare_worker_queue(self._consume_ch, self._config, worker_name=self._worker_name)
        declare_rpc_topology(self._publish_ch, self._config, worker_name=self._worker_name)

        self._publish_ch.confirm_delivery()
        self._consume_ch.basic_qos(prefetch_count=self._config.prefetch_count)

    def _on_request(self, ch, method, props: pika.BasicProperties, body: bytes) -> None:  # type: ignore[no-untyped-def]
        assert self._publish_ch is not None

        try:
            req = decode_json(body)
            method_name = str(req.get("method"))
            args = req.get("args") or []
            kwargs = req.get("kwargs") or {}
            if not isinstance(args, list) or not isinstance(kwargs, dict):
                raise ValueError("invalid request payload")

            fn = self._handlers.get(method_name)
            if fn is None:
                raise KeyError(f"unknown method: {method_name}")

            result = fn(*args, **kwargs)
            resp = build_ok_response(result)
        except KeyError as e:
            logger.warning(str(e))
            resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)
        except Exception as e:
            logger.exception("handler error")
            resp = build_error_response(e, include_traceback=self._config.include_traceback_in_error)

        try:
            resp_body = encode_json(resp)
        except Exception as e:
            logger.exception("failed to serialize response")
            resp_body = encode_json(build_error_response(e, include_traceback=self._config.include_traceback_in_error))
        if props.reply_to:
            try:
                self._publish_ch.basic_publish(
                    exchange=self._reply_exchange,
                    routing_key=props.reply_to,
                    body=resp_body,
                    properties=pika.BasicProperties(
                        content_type="application/json",
                        correlation_id=props.correlation_id,
                        app_id=self._worker_id,
                        type="tanuki.response",
                    ),
                    mandatory=True,
                )
            except (pika.exceptions.UnroutableError, pika.exceptions.NackError):
                logger.warning("response unroutable (client likely gone): reply_to=%s", props.reply_to)
            except pika.exceptions.AMQPError:
                logger.exception("failed to publish response")
        else:
            logger.debug("no reply_to set; dropping response")

        try:
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.debug("ignore ack error", exc_info=True)

    def run(self, *, configure_logging: bool = True, log_level: int | str = "INFO") -> None:
        if configure_logging:
            _ensure_default_logging(log_level)

        startup_logged = False
        while True:
            try:
                self._ensure_connected()
                assert self._consume_ch and self._queue_name

                self._consume_ch.basic_consume(queue=self._queue_name, on_message_callback=self._on_request, auto_ack=False)
                if not startup_logged:
                    commands = sorted(k for k in self._handlers.keys() if not k.startswith("__tanuki_"))
                    cmd_str = ",".join(commands) if commands else "-"
                    realm = self._realm or "local"
                    if self._realm is None:
                        logger.info("TanukiWorker ready: %s (local) queue=%s cmds=%s", self._worker_name, self._queue_name, cmd_str)
                    else:
                        logger.info(
                            "TanukiWorker ready: %s (realm=%s) queue=%s req=%s rep=%s cmds=%s",
                            self._worker_name,
                            realm,
                            self._queue_name,
                            self._request_exchange,
                            self._reply_exchange,
                            cmd_str,
                        )
                    logger.debug(
                        "TanukiWorker connection: rabbitmq=%s:%s vhost=%s",
                        self._config.host,
                        self._config.port,
                        self._config.virtual_host,
                    )
                    startup_logged = True
                else:
                    logger.info("TanukiWorker reconnected: %s (realm=%s) queue=%s", self._worker_name, self._realm or "local", self._queue_name)
                self._consume_ch.start_consuming()
            except KeyboardInterrupt:
                logger.info("TanukiWorker stopping (KeyboardInterrupt)")
                break
            except pika.exceptions.AMQPError:
                logger.exception("AMQP error; reconnecting soon")
                time.sleep(1.0)
            finally:
                self.stop()

    def start(self, *, configure_logging: bool = True, log_level: int | str = "INFO") -> None:
        self.run(configure_logging=configure_logging, log_level=log_level)


def _coerce_log_level(level: int | str) -> int:
    if isinstance(level, int):
        return level
    name = level.strip().upper()
    mapping = logging.getLevelNamesMapping()
    if name not in mapping:
        raise ValueError(f"unknown log level: {level!r}")
    return int(mapping[name])


def _ensure_default_logging(level: int | str) -> None:
    target_level = _coerce_log_level(level)
    logging.getLogger("tanu").setLevel(target_level)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    logging.basicConfig(
        level=target_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Silence noisy pika internals by default (opt-in via user logging config).
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("pika.adapters.blocking_connection").setLevel(logging.WARNING)
    logging.getLogger("pika.adapters.utils.connection_workflow").setLevel(logging.CRITICAL)
    logging.getLogger("pika.adapters.utils.io_services_utils").setLevel(logging.CRITICAL)

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import pika

from .config import RabbitMQConfig
from .exceptions import RemoteErrorPayload, TanukiConnectionError, TanukiRemoteError, TanukiTimeoutError
from .protocol import build_request
from .rabbitmq import connect_blocking, declare_rpc_topology
from .utils.object_encoder_decoder import decode_json, encode_json

logger = logging.getLogger("tanu.client")


class Tanuki:
    def __init__(
        self,
        worker_name: str,
        config: RabbitMQConfig | None = None,
        *,
        client_name: str | None = None,
    ) -> None:
        self._worker_name = worker_name
        self._config = config or RabbitMQConfig()
        self._client_name = client_name or f"tanuki-client:{uuid.uuid4().hex[:8]}"

        self._request_exchange = self._config.request_exchange_name(worker_name)
        self._reply_exchange = self._config.reply_exchange_name(worker_name)
        self._routing_key = self._config.request_routing_key(worker_name)

        self._connection: pika.BlockingConnection | None = None
        self._pub_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._sub_ch: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._callback_queue: str | None = None
        self._reply_key: str | None = None

        self._pending_correlation_id: str | None = None
        self._response: dict[str, Any] | None = None

        self._ensure_connected()

    @property
    def config(self) -> RabbitMQConfig:
        return self._config

    @property
    def worker_name(self) -> str:
        return self._worker_name

    def close(self) -> None:
        if self._sub_ch and self._sub_ch.is_open:
            try:
                self._sub_ch.close()
            except Exception:
                logger.debug("ignore close(sub_ch) error", exc_info=True)
        if self._pub_ch and self._pub_ch.is_open:
            try:
                self._pub_ch.close()
            except Exception:
                logger.debug("ignore close(pub_ch) error", exc_info=True)
        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                logger.debug("ignore close(connection) error", exc_info=True)
        self._connection = None
        self._pub_ch = None
        self._sub_ch = None
        self._callback_queue = None
        self._reply_key = None

    def __enter__(self) -> "Tanuki":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def __call__(self, method: str, *args: Any, timeout: float | None = None, **kwargs: Any) -> Any:
        return self.call(method, *args, timeout=timeout, **kwargs)

    def _ensure_connected(self) -> None:
        if self._connection and self._connection.is_open and self._pub_ch and self._sub_ch:
            return

        self.close()

        self._connection = connect_blocking(self._config, connection_name=self._client_name, max_retries=3)
        self._pub_ch = self._connection.channel()
        self._sub_ch = self._connection.channel()

        declare_rpc_topology(self._pub_ch, self._config, worker_name=self._worker_name)
        self._pub_ch.confirm_delivery()

        result = self._sub_ch.queue_declare(queue="", exclusive=True, auto_delete=True)
        self._callback_queue = result.method.queue
        self._reply_key = uuid.uuid4().hex
        self._sub_ch.queue_bind(queue=self._callback_queue, exchange=self._reply_exchange, routing_key=self._reply_key)
        self._sub_ch.basic_consume(queue=self._callback_queue, on_message_callback=self._on_response, auto_ack=True)

    def _on_response(self, ch, method, props: pika.BasicProperties, body: bytes) -> None:  # type: ignore[no-untyped-def]
        if self._pending_correlation_id is None:
            return
        if props.correlation_id != self._pending_correlation_id:
            return
        try:
            self._response = decode_json(body)
        except Exception:
            logger.exception("failed to decode response body")
            self._response = {"ok": False, "error": {"type": "DecodeError", "message": "failed to decode response"}}

    def call(self, method: str, *args: Any, timeout: float | None = None, **kwargs: Any) -> Any:
        self._ensure_connected()
        assert self._connection and self._pub_ch and self._reply_key and self._callback_queue

        payload = build_request(method, args, kwargs)
        body = encode_json(payload)
        correlation_id = uuid.uuid4().hex

        self._pending_correlation_id = correlation_id
        self._response = None

        try:
            self._pub_ch.basic_publish(
                exchange=self._request_exchange,
                routing_key=self._routing_key,
                body=body,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    correlation_id=correlation_id,
                    reply_to=self._reply_key,
                    delivery_mode=2,
                    app_id=self._client_name,
                    type="tanuki.request",
                ),
                mandatory=True,
            )
        except (pika.exceptions.UnroutableError, pika.exceptions.NackError) as e:
            raise TanukiConnectionError(f"publish failed: {e}") from e
        except pika.exceptions.AMQPError as e:
            self.close()
            raise TanukiConnectionError(str(e)) from e

        timeout_s = timeout if timeout is not None else self._config.rpc_timeout
        deadline = time.monotonic() + timeout_s
        while self._response is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._pending_correlation_id = None
                raise TanukiTimeoutError(f"timeout waiting for response: {method}")
            try:
                self._connection.process_data_events(time_limit=min(1.0, remaining))
            except pika.exceptions.AMQPError as e:
                self.close()
                raise TanukiConnectionError(str(e)) from e

        self._pending_correlation_id = None
        resp = self._response
        self._response = None

        if resp.get("ok") is True:
            return resp.get("result")

        err = resp.get("error") or {}
        payload = RemoteErrorPayload(
            type=str(err.get("type") or "RemoteError"),
            message=str(err.get("message") or "remote error"),
            traceback=err.get("traceback"),
        )
        raise TanukiRemoteError(payload)

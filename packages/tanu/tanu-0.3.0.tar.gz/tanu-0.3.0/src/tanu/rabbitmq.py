from __future__ import annotations

import logging
import time
from typing import Any, Callable

import pika

from .config import RabbitMQConfig
from .exceptions import TanukiConnectionError

logger = logging.getLogger("tanu.rabbitmq")


def build_parameters(config: RabbitMQConfig, *, connection_name: str) -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(config.username, config.password)
    return pika.ConnectionParameters(
        host=config.host,
        port=config.port,
        virtual_host=config.virtual_host,
        credentials=credentials,
        heartbeat=config.heartbeat,
        blocked_connection_timeout=config.blocked_connection_timeout,
        connection_attempts=config.connection_attempts,
        retry_delay=config.retry_delay,
        socket_timeout=config.socket_timeout,
        client_properties={"connection_name": connection_name},
    )


def connect_blocking(
    config: RabbitMQConfig,
    *,
    connection_name: str,
    max_retries: int = 0,
    sleep: Callable[[float], Any] = time.sleep,
) -> pika.BlockingConnection:
    params = build_parameters(config, connection_name=connection_name)
    attempt = 0
    while True:
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError as e:
            if max_retries and attempt >= max_retries:
                raise TanukiConnectionError(str(e)) from e
            delay = min(30.0, 0.5 * (2**attempt))
            logger.warning("RabbitMQ connection failed: %s (retry in %.1fs)", e, delay)
            sleep(delay)
            attempt += 1


def declare_rpc_topology(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    config: RabbitMQConfig,
    *,
    worker_name: str | None,
) -> str | None:
    if worker_name is None:
        raise ValueError("worker_name is required")

    request_exchange = config.request_exchange_name(worker_name)
    reply_exchange = config.reply_exchange_name(worker_name)

    channel.exchange_declare(
        exchange=request_exchange,
        exchange_type=config.request_exchange_type(worker_name),
        durable=True,
    )
    channel.exchange_declare(
        exchange=reply_exchange,
        exchange_type=config.reply_exchange_type_for(worker_name),
        durable=True,
    )

    return None


def declare_worker_queue(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    config: RabbitMQConfig,
    *,
    worker_name: str,
) -> str:
    request_exchange = config.request_exchange_name(worker_name)
    routing_key = config.request_routing_key(worker_name)

    queue_name = config.request_queue_name(worker_name)
    arguments: dict[str, Any] = {}
    if config.queue_type == "quorum":
        arguments["x-queue-type"] = "quorum"

    channel.queue_declare(queue=queue_name, durable=True, arguments=arguments)
    channel.queue_bind(queue=queue_name, exchange=request_exchange, routing_key=routing_key)
    return queue_name

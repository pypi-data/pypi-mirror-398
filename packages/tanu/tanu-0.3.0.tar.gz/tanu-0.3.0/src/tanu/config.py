from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RabbitMQConfig:
    host: str = "127.0.0.1"
    port: int = 5672
    virtual_host: str = "/"
    username: str = "guest"
    password: str = "guest"

    heartbeat: int = 30
    blocked_connection_timeout: int = 30
    connection_attempts: int = 5
    retry_delay: float = 1.0
    socket_timeout: float = 10.0

    exchange: str = "tanuki.rpc"
    exchange_type: str = "direct"
    remote_exchange_type: str = "topic"
    request_queue_prefix: str = "tanuki.rpc"

    reply_exchange: str = "tanuki.reply"
    reply_exchange_type: str = "topic"
    remote_reply_exchange_type: str = "topic"

    rpc_timeout: float = 30.0
    prefetch_count: int = 1

    include_traceback_in_error: bool = True

    queue_type: str = "classic"  # "classic" or "quorum"

    def split_worker_name(self, worker_name: str) -> tuple[str, str | None]:
        if "@" not in worker_name:
            return worker_name, None
        name, realm = worker_name.split("@", 1)
        if not name or not realm:
            raise ValueError(f"invalid worker_name: {worker_name!r}")
        return name, realm

    def request_exchange_name(self, worker_name: str) -> str:
        _, realm = self.split_worker_name(worker_name)
        return self.exchange if realm is None else f"{self.exchange}.{realm}"

    def request_exchange_type(self, worker_name: str) -> str:
        _, realm = self.split_worker_name(worker_name)
        return self.exchange_type if realm is None else self.remote_exchange_type

    def reply_exchange_name(self, worker_name: str) -> str:
        _, realm = self.split_worker_name(worker_name)
        return self.reply_exchange if realm is None else f"{self.reply_exchange}.{realm}"

    def reply_exchange_type_for(self, worker_name: str) -> str:
        _, realm = self.split_worker_name(worker_name)
        return self.reply_exchange_type if realm is None else self.remote_reply_exchange_type

    def request_routing_key(self, worker_name: str) -> str:
        name, _ = self.split_worker_name(worker_name)
        return name

    def request_queue_name(self, worker_name: str) -> str:
        name, realm = self.split_worker_name(worker_name)
        if realm is None:
            return f"{self.request_queue_prefix}.{name}"
        return f"{self.request_queue_prefix}.{realm}.{name}"

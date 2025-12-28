from _typeshed import Incomplete
from confluent_kafka import KafkaError, Message
from typing import Any, Callable

class KafkaProducerSettings:
    bootstrap_servers: Incomplete
    max_retries: Incomplete
    retry_backoff_ms: Incomplete
    retry_backoff_max_ms: Incomplete
    delivery_timeout_ms: Incomplete
    request_timeout_ms: Incomplete
    producer_config: Incomplete
    on_delivery: Incomplete
    def __init__(self, bootstrap_servers: str, max_retries: int = 3, retry_backoff_ms: int = 100, retry_backoff_max_ms: int = 1000, delivery_timeout_ms: int = 300000, request_timeout_ms: int = 30000, on_delivery: Callable[[KafkaError | None, Message], None] | None = None, producer_config: dict[str, Any] | None = None) -> None: ...

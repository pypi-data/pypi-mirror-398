from _typeshed import Incomplete

class KafkaConsumerSettings:
    bootstrap_servers: Incomplete
    consumer_group: Incomplete
    topic_name: Incomplete
    num_consumers: Incomplete
    max_poll_interval_ms: Incomplete
    auto_offset_reset: Incomplete
    def __init__(self, bootstrap_servers: str, consumer_group: str, topic_name: str, num_consumers: int = 1, max_poll_interval_ms: int = 300000, auto_offset_reset: str = 'earliest') -> None: ...

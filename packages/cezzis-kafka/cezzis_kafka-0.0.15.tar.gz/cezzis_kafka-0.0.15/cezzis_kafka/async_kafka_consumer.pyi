from _typeshed import Incomplete
from cezzis_kafka.iasync_kafka_message_processor import IAsyncKafkaMessageProcessor as IAsyncKafkaMessageProcessor
from cezzis_kafka.kafka_consumer_settings import KafkaConsumerSettings as KafkaConsumerSettings
from typing import TypeVar

logger: Incomplete
TAsyncProcessor = TypeVar('TAsyncProcessor', bound=IAsyncKafkaMessageProcessor)

async def start_consumer_async(processor: IAsyncKafkaMessageProcessor) -> None: ...
async def spawn_consumers_async(factory_type: type[TAsyncProcessor], num_consumers: int, bootstrap_servers: str, consumer_group: str, topic_name: str, max_poll_interval_ms: int = 300000, auto_offset_reset: str = 'earliest') -> None: ...
def shutdown_consumers() -> None: ...

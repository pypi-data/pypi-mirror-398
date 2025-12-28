from _typeshed import Incomplete
from cezzis_kafka.ikafka_message_processor import IKafkaMessageProcessor as IKafkaMessageProcessor
from cezzis_kafka.kafka_consumer_settings import KafkaConsumerSettings as KafkaConsumerSettings
from multiprocessing.synchronize import Event as EventType
from typing import TypeVar

logger: Incomplete

def start_consumer(stop_event: EventType, processor: IKafkaMessageProcessor) -> None: ...
TProcessor = TypeVar('TProcessor', bound=IKafkaMessageProcessor)

def spawn_consumers(factory_type: type[TProcessor], num_consumers: int, stop_event: EventType, bootstrap_servers: str, consumer_group: str, topic_name: str) -> None: ...

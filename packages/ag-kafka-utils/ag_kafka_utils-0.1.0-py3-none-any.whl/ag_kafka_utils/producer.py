from kafka import KafkaProducer
import orjson
from typing import ClassVar
from ag_kafka_utils.base import BaseKafka


class Producer(BaseKafka):
    producer_: ClassVar[KafkaProducer | None] = None
    address: str
    client_id: str

    @property
    def producer(self):
        if self.producer_ is None:
            Producer.producer_ = KafkaProducer(
                bootstrap_servers=self.address,
                client_id=self.client_id,
                value_serializer=lambda v: orjson.dumps(v),
                **self.con_kw
            )
        return self.producer_

    def produce(self, topic: str, data: dict, **kw):
        return self.producer.send(topic, data, **kw)

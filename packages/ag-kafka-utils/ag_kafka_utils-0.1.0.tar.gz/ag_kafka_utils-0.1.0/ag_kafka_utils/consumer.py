from threading import Event
import logging
from pydantic import Field
from ag_kafka_utils.base import BaseKafka
from kafka import KafkaConsumer
import orjson
from typing import Literal


def value_deserializer(value):
    try:
        return orjson.loads(value)
    except Exception as e:
        logging.info(e)
        return dict()


class BaseKafkaConsumerConnection(BaseKafka):
    topic: str
    address: str
    group_id: str
    client_id: str
    auto_commit: bool = True
    auto_offset_reset_policy: Literal["earliest", "latest"] = "earliest"
    auto_commit_interval: float = 3
    retry_backoff_ms: int = 300
    reconnect_backoff_ms: int = 100


class Consumer(BaseKafkaConsumerConnection):
    consumer_: KafkaConsumer | None = Field(None, init=False, init_var=False)

    @property
    def consumer(self):
        if self.consumer_ is None:
            self.consumer_ = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.address,
                client_id=self.client_id,
                group_id=self.group_id,
                auto_offset_reset=self.auto_offset_reset_policy,
                value_deserializer=value_deserializer,
                enable_auto_commit=self.auto_commit,
                auto_commit_interval_ms=self.auto_commit_interval * 1000,
                retry_backoff_ms=self.retry_backoff_ms,
                reconnect_backoff_ms=self.reconnect_backoff_ms,
                **self.con_kw,
            )
        return self.consumer_

    def safe_poll(self, timeout, max_records=5):
        try:
            return self.consumer.poll(timeout, max_records=max_records)
        except Exception as e:
            logging.info(e)
            logging.info("kafka consumer poll renew...")
            try:
                self.consumer.close()
            except:
                pass
            self.consumer_ = None
            return self.safe_poll(timeout, max_records)


class BaseKafkaWorker(Consumer):
    auto_commit: bool = False

    async def handler(self, item: dict): ...

    async def job(self, shared_event: Event):
        for item in self.consumer:
            if shared_event.is_set():
                logging.info("shutdown signal received")
                return
            try:
                await self.handler(item.value)
                self.consumer.commit()
            except Exception as e:
                logging.info(e)
                logging.info("BaseKafkaWorker error")

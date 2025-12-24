from unittest import TestCase
from ag_kafka_utils.producer import Producer
from ag_kafka_utils.consumer import Consumer
from ag_kafka_utils.admin import Admin


class Test(TestCase):
    def setUp(self):
        Admin(address="kafka:9092").create_topic_ifnot_exists(["test_test"]).close()
        self.producer = Producer(address="kafka:9092", client_id="test_producer")
        self.consumer = Consumer(
            address="kafka:9092",
            client_id="test_consumer",
            group_id="consumers",
            topic="test_test",
        )

    def test_producer(self):
        self.producer.produce("test_test", {"name": "test"})

    def test_consumer(self):
        p = self.consumer.safe_poll(1_000)
        self.assertIsNotNone(p)

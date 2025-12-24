from kafka import KafkaAdminClient
from kafka.admin import NewTopic
from pydantic import Field
from ag_kafka_utils.base import BaseKafka


class Admin(BaseKafka):
    admin_: KafkaAdminClient | None = Field(None, init=False, init_var=False)
    address: str

    @property
    def admin(self):
        if self.admin_ is None:
            self.admin_ = KafkaAdminClient(
                bootstrap_servers=self.address, **self.con_kw
            )
        return self.admin_

    def create_topic_ifnot_exists(self, topics: list[str]):
        existed_topics = self.admin.list_topics()
        for topic in topics:
            if topic not in existed_topics:
                self.admin.create_topics(
                    [
                        NewTopic(
                            name=topic,
                            num_partitions=3,
                            replication_factor=1
                        )
                    ]
                )
        return self

    def close(self):
        self.admin.close()

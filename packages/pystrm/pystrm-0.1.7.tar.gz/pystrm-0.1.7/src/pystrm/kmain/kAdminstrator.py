import logging
from attrs import define
from confluent_kafka.admin import AdminClient, NewTopic
from pystrm.utils.constants import KAFKA_BROKERS

logger = logging.getLogger(__name__)


@define(kw_only=True)
class KAdmin:
    admin = AdminClient(KAFKA_BROKERS)

    def topic_exists(self, topic: str) -> bool:
        try:
            all_topics = self.admin.list_topics()
        except Exception as err:
            logger.error(f"Failed to fetch list of topics. Error : {str(err)}")
        return topic in all_topics.topics.keys()
    
    
    def create_topic(self, topic: str, num_part: int = 1, replica: int = 1) -> None:
        if not self.topic_exists(topic):
            new_topic = [NewTopic(topic, num_partitions=num_part, replication_factor=replica)]
            try:
                self.admin.create_topics(new_topic)
                logger.info(f"Topic {topic} has been created")
            except Exception as err:
                logger.error(f"Failed to create topic: {topic}. Error : {str(err)}")
        else:
            logger.warning(f"Topic {topic} already exists")

    
    def delete_topic(self, topics: list[str]) -> None:
        for topic in topics:
            if not self.topic_exists(topic):
                try:
                    self.admin.delete_topics([topic])
                    logger.warning(f"'{topic}' topic deleted")
                except Exception as err:
                    logger.error(f"Failed to delete topic: {topic}. Error : {str(err)}")
            else:
                logger.info(f"Topic name {topic} does not exists")
import logging
from attrs import define, field
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.error import SchemaRegistryError
from pystrm.utils.constants import KAFKA_SCHEMA_CLIENT

logger = logging.getLogger(__name__)


@define(kw_only=True)
class KSR:
    topic: str = field(eq=str)
    schema_str: str = field(eq=str)
    schema_type: str = field(eq=str, default="AVRO")
    schema_client = SchemaRegistryClient(KAFKA_SCHEMA_CLIENT)
    

    def get_schema_version(self):
        try:
            schema_version = self.schema_client.get_latest_version(self.topic)
            logger.info(f"{self.topic} schema does exists.")
            return schema_version.schema_id
        except SchemaRegistryError as err:
            logger.warning("Schema does not exists : " + str(err))
            return False
    
    
    def get_schema_str(self):
        try:
            schema_id = self.get_schema_version()
            schema = self.schema_client.get_schema(schema_id)
            return schema.schema_str
        except SchemaRegistryError as err:
            logger.warning(f"Some error occured while fetching schema_id '{schema_id}': " + str(err))


    def register_schema(self):
        if not self.get_schema_version():
            try:
                schema = Schema(self.schema_str, self.schema_type)
                self.schema_client.register_schema(self.topic, schema)
                logger.info("Schema Registered")
            except SchemaRegistryError as err:
                logger.warning("Schema registry failed. Error: " + str(err))
        else:
            logger.warning(f"{self.topic} already registered")
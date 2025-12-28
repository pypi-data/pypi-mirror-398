import logging
from functools import lru_cache
from attrs import define, field
from json import dumps
from uuid import uuid4
from jsonschema import validate as jsonValidate, ValidationError as jsonValidationError
from fastavro import validate as avroValidate
from fastavro.validation import ValidationError as avroValidationError

from confluent_kafka import Producer
from confluent_kafka.serialization import (
    IntegerSerializer,
    StringSerializer,
    SerializationContext,
    MessageField,
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from numpy import int64

from pystrm.utils.constants import KAFKA_BROKERS, KAFKA_SCHEMA_CLIENT
from pystrm.utils.logger.logDecor import logtimer

logger = logging.getLogger(__name__)

@lru_cache
def get_producer():
    return Producer(KAFKA_BROKERS)


@lru_cache
def get_ksr():
    return SchemaRegistryClient(KAFKA_SCHEMA_CLIENT)


@define(kw_only=True)
class Kprod:
    topic: str = field(eq=str)


    @logtimer
    def acked(self, err, msg) -> None:
        if err is not None:
            logger.error("Failed to deliv" \
            "er message: %s: %s" % (str(msg), str(err)))
        else:
            logger.info("Message produced: %s" % (str(msg)))

        return None


    @logtimer
    def prodDataWithJsonSerial(self, data: str, mykey: int | str | None) -> None:
        
        producer = get_producer()

        try:
            producer.produce(self.topic, key=mykey, value=dumps(data).encode(), on_delivery=self.acked)

            producer.flush()
        except Exception as err:
            logger.error(f"Error sending message: {str(err)}")
            return None


    @logtimer
    def prodDataWithSerialSchema(self, schema, data: dict[str, int64 | str], mykey: int | str, schema_type: str = "JSON") -> None:

        producer = get_producer()
        schema_client = get_ksr()

        try:
            jsonValidate(data, schema) if schema_type == "JSON" else avroValidate(data, schema)
            logger.info("Schema Validated")

            key_serializer = IntegerSerializer() if isinstance(mykey, int) else StringSerializer()
            value_serializer = JSONSerializer(dumps(schema), schema_client) if schema_type == "JSON" else AvroSerializer(schema_client, dumps(schema))

            producer.produce(
                topic=self.topic,
                key=key_serializer(mykey),
                value=value_serializer(data, SerializationContext(self.topic, MessageField.VALUE)),
                headers={"correlation_id": key_serializer(str(uuid4()))},
                on_delivery=self.acked
            )
            
            producer.flush()
        except jsonValidationError as err:
            logger.error(f"Json Validation Error: {str(err)}")
            return None
        except avroValidationError as err:
            logger.error(f"Avro Validation Error: {str(err)}")
            return None
        except Exception as err:
            logger.error(f"Error sending message: {str(err)}")
            return None


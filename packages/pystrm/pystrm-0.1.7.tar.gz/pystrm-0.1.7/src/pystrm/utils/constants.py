from typing import Final
from datetime import datetime
from pystrm.utils.confs import fetch_conf
from socket import gethostname
from xxhash import xxh32_intdigest


RUN_ID: Final[int] = int(datetime.now().strftime('%Y%m%d')  + str(xxh32_intdigest("pystream" + datetime.now().strftime('%H:%M:%S.%f'))))

CURRENT_DATE: Final[str] = datetime.today().strftime('%Y-%m-%d')

KAFKA_BROKERS: Final[dict[str, str]] = fetch_conf()['Kafka']['kafka-broker-conf'] | {'client.id': gethostname()}

KAFKA_SCHEMA_CLIENT: Final[dict[str, str]] = fetch_conf()['Kafka']['kafka-schema-client-conf']


__all__ = ('CURRENT_DATE', 'KAFKA_BROKERS', 'KAFKA_SCHEMA_CLIENT')
from json import dumps
from pystrm.kmain.kAdminstrator import KAdmin
from pystrm.kmain.kSchemaRegistry import KSR
from pystrm.utils.confs import get_clientSchema


def createKtopic(topic: str, num_part: int = 1, replica: int = 1) -> None:

    adm = KAdmin()
    adm.create_topic(topic=topic, num_part=num_part, replica=replica)   

    return None


def registerClientSchema(topic: str, schema_type: str) -> None:

    schema_str = get_clientSchema(topic, schema_type=schema_type)
    schema_register = KSR(topic=topic, schema_str=dumps(schema_str), schema_type=schema_type)
    schema_register.register_schema()

    return None

def to_dict(obj: object, ctx):
    return dict(vars(obj))
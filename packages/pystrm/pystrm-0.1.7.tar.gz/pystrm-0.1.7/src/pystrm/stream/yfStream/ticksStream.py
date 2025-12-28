import logging
import asyncio
from operator import itemgetter
from multiprocessing import Pool
from time import sleep
from typing import Any
import os

from numpy import int64

from pystrm.kmain.kProducer import Kprod
# from pystrm.schema.yfSchema.ticksSchemaObj import fastInfoSchemaObject

from pystrm.utils.confs import fetch_conf, get_clientSchema, streamConf
from pystrm.utils.kUtils import createKtopic, registerClientSchema
from pystrm.utils.logger.logDecor import logtimer, inOutLog


import appdirs as ad
ad.user_cache_dir = lambda *args: "/tmp"
import yfinance as yf  # noqa: E402

logger = logging.getLogger(__name__)


def dataDupCheck(data_dct: dict[str, Any], typ: str, data: dict[str, int64 | str], symb: str) -> bool:
    
    if (typ + "." + symb) in data_dct.keys():
        if data_dct[typ + "." + symb] == data:
            return False
        else:
            data_dct[typ + "." + symb] = data
            return True
    else:
        data_dct[typ + "." + symb] = data
        return True


async def validSend(kobj: Kprod, typ: str, data_dct: dict[str, Any], symb: str, data: dict[str, int64 | str], schema_type: str, schema: object) -> None:
    if dataDupCheck(data_dct=data_dct, typ=typ, data=data, symb=symb):
        logger.info(f"New record found for symbol {symb}")
        kobj.prodDataWithSerialSchema(schema=schema, data=data, mykey=symb, schema_type=schema_type)
    else:
        logger.info(f"Duplicate record found for symbol {symb}")


@logtimer
async def asyncTicker(kobj: Kprod, symb: str, meth: str):
    data = yf.Ticker(symb+".NS").__getattribute__(meth)
    kobj.prodDataWithJsonSerial(data=data, mykey=symb)


@inOutLog
async def ticker(kobj: Kprod, symbol: list[str], param_dct: dict[str, Any]) -> None:
    """_summary_

    Args:
        symbol (str): symbol for which ticker data will be generated
    """
    
    indx: int = 0

    if len(symbol) == 0:
        logger.info("Symbol list is of zero size")
        return

    while True: 
        indx = indx % len(symbol)

        if indx == 0:
            sleep(1)

        try:
            await asyncTicker(kobj, symbol[indx], param_dct['prop_key'])
        except KeyboardInterrupt:
            logger.error("KeyboardInterrrupt happened")
            break
        except Exception as e:
            logger.error(str(e))
        
        if param_dct['type'] != 'Streaming':
            sleep(5)
            break
        
        indx += 1
    
    return None


@logtimer
async def asyncFastInfo(symb: str, meth: list[str]) -> object:
    data = dict(zip([item.lower() for item in meth], list(itemgetter(*meth)(yf.Ticker(symb+".NS").fast_info))))
    # dataObjt = fastInfoSchemaObject(*data)
    return data


@inOutLog
async def fastInfo(kobj: Kprod, symbol: list[str], param_dct: dict[str, Any]) -> None:
    """_summary_

    Args:
        symbol (str): symbol for which ticker data will be generated
    """

    indx: int = 0

    if len(symbol) == 0:
        logger.info("Symbol list is of zero size")
        return

    schema = get_clientSchema(param_dct['prop_key'], param_dct['schema_type'])

    dupCheck = dict()

    while True: 
        print(dupCheck)
        indx = indx % len(symbol)

        if indx == 0:
            sleep(1)

        try:  
            data = await asyncFastInfo(symbol[indx], param_dct['infolst'])
            await validSend(kobj, "fastInfo", dupCheck, symbol[indx], data, param_dct['schema_type'], schema)
        except KeyboardInterrupt:
            logger.warning("KeyboardInterrrupt happened")
        except Exception as e:
            logger.error(str(e))
        
        if param_dct['type'] != 'Streaming':
            sleep(5)
            break
        
        indx += 1

    return None


# @inOutLog
# @logtimer
# async def multiTicker(kobj: Kprod, symbol: list[str], param_dct: dict[str, Any]) -> None:
#     """_summary_

#     Args:
#         symbol (str): symbol for which ticker data will be generated

#     Returns:
#         dict[str, Any]: Fetch ticker data 
#     """

#     # schema_client = SchemaRegistryClient(KAFKA_SCHEMA_CLIENT)

#     indx: int = 0

#     if len(symbol) == 0:
#         logger.info("Symbol list is of zero size")
#         return

#     while True: 
#         indx = indx % len(symbol)
#         try:
#             data = await asyncFastInfo(symbol[indx],  param_dct['infolst'])
#             await kobj.prodDataWithAvroSerialSchema(value=data, key=symbol[indx])
#             sleep(1)
#         except KeyboardInterrupt:
#             logger.warning("KeyboardInterrrupt happened")
#             break
#         except Exception as e:
#             logger.error(str(e))
        
#         if param_dct['type'] != 'Streaming':
#             sleep(5)
#             break
        
#         indx += 1
#     return None


@inOutLog
@logtimer
def procHandler(param_dct: dict[str, Any], symb: list[str]) -> None:
    """Fetch data from Yahoo Finance till market close in multiprocess and concurrrent waiting manner

    Args:
        param_dct (dict[str, str]): Parameter dictionary for execution
        symb (list[str]): List of stock symbols for fetch data
    """
    

    kobj = Kprod(topic=param_dct['prop_key'])

    __EXECUTE_METHOD = {
        "tick": ticker
        # ,"multitick": multiTicker
        ,"fastinfo": fastInfo
    }

    asyncio.run(__EXECUTE_METHOD[param_dct['ldt']](kobj, symb, param_dct))
    return None


def process_status(err):
    if err is not None:
        logger.error("Failed process: %s" % (str(err)))
    else:
        logger.info("Process Success")
        

@inOutLog
def getStreamData(key: str) -> None:
    """Generate data from Jugaad package

    Args:
        key (str): Take config key as input
    """

    num_proc, num_process, symbols, prop_dict = streamConf(key)

    createKtopic(topic=prop_dict['prop_key'], num_part=9, replica=3)

    if 'schema_type' in prop_dict.keys():
        registerClientSchema(topic=prop_dict['prop_key'], schema_type=prop_dict['schema_type'])

    try:
        pool = Pool(processes=os.cpu_count())

        input_list = list()
        for i in range(1, num_proc+1):
            if i == num_proc:
                input_list.append((prop_dict, symbols[(i - 1)*num_process:]))
            else:
                input_list.append((prop_dict, symbols[(i-1)*num_process:i*num_process]))
            
        ar = pool.starmap_async(procHandler, input_list, error_callback=process_status)
        ar.wait(timeout=fetch_conf()['Market']['LiveTime'])
        if ar.ready():
            logger.info("All task finished")
        else:
            logger.error("Some task still running")
            pool.terminate()
            return None
    except KeyboardInterrupt as e:
        logger.warning("Keyboard Interrupt : " + str(e))
        pool.terminate()
        return None
    except Exception as e:
        logger.error(str(e))
        pool.terminate()
        return None

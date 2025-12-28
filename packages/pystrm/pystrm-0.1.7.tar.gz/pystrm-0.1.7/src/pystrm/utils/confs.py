from typing import Any
from yaml import safe_load
from fastavro.schema import load_schema
import json
import os

current_directory = os.getcwd()
#import requests
#from utils import BASE_URL, HEADERS, NIFTY50


def fetch_prop() -> dict[str, Any]:

    with open(current_directory + '/tables.yaml', 'r') as tblinfo:
        prop_dict = safe_load(tblinfo.read())

    return prop_dict


def fetch_conf() -> dict[str, Any]:

    with open(current_directory + '/config.yaml', 'r') as cfginfo:
        conf_dict = safe_load(cfginfo.read())

    return conf_dict


def param_init(key: str) -> Any:

    conf_key = key.split('.')[0]
    prop_key = key.split('.')[1]
    conf_dict = fetch_conf()[conf_key]
    prop_dict = fetch_prop()[conf_key][prop_key]

    return conf_key, prop_key, conf_dict, prop_dict


def fetch_db_dtl(db_type: str) -> dict[str, str | int]:
    db_dtl = fetch_conf()[db_type]
    return db_dtl


def get_clientSchema(fl_nm: str, schema_type: str):

    path = fetch_conf()["Kafka"]["schema"][schema_type.lower()]

    if schema_type == "JSON":
        fl_nm += ".json"
        with open(current_directory + path + fl_nm) as fl:
            schema = json.load(fl)
    else:
        fl_nm += ".avsc"
        schema = load_schema(current_directory + path + fl_nm)

    return schema

def streamConf(key: str) -> tuple[int, int, list[str], dict[str, Any]]:

    conf_key, prop_key, conf_dict, prop_dict = param_init(key)
    symbols: list[str] = fetch_conf()['Market']['Symbols'] 
    
    prop_dict['prop_key'] = prop_key.lower()

    num_proc: int = int(conf_dict['num_process'])

    num_process: int = len(symbols)//num_proc

    if len(symbols) % num_proc == 0:
        num_proc = num_proc
    else:
        num_proc = num_proc + 1
    
    return (num_proc, num_process, symbols, prop_dict)

'''@logtimer
@staticmethod
def niftySymbols(url: str) -> list[str]:
    
    session = requests.Session()
    r = session.get(BASE_URL, headers=HEADERS, timeout=5)
    cookies = dict(r.cookies)
    
    response = session.get(url, timeout=5, headers=HEADERS, cookies=cookies)
    content = response.content.decode('utf-8')

    columns=['Company Name', 'Industry', 'Symbol', 'Series', 'ISIN Code']
    data_lst = [x.strip().split(',') for x in content.splitlines() if x.strip().split(',') != columns]              

    df=pd.DataFrame(data_lst, columns=columns)
    symbols_lst = df['Symbol'].tolist()
    
    return symbols_lst'''
    

#print(niftySymbols(NIFTY50))
#print(param_init('JugaadData.PriceInfo'))
#print(fetch_conf())
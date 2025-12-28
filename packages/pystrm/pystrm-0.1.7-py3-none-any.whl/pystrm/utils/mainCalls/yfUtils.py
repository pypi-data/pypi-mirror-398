from pystrm.stream.yfStream.ticksStream import getStreamData
from pystrm.utils.logger.logDecor import inOutLog

@inOutLog
@staticmethod
def getLiveTickData(key: str) -> None:
    """_summary_

    Args:
        key (str): Fetch live quote data from package yfinance and push it to kafka producer. 
    """

    getStreamData(key=key)
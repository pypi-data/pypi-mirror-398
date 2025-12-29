from typing import Union
from qe.lib.trading_enums import TradingPairMarketType


def trading_pairs(self, **kwargs):
    """Get trading pairs list (PUBLIC)
    
    Get list of trading pairs
    
    GET /pub/trading-pairs
    
    Keyword Args:
        page (int, optional): Page number for pagination
        pageSize (int, optional): Number of items per page
        exchange (str, optional): Exchange name filter
        marketType (TradingPairMarketType | str, optional): Market type filter
        isCoin (bool, optional): Coin filter
    """
    # 处理枚举类型参数
    if 'marketType' in kwargs and isinstance(kwargs['marketType'], TradingPairMarketType):
        kwargs['marketType'] = kwargs['marketType'].value
    
    url_path = "/pub/trading-pairs"
    return self.query(url_path, {**kwargs})

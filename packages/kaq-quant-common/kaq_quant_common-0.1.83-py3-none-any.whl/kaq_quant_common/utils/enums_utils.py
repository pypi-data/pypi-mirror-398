from enum import Enum

class KaqCommsionRateRedisPrefixEnum(Enum):
    binance_future = 'kaq_binance_futures_commission_rate'
    bybit_future = 'kaq_bybit_futures_commission_rate'
    okx_future = 'kaq_okx_futures_commission_rate'
    mexc_future = 'kaq_mexc_futures_commission_rate'
    bitget_future = 'kaq_bitget_futures_commission_rate'
    gate_future = 'kaq_gate_futures_commission_rate'
    htx_future = 'kaq_gate_futures_commission_rate'
    
    binance_spot = 'kaq_binance_spot_commsion_rate'
    bybit_spot = 'kaq_bybit_spot_commsion_rate'
    okx_spot = 'kaq_okx_spot_commsion_rate'
    bitget_spot = 'kaq_bitget_spot_commsion_rate'
    gate_spot = 'kaq_gate_spot_commsion_rate'
    mexc_future_spot = 'kaq_mexc_spot_commsion_rate'
    htx_spot = 'kaq_htx_spot_commsion_rate'
    
class KaqSpotInterestRateRedisPrefixEnum(Enum):
    
    binance_spot = 'kaq_binance_spot_interest_rate'
    bybit_spot = 'kaq_bybit_spot_interest_rate'
    okx_spot = 'kaq_okx_spot_interest_rate'
    bitget_spot = 'kaq_bitget_spot_interest_rate'
    gate_spot = 'kaq_gate_spot_interest_rate'
    htx_spot = 'kaq_htx_spot_interest_rate'
    mexc_spot = 'kaq_mexc_spot_interest_rate'

class KaqCoinDataEnum(Enum):
    '''
    枚举检测
    '''
    klines = 'klines' # klines
    global_long_short_account_ratio = 'global_long_short_account_ratio' # 多空持仓人数比
    open_interest_hist = 'open_interest_hist' # 合约持仓量历史
    taker_long_short_ratio = 'taker_long_short_ratio' # 合约主动买卖量
    top_long_short_account_ratio = 'top_long_short_account_ratio' # 大户账户数多空比
    top_long_short_position_ratio = 'top_long_short_position_ratio' # 大户持仓量多空比
    
    
class KaqHighCirculationSymbolsEnum(Enum):
    '''
    高流通量的交易对列表: 由大到小排列
    '''
    symbols = 'Kaq_high_circulation_symbols' 
    
    
class KaqPriceAndVolumeSymbolsEnum(Enum):
    '''
    量价更新订阅
    '''
    symbols = 'kaq_all_futures_limit_order_symbols_config' 
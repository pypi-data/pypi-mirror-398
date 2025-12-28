import json

from kaq_quant_common.common.redis_table_monitor import RedisTableMonitor
from kaq_quant_common.utils import yml_utils


# 订单簿交易对监听器
class LimitOrderSymbolMonitor(RedisTableMonitor):
    def __init__(self, exchange: str, handler: callable = None, default_symbols=["BTCUSDT", "ETHUSDT"]):
        #
        self._exchange = exchange
        # 回调
        self._handler = handler
        #
        self._support_symbols = default_symbols
        # 记录一下之前的字符串
        self._str_value = None

        # 间隔1秒
        super().__init__(table_name="kaq_all_futures_limit_order_symbols_config", interval=1)

        # 输出一下支持的交易对
        # self._logger.info(f"init {self._exchange} limit order support symbols: {self._support_symbols}")

    def _on_get_redis_config(self):
        # 获取redis配置
        host, port, passwd = yml_utils.get(f"kaq_{self._exchange}_quant", "redis", ["host", "port", "passwd"])
        return {"host": host, "port": int(port), "passwd": passwd}

    def _do_query(self) -> str:
        # 获取字符串
        str = super()._do_query()
        try:
            # 解析为json
            json_obj = json.loads(str)
            # 只要平台的值
            symbols = json_obj.get(self._exchange, self._support_symbols)

            #
            tmp_symbols = []
            tmp_symbols.extend(symbols)

            if self._support_symbols is not None and len(self._support_symbols) > 0: 
                # !! 注意，这里需要过滤一下，只保留支持的交易对
                tmp_symbols = [symbol for symbol in symbols if symbol in self._support_symbols]
            # df_symbols = pd.Series(symbols)
            # df_symbols = df_symbols[df_symbols.isin(self._support_symbols)]
            # symbols = df_symbols.tolist()
            if tmp_symbols != symbols and self._str_value != str:
                # 输出一下日志
                self._logger.warning(f"{self._exchange} limit order symbols contain unsupported symbols, before: {symbols} filtered: {tmp_symbols}")

            symbols = tmp_symbols
        except Exception as e:
            symbols = self._support_symbols

        self._str_value = str

        return symbols

    def _do_compare(self, value1: list[str], value2: list[str]) -> bool:
        # 判断数组是否一样，数组也是这样判断也可以
        return value1 == value2

    def _on_value_change(self, value: list[str]):
        # 输出一下变化的交易对
        self._logger.info(f"{self._exchange} limit order symbols changed: {value}")
        if self._handler is not None:
            self._handler(value)

    # get, set
    def set_handler(self, handler: callable):
        self._handler = handler

    def get_symbols(self) -> list[str]:
        return self._value

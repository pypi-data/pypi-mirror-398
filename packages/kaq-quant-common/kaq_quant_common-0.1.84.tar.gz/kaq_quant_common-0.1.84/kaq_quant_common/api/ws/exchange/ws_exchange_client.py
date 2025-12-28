from typing import Callable

from kaq_quant_common.api.ws.ws_client_base import WsClientBase
from kaq_quant_common.api.ws.exchange.models import FundingRateEvent


class WsExchangeClient(WsClientBase):
    """模拟交易所 WS 客户端：资金费率订阅封装"""

    def subscribe_all(self, handler: Callable[[FundingRateEvent], None]):
        def _wrap(payload: dict):
            try:
                evt = FundingRateEvent(**payload)
                handler(evt)
            except Exception:
                # 忽略解析错误，避免阻断接收循环
                pass

        self.subscribe("funding_rate.all", _wrap)

    def subscribe_funding_rate(self, symbol: str, handler: Callable[[FundingRateEvent], None]):
        topic = f"funding_rate.{symbol}"

        def _wrap(payload: dict):
            try:
                evt = FundingRateEvent(**payload)
                handler(evt)
            except Exception:
                pass

        self.subscribe(topic, _wrap)
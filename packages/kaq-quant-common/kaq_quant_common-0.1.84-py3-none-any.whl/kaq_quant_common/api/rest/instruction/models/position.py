from enum import Enum
from typing import Optional

from pydantic import BaseModel

from . import InstructionRequestBase, InstructionResponseBase


# 持仓方向
class PositionSide(str, Enum):
    # 看多
    LONG = "long"
    # 看空
    SHORT = "short"
    # 双向
    BOTH = "both"


class PositionInfo(BaseModel):
    # 交易对
    symbol: str
    # 持仓方向
    position: PositionSide
    # 持仓数量
    amount: float
    # 开仓价格
    open_price: float
    # 标记价格
    mark_price: float
    # 强平价格
    liquidation_price: float
    # 未实现盈亏
    unrealized_pnl: float
    # 初始保证金
    initial_margin: float
    # 维持保证金
    maintain_margin: float
    # 仓位初始保证金
    position_initial_margin: float
    # 订单初始保证金
    order_initial_margin: float
    # 更新时间
    update_time: int


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 持仓


class QueryPositionRequest(InstructionRequestBase):
    # 交易对
    symbol: Optional[str] = None


class QueryPositionResponse(InstructionResponseBase):
    #
    positions: list[PositionInfo]

from typing import Optional

from pydantic import BaseModel


class FundingRateEvent(BaseModel):
    # 使用毫秒时间戳，保持与现有事件风格一致
    event_time: int
    exchange_symbol: Optional[str] = None
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    open_rate: Optional[float] = None
    close_rate: Optional[float] = None
    high_rate: Optional[float] = None
    low_rate: Optional[float] = None
    # 毫秒时间戳
    close_time: Optional[int] = None
    # 毫秒时间戳
    next_event_time: Optional[int] = None

    # 兼容表中其他字段
    id: Optional[str] = None
    ctimestamp: Optional[str] = None

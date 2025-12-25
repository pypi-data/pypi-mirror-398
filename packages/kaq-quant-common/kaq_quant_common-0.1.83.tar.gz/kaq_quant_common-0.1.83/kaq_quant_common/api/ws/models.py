from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


# ws 消息类型
class WsMessageType(str, Enum):
    # 请求，对应RESPONSE
    REQUEST = "request"
    # 响应，对应REQUEST
    RESPONSE = "response"
    # 推送
    PUSH = "push"
    # 心跳
    PING = "ping"
    PONG = "pong"
    # 订阅
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    #
    ACK = "ack"


class WsError(BaseModel):
    code: int
    message: str
    details: Optional[Dict[str, Any]] = None


class WsEnvelope(BaseModel):
    # 请求的类型
    type: WsMessageType
    # 请求/响应相关
    req_id: Optional[str] = None
    method: Optional[str] = None
    # 推送相关
    topic: Optional[str] = None
    # 负载
    payload: Optional[Dict[str, Any]] = None
    # 错误
    error: Optional[WsError] = None

    def model_dump_json(self) -> str:
        # 简单包装，确保枚举序列化为字符串
        return super().model_dump_json()

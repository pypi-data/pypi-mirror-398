from enum import Enum

from . import InstructionRequestBase, InstructionResponseBase

# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 划转


# 划转类型
class TransferType(int, Enum):
    # 资金&现货
    FUNDING_SPOT = 1
    # 资金&合约
    FUNDING_FUTURES = 2
    # 合约&现货
    SPOT_FUTURES = 3


# 划转请求
class TransferRequest(InstructionRequestBase):
    # 划转类型
    type: TransferType
    # 资产/币种
    assets: str
    # 划转数量
    amount: float
    # 划转方向 1正向，2反向
    direction: int


# 划转响应
class TransferResponse(InstructionResponseBase):
    transfer_id: str

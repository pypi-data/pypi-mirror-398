from typing import Optional

from pydantic import BaseModel

from . import InstructionRequestBase, InstructionResponseBase


# 资产信息
class AssetsInfo(BaseModel):
    # 币种
    coin: str
    # 余额
    balance: float


# ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 查询合约账户余额
class ContractBalanceRequest(InstructionRequestBase):
    # 币种
    coin: Optional[str] = None


class ContractBalanceResponse(InstructionResponseBase):
    #
    assets: list[AssetsInfo]

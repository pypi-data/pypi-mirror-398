# 定义 客户端
import time
from typing import Type, TypeVar

from kaq_quant_common.api.rest.api_client_base import ApiClientBase
from kaq_quant_common.api.rest.instruction.models import (
    InstructionRequestBase,
    InstructionResponseBase,
)
from kaq_quant_common.api.rest.instruction.models.account import (
    ContractBalanceRequest,
    ContractBalanceResponse,
)
from kaq_quant_common.api.rest.instruction.models.order import (
    AllOpenOrdersRequest,
    AllOpenOrdersResponse,
    CancelOrderRequest,
    CancelOrderResponse,
    ChangeLeverageRequest,
    ChangeLeverageResponse,
    ModifyOrderRequest,
    ModifyOrderResponse,
    OrderRequest,
    OrderResponse,
    QuerySymbolConfigRequest,
    QuerySymbolConfigResponse,
)
from kaq_quant_common.api.rest.instruction.models.position import (
    QueryPositionRequest,
    QueryPositionResponse,
)
from kaq_quant_common.api.rest.instruction.models.transfer import (
    TransferRequest,
    TransferResponse,
)
from kaq_quant_common.utils import uuid_utils

R = TypeVar("R", bound=InstructionResponseBase)


class InstructionClient(ApiClientBase):

    # 重写一下make_request处理公用字段
    def _make_request(self, method: str, request: InstructionRequestBase, response_model: Type[R]) -> R:
        # 处理公用字段
        # 时间
        if request.event_time is None:
            request.event_time = int(time.time() * 1000)
        # TODO 任务id
        if request.task_id is None:
            request.task_id = f"t_{uuid_utils.generate_uuid()}"
        return super()._make_request(method, request, response_model)

    # 下单
    def order(self, request: OrderRequest) -> OrderResponse:
        return self._make_request("order", request, OrderResponse)

    # 修改订单
    def modify_order(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        return self._make_request("modify_order", request, ModifyOrderResponse)

    # 取消订单
    def cancel_order(self, request: CancelOrderRequest) -> CancelOrderResponse:
        return self._make_request("cancel_order", request, CancelOrderResponse)

    # 查询当前全部挂单
    def all_open_orders(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        return self._make_request("all_open_orders", request, AllOpenOrdersResponse)

    # 查询交易对设置
    def query_symbol_config(self, request: QuerySymbolConfigRequest) -> QuerySymbolConfigResponse:
        return self._make_request("query_symbol_config", request, QuerySymbolConfigResponse)

    # 调整杠杆
    def change_leverage(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        return self._make_request("change_leverage", request, ChangeLeverageResponse)

    # 查询持仓
    def query_position(self, request: QueryPositionRequest) -> QueryPositionResponse:
        return self._make_request("query_position", request, QueryPositionResponse)

    # 划转
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._make_request("transfer", request, TransferResponse)

    # 查询合约账户余额
    def contract_balance(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        return self._make_request("contract_balance", request, ContractBalanceResponse)

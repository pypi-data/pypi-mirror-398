import time
from typing import Type, TypeVar

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
    ChangeMarginModeRequest,
    ChangeMarginModeResponse,
    ModifyOrderRequest,
    ModifyOrderResponse,
    OrderRequest,
    OrderResponse,
    QueryMarginModeRequest,
    QueryMarginModeResponse,
)
from kaq_quant_common.api.rest.instruction.models.transfer import (
    TransferRequest,
    TransferResponse,
)
from kaq_quant_common.api.ws.ws_client_base import WsClientBase
from kaq_quant_common.utils import uuid_utils

R = TypeVar("R", bound=InstructionResponseBase)


class WsInstructionClient(WsClientBase):

    # 统一处理公用字段并发起请求
    def _make_request(self, method: str, request: InstructionRequestBase, response_model: Type[R]) -> R:
        if request.event_time is None:
            request.event_time = int(time.time() * 1000)
        if request.task_id is None:
            request.task_id = f"t_{uuid_utils.generate_uuid()}"
        return self.send_request(method, request, response_model)

    # 下单
    def order(self, request: OrderRequest) -> OrderResponse:
        return self._make_request("order", request, OrderResponse)

    # 修改订单
    def modify_order(self, request: ModifyOrderRequest) -> ModifyOrderResponse:
        return self._make_request("modify_order", request, ModifyOrderResponse)

    # 撤销订单
    def cancel_order(self, request: CancelOrderRequest) -> CancelOrderResponse:
        return self._make_request("cancel_order", request, CancelOrderResponse)

    # 查询当前全部挂单
    def all_open_orders(self, request: AllOpenOrdersRequest) -> AllOpenOrdersResponse:
        return self._make_request("all_open_orders", request, AllOpenOrdersResponse)

    # 调整杠杆
    def change_leverage(self, request: ChangeLeverageRequest) -> ChangeLeverageResponse:
        return self._make_request("change_leverage", request, ChangeLeverageResponse)

    # 查询联合保证金模式
    def query_margin_mode(self, request: QueryMarginModeRequest) -> QueryMarginModeResponse:
        return self._make_request("query_margin_mode", request, QueryMarginModeResponse)

    # 调整联合保证金模式
    def change_margin_mode(self, request: ChangeMarginModeRequest) -> ChangeMarginModeResponse:
        return self._make_request("change_margin_mode", request, ChangeMarginModeResponse)

    # 划转
    def transfer(self, request: TransferRequest) -> TransferResponse:
        return self._make_request("transfer", request, TransferResponse)

    # 查询合约账户余额
    def contract_balance(self, request: ContractBalanceRequest) -> ContractBalanceResponse:
        return self._make_request("contract_balance", request, ContractBalanceResponse)

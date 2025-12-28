import json
import threading
import time
from typing import Callable

from kaq_quant_common.api.rest.instruction.models.order import (
    OrderInfo,
    OrderSide,
    OrderStatus,
    PositionStatus,
)
from kaq_quant_common.api.rest.instruction.models.position import PositionSide
from kaq_quant_common.utils import logger_utils, uuid_utils


class OrderHelper:
    def __init__(self, ins_server):
        # 必须放在这里 延迟引入，否则会有循环引用问题
        from kaq_quant_common.api.rest.instruction.instruction_server_base import (
            InstructionServerBase,
        )

        self._server: InstructionServerBase = ins_server
        self._logger = logger_utils.get_logger(self)

        self._mysql_table_name_order = "kaq_futures_instruction_order"
        self._mysql_table_name_position = "kaq_futures_instruction_position"
        # 当前持仓
        self._redis_key_position = "kaq_futures_instruction_position"
        # 持仓历史
        self._redis_key_position_history = "kaq_futures_instruction_position_history"

    def _write_position_open_to_redis(
        self,
        position_id: str,
        exchange: str,
        symbol: str,
        position_side,
        coin_quantity: float,
        usdt_quantity: float,
        open_ins_id: str,
        open_price: float,
        open_fee: float,
        open_fee_rate: float,
        open_time: int,
    ):
        redis = self._server._redis
        if redis is None:
            return
        data = {
            "id": position_id,
            "exchange": exchange,
            "symbol": symbol,
            "position_side": position_side.value,
            "coin_quantity": coin_quantity,
            "usdt_quantity": usdt_quantity,
            "open_ins_id": open_ins_id,
            "open_price": open_price,
            "open_fee": open_fee,
            "open_fee_rate": open_fee_rate,
            "open_time": open_time,
            "close_ins_id": None,
            "close_price": 0,
            "close_time": 0,
            "status": PositionStatus.OPEN.value,
        }
        redis.client.hset(self._redis_key_position, position_id, json.dumps(data))

    def _write_position_close_to_redis(
        self,
        position_id: str,
        exchange: str,
        symbol: str,
        position_side,
        coin_quantity: float,
        usdt_quantity: float,
        open_ins_id: str,
        open_price: float,
        open_fee: float,
        open_fee_rate: float,
        open_time: int,
        close_ins_id: str,
        close_price: float,
        close_fee: float,
        close_fee_rate: float,
        close_time: int,
    ):
        redis = self._server._redis
        if redis is None:
            return
        data = {
            "id": position_id,
            "exchange": exchange,
            "symbol": symbol,
            "position_side": position_side.value,
            "coin_quantity": coin_quantity,
            "usdt_quantity": usdt_quantity,
            "open_ins_id": open_ins_id,
            "open_price": open_price,
            "open_fee": open_fee,
            "open_fee_rate": open_fee_rate,
            "open_time": open_time,
            "close_ins_id": close_ins_id,
            "close_price": close_price,
            "close_fee": close_fee,
            "close_fee_rate": close_fee_rate,
            "close_time": close_time,
            "status": PositionStatus.CLOSE.value,
        }
        redis.client.hdel(self._redis_key_position, position_id)
        redis.client.rpush(self._redis_key_position_history, json.dumps(data))

    def process_order(self, order: OrderInfo, get_order_result: Callable):
        # 获取交易所
        exchange = self._server._exchange

        # 记录时间，统计成交耗时
        start_time = time.time()

        #
        if not self._do_process_order(exchange, order, get_order_result, True, start_time):
            # 马上执行，没有成功，开启线程执行
            thread = threading.Thread(
                target=self._do_process_order,
                args=(exchange, order, get_order_result, False, start_time),
            )
            thread.name = f"process_order_{order.instruction_id}_{exchange}_{order.symbol}_{order.order_id}"
            thread.daemon = True
            thread.start()

    def _do_process_order(
        self,
        exchange: str,
        order: OrderInfo,
        get_order_result: Callable,
        first=True,
        start_time: float = 0,
    ):
        # 获取mysql
        mysql = self._server._mysql

        #
        ins_id = order.instruction_id
        order_id = order.order_id
        symbol = order.symbol
        side = order.side
        position_side = order.position_side

        is_open = True
        side_str = "开仓"
        if position_side == PositionSide.LONG:
            # 多单是正向理解的
            if side == OrderSide.SELL:
                side_str = "平仓"
                is_open = False
            else:
                side_str = "开仓"
                is_open = True
        else:
            # 空单是反向理解的
            if side == OrderSide.SELL:
                side_str = "开仓"
                is_open = True
            else:
                side_str = "平仓"
                is_open = False

        if first:
            self._logger.info(f"{ins_id}_{exchange}_{symbol} step 1. {side_str}挂单成功 {order_id}")

            # 步骤1.挂单成功 插入到订单记录
            # 获取当前时间-ms
            current_time = int(time.time() * 1000)

            if mysql is not None:
                status = OrderStatus.CREATE
                sql = f"""
                INSERT INTO {self._mysql_table_name_order} (ins_id, exchange, symbol, side, position_side, orig_price, orig_coin_quantity, order_id, status, create_time, last_update_time) 
                VALUES ( '{ins_id}', '{exchange}', '{symbol}', '{side.value}', '{order.position_side.value}', {order.target_price}, {order.quantity}, '{order_id}', '{status.value}', {current_time}, {current_time} );
                """
                execute_ret = mysql.execute_sql(sql, True)

        # 步骤2.查询订单状态 直到订单成交后
        # 统计查询次数
        query_counter = 0
        while True:
            query_counter += 1
            # 获取订单结果
            order_info = None
            try:
                order_info = get_order_result()
            except Exception as e:
                self._logger.error(f"{ins_id}_{exchange}_{symbol} step 2. {side_str}订单 查询状态失败 {e}")

            if order_info is not None:
                break
            # 只查询一次
            if first:
                return False
            # 等待
            time.sleep(1)

        if not first:
            # 需要加上第一查询
            query_counter += 1

        # 记录时间，统计成交耗时
        end_time = time.time()
        cost_time = end_time - start_time
        self._logger.info(
            f"{ins_id}_{exchange}_{symbol} step 2. {side_str}订单  {order_id} 成交 耗时 {int(cost_time * 1000)}ms, 查询次数 {query_counter}"
        )

        # 步骤3.把最终持仓写进去
        # 平均成交价格 转float
        avg_price = float(order_info["avg_price"])
        # 最终成交数量 转float
        executed_qty = float(order_info["executed_qty"])
        # 计算出usdt数量
        executed_usdt = avg_price * executed_qty
        # 手续费,不一定有
        fee = float(order_info["fee"]) if "fee" in order_info else 0.0
        # 费率
        fee_rate = fee / executed_usdt

        current_time = int(time.time() * 1000)

        if mysql is None:
            self._logger.warning(f"{ins_id}_{exchange}_{symbol} 仅操作，没有入库，请设置 mysql!!")
            return

        status = OrderStatus.FINISH
        # 更新写入最终信息
        sql = f"""
        UPDATE {self._mysql_table_name_order} 
        SET price = {avg_price}, coin_quantity = {executed_qty}, usdt_quantity = {executed_usdt}, fee = {fee}, fee_rate = {fee_rate}, status = '{status.value}', last_update_time = {current_time} 
        WHERE ins_id = '{ins_id}' AND exchange = '{exchange}' AND symbol = '{symbol}';
        """
        execute_ret = mysql.execute_sql(sql, True)

        self._logger.info(
            f"{ins_id}_{exchange}_{symbol} step 2. 订单成交 {order_id}, {side_str}价格 {avg_price}, {side_str}数量 {executed_qty}, {side_str}usdt {executed_usdt}"
        )
        if is_open:
            # 同时插入持仓表
            position_id = uuid_utils.generate_uuid()
            sql = f"""
            INSERT INTO {self._mysql_table_name_position} (id, exchange, symbol, position_side, coin_quantity, usdt_quantity, open_ins_id, open_price, open_fee, open_fee_rate, open_time, status) 
            VALUES ( '{position_id}', '{exchange}', '{symbol}', '{position_side.value}', '{executed_qty}', '{executed_usdt}', '{ins_id}', '{avg_price}', '{fee}', '{fee_rate}', {current_time}, '{PositionStatus.OPEN.value}' );
            """
            execute_ret = mysql.execute_sql(sql, True)

            self._logger.info(f"{ins_id}_{exchange}_{symbol} step 3. 创建持仓记录 {position_id}")
            try:
                self._write_position_open_to_redis(
                    position_id,
                    exchange,
                    symbol,
                    position_side,
                    executed_qty,
                    executed_usdt,
                    ins_id,
                    avg_price,
                    fee,
                    fee_rate,
                    current_time,
                )
            except:
                pass
        else:
            # 需要找到对应的持仓记录
            sql = f"""
            SELECT * FROM {self._mysql_table_name_position}
            WHERE exchange = '{exchange}' AND symbol = '{symbol}' AND position_side = '{position_side.value}' AND status = '{PositionStatus.OPEN.value}' 
            ORDER BY open_time ASC;
            """

            # 如果有指定仓位id，就用指定的
            if hasattr(order, "position_id") and order.position_id:
                sql = f"""
                SELECT * FROM {self._mysql_table_name_position}
                WHERE id = '{order.position_id}' AND status = '{PositionStatus.OPEN.value}'
                """
                self._logger.info(f"{ins_id}_{exchange}_{symbol} get position by id {order.position_id}")

            execute_ret = mysql.execute_sql(sql)
            try:
                row = execute_ret.fetchone()
                position_id = row.id
                if position_id is not None:
                    # 更新持仓信息
                    sql = f"""
                    UPDATE {self._mysql_table_name_position} 
                    SET close_ins_id = '{ins_id}', close_price = {avg_price}, close_fee = '{fee}', close_fee_rate = '{fee_rate}', close_time = {current_time}, status = '{PositionStatus.CLOSE.value}'
                    WHERE id = '{position_id}';
                    """
                    execute_ret = mysql.execute_sql(sql, True)

                    self._logger.info(f"{ins_id}_{exchange}_{symbol} step 3. 更新持仓记录 {position_id}")
                    try:
                        self._write_position_close_to_redis(
                            position_id,
                            exchange,
                            symbol,
                            position_side,
                            float(row.coin_quantity),
                            float(row.usdt_quantity),
                            row.open_ins_id,
                            float(row.open_price),
                            float(row.open_fee),
                            float(row.open_fee_rate),
                            int(row.open_time),
                            ins_id,
                            avg_price,
                            fee,
                            fee_rate,
                            current_time,
                        )
                    except:
                        pass
            except:
                pass

        return True

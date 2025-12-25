import asyncio
import signal
import threading
import time
from typing import Dict, Optional, Set, Tuple

import websockets
from websockets.server import WebSocketServerProtocol

from kaq_quant_common.api.common.api_interface import ApiInterface
from kaq_quant_common.api.common.auth import verify_ws_handshake
from kaq_quant_common.api.ws.models import WsEnvelope, WsMessageType
from kaq_quant_common.utils import logger_utils, signal_utils, uuid_utils


class WsServerBase:
    """
    WebSocket 服务器基类：
    - 动态发现并分派 @api_method 标注的接口方法
    - 维护连接集合与订阅主题
    - 支持请求/响应与服务器端推送
    - 心跳（处理 ping/pong 消息）
    """

    def __init__(self, api: ApiInterface, host: str = "0.0.0.0", port: int = 8765):
        self._api = api
        self._host = host
        self._port = port
        self._logger = logger_utils.get_logger(self)
        # method 映射：name -> (func, request_model, response_model)
        self._api_methods: Dict[str, Tuple] = self._discover_api_methods()
        # 连接管理
        self._connections: Dict[str, WebSocketServerProtocol] = {}
        # 订阅
        self._subscriptions: Dict[str, Set[str]] = {}  # topic -> set(connection_id)

        # 事件循环/服务器控制
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server: Optional[websockets.server.Server] = None
        self._server_thread: Optional[threading.Thread] = None

    # 动态注册消息处理函数
    def _discover_api_methods(self) -> Dict[str, Tuple]:
        import inspect

        methods = {}
        #
        for name, func in inspect.getmembers(self._api, predicate=inspect.ismethod):
            if hasattr(func, "_is_api_method") and func._is_api_method:
                methods[name] = (func, func._request_model, func._response_model)
        return methods

    # 子类可重写以包装响应（例如添加时间戳）
    def _wrap_response(self, rsp: any):
        return rsp

    # 新的连接
    async def _handle_connection(self, ws: WebSocketServerProtocol):
        connection_id = f"c_{uuid_utils.generate_uuid()}"
        # 创建id
        self._connections[connection_id] = ws
        self._logger.info(f"WS 新连接: {connection_id}")
        try:
            # 接收消息
            async for message in ws:
                try:
                    # 校验消息结构是否正确
                    env = WsEnvelope.model_validate_json(message)
                except Exception as e:
                    self._logger.error(f"解析消息失败: {e}")
                    await ws.send(WsEnvelope(type=WsMessageType.ACK, payload={"error": "invalid message"}).model_dump_json())
                    continue

                # 记录收到的消息类型
                try:
                    self._logger.debug(f"收到消息 type={env.type} method={env.method} topic={env.topic}")
                except Exception:
                    pass

                if env.type == WsMessageType.REQUEST:
                    # 请求->响应
                    await self._on_request(ws, connection_id, env)
                elif env.type == WsMessageType.SUBSCRIBE:
                    # 订阅
                    topic = env.topic or ""
                    if topic:
                        self._subscriptions.setdefault(topic, set()).add(connection_id)
                        await ws.send(WsEnvelope(type=WsMessageType.ACK, payload={"subscribed": topic}).model_dump_json())
                elif env.type == WsMessageType.UNSUBSCRIBE:
                    # 取消订阅
                    topic = env.topic or ""
                    if topic and topic in self._subscriptions and connection_id in self._subscriptions[topic]:
                        self._subscriptions[topic].discard(connection_id)
                        await ws.send(WsEnvelope(type=WsMessageType.ACK, payload={"unsubscribed": topic}).model_dump_json())
                elif env.type == WsMessageType.PING:
                    # 心跳
                    await ws.send(WsEnvelope(type=WsMessageType.PONG).model_dump_json())
                # PUSH 从客户端来的推送默认忽略，按需在子类扩展
        except Exception as e:
            self._logger.warning(f"WS 连接异常 {connection_id}: {e}")
        finally:
            self._connections.pop(connection_id, None)
            # 清理订阅
            for topic, conn_set in self._subscriptions.items():
                conn_set.discard(connection_id)
            self._logger.info(f"WS 连接关闭: {connection_id}")

    # 处理请求，返回响应
    async def _on_request(self, ws: WebSocketServerProtocol, connection_id: str, env: WsEnvelope):
        method_name = env.method or ""
        self._logger.debug(f"处理请求: method={method_name} req_id={env.req_id}")
        req_id = env.req_id

        if method_name not in self._api_methods:
            # 找不到消息处理函数 返回404
            rsp = WsEnvelope(
                type=WsMessageType.RESPONSE,
                req_id=req_id,
                error={"code": 404, "message": f"Method '{method_name}' not found"},
            )
            try:
                await ws.send(rsp.model_dump_json())
            except Exception as e:
                self._logger.error(f"发送404响应失败: {e}")
            return

        # 获取处理函数，请求，返回结构
        method, request_model, response_model = self._api_methods[method_name]
        try:
            # 解析model
            request_obj = request_model(**(env.payload or {}))
            # 执行处理函数，获取返回数据
            response_obj = method(request_obj)
            # 校验响应类型
            if not isinstance(response_obj, response_model):
                raise TypeError("Invalid response type from method")

            # wrap
            response_obj = self._wrap_response(response_obj)
            # 数据
            payload = response_obj.model_dump()
            # 请求返回外层结构，RESPONSE 并且附带 req_id
            rsp = WsEnvelope(type=WsMessageType.RESPONSE, req_id=req_id, payload=payload)
            # 发送消息
            await ws.send(rsp.model_dump_json())
        except Exception as e:
            # 异常处理
            self._logger.error(f"处理请求失败: {e}")
            rsp = WsEnvelope(
                type=WsMessageType.RESPONSE,
                req_id=req_id,
                error={"code": 500, "message": str(e)},
            )
            try:
                await ws.send(rsp.model_dump_json())
            except Exception as send_e:
                self._logger.error(f"发送错误响应失败: {send_e}")

    async def _ws_handler(self, ws: WebSocketServerProtocol):
        # websockets v12+ 新实现的 handler 仅接收 websocket 一个参数
        try:
            # 简单鉴权（若未配置 token 则默认放行）
            ok, err = verify_ws_handshake(getattr(ws, "path", None), getattr(ws, "request_headers", {}))
            if not ok:
                self._logger.warning(f"WS 鉴权失败: {err}")
                try:
                    await ws.close(code=1008, reason=err or "Unauthorized")
                except Exception:
                    pass
                return
            await self._handle_connection(ws)
        except Exception as e:
            # 捕获顶层异常，避免直接导致连接以1011关闭
            self._logger.error(f"WS handler 异常: {e}")

    # 广播消息
    def broadcast(self, topic: str, payload: dict):
        """广播推送到订阅了topic的连接"""
        if not self._loop:
            return
        env = WsEnvelope(type=WsMessageType.PUSH, topic=topic, payload=payload)
        data = env.model_dump_json()

        async def _do_broadcast():
            conns = []
            for conn_id, ws in list(self._connections.items()):
                subs = self._subscriptions.get(topic, set())
                if conn_id in subs:
                    conns.append(ws)
            for ws in conns:
                try:
                    await ws.send(data)
                except Exception as e:
                    self._logger.warning(f"广播失败: {e}")

        asyncio.run_coroutine_threadsafe(_do_broadcast(), self._loop)

    # 定向消息
    def send_to(self, connection_id: str, topic: str, payload: dict):
        """向指定连接推送消息"""
        if not self._loop:
            return
        ws = self._connections.get(connection_id)
        if not ws:
            return
        env = WsEnvelope(type=WsMessageType.PUSH, topic=topic, payload=payload)
        data = env.model_dump_json()

        async def _do_send():
            try:
                await ws.send(data)
            except Exception as e:
                self._logger.warning(f"点对点推送失败: {e}")

        asyncio.run_coroutine_threadsafe(_do_send(), self._loop)

    def run(self):
        """在当前线程启动服务器，阻塞运行"""
        self._logger.info(f"Starting WS server on {self._host}:{self._port}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop

        try:

            async def _start():
                self._server = await websockets.serve(self._ws_handler, self._host, self._port, ping_interval=None)

            # 在事件循环运行中启动服务器（await serve）
            loop.run_until_complete(_start())
            # 运行事件循环直至停止
            loop.run_forever()
        finally:
            # 关闭服务器
            if self._server:
                self._server.close()
                try:
                    loop.run_until_complete(self._server.wait_closed())
                except Exception:
                    pass
            self._logger.warning("WS Server 事件循环结束")
            try:
                loop.close()
            except Exception:
                pass

    def shutdown(self):
        """触发停止事件，优雅关闭服务器"""
        self._logger.info(f"Shutting down WS server on {self._host}:{self._port}")
        if self._loop:
            # 停止事件循环，run() 中的 run_forever 将退出
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

    def run_with_thread(self, block: bool = True):
        self._server_thread = threading.Thread(target=self.run, name="WsServerThread", daemon=True)
        self._server_thread.start()
        # 等待服务器准备就绪的短暂时间
        # 在更复杂场景可使用事件通知ready
        time.sleep(0.5)

        if block:
            self.wait_for_termination()

    def wait_for_termination(self):
        # 终止信号监听
        exit_event = threading.Event()

        def handle_terminate_signal(signum, frame=None):
            self._logger.info(f"收到终止信号 {signum}")
            exit_event.set()
            self.shutdown()

        signal_utils.register_signal_handler(handle_terminate_signal)

        while not exit_event.is_set():
            time.sleep(1)

        self._logger.warning("WsServer 线程退出")

    def shutdown_with_thread(self):
        try:
            self.shutdown()
        finally:
            if hasattr(self, "_server_thread") and self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=3)

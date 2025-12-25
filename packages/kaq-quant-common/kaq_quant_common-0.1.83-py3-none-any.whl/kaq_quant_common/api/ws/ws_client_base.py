import asyncio
import threading
from typing import Callable, Dict, Optional, Type, TypeVar

import websockets
from pydantic import BaseModel

from kaq_quant_common.api.ws.models import WsEnvelope, WsMessageType
from kaq_quant_common.utils import logger_utils, uuid_utils
from kaq_quant_common.api.common.auth import get_auth_token

R = TypeVar("R", bound=BaseModel)


class WsClientBase:
    """
    WebSocket 客户端基类：
    - 管理长连接、自动重连和心跳（基于自定义 ping/pong）
    - 请求/响应关联（req_id -> Future）
    - 订阅主题并接收服务器推送
    提供同步方法封装，便于调用。
    """

    def __init__(self, url: str, auto_reconnect: bool = True, token: Optional[str] = None):
        self._url = url
        self._auto_reconnect = auto_reconnect
        self._token = token if token is not None else get_auth_token()
        self._logger = logger_utils.get_logger(self)

        # 事件循环线程
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None

        # 连接与控制
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected_event = threading.Event()
        self._stop_flag = threading.Event()

        # 请求映射
        self._pending_requests: Dict[str, asyncio.Future] = {}

        # 订阅映射：topic -> handler
        self._subscriptions: Dict[str, Callable[[dict], None]] = {}

        # 重连参数
        self._reconnect_initial = 1.0
        self._reconnect_max = 30.0

    # ============================== 外部API ==============================
    def connect(self):
        """启动事件循环与连接任务"""
        if self._loop_thread and self._loop_thread.is_alive():
            return

        # 开一条线程跑事件循环
        def _run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._connect_forever())
            finally:
                try:
                    self._loop.close()
                except Exception:
                    pass
                self._logger.warning("WsClient 事件循环结束")

        # 循环接收线程，设置为守护进程，主线程关闭就自动关闭
        self._loop_thread = threading.Thread(target=_run_loop, name="WsClientLoop", daemon=True)
        self._loop_thread.start()

    # 断开连接
    def disconnect(self):
        self._stop_flag.set()
        if self._loop and self._ws:

            async def _close():
                # 关闭ws
                try:
                    await self._ws.close()
                except Exception:
                    pass

            try:
                fut = asyncio.run_coroutine_threadsafe(_close(), self._loop)
                # 尝试快速关闭，若事件循环已结束则忽略超时
                fut.result(timeout=1)
            except Exception:
                pass
        # 等待线程结束
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=5)

    # 订阅，向服务器注册订阅
    def subscribe(self, topic: str, handler: Callable[[dict], None]):
        """注册订阅，并在连接后自动发送SUBSCRIBE"""
        self._subscriptions[topic] = handler
        if self._loop and self._ws:

            async def _send_sub():
                # 构造订阅消息
                env = WsEnvelope(type=WsMessageType.SUBSCRIBE, topic=topic)
                await self._ws.send(env.model_dump_json())

            asyncio.run_coroutine_threadsafe(_send_sub(), self._loop)

    # 取消订阅
    def unsubscribe(self, topic: str):
        self._subscriptions.pop(topic, None)
        if self._loop and self._ws:

            async def _send_unsub():
                # 构造取消订阅消息
                env = WsEnvelope(type=WsMessageType.UNSUBSCRIBE, topic=topic)
                # 发送取消订阅消息
                await self._ws.send(env.model_dump_json())

            asyncio.run_coroutine_threadsafe(_send_unsub(), self._loop)

    #
    def send_request(self, method: str, request_data: BaseModel, response_model: Type[R], timeout: float = 10.0) -> R:
        """同步请求封装，等待响应返回"""
        if not self._connected_event.wait(timeout=5.0):
            raise RuntimeError("WS not connected")

        async def _send_and_wait() -> R:
            # 生成请求id，用来处理响应
            req_id = f"r_{uuid_utils.generate_uuid()}"
            # 在事件循环中创建Future
            fut = self._loop.create_future()
            # 记录正在处理的请求
            self._pending_requests[req_id] = fut
            # 构造请求消息
            env = WsEnvelope(type=WsMessageType.REQUEST, req_id=req_id, method=method, payload=request_data.model_dump())
            # 发送
            await self._ws.send(env.model_dump_json())
            try:
                # 等待执行完毕
                payload: dict = await asyncio.wait_for(fut, timeout=timeout)
                # 构造返回结构
                return response_model(**payload)
            finally:
                # 移除已处理请求
                self._pending_requests.pop(req_id, None)

        # 提交到事件循环执行
        cfut = asyncio.run_coroutine_threadsafe(_send_and_wait(), self._loop)
        return cfut.result()

    # ============================== 内部协程 ==============================
    async def _connect_forever(self):
        backoff = self._reconnect_initial
        while not self._stop_flag.is_set():
            try:
                self._logger.info(f"WS connecting to {self._url}")
                headers = {}
                if self._token:
                    headers["Authorization"] = f"Bearer {self._token}"
                self._ws = await websockets.connect(self._url, ping_interval=None, additional_headers=headers or None)
                self._connected_event.set()
                self._logger.info("WS connected")
                # 连接恢复后自动订阅
                await self._resubscribe_all()
                # 启动接收循环
                await self._recv_loop()
                # 正常退出接收循环（例如主动断开）
                if self._stop_flag.is_set():
                    break
            except Exception as e:
                self._connected_event.clear()
                self._logger.warning(f"WS 连接失败或中断: {e}")
                if not self._auto_reconnect or self._stop_flag.is_set():
                    break
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, self._reconnect_max)

        # 退出时确保关闭连接
        try:
            if self._ws:
                await self._ws.close()
        except Exception:
            pass

    # 重新自动订阅
    async def _resubscribe_all(self):
        for topic in list(self._subscriptions.keys()):
            try:
                env = WsEnvelope(type=WsMessageType.SUBSCRIBE, topic=topic)
                await self._ws.send(env.model_dump_json())
            except Exception as e:
                self._logger.warning(f"自动订阅 {topic} 失败: {e}")

    # 循环接收
    async def _recv_loop(self):
        assert self._ws is not None
        try:
            async for message in self._ws:
                # 收到消息会进入到这里
                env = None
                try:
                    # 校验消息格式是否正确
                    env = WsEnvelope.model_validate_json(message)
                except Exception as e:
                    self._logger.error(f"解析消息失败: {e}")
                    continue

                if env.type == WsMessageType.RESPONSE:
                    # 对应REQUEST的响应
                    req_id = env.req_id or ""
                    # 找到对应的请求Future
                    fut = self._pending_requests.get(req_id)
                    # 如果Future存在且未完成
                    if fut and not fut.done():
                        if env.error:
                            # 异常响应，设置Future异常
                            fut.set_exception(RuntimeError(env.error.get("message") if isinstance(env.error, dict) else str(env.error)))
                        else:
                            # 成功响应，设置Future结果
                            fut.set_result(env.payload or {})
                elif env.type == WsMessageType.PUSH:
                    # 推送过来的订阅的消息
                    topic = env.topic or ""
                    # 找到对应订阅处理的函数
                    handler = self._subscriptions.get(topic)
                    if handler and env.payload is not None:
                        # 在后台执行handler，避免阻塞事件循环
                        asyncio.create_task(asyncio.to_thread(handler, env.payload))
                elif env.type == WsMessageType.PING:
                    # 心跳
                    pong = WsEnvelope(type=WsMessageType.PONG)
                    await self._ws.send(pong.model_dump_json())
        except Exception as e:
            self._logger.warning(f"WS 接收循环异常: {e}")
        finally:
            self._connected_event.clear()

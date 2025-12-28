import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union

import pandas as pd

from kaq_quant_common.api.ws.exchange.models import FundingRateEvent
from kaq_quant_common.api.ws.ws_server_base import WsServerBase
from kaq_quant_common.resources.kaq_mysql_resources import KaqQuantMysqlRepository
from kaq_quant_common.utils import logger_utils


class WsExchangeServer(WsServerBase):
    """
    模拟加密货币平台 WS 服务器：
    - 从 MySQL 按 exchange 读取资金费率历史数据
    - 从指定 start_time 开始，按事件时间差和加速倍数推送
    - 支持将推送事件的 event_time 重写为实时时间
    - 主题：
      * funding_rate.all
      * funding_rate.<symbol>
    """

    def __init__(
        self,
        exchange: str,
        mysql_host: str,
        mysql_port: int,
        mysql_user: str,
        mysql_passwd: str,
        mysql_db: str,
        charset: str = "utf8mb4",
        start_time: Union[int, float, datetime] = None,
        speed_multiplier: float = 1.0,
        use_realtime_event_time: bool = False,
        inject_sample_on_empty: bool = True,
        host: str = "0.0.0.0",
        port: int = 8767,
    ):
        super().__init__(self, host, port)
        self._logger = logger_utils.get_logger(self)
        # 平台
        self._exchange = exchange
        # 加速设置
        self._speed_multiplier = max(speed_multiplier if speed_multiplier and speed_multiplier > 0 else 1.0, 1e-6)
        # 是否使用实时时间
        self._use_realtime_event_time = use_realtime_event_time
        # 示例数据注入开关
        self._inject_sample_on_empty = inject_sample_on_empty

        # 单次增量加载的窗口大小
        self._window_size: timedelta = timedelta(minutes=10)
        # 触发预加载的阈值
        self._preload_horizon: timedelta = timedelta(minutes=5)
        # 丢弃数据的阈值
        self._retain_horizon: timedelta = timedelta(minutes=10)

        # 数据开始游标（时间） 支持毫秒时间戳或 datetime
        if isinstance(start_time, (int, float)):
            self._start_dt = datetime.fromtimestamp(start_time / 1000.0)
        elif isinstance(start_time, datetime):
            self._start_dt = start_time
        else:
            # 默认很早的时间，确保可以从最早记录开始
            self._start_dt = datetime.fromtimestamp(0)

        # DB
        self._repo = KaqQuantMysqlRepository(mysql_host, mysql_port, mysql_user, mysql_passwd, mysql_db, charset)

        # 推送控制
        self._push_thread: Optional[threading.Thread] = None
        self._stop_push = threading.Event()

        # 预拉取首批数据,开始的时候加载多一点
        initial_end = self._start_dt + self._preload_horizon * 2
        self._events: List[Tuple[datetime, FundingRateEvent]] = self._load_events_window(self._start_dt, initial_end)
        self._last_fetched_dt = initial_end
        self._logger.info(f"资金费率事件已加载: {len(self._events)} 条")
        # 添加测试数据
        if not self._events and self._inject_sample_on_empty:
            base_dt = self._start_dt if self._start_dt else datetime.fromtimestamp(0)
            sample: List[Tuple[datetime, FundingRateEvent]] = []
            for i in range(5):
                dt = base_dt if i == 0 else base_dt + pd.Timedelta(minutes=i)
                evt = FundingRateEvent(
                    event_time=int(dt.timestamp() * 1000),
                    exchange_symbol=f"{self._exchange}:BTCUSDT",
                    exchange=self._exchange,
                    symbol="BTCUSDT",
                    open_rate=0.0001,
                    close_rate=0.0001,
                    high_rate=0.0002,
                    low_rate=0.0000,
                )
                sample.append((dt, evt))
            self._events = sample
            self._logger.warning("资金费率历史为空，已注入示例数据用于推送测试")

        # 把开始时间调整为第一条数据的时间
        if self._events:
            self._start_dt = self._events[0][0]
        # 最后对齐整分钟
        self._start_dt = self._start_dt.replace(second=0, microsecond=0)

        # 实际启动时间，用于计算虚拟时间，需要对齐整分钟
        self._real_start_dt: datetime = datetime.now()
        self._real_start_dt = self._real_start_dt.replace(second=0, microsecond=0)

    # 原始全量拉取（保留以兼容旧逻辑）
    def _load_events(self) -> List[Tuple[datetime, FundingRateEvent]]:
        try:
            query = (
                "SELECT event_time, exchange_symbol, exchange, symbol, open_rate, close_rate, high_rate, low_rate, close_time, next_event_time, id, ctimestamp "
                "FROM kaq_future_fr_klines_1m "
                f"WHERE exchange = '{self._exchange}' AND event_time >= '{self._start_dt.strftime('%Y-%m-%d %H:%M:%S')}' "
                "ORDER BY event_time ASC"
            )
            df: pd.DataFrame = self._repo.fetch_data(query)
            if df is None or df.empty:
                self._logger.warning("资金费率表无数据或查询为空")
                return []

            events: List[Tuple[datetime, FundingRateEvent]] = []
            for _, row in df.iterrows():
                evt_dt: datetime = row.get("event_time")
                if not isinstance(evt_dt, datetime):
                    try:
                        evt_dt = pd.to_datetime(evt_dt).to_pydatetime()
                    except Exception:
                        continue
                # 转为毫秒时间戳
                close_time_val = row.get("close_time")
                next_event_time_val = row.get("next_event_time")
                try:
                    close_time_ms = int(pd.to_datetime(close_time_val).timestamp() * 1000) if close_time_val is not None else None
                except Exception:
                    close_time_ms = None
                try:
                    next_event_time_ms = int(pd.to_datetime(next_event_time_val).timestamp() * 1000) if next_event_time_val is not None else None
                except Exception:
                    next_event_time_ms = None
                evt_ms = int(evt_dt.timestamp() * 1000)
                event = FundingRateEvent(
                    event_time=evt_ms,
                    exchange_symbol=row.get("exchange_symbol"),
                    exchange=row.get("exchange"),
                    symbol=row.get("symbol"),
                    open_rate=row.get("open_rate"),
                    close_rate=row.get("close_rate"),
                    high_rate=row.get("high_rate"),
                    low_rate=row.get("low_rate"),
                    close_time=close_time_ms,
                    next_event_time=next_event_time_ms,
                    #
                    id=row.get("id"),
                    ctimestamp=row.get("ctimestamp"),
                )
                events.append((evt_dt, event))
            return events
        except Exception as e:
            self._logger.error(f"加载资金费率事件失败: {e}")
            return []

    # 增量批量拉取（保留以兼容旧逻辑）
    def _load_events_batch(self, start_from: datetime, limit: int) -> List[Tuple[datetime, FundingRateEvent]]:
        try:
            query = (
                "SELECT event_time, exchange_symbol, exchange, symbol, open_rate, close_rate, high_rate, low_rate, close_time, next_event_time, id, ctimestamp "
                "FROM kaq_future_fr_klines_1m "
                f"WHERE exchange = '{self._exchange}' AND event_time > '{start_from.strftime('%Y-%m-%d %H:%M:%S')}' "
                "ORDER BY event_time ASC "
                f"LIMIT {int(limit)}"
            )
            df: pd.DataFrame = self._repo.fetch_data(query)
            if df is None or df.empty:
                return []
            events: List[Tuple[datetime, FundingRateEvent]] = []
            for _, row in df.iterrows():
                evt_dt: datetime = row.get("event_time")
                if not isinstance(evt_dt, datetime):
                    try:
                        evt_dt = pd.to_datetime(evt_dt).to_pydatetime()
                    except Exception:
                        continue
                # 转为毫秒时间戳
                close_time_val = row.get("close_time")
                next_event_time_val = row.get("next_event_time")
                try:
                    close_time_ms = int(pd.to_datetime(close_time_val).timestamp() * 1000) if close_time_val is not None else None
                except Exception:
                    close_time_ms = None
                try:
                    next_event_time_ms = int(pd.to_datetime(next_event_time_val).timestamp() * 1000) if next_event_time_val is not None else None
                except Exception:
                    next_event_time_ms = None
                evt_ms = int(evt_dt.timestamp() * 1000)
                event = FundingRateEvent(
                    event_time=evt_ms,
                    exchange_symbol=row.get("exchange_symbol"),
                    exchange=row.get("exchange"),
                    symbol=row.get("symbol"),
                    open_rate=row.get("open_rate"),
                    close_rate=row.get("close_rate"),
                    high_rate=row.get("high_rate"),
                    low_rate=row.get("low_rate"),
                    close_time=close_time_ms,
                    next_event_time=next_event_time_ms,
                    #
                    id=row.get("id"),
                    ctimestamp=row.get("ctimestamp"),
                )
                events.append((evt_dt, event))
            return events
        except Exception as e:
            self._logger.error(f"增量加载资金费率事件失败: {e}")
            return []

    # 按照时间窗口拉取
    def _load_events_window(self, start_from: datetime, end_until: datetime) -> List[Tuple[datetime, FundingRateEvent]]:
        try:
            query = (
                "SELECT event_time, exchange_symbol, exchange, symbol, open_rate, close_rate, high_rate, low_rate, close_time, next_event_time, id, ctimestamp "
                "FROM kaq_future_fr_klines_1m "
                f"WHERE exchange = '{self._exchange}' AND event_time > '{start_from.strftime('%Y-%m-%d %H:%M:%S')}' AND event_time <= '{end_until.strftime('%Y-%m-%d %H:%M:%S')}' "
                "ORDER BY event_time ASC"
            )
            df: pd.DataFrame = self._repo.fetch_data(query)
            if df is None or df.empty:
                return []
            events: List[Tuple[datetime, FundingRateEvent]] = []
            for _, row in df.iterrows():
                evt_dt: datetime = row.get("event_time")
                if not isinstance(evt_dt, datetime):
                    try:
                        evt_dt = pd.to_datetime(evt_dt).to_pydatetime()
                    except Exception:
                        continue
                close_time_val = row.get("close_time")
                next_event_time_val = row.get("next_event_time")
                try:
                    close_time_ms = int(pd.to_datetime(close_time_val).timestamp() * 1000) if close_time_val is not None else None
                except Exception:
                    close_time_ms = None
                try:
                    next_event_time_ms = int(pd.to_datetime(next_event_time_val).timestamp() * 1000) if next_event_time_val is not None else None
                except Exception:
                    next_event_time_ms = None
                evt_ms = int(evt_dt.timestamp() * 1000)
                event = FundingRateEvent(
                    event_time=evt_ms,
                    exchange_symbol=row.get("exchange_symbol"),
                    exchange=row.get("exchange"),
                    symbol=row.get("symbol"),
                    open_rate=row.get("open_rate"),
                    close_rate=row.get("close_rate"),
                    high_rate=row.get("high_rate"),
                    low_rate=row.get("low_rate"),
                    close_time=close_time_ms,
                    next_event_time=next_event_time_ms,
                    #
                    id=row.get("id"),
                    ctimestamp=row.get("ctimestamp"),
                )
                events.append((evt_dt, event))
            return events
        except Exception as e:
            self._logger.error(f"时间窗加载资金费率事件失败: {e}")
            return []

    # 从数据库拉取最新的记录
    def _get_latest_event_dt(self) -> Optional[datetime]:
        try:
            query = "SELECT MAX(event_time) AS max_event_time " "FROM kaq_future_fr_klines_1m " f"WHERE exchange = '{self._exchange}'"
            df: pd.DataFrame = self._repo.fetch_data(query)
            if df is None or df.empty:
                return None
            val = df.iloc[0].get("max_event_time")

            if isinstance(val, datetime):
                return val
            try:
                return pd.to_datetime(val).to_pydatetime()
            except Exception:
                return None
        except Exception as e:
            self._logger.error(f"查询最新资金费率事件时间失败: {e}")
            return None

    def _push_loop(self):
        # 初始缓冲检查
        if not self._events:
            # 获取一次最新记录
            latest_dt = self._get_latest_event_dt()
            initial_end = self._last_fetched_dt + self._window_size
            # 防止超过
            if latest_dt is not None and initial_end > latest_dt:
                initial_end = latest_dt
            self._events = self._load_events_window(self._last_fetched_dt, initial_end)
            # 主要是为了记录这个最新拉取的时间点，下一次增量加载从这里开始
            self._last_fetched_dt = initial_end
        if not self._events:
            self._logger.warning("无可推送的资金费率历史事件")
            return

        prev_dt = None
        prev_counter = 0
        discard_dt = None
        idx = 0
        while not self._stop_push.is_set():
            # 虚拟时钟，考虑加速比
            now_real = datetime.now()
            # 计算出虚拟时间点
            now_virtual = self._start_dt + (now_real - self._real_start_dt) * self._speed_multiplier

            # 确保缓冲区覆盖到虚拟时间的预加载阈值
            # 获取缓冲区最新的记录时间
            buffer_max_dt = self._events[-1][0] if self._events else self._last_fetched_dt
            # 根据虚拟时间点计算出需要覆盖的时间点
            target_cover_dt = now_virtual + self._preload_horizon
            # 最新的记录时间
            latest_dt: datetime = None
            while buffer_max_dt < target_cover_dt and not self._stop_push.is_set():
                # 每次进入循环，先拉取一次最新数据时间
                if latest_dt is None:
                    latest_dt = self._get_latest_event_dt()
                # 若数据库已无更晚数据，停止增量加载
                if latest_dt is not None and self._last_fetched_dt >= latest_dt:
                    buffer_max_dt = latest_dt
                    self._logger.debug("已到达数据库最新事件时间，停止增量加载")
                    break
                # 计算出增量加载的窗口时间点
                window_end = self._last_fetched_dt + self._window_size
                # 限制窗口终点不超过数据库最新时间
                if latest_dt is not None and window_end > latest_dt:
                    window_end = latest_dt
                # 增量加载
                new_events = self._load_events_window(self._last_fetched_dt, window_end)
                self._last_fetched_dt = window_end
                if new_events:
                    self._logger.debug(f"增量获取{len(new_events)}条数据,截止时间{window_end}")
                    self._events.extend(new_events)
                    buffer_max_dt = self._events[-1][0]
                else:
                    # 即便当前窗无数据，推进游标，避免卡住
                    buffer_max_dt = max(buffer_max_dt, window_end)
                    self._logger.debug(f"增量获取{0}条数据,截止时间{window_end}")
            latest_dt = None

            # 如果缓冲区已消费完，退出（或等待下一轮覆盖）
            if idx >= len(self._events):
                time.sleep(0.05)
                continue

            # 取出一条数据
            evt_dt, evt = self._events[idx]

            # 计算等待时间，按加速比缩放
            try:
                # 数据时间 - 当前虚拟时间
                delta = (evt_dt - now_virtual).total_seconds()
                # 等待秒数
                wait_s = max(delta, 0.0)
                if wait_s > 0:
                    time.sleep(0.05)
                    continue

                if prev_dt != evt_dt:
                    # 输出一下时间
                    if prev_dt is not None:
                        self._logger.debug(f"完成处理{prev_dt}的资金费率{prev_counter}条")
                    self._logger.debug(f"开始处理{evt_dt}的资金费率")
                    prev_counter = 0
                    prev_dt = evt_dt
                    #
                    if discard_dt is None:
                        discard_dt = prev_dt
            except Exception:
                pass

            #
            idx += 1
            prev_counter += 1

            # 构造推送数据
            payload = evt.model_dump()
            if self._use_realtime_event_time:
                # 调整为实时时间
                payload["event_time"] = int(time.time() * 1000)
            # 广播到主题：all 和 symbol
            try:
                self.broadcast("funding_rate.all", payload)
                sym = payload.get("symbol") or ""
                if sym:
                    self.broadcast(f"funding_rate.{sym}", payload)
            except Exception as e:
                self._logger.warning(f"广播资金费率事件失败: {e}")

            # 时间型丢弃：移除过旧数据以控制内存
            if prev_dt - discard_dt > self._retain_horizon:
                discard_dt = prev_dt
                cut_idx = -1
                for i in range(len(self._events)):
                    if self._events[i][0] < discard_dt:
                        cut_idx = i
                    elif self._events[i][0] >= discard_dt:
                        break
                # 裁剪
                if cut_idx > 0:
                    cut_count = cut_idx + 1
                    self._logger.debug(f"丢弃{cut_count}条过期数据")
                    self._events = self._events[cut_count:]
                    # 修正idx
                    idx = max(0, idx - cut_count)

    def run_with_thread(self, block: bool = True):
        # 启动推送线程
        self._stop_push.clear()
        self._push_thread = threading.Thread(target=self._push_loop, name="WsExchangePush", daemon=True)
        self._push_thread.start()
        # 启动WS服务器线程
        super().run_with_thread(block)

    def shutdown_with_thread(self):
        # 先停止推送线程
        try:
            self._stop_push.set()
            if self._push_thread and self._push_thread.is_alive():
                self._push_thread.join(timeout=3)
        except Exception:
            pass
        # 再关闭WS服务器
        super().shutdown_with_thread()

    async def _ws_handler(self, ws):
        # 覆盖基类鉴权，模拟平台测试环境不启用鉴权
        try:
            await self._handle_connection(ws)
        except Exception:
            pass

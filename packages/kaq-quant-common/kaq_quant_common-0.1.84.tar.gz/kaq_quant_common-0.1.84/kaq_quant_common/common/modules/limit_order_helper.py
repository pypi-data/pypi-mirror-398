# 避免写入导致阻塞
import datetime
import threading
import time

import pandas as pd
from kaq_quant_common.resources.kaq_ddb_stream_write_resources import (
    KaqQuantDdbStreamWriteRepository,
)
from kaq_quant_common.utils import logger_utils


class LimitOrderHelper:

    def __init__(self, ddb: KaqQuantDdbStreamWriteRepository, ddb_table_name: str):
        # 最新快照缓存与刷库线程控制
        self._latest_snapshots: dict[str, tuple] = {}
        self._latest_lock = threading.Lock()
        # 写入到ddb的频率，默认100ms
        self._flush_interval_ms = 100
        self._stop_event = threading.Event()
        self._flusher_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flusher_thread.name = "LimitOrderHelperFlusherThread"

        #
        self._ddb = ddb
        self._ddb_table_name = ddb_table_name

        #
        self._logger = logger_utils.get_logger(self)

        self._build_data: callable = None

    def set_build_data(self, build_data: callable):
        self._build_data = build_data

    def push_data(self, symbol: str, data: dict, arg: dict = None):
        with self._latest_lock:
            self._latest_snapshots[symbol] = (data, arg)

    def start(self):
        self._flusher_thread.start()

    def stop(self):
        self._stop_event.set()
        self._flusher_thread.join()

    def _flush_loop(self):
        # 周期性地将每个symbol的最新快照批量入库
        while not self._stop_event.is_set():
            to_process = None
            with self._latest_lock:
                if self._latest_snapshots:
                    to_process = list(self._latest_snapshots.items())
                    self._latest_snapshots.clear()

            if to_process:
                df: pd.DataFrame = None
                now = int(datetime.datetime.now().timestamp() * 1000)

                for symbol, (data, arg) in to_process:
                    sub_df = self._build_data(symbol, data, arg)
                    # 输出一下
                    data_first_now = int(sub_df["create_time"].iloc[0])
                    if now - data_first_now > 2000:
                        self._logger.debug(f"数据时间{data_first_now} 与当前时间{now} 差值{now - data_first_now} 超过2000ms")

                    if df is None:
                        df = sub_df
                    else:
                        df = pd.concat([df, sub_df], ignore_index=True)

                # 入库
                if df is not None and not df.empty:
                    try:
                        self._ddb.save2stream_batch(self._ddb_table_name, df=df)
                    except Exception as e:
                        # 避免刷库异常导致线程退出
                        self._logger.error(f"批量写入失败: {e}")

            time.sleep(self._flush_interval_ms / 1000.0)

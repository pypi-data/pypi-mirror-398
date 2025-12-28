import threading
import time
from abc import abstractmethod

from kaq_quant_common.common.monitor_base import MonitorBase
from kaq_quant_common.common.ws_wrapper import WsWrapper
from kaq_quant_common.utils import logger_utils


# 封装http定时请求
class HttpMonitor(MonitorBase):
    def __init__(self, interval=5):
        super().__init__()
        # 执行间隔
        self._interval = interval
        self._logger = logger_utils.get_logger()

    def _do_start(self):
        # 开启一条线程，定时执行http请求
        self._ticker_thread_event = threading.Event()

        def http_request():
            # 上次请求时间
            last_request_time = 0
            while True:
                # 检查是否需要退出
                if self._ticker_thread_event.is_set():
                    self._logger.info("ticker thread exit")
                    break

                # 当前时间
                current_time = time.time()
                # 如果上次请求时间距离当前时间不足，等待
                if current_time - last_request_time < self._interval:
                    time.sleep(0.1)
                    continue

                #
                last_request_time = time.time()

                # self._logger.debug('tick start')
                try:
                    self._do_request()
                except Exception as e:
                    self._logger.error(f"http request error: {e}")
                # self._logger.debug('tick finish')
                #
                time.sleep(0.1)

        # 开启线程
        self._ticker_thread = threading.Thread(target=http_request)
        # 设置为守护线程
        self._ticker_thread.daemon = True
        self._ticker_thread.start()

    def _do_stop(self):
        if self._ticker_thread_event is not None:
            self._ticker_thread_event.set()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

    @abstractmethod
    def _do_request(self):
        """
        子类实现
        """
        pass

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

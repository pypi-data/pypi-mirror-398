import threading
import time

from kaq_quant_common.common.monitor_base import MonitorBase
from kaq_quant_common.utils import logger_utils, signal_utils


class MonitorGroup:

    def __init__(self):
        #
        self._monitors: list[MonitorBase] = []
        self._logger = logger_utils.get_logger(self)

    def get_monitors(self) -> list[MonitorBase]:
        return self._monitors

    # 开始，需要确保这个方法在op线程执行，执行这个方法会阻塞当前线程！
    def start(self, block=True):
        # 全局退出事件，用于传递终止信号
        exit_event = threading.Event()
        self._exit_event = exit_event

        logger = self._logger

        #
        def handle_terminate_signal(signum, frame=None):
            """信号处理函数：捕获终止信号并触发退出事件"""
            logger.info(f"收到终止信号 {signum}")
            exit_event.set()
            # 优雅地停止
            try:
                self.stop()
            except Exception as e:
                pass

        signal_utils.register_signal_handler(handle_terminate_signal)

        # 需要阻塞
        if block:
            # 监听退出事件
            while not exit_event.is_set():
                time.sleep(1)
                if self._check_exit():
                    # 假装发送信号
                    handle_terminate_signal("exit")

            logger.warning("MonitorGroup 线程退出")

    # 停止
    def stop(self):
        #
        self.stop_monitors()
        #
        self._exit_event.set()

    def _check_exit(self):
        # 避免还没有链接monitor
        if len(self._monitors) == 0:
            return False

        # 标识是否全部都已经退出
        all_exit = True
        one_exit = False

        # 遍历检测是否全部都退出了
        for monitor in self._monitors:
            if not monitor._check_exit():
                all_exit = False
            else:
                one_exit = True

        return one_exit

    # 只停止 monitor
    def stop_monitors(self, clear=False):
        self._logger.info(f"停止 {len(self._monitors)} 个 monitor")
        tmp_monitors = self._monitors.copy()
        if clear:
            # 清空数组
            self._monitors.clear()
        for monitor in tmp_monitors:
            monitor.stop()

    #
    def link(self, monitors: list[MonitorBase], clear=False):
        # 如果需要clear,先清空之前的
        if clear:
            self.stop_monitors(clear=True)
        self._logger.info(f"开启 {len(monitors)} 个 monitor")
        # 遍历调用start
        for monitor in monitors:
            monitor.start(block=False)
            # 延迟一下，防止同时创建多个连接有问题
            time.sleep(1)
        # 追加新的
        self._monitors.extend(monitors)

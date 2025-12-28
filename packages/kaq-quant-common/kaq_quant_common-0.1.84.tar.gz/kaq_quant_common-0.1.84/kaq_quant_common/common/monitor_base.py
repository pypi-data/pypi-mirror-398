import threading
import time
from abc import ABC, abstractmethod

from kaq_quant_common.utils import logger_utils, signal_utils


# 通用的抽象类
class MonitorBase(ABC):
    def __init__(self):
        # 初始化
        self.init()
        # 用来标记最后一次收到数据的时间，超过指定时间没有收到数据，认为连接断开
        self._keep_alive_deadline = 0

    # 初始化
    def init(self):
        # 执行初始化
        self._do_init()

    @abstractmethod
    def _do_init(self):
        pass

    # 开始，需要确保这个方法在op线程执行，执行这个方法会阻塞当前线程！
    def start(self, block=True):
        # 全局退出事件，用于传递终止信号
        exit_event = threading.Event()
        self._exit_event = exit_event

        logger = logger_utils.get_logger(self)

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

        self._do_start()

        # 需要阻塞
        if block:
            # 监听退出事件
            while not exit_event.is_set():
                time.sleep(1)
                if self._check_exit():
                    # 假装发送信号
                    handle_terminate_signal("exit")
                if self._keep_alive_deadline > 0 and time.time() > self._keep_alive_deadline:
                    logger.warning("MonitorBase 收据接收超时，需要停止 MonitorBase")
                    # 假装发送信号
                    handle_terminate_signal("recv time out")

            logger.warning("MonitorBase 线程退出")

    # 子类实现，判断连接是否断开，断开返回True
    def _check_exit(self):
        return False

    @abstractmethod
    def _do_start(self):
        pass

    # 停止
    def stop(self):
        self._do_stop()

    @abstractmethod
    def _do_stop(self):
        pass

    def keep_alive(self, deadline: int = 60):
        """
        保持连接alive，超过指定时间不活跃，认为需要停止
        """
        cur_time = time.time()
        self._keep_alive_deadline = cur_time + deadline

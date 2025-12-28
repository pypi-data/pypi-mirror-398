from abc import abstractmethod

from kaq_quant_common.common.monitor_base import MonitorBase


# 通用的抽象类，包装一层ws操作
class WsWrapper(MonitorBase):
    def __init__(self):
        super().__init__()

    # stop 就是调用close，ws 更好理解
    def _do_stop(self):
        self._do_close()

    # 断开连接，主动关闭
    def close(self):
        self.stop()

    @abstractmethod
    def _do_close(self):
        pass

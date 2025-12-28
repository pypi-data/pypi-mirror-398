from binascii import Error

from kaq_quant_common.common.modules.limit_order_symbol_monitor import (
    LimitOrderSymbolMonitor,
)
from kaq_quant_common.common.monitor_group import MonitorGroup


class LimitOrderSymbolMonitorGroup(MonitorGroup):
    def __init__(self, exchange: str, default_symbols: list[str]):
        super().__init__()

        # 监听交易对变化
        symbol_monitor = LimitOrderSymbolMonitor(exchange=exchange, default_symbols=default_symbols)
        self._symbol_monitor = symbol_monitor
        # 用来创建监听器
        self._create_monitor_fun = None
        self._monitor_cls = None

    def set_create_monitor_fun(self, create_monitor_fun):
        self._create_monitor_fun = create_monitor_fun

    def set_monitor_cls(self, monitor_cls):
        self._monitor_cls = monitor_cls
        self._create_monitor_fun = lambda symbols: self._monitor_cls(symbols)

    def start(self, group_size=9):

        # 检查是否设置了创建监听器的函数
        if self._create_monitor_fun is None:
            raise Error("create_monitor_fun is not set")

        #
        symbol_monitor = self._symbol_monitor
        symbol_monitor.start()

        create_monitor_fun = self._create_monitor_fun

        def do_start_monitor(symbols: list[str]):
            # 先停止之前的
            self.stop_monitors(clear=True)

            # 创建新的 monitors
            monitors: list = []
            # 遍历交易对，拆分group_size个一组
            for i in range(0, len(symbols), group_size):
                sub_symbols = symbols[i : i + group_size]
                # 日志
                self._logger.info(f"创建监听器[{len(monitors)+1}]，监听交易对{sub_symbols}")
                # 创建监听器
                wsMonitor = create_monitor_fun(sub_symbols)
                monitors.append(wsMonitor)

            # 链接新的 monitors
            self.link(monitors=monitors, clear=False)

        # 监听器
        def on_symbol_change(symbols: list[str]):
            do_start_monitor(symbols=symbols)
            # self.stop()

        # 设置监听回调
        symbol_monitor.set_handler(on_symbol_change)

        # 订阅一次
        do_start_monitor(symbols=symbol_monitor.get_symbols())

        #
        super().start()

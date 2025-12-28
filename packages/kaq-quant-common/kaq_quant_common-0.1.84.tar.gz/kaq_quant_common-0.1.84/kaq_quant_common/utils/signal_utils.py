import signal
import sys

# 1. 为目标信号（例如 SIGINT，即 Ctrl+C 触发）维护一个处理函数列表
signal_handlers = []


# 2. 定义「总处理函数」：触发时依次执行列表中的所有处理逻辑
def total_handler(signalnum, frame):
    # 依次调用所有注册的处理函数
    for handler in signal_handlers:
        handler(signalnum, frame)


# 3. 注册「总处理函数」到目标信号（例如 SIGINT）
# SIGTERM：Dagster通常发送此信号进行终止
# SIGINT：对应Ctrl+C，用于本地测试
signal.signal(signal.SIGTERM, total_handler)
signal.signal(signal.SIGINT, total_handler)


def register_signal_handler(handler):
    signal_handlers.append(handler)

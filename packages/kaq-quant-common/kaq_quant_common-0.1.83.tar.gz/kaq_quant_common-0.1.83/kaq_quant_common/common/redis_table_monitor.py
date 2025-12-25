import threading
import time
from abc import abstractmethod

from kaq_quant_common.common.monitor_base import MonitorBase
from kaq_quant_common.resources.kaq_redis_resources import KaqQuantRedisRepository
from kaq_quant_common.utils import logger_utils

mutex = threading.Lock()


# redis表监听器
class RedisTableMonitor(MonitorBase):

    def __init__(self, table_name: str, interval=1):
        # 表名
        self._table_name = table_name
        # 执行间隔
        self._interval = interval
        # logger
        self._logger = logger_utils.get_logger(self)
        #
        super().__init__()

    # 这种监听器是辅助型的，而且会开启一个线程，主线程不需要阻塞
    def start(self):
        return super().start(False)

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ abstract methods
    def _do_init(self):
        # 初始化redis
        self._redis = self._init_redis()
        # 查询一次
        self._value = self._do_query()

    def _do_start(self):
        # 开启监听
        self._start_monitor()

    def _do_stop(self):
        # 停止
        self._stop_monitor()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    # 初始化redis
    def _init_redis(self) -> KaqQuantRedisRepository:
        """
        创建redis连接
        """
        redis_config = self._on_get_redis_config()
        host, port, passwd = redis_config["host"], redis_config["port"], redis_config["passwd"]
        return KaqQuantRedisRepository(host=host, port=port, password=passwd)

    # 开启订阅
    def _start_monitor(self):
        # 开启一条线程，定时执行redis查询
        self._ticker_thread_event = threading.Event()

        def query_redis():
            # 上次查询时间
            last_query_time = 0
            while True:
                # 检查是否需要退出
                if self._ticker_thread_event.is_set():
                    self._logger.info("ticker thread exit")
                    break

                # 当前时间
                current_time = time.time()
                # 如果上次请求时间距离当前时间不足，等待
                if current_time - last_query_time < self._interval:
                    time.sleep(0.1)
                    continue

                #
                last_query_time = time.time()

                # self._logger.debug('tick start')
                try:
                    value = self._do_query()

                    # 对比前后的数值
                    if not self._do_compare(value, self._value):
                        # 有变化
                        self._value = value
                        self._on_value_change(value)
                except Exception as e:
                    self._logger.error(f"redis query error: {e}")
                # self._logger.debug('tick finish')
                #
                time.sleep(0.1)

        # 开启线程
        self._ticker_thread = threading.Thread(target=query_redis)
        # 设置为守护线程
        self._ticker_thread.daemon = True
        self._ticker_thread.start()

    def _stop_monitor(self):
        if self._ticker_thread_event is not None:
            self._ticker_thread_event.set()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ 子类可以重写
    @abstractmethod
    def _do_query(self) -> str:
        # 默认是获取字符串
        str = self._redis.get(self._table_name)
        return str

    @abstractmethod
    def _do_compare(self, value1: any, value2: any) -> bool:
        # 默认认为是字符串
        return value1 == value2

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ abstract methods
    # 需要返回redis配置，包含host, port, passwd 添加类型提示
    @abstractmethod
    def _on_get_redis_config(self) -> dict:
        pass

    @abstractmethod
    def _on_value_change(self, value):
        pass

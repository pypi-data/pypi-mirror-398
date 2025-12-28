import threading
import traceback
from abc import abstractmethod

import dolphindb as ddb
import numpy as np
from kaq_quant_common.common.monitor_base import MonitorBase
from kaq_quant_common.utils import logger_utils

mutex = threading.Lock()


# ddb表订阅监听器
class DdbTableMonitor(MonitorBase):

    def __init__(self, table_name: str, action_name: str, batch_size=1000, filter=[]):
        # 表名
        self._table_name = table_name
        #
        self._action_name = action_name
        #
        self._batch_size = batch_size
        #
        self._filter = filter

        # logger
        self._logger = logger_utils.get_logger(self)
        #
        super().__init__()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ abstract methods
    def _do_init(self):
        # 初始化ddb
        self._init_ddb()

    def _do_start(self):
        # 开启ddb订阅
        self._start_subscribe()

    def _do_stop(self):
        # 关闭订阅
        self._stop_subscribe()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    # 初始化ddb
    def _init_ddb(self):
        '''
        创建ddb连接 && 添加ddb流数据表支持
        '''
        try:
            ddb_config = self._on_get_ddb_config()
            host, port, user, passwd = ddb_config['host'], ddb_config['port'], ddb_config['user'], ddb_config['passwd']
            mutex.acquire()
            self._session = ddb.session(enableASYNC=True)
            self._host = host
            self._port = port
            self._user = user
            self._passwd = passwd
            self._session.connect(host, port, user, passwd)
            self._session.enableStreaming()
        except Exception as e:
            self._logger.error(f'DdbTableMonitor._init_ddb error: {str(e)} - {str(traceback.format_exc())}')
        finally:
            mutex.release()

    # 开启订阅
    def _start_subscribe(self):
        '''
        订阅ddb表
        '''
        self._session.subscribe(
            self._host,
            self._port,
            self._handle,
            tableName=self._table_name,
            actionName=self._action_name,
            filter=np.array(self._filter),
            offset=-1,
            batchSize=self._batch_size,
            throttle=5,
            msgAsTable=True,
        )
        self._logger.info(f'开始订阅 {self._host}:{self._port} {self._table_name} - {self._action_name}')

    def _stop_subscribe(self):
        # TODO
        # script = f"""
        # existsSubscriptionTopic(,`{self._table_name},`{self._action_name})
        # """
        # exitsTopic = self._session.run(script)
        exitsTopic = True
        if exitsTopic is True:
            self._session.unsubscribe(self._host, self._port, self._table_name, self._action_name)
            self._logger.info(f'取消订阅 {self._table_name} - {self._action_name}')
        if not self._session.isClosed():
            self._session.close()

    # ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓ abstract methods
    # 需要返回ddb配置，包含host, port, user, passwd 添加类型提示
    @abstractmethod
    def _on_get_ddb_config(self, data) -> dict:
        pass

    @abstractmethod
    def _handle(self, data):
        pass

import os
import time
import dolphindb as ddb
from kaq_quant_common.utils import yml_utils
import pandas as pd
import threading
from kaq_quant_common.utils.logger_utils import get_logger
import traceback

mutex = threading.Lock()

class KaqQuantDdbStreamWriteRepository:
    '''
    定义 asof_join的级联方式, 合并数据到一起, 然后可以订阅判断
    '''
    def __init__(self, host, port, user, passwd):
        self.logger = get_logger(self)
        '''
        创建ddb连接 && 添加ddb流数据表支持
        '''
        try:
            mutex.acquire()
            self.session = ddb.session(enableASYNC=True)
            self.session.connect(host, port, user, passwd, tryReconnectNums=10, reconnect=True, keepAliveTime=1000, readTimeout=10, writeTimeout=5)
            self.session.enableStreaming(threadCount=5)
            # self.pool = ddb.DBConnectionPool(host, port, userid=user, password=passwd, loadBalance=True, reConnect=True, tryReconnectNums=5, sqlStd=SqlStd.MySQL)

            # 需要注意的是 fetchSize 取值不能小于 8192 （记录条数）
            self.size = 8192
        except Exception as e:
            self.logger.error(f'KaqQuantDdbStreamWriteRepository.__init__ is occured error: {str(e)} - {str(traceback.format_exc())}')
        finally:
            mutex.release()
        
    def save2stream(self, ddb_table_name: str, df : pd.DataFrame):
        '''
        调用此方法之前, 需要将dataframe中的字符串类型的值 ，添加引号
        '''
        # 遍历每列的数据类型
        for column, dtype in df.dtypes.items():
            if dtype == 'object' or dtype == 'str':
                df[column] = '\'' + df[column] + '\''
        for index, row in df.iterrows():
            script = f"insert into {ddb_table_name} values({', '.join(str(x) for x in row.values)})"
            try:
                self.session.run(script, clearMemory=True)
            except Exception as e:
                self.logger.error(f'KaqQuantDdbStreamWriteRepository.save2stream is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}')
                
    def build_insert_values_fast(self, df):
        dtypes = df.dtypes.tolist()
        # 提前确定哪些列需要加引号
        str_idx = {i for i, dt in enumerate(dtypes) if dt == object or dt == 'object' or dt == 'str'}
        # 转成 ndarray，减少 pandas 参与
        arr = df.to_numpy()
        rows = []
        for row in arr:
            parts = []
            for i, v in enumerate(row):
                if i in str_idx:
                    parts.append(f"'{v}'")   # 直接拼接最快
                else:
                    parts.append(str(v))
            rows.append("(" + ", ".join(parts) + ")")
        return rows            
    
    def save2stream_batch(self, ddb_table_name: str, df : pd.DataFrame):
        '''
        调用此方法之前, 需要将dataframe中的字符串类型的值 ，添加引号
        '''
        try:
            start1 = time.monotonic_ns()
            row = self.build_insert_values_fast(df)
            values = ', '.join(row)
            script = f"insert into {ddb_table_name} values {values}"
            start2 = time.monotonic_ns()
            self.session.run(script, clearMemory=True)
            end = time.monotonic_ns()
            if "KAQ_QUANT_LOG" in os.environ:
                diff = end - start2
                if diff > 1_000_000_0:  # 超过1毫秒
                    self.logger.warning(f'KaqQuantDdbStreamWriteRepository.save2stream cost time is only write : {end - start2} ns, save2stream_batch :{end - start1} ns, batch size is {len(df)}, tableName is {ddb_table_name}')
        except Exception as e:
            self.logger.error(f'KaqQuantDdbStreamWriteRepository.save2stream_batch is occured error: tableName is {ddb_table_name} - {str(e)} - {str(traceback.format_exc())}')


if __name__ == '__main__':
    host, port, user, passwd = yml_utils.get_ddb_info(os.getcwd())
    kaq = KaqQuantDdbStreamWriteRepository(host, port, user, passwd)
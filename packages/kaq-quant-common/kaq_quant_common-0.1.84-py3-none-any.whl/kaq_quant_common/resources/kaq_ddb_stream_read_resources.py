import os
import dolphindb as ddb
from kaq_quant_common.utils import yml_utils
import pandas as pd
import threading
from kaq_quant_common.utils.logger_utils import get_logger
import traceback

mutex = threading.Lock()

class KaqQuantDdbStreamReadRepository:
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
            # 程序读取的时候 同步读取即可, ddb的异步读取，可以使用订阅的方式来实现
            self.session = ddb.session(enableASYNC=False)
            self.session.setTimeout(3600)
            self.session.connect(host, port, user, passwd, keepAliveTime=240, reconnect=True, tryReconnectNums=10)
            self.session.enableStreaming()

            # 需要注意的是 fetchSize 取值不能小于 8192 （记录条数）
            self.size = 8192
        except Exception as e:
            self.logger.error(f'KaqQuantDdbStreamReadRepository.__init__ is occured error: {str(e)} - {str(traceback.format_exc())}')
        finally:
            mutex.release()

    def count(self, query: str) -> int:
        '''
        获取数量, 再去获取总数据
        sql语句中必须返回的是 count 字段
        '''
        try:
            number_blocks = self.session.run(query, fetchSize=self.size)
            number = 0
            while number_blocks.hasNext():
                number = number_blocks.read()['count'][0]
            return number
        except Exception as e:
            self.logger.error(f'KaqQuantDdbStreamReadRepository.countStream is occured error: {str(e)} - {str(traceback.format_exc())}')
        return -1

    def cal_page(self, number: int):
        page = number / self.size
        if number % self.size > 0:
            page = page + 1
        return int(page)

    def query(self, query: str) -> pd.DataFrame:
        '''
        从流数据表中获取数据
        '''
        try:
            block = self.session.run(query, fetchSize=self.size)
            if block is None:
                return pd.DataFrame()
            big_df = pd.DataFrame()
            while block.hasNext():
                temp_df = block.read()
                big_df = pd.concat([big_df, temp_df])
            big_df = big_df.reset_index()
            return big_df
        except Exception as e:
            self.logger.error(f'KaqQuantDdbStreamReadRepository.getStreamQuery is occured error: {str(e)} - {str(traceback.format_exc())}')
        return pd.DataFrame()


if __name__ == '__main__':
    host, port, user, passwd = yml_utils.get_ddb_info(os.getcwd())
    kaq = KaqQuantDdbStreamReadRepository(host, port, user, passwd)
    # kaq.drop_streaming()
    count = kaq.countStream(f"select count(*) from kaq_binance_force_order_streaming where symbol == 'FIOUSDT'")
    df = kaq.getStreamQuery(query=f"select * from kaq_binance_force_order_streaming where symbol == 'FIOUSDT' order by create_time asc")
    print(df.head(5))
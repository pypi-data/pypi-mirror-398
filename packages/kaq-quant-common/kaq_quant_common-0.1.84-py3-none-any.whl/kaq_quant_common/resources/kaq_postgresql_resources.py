import os
from kaq_quant_common.utils import yml_utils
import pandas as pd
import threading
import psycopg2
from kaq_quant_common.utils.logger_utils import get_logger

mutex = threading.Lock()

class KaqQuantPostgreSqlRepository:
    '''
    timescaleDB的操作类
    '''
    def __init__(self, host, port, user, passwd, database, charset='utf8'):
        self.logger = get_logger(self)
        # 数据库连接参数
        conn_params = {
            "dbname": database,
            "user": user,
            "password": passwd,
            "host": host,
            "port": port
        }
        # 创建写入引擎数据库连接池
        # 建立连接和游标
        self.conn = psycopg2.connect(**conn_params)
        self.cur = self.conn.cursor()
        
        # 关闭游标和连接
        # self.cur.close()
        # self.conn.close()

    def fetch_data(self, query):
        '''
        查询操作，输入查询语句
        '''
        try:
            # 执行查询
            self.cur.execute(query)
            rows = self.cur.fetchall()
            field_names = [desc[0] for desc in self.cur.description]
            df = pd.DataFrame(rows, columns=field_names)
            return df
        except Exception as e:
            self.logger.error(f'【posgresql-fetch_data】异常, {query} - {str(e)}')
        return pd.DataFrame()


def main(query='select * from footprint_candle limit 5;'):
        
    # alias
    host, port, user, passwd, database, charset  = yml_utils.get_posgresql_info(os.getcwd())
    kaqBtcTimeScaleDbRepository = KaqQuantPostgreSqlRepository(host, port, user, passwd, database)
    df = kaqBtcTimeScaleDbRepository.fetch_data(query)
    print(df.head(3))

if __name__ == '__main__':
    main()
